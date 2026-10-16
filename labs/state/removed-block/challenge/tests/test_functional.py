"""Tests fonctionnels du lab « leguer une infra sans la detruire ».

Le bloc `removed` sert deux intentions opposees avec presque la meme syntaxe :
leguer un objet (`destroy = false`) ou le supprimer (le defaut). Les tests
verifient donc les deux cotes, le state ET le disque, et prouvent par execution
la frontiere du mecanisme : une cle d'instance y est refusee.

Faits verifies sur Terraform 1.15.4 (local + random, hors ligne) :
- un `removed` sur une ressource en `for_each` avec `destroy = false` rend une
  action `forget` PAR INSTANCE, et les fichiers survivent ;
- le meme bloc sans `lifecycle` rend `delete` et supprime l'objet. Les deux
  coexistent dans un seul plan : `Plan: 0 to add, 0 to change, 1 to destroy.`,
  les `forget` n'etant pas comptes dans le compteur de destructions ;
- `from = local_file.bacs["beta"]` est refuse par `Resource instance keys not
  allowed` : cette granularite n'existe que via `terraform state rm` ;
- apres un `state rm` sur une instance, tant que la cle reste dans le `for_each`
  le plan la RECREE (`actions == ["create"]`) et ecrase le fichier legue ;
- un bloc `removed` ecrit mais non applique laisse `plan -detailed-exitcode` en
  code 2, avec un unique changement `forget` : la migration est prevue, relisible
  en revue, et pas encore jouee.
"""

import json
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, message, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "state-removed-block"

GEREES = {
    "random_pet.jeton",
    'local_file.bacs["alpha"]',
    'local_file.bacs["gamma"]',
    "local_file.journaux",
}
LEGUES = {
    "rapport-mensuel.txt": "rapport mensuel",
    "rapport-annuel.txt": "rapport annuel",
    "bac-alpha.txt": "bac alpha",
    "bac-beta.txt": "bac beta",
    "bac-gamma.txt": "bac gamma",
    "journaux.txt": "journaux",
}
DETRUIT = "cache.txt"


def _ressources(cwd: Path) -> list[dict]:
    racine = show_json(cwd)["values"]["root_module"]
    return [r for r in racine.get("resources", []) if r.get("mode") == "managed"]


def _adresses_managees(cwd: Path) -> set[str]:
    return {r["address"] for r in _ressources(cwd)}


def _jeton(cwd: Path) -> str:
    """Identifiant de `random_pet.jeton`, lu dans le state et jamais en dur."""
    for ressource in _ressources(cwd):
        if ressource["address"] == "random_pet.jeton":
            return str(ressource["values"]["id"])
    pytest.fail(
        message(
        en="`random_pet.jeton` has disappeared from the state. It was supposed to stay managed from "
        "beginning to end: it is what names the batch's files.",
        fr="`random_pet.jeton` a disparu du state. Il devait rester géré du début "
        "à la fin : c'est lui qui nomme les fichiers du lot.",
    )
    )


def _changements(cwd: Path, nom: str) -> dict[str, list[str]]:
    """Actions non `no-op` d'un plan enregistre, par adresse."""
    plan = terraform("plan", "-input=false", "-no-color", f"-out={nom}", cwd=cwd)
    if plan.returncode != 0:
        pytest.fail(message(
            en=f"`terraform plan -out` failed.\n{plan.stderr[-900:]}",
            fr=f"`terraform plan -out` a échoué.\n{plan.stderr[-900:]}",
        ))
    montre = terraform("show", "-json", nom, cwd=cwd)
    montre.check_returncode()
    return {
        c["address"]: c["change"]["actions"]
        for c in json.loads(montre.stdout).get("resource_changes", [])
        if c["change"]["actions"] != ["no-op"]
    }


@pytest.fixture(scope="module")
def applied() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(
            message(
            en="`terraform init` failed. A leftover `???` in a `removed` block "
            f"you uncommented?\n{init.stderr[-1200:]}",
            fr="`terraform init` a échoué. Un `???` restant dans un bloc `removed` "
            f"que vous avez décommenté ?\n{init.stderr[-1200:]}",
        )
        )
    if "values" not in show_json(WORKDIR):
        pytest.fail(
            message(
            en="The state is empty: the project was never applied. Run "
            "`terraform apply` in challenge/work to lay down the starting state "
            "(eight addresses, seven files), then carry out the migration.",
            fr="Le state est vide : le projet n'a jamais été appliqué. Lancez "
            "`terraform apply` dans challenge/work pour poser l'état de départ "
            "(huit adresses, sept fichiers), puis menez la migration.",
        )
        )
    yield WORKDIR


