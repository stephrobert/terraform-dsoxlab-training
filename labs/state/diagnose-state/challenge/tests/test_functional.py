"""Tests fonctionnels du lab « diagnostiquer une derive, adopter une orpheline ».

Deux capacites distinctes, prouvees par l'etat structure : reconnaitre une
DERIVE (l'objet reel a change hors Terraform) et ADOPTER une ressource
preexistante sans que sa valeur soit regeneree.

Faits verifies sur Terraform 1.15.4 (local + random, hors ligne) :
- apres une modification faite a la main, un plan ORDINAIRE range l'information
  dans `resource_drift` ET dans `resource_changes` ; un plan `-refresh-only`
  laisse `resource_changes` VIDE. C'est cette absence qui prouve qu'un plan
  refresh-only a bien ete enregistre ;
- les deux `-detailed-exitcode` ne disent pas la meme chose : apres un
  `apply -refresh-only`, le refresh-only rend 0 (le state colle au reel) alors
  que le plan ordinaire rend encore 2 (le reel ne colle pas au code) ;
- un bloc `import` dont les attributs declares divergent de l'objet adopte
  planifie `['delete', 'create']` avec `replace_paths: [['length']]`, sous
  l'avertissement `Warning: this will destroy the imported resource`. Applique,
  il REGENERE la valeur : le jeton herite est perdu, et le plan suivant rend
  pourtant `No changes` ;
- avec `lifecycle { ignore_changes = all }`, la meme adoption conserve la valeur
  exacte.
"""

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "state-diagnose-state"

PLAN_DERIVE = "derive-plan.json"
JETON = "token-herite.txt"
NOTE = "data/note.txt"
ADRESSES = {"local_file.note", "random_string.legacy"}


def _ressources(cwd: Path) -> dict[str, dict]:
    racine = show_json(cwd)["values"]["root_module"]
    return {
        r["address"]: r
        for r in racine.get("resources", [])
        if r.get("mode") == "managed"
    }


