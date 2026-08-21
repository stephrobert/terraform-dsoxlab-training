"""Tests fonctionnels du lab « le bloc lifecycle décide de l'ordre, pas vous ».

Principe : on ne lit jamais les `.tf` de l'apprenant. On pilote Terraform et on
n'exploite que le **plan en JSON** (`resource_changes[].actions`,
`action_reason`), le tableau `checks` et des **codes retour**.

Le tableau `actions` est la seule preuve non ambiguë du sens de
`create_before_destroy` : `["delete", "create"]` est l'ordre par défaut,
`["create", "delete"]` prouve que la règle est active. Une sortie humaine
recopiée ne prouverait rien.

Faits vérifiés sur Terraform v1.15.4 avant écriture de ces tests : la
propagation de `create_before_destroy` descend vers les **dépendances** ;
retirer un bloc `resource` contourne `prevent_destroy` ; `ignore_changes`
compare la configuration à l'état ; `action_reason` vaut `replace_by_triggers`.
"""

import json
import shutil
from pathlib import Path

import pytest

from conftest import exiger_workdir, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "write-code-lifecycle"


def plan_json(*args: str, cwd: Path | None = None) -> dict:
    """Rend le plan en JSON. Rend {} si le plan échoue."""
    rep = cwd or WORKDIR
    p = terraform("plan", "-input=false", "-no-color", "-out=tf.plan", *args, cwd=rep)
    if p.returncode != 0:
        return {}
    return json.loads(terraform("show", "-json", "tf.plan", cwd=rep).stdout)


def actions(plan: dict, adresse: str) -> list[str] | None:
    for rc in plan.get("resource_changes", []):
        if rc["address"] == adresse:
            return rc["change"]["actions"]
    return None


def raison(plan: dict, adresse: str) -> str | None:
    for rc in plan.get("resource_changes", []):
        if rc["address"] == adresse:
            return rc.get("action_reason")
    return None


@pytest.fixture(scope="module")
def applied() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(f"`terraform init` a échoué.\n{init.stderr[-1200:]}")
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(
            "`terraform apply` a échoué. La configuration comporte encore des "
            "expressions incomplètes, ou une règle bloquante a été posée sur la "
            "mauvaise ressource.\n"
            f"{app.stderr[-1500:]}"
        )
    return WORKDIR


@pytest.fixture(scope="module")
def plan_revision(applied: Path) -> dict:
    """Le plan de référence : une révision qui bouge, donc un remplacement."""
    return plan_json("-var", "revision=2")


# --------------------------------------------------------------------------
# 1. create_before_destroy : l'ordre, et le sens de sa propagation
# --------------------------------------------------------------------------

def test_le_fichier_applicatif_est_cree_avant_d_etre_detruit(plan_revision: dict) -> None:
    a = actions(plan_revision, "local_file.app")
    assert a is not None, (
        "`local_file.app` n'apparaît pas dans le plan pour `revision=2`. Son nom "
        "de fichier doit dépendre de `random_pet.version.id`."
    )
    assert a == ["create", "delete"], (
        f"actions = {a}. L'ordre par défaut `['delete', 'create']` signifie qu'il "
        "existe une fenêtre où le fichier n'existe plus. `create_before_destroy` "
        "l'inverse. Vérifiez que la règle est bien posée sur `local_file.app`."
    )


def test_la_propagation_descend_vers_la_dependance(plan_revision: dict) -> None:
    """Le piège central : la règle se propage vers les DÉPENDANCES, pas les dépendants.

    `local_file.app` dépend de `random_pet.version`. Poser `create_before_destroy`
    sur `app` l'applique implicitement à `version`, sans que l'apprenant n'écrive
    rien dessus. Poser la règle sur `version` au lieu de `app` ne produit pas
    l'inverse : ce test et le précédent échouent ensemble, ce qui désigne l'erreur.
    """
    a = actions(plan_revision, "random_pet.version")
    assert a == ["create", "delete"], (
        f"actions = {a} sur `random_pet.version`, alors qu'aucune règle ne doit y "
        "être écrite. Terraform propage `create_before_destroy` vers les "
        "dépendances de la ressource qui le porte. Si vous voyez "
        "`['delete', 'create']`, la règle est posée au mauvais endroit."
    )


# --------------------------------------------------------------------------
# 2. prevent_destroy : ce qu'il protège, et ce qu'il ne protège pas
# --------------------------------------------------------------------------

def test_la_donnee_critique_refuse_le_plan_de_destruction(applied: Path) -> None:
    p = terraform("plan", "-input=false", "-destroy", "-no-color", cwd=applied)
    assert p.returncode != 0, (
        "`terraform plan -destroy` a réussi. La donnée critique n'est protégée "
        "par aucune règle."
    )
    assert "local_file.donnees" in (p.stdout + p.stderr), (
        "Le plan échoue, mais sans désigner `local_file.donnees` : la protection "
        "porte sur la mauvaise ressource."
    )