# --------------------------------------------------------------------------
# 1. Ce qui reste gere, et rien d'autre
# --------------------------------------------------------------------------

def test_le_state_ne_porte_plus_que_les_quatre_adresses(applied: Path) -> None:
    presentes = _adresses_managees(applied)
    assert presentes == GEREES, message(
        en=f"The state carries {sorted(presentes)}.\nExactly "
        f"{sorted(GEREES)} expected. The reports and the cache were supposed to come out "
        "entirely, the bins only for the `beta` key.",
        fr=f"Le state porte {sorted(presentes)}.\nAttendu exactement "
        f"{sorted(GEREES)}. Les rapports et le cache devaient en sortir "
        "entièrement, les bacs seulement pour la clé `beta`.",
    )


# --------------------------------------------------------------------------
# 2. Legues : sortis du state, intacts sur le disque
# --------------------------------------------------------------------------

def test_les_fichiers_legues_ont_survecu(applied: Path) -> None:
    jeton = _jeton(applied)
    manquants, contenus_faux = [], []
    for nom, prefixe in LEGUES.items():
        chemin = applied / nom
        if not chemin.is_file():
            manquants.append(nom)
            continue
        attendu = f"{prefixe} - {jeton}\n"
        if chemin.read_text(encoding="utf-8") != attendu:
            contenus_faux.append(nom)
    assert not manquants, message(
        en=f"These files were DESTROYED: {sorted(manquants)}. A `removed` block "
        "only keeps the real object if it carries `destroy = false`: without it, the "
        "default is to destroy.",
        fr=f"Ces fichiers ont été DÉTRUITS : {sorted(manquants)}. Un bloc `removed` "
        "ne conserve l'objet réel que s'il porte `destroy = false` : sans lui, le "
        "défaut est de détruire.",
    )
    assert not contenus_faux, message(
        en=f"These files were RECREATED instead of being kept: "
        f"{sorted(contenus_faux)}. Their content no longer carries the state's "
        f"`{jeton}` token, so they are no longer those of the original apply.",
        fr=f"Ces fichiers ont été RECRÉÉS au lieu d'être conservés : "
        f"{sorted(contenus_faux)}. Leur contenu ne porte plus le jeton "
        f"`{jeton}` du state, donc ils ne sont plus ceux de l'apply d'origine.",
    )


# --------------------------------------------------------------------------
# 3. Detruit : le meme bloc, sans le garde-fou
# --------------------------------------------------------------------------

def test_le_cache_a_bien_ete_detruit(applied: Path) -> None:
    assert not (applied / DETRUIT).exists(), message(
        en=f"{DETRUIT} is still there. The cache was supposed to disappear WITH its file, "
        "which a `removed` block does by default, without `destroy = false`.",
        fr=f"{DETRUIT} est encore là. Le cache devait disparaître AVEC son fichier, "
        "ce qu'un bloc `removed` fait par défaut, sans `destroy = false`.",
    )
    assert "local_file.cache" not in _adresses_managees(applied), message(
        en="`local_file.cache` is still managed: its `removed` block was not "
        "applied.",
        fr="`local_file.cache` est encore géré : son bloc `removed` n'a pas été "
        "appliqué.",
    )


# --------------------------------------------------------------------------
# 4. Le for_each a suivi le retrait de l'instance
# --------------------------------------------------------------------------

def test_le_for_each_des_bacs_a_ete_aligne(applied: Path, tmp_path: Path) -> None:
    """Sans alignement, le plan recree l'instance sortie et ecrase le fichier."""
    copie = tmp_path / "bacs"
    shutil.copytree(applied, copie)
    concernant_bacs = {
        adresse: actions
        for adresse, actions in _changements(copie, "bacs.tfplan").items()
        if adresse.startswith("local_file.bacs")
    }
    assert not concernant_bacs, message(
        en=f"The plan still carries changes on the bins: {concernant_bacs}. "
        "A `create` means that the key removed from the state is still in the "
        "`for_each`: Terraform would recreate it and overwrite the inherited file.",
        fr=f"Le plan porte encore des changements sur les bacs : {concernant_bacs}. "
        "Un `create` signifie que la clé retirée du state est toujours dans le "
        "`for_each` : Terraform la recréerait et écraserait le fichier légué.",
    )