def _plan_json(cwd: Path, fichier: str) -> dict:
    """Document de plan, tel que `terraform show -json <plan>` le rend."""
    chemin = cwd / fichier
    try:
        document = json.loads(chemin.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erreur:
        pytest.fail(
            f"{fichier} n'est pas un JSON valide ({erreur}). Il s'obtient par "
            "`terraform show -json derive.tfplan > " + fichier + "`."
        )
    if "format_version" not in document:
        pytest.fail(
            f"{fichier} ne ressemble pas a un document de plan : le champ "
            "`format_version` manque. C'est la sortie de "
            "`terraform show -json <plan enregistre>` qui est attendue."
        )
    return document


@pytest.fixture(scope="module")
def projet() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(
            "`terraform init` a echoue. Un `???` restant dans adoption.tf ?"
            f"\n{init.stderr[-1200:]}"
        )
    if "values" not in show_json(WORKDIR):
        pytest.fail(
            "Le state est vide : le projet n'a jamais ete applique. Lancez "
            "`terraform apply` pour construire l'etat de reference, puis "
            "simulez la derive avant de la diagnostiquer."
        )
    yield WORKDIR


# --------------------------------------------------------------------------
# 1. La derive a ete prouvee par un plan refresh-only ENREGISTRE
# --------------------------------------------------------------------------

def test_un_plan_refresh_only_a_ete_enregistre(projet: Path) -> None:
    chemin = projet / PLAN_DERIVE
    assert chemin.is_file(), (
        f"{PLAN_DERIVE} est absent. La derive se prouve par un plan ENREGISTRE, "
        "puis converti : `terraform plan -refresh-only -out=derive.tfplan` suivi "
        f"de `terraform show -json derive.tfplan > {PLAN_DERIVE}`."
    )
    plan = _plan_json(projet, PLAN_DERIVE)

    derives = {c["address"] for c in plan.get("resource_drift", [])}
    assert "local_file.note" in derives, (
        f"Le plan ne signale aucune derive sur `local_file.note`. Releve : "
        f"{sorted(derives) or 'aucune'}. Un plan pris AVANT la modification du "
        "fichier, ou APRES sa reconciliation, ne montre rien."
    )

    changements = [
        c["address"]
        for c in plan.get("resource_changes", [])
        if c["change"]["actions"] != ["no-op"]
    ]
    assert not changements, (
        f"`resource_changes` porte {changements}, il devrait etre vide. C'est la "
        "signature d'un plan ORDINAIRE : il range la meme derive dans "
        "`resource_changes`, la ou `-refresh-only` ne decrit que le rattrapage "
        "du state."
    )


# --------------------------------------------------------------------------
# 2. Le state a ete reconcilie, et le fichier remis en conformite
# --------------------------------------------------------------------------

def test_le_state_colle_au_reel(projet: Path) -> None:
    plan = terraform("plan", "-refresh-only", "-input=false",
                     "-detailed-exitcode", "-no-color", cwd=projet)
    assert plan.returncode == 0, (
        f"`plan -refresh-only -detailed-exitcode` rend {plan.returncode}, "
        "attendu 0. Le state decrit encore autre chose que la realite : il "
        "reste une derive a reconcilier par `terraform apply -refresh-only`."
    )


def test_la_note_a_retrouve_le_contenu_declare(projet: Path) -> None:
    ressources = _ressources(projet)
    assert "local_file.note" in ressources, (
        f"`local_file.note` a disparu du state. Adresses gerees : "
        f"{sorted(ressources)}"
    )
    attendu = ressources["local_file.note"]["values"]["content"]
    reel = (projet / NOTE).read_text(encoding="utf-8")
    assert reel == attendu, (
        f"{NOTE} contient {reel!r}, alors que le state lui prete {attendu!r}. "
        "Reconcilier le state ne suffit pas : il faut ensuite remettre l'objet "
        "reel en conformite avec le code."
    )


# --------------------------------------------------------------------------
# 3. Le jeton herite a ete adopte, pas regenere
# --------------------------------------------------------------------------

def test_le_jeton_herite_a_ete_adopte_tel_quel(projet: Path) -> None:
    ressources = _ressources(projet)
    assert "random_string.legacy" in ressources, (
        "`random_string.legacy` n'est pas dans le state. Le bloc `import` "
        "a-t-il ete decommente et complete, puis applique ? Adresses gerees : "
        f"{sorted(ressources)}"
    )
    attendu = (projet / JETON).read_text(encoding="utf-8").strip()
    obtenu = ressources["random_string.legacy"]["values"]["result"]
    assert obtenu == attendu, (
        f"Le jeton du state vaut {obtenu!r}, attendu {attendu!r}. Terraform l'a "
        "REGENERE au lieu de l'adopter : quand les attributs declares divergent "
        "de l'objet importe, le plan annonce `must be replaced` avec "
        "`Warning: this will destroy the imported resource`. Le jeton herite "
        "est connu d'un service tiers, il ne se regenere pas."
    )


def test_le_state_porte_exactement_les_deux_adresses(projet: Path) -> None:
    presentes = set(_ressources(projet))
    assert presentes == ADRESSES, (
        f"Le state porte {sorted(presentes)}, attendu {sorted(ADRESSES)}."
    )


# --------------------------------------------------------------------------
# 4. Les deux codes de sortie a zero, en meme temps
# --------------------------------------------------------------------------

def test_plus_aucun_changement_en_attente(projet: Path) -> None:
    plan = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color",
                     cwd=projet)
    assert plan.returncode == 0, (
        f"`plan -detailed-exitcode` rend {plan.returncode}, attendu 0. Un code 2 "
        "signale un changement en attente : soit l'objet reel diverge encore du "
        "code, soit l'adoption laisse un remplacement a jouer, ce que le bloc "
        f"`lifecycle` doit empecher.\n{plan.stdout[-900:]}"
    )