def test_retirer_le_bloc_resource_contourne_la_protection(applied: Path, tmp_path: Path) -> None:
    """La limite documentée, et la seule raison de ne pas se fier à prevent_destroy.

    « Except for create_before_destroy, Terraform does not explicitly record a
    resource's lifecycle rule to state. As a result, Terraform destroys the
    actual infrastructure during an apply operation if you remove the resource's
    configuration, even if prevent_destroy is enabled. »

    Ce test ne juge pas le travail de l'apprenant : il matérialise le fait.
    """
    copie = tmp_path / "ampute"
    shutil.copytree(applied, copie)
    source = (copie / "main.tf").read_text(encoding="utf-8")
    debut = source.find('resource "local_file" "donnees"')
    if debut == -1:
        pytest.skip("`local_file.donnees` n'est pas déclaré dans main.tf.")
    suite = source.find('resource "', debut + 10)
    (copie / "main.tf").write_text(
        source[:debut] + (source[suite:] if suite != -1 else ""), encoding="utf-8"
    )

    p = terraform("plan", "-input=false", "-destroy", "-no-color", cwd=copie)
    assert p.returncode == 0, (
        "La destruction reste refusée après suppression du bloc `resource`. Ce "
        "n'est pas le comportement documenté de Terraform.\n"
        f"{(p.stdout + p.stderr)[-1200:]}"
    )


# --------------------------------------------------------------------------
# 3. ignore_changes : une portée, pas un interrupteur général
# --------------------------------------------------------------------------

def test_le_journal_ignore_un_changement_de_contenu(applied: Path) -> None:
    a = actions(plan_json("-var", "message=v2"), "local_file.journal")
    assert a == ["no-op"], (
        f"actions = {a}. Un changement de `content` venu de la configuration doit "
        "être absorbé. Attention : `ignore_changes` compare la configuration à "
        "l'état, il n'absorbe pas une modification du fichier sur le disque."
    )


def test_le_journal_planifie_toujours_un_changement_de_permissions(applied: Path) -> None:
    """Contrôle négatif du précédent : `ignore_changes = all` le ferait échouer."""
    a = actions(plan_json("-var", "permissions=0600"), "local_file.journal")
    assert a is not None and a != ["no-op"], (
        f"actions = {a}. Les permissions doivent rester sous contrôle. Si le plan "
        "est vide, vous avez écrit `ignore_changes = all`, qui aveugle la "
        "ressource entière au lieu du seul attribut visé."
    )


# --------------------------------------------------------------------------
# 4. replace_triggered_by : n'accepte qu'une ressource gérée
# --------------------------------------------------------------------------

def test_le_marqueur_est_remplace_quand_la_revision_bouge(plan_revision: dict) -> None:
    a = actions(plan_revision, "local_file.marqueur")
    assert a == ["delete", "create"], (
        f"actions = {a}. `local_file.marqueur` ne dépend d'aucun attribut qui "
        "bouge : seul un `replace_triggered_by` peut le faire remplacer. Rappel : "
        "`replace_triggered_by = [var.revision]` ne compile pas, Terraform répond "
        "« Only resources, count.index, and each.key may be used in "
        "replace_triggered_by ». Il faut une ressource gérée qui porte la valeur."
    )


def test_le_remplacement_du_marqueur_vient_bien_d_un_declencheur(plan_revision: dict) -> None:
    r = raison(plan_revision, "local_file.marqueur")
    assert r == "replace_by_triggers", (
        f"action_reason = {r!r}. Le marqueur est bien remplacé, mais pas pour la "
        "bonne raison : `replace_by_triggers` est la seule valeur qui prouve un "
        "`replace_triggered_by`. Une autre valeur signifie que le remplacement "
        "vient d'un changement d'attribut, donc d'une dépendance déguisée."
    )


# --------------------------------------------------------------------------
# 5. precondition et postcondition, au bon niveau
# --------------------------------------------------------------------------

def test_un_environnement_hors_enumere_est_refuse_au_plan(applied: Path) -> None:
    p = terraform("plan", "-input=false", "-no-color", "-var", "env=bidon", cwd=applied)
    assert p.returncode != 0, (
        "`env=bidon` produit un plan valide. Aucune condition ne filtre la valeur."
    )


def test_un_environnement_valide_passe(applied: Path) -> None:
    """Contrôle positif indispensable : sans lui, une configuration entièrement
    cassée ferait passer le test précédent pour la mauvaise raison."""
    p = terraform("plan", "-input=false", "-no-color", "-var", "env=staging", cwd=applied)
    assert p.returncode == 0, (
        "`env=staging` est refusé alors qu'il fait partie des valeurs admises. La "
        f"condition est trop stricte.\n{(p.stdout + p.stderr)[-1200:]}"
    )


def test_les_conditions_vivent_dans_la_ressource_pas_dans_la_variable(applied: Path) -> None:
    """`checks[].address.kind` prouve où le mécanisme est réellement écrit.

    Un bloc `validation` sur la variable sortirait en `kind: var`. L'énoncé
    demande une `precondition`, qui sort en `kind: resource`.
    """
    kinds = {c["address"].get("kind") for c in show_json(applied).get("checks", [])}
    assert "resource" in kinds, (
        f"kinds observés = {kinds or 'aucun'}. Aucune `precondition` ni "
        "`postcondition` n'est enregistrée sur une ressource. Un bloc `validation` "
        "posé sur la variable `env` sortirait en `kind: var` : il filtrerait bien "
        "la valeur, mais ne répond pas à l'énoncé."
    )


# --------------------------------------------------------------------------
# 6. Idempotence
# --------------------------------------------------------------------------

def test_la_configuration_est_stable_apres_apply(applied: Path) -> None:
    p = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=applied)
    assert p.returncode == 0, (
        f"`terraform plan -detailed-exitcode` rend {p.returncode} (2 = des "
        "changements restent planifiés). Un apply doit converger."
    )