# --------------------------------------------------------------------------
# 5. La migration des journaux est ecrite, pas jouee
# --------------------------------------------------------------------------

def test_la_migration_des_journaux_est_preparee_non_appliquee(
    applied: Path, tmp_path: Path
) -> None:
    copie = tmp_path / "journaux"
    shutil.copytree(applied, copie)
    changements = _changements(copie, "journaux.tfplan")
    assert changements == {"local_file.journaux": ["forget"]}, message(
        en=f"The plan was supposed to carry exactly one change, `forget` on "
        f"`local_file.journaux`. Recorded: {changements}. An empty plan means "
        "that the `removed` block is missing or has already been applied, a `delete` that "
        "it lacks `destroy = false`.",
        fr=f"Le plan devait porter exactement un changement, `forget` sur "
        f"`local_file.journaux`. Relevé : {changements}. Un plan vide signifie "
        "que le bloc `removed` manque ou a déjà été appliqué, un `delete` qu'il "
        "lui manque `destroy = false`.",
    )
    plan = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color",
                     cwd=applied)
    assert plan.returncode == 2, message(
        en=f"plan -detailed-exitcode returns {plan.returncode}, expected 2: the "
        "migration of the journals must stay PENDING. That is the whole point of the "
        "`removed` block: the operation is reviewed before being played.",
        fr=f"plan -detailed-exitcode rend {plan.returncode}, attendu 2 : la "
        "migration des journaux doit rester EN ATTENTE. C'est tout l'intérêt du "
        "bloc `removed` : l'opération se relit en revue avant d'être jouée.",
    )


# --------------------------------------------------------------------------
# 6. La frontiere du mecanisme, prouvee par execution
# --------------------------------------------------------------------------

def test_une_cle_d_instance_est_refusee_par_le_bloc_removed(
    applied: Path, tmp_path: Path
) -> None:
    """C'est pourquoi la sortie d'un seul bac passe par `terraform state rm`."""
    copie = tmp_path / "cle-instance"
    shutil.copytree(applied, copie)
    (copie / "cobaye.tf").write_text(
        'removed {\n  from = local_file.bacs["alpha"]\n\n'
        "  lifecycle {\n    destroy = false\n  }\n}\n",
        encoding="utf-8",
    )
    plan = terraform("plan", "-input=false", "-no-color", cwd=copie)
    assert plan.returncode != 0, message(
        en="A `removed` targeting an instance key should fail. If this test "
        "passes, Terraform has changed and the lab must be revised.",
        fr="Un `removed` visant une clé d'instance devrait échouer. Si ce test "
        "passe, Terraform a changé et le lab doit être revu.",
    )
    assert "Resource instance keys not allowed" in plan.stderr, message(
        en="The expected error is `Resource instance keys not allowed`. Recorded:\n"
        f"{plan.stderr[-800:]}",
        fr="L'erreur attendue est `Resource instance keys not allowed`. Relevée :\n"
        f"{plan.stderr[-800:]}",
    )


def test_sans_destroy_false_le_bloc_removed_detruit(
    applied: Path, tmp_path: Path
) -> None:
    """Le defaut du bloc, verifie sur les bacs restants et dans une copie."""
    copie = tmp_path / "sans-garde-fou"
    shutil.copytree(applied, copie)
    main = copie / "main.tf"
    contenu = main.read_text(encoding="utf-8")
    debut = contenu.index('resource "local_file" "bacs"')
    fin = contenu.index("}\n", contenu.index("content", debut)) + 2
    main.write_text(contenu[:debut] + contenu[fin:], encoding="utf-8")
    (copie / "cobaye.tf").write_text(
        "removed {\n  from = local_file.bacs\n}\n", encoding="utf-8"
    )
    # Le `forget` en attente sur les journaux fait partie de l'etat attendu :
    # on ne regarde donc que les bacs, cible du cobaye.
    actions = {
        adresse: liste
        for adresse, liste in _changements(copie, "cobaye.tfplan").items()
        if adresse.startswith("local_file.bacs")
    }
    attendu = {
        'local_file.bacs["alpha"]': ["delete"],
        'local_file.bacs["gamma"]': ["delete"],
    }
    assert actions == attendu, message(
        en="Without `destroy = false`, the `removed` block should plan a "
        f"DESTRUCTION per instance. Actions recorded: {actions}",
        fr="Sans `destroy = false`, le bloc `removed` devrait planifier une "
        f"DESTRUCTION par instance. Actions relevées : {actions}",
    )
