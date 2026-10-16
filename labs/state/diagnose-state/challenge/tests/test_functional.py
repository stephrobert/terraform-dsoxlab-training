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

from conftest import exiger_workdir, message, show_json, terraform, workdir_lab

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
            message(
            en=f"{fichier} is not valid JSON ({erreur}). It is obtained with "
            "`terraform show -json derive.tfplan > " + fichier + "`.",
            fr=f"{fichier} n'est pas un JSON valide ({erreur}). Il s'obtient par "
            "`terraform show -json derive.tfplan > " + fichier + "`.",
        )
        )
    if "format_version" not in document:
        pytest.fail(
            message(
            en=f"{fichier} does not look like a plan document: the "
            "`format_version` field is missing. The output of "
            "`terraform show -json <saved plan>` is what is expected.",
            fr=f"{fichier} ne ressemble pas à un document de plan : le champ "
            "`format_version` manque. C'est la sortie de "
            "`terraform show -json <plan enregistré>` qui est attendue.",
        )
        )
    return document


@pytest.fixture(scope="module")
def projet() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(
            message(
            en="`terraform init` failed. A leftover `???` in adoption.tf?"
            f"\n{init.stderr[-1200:]}",
            fr="`terraform init` a échoué. Un `???` restant dans adoption.tf ?"
            f"\n{init.stderr[-1200:]}",
        )
        )
    if "values" not in show_json(WORKDIR):
        pytest.fail(
            message(
            en="The state is empty: the project was never applied. Run "
            "`terraform apply` to build the reference state, then "
            "simulate the drift before diagnosing it.",
            fr="Le state est vide : le projet n'a jamais été appliqué. Lancez "
            "`terraform apply` pour construire l'état de référence, puis "
            "simulez la dérive avant de la diagnostiquer.",
        )
        )
    yield WORKDIR


# --------------------------------------------------------------------------
# 1. La derive a ete prouvee par un plan refresh-only ENREGISTRE
# --------------------------------------------------------------------------

def test_un_plan_refresh_only_a_ete_enregistre(projet: Path) -> None:
    chemin = projet / PLAN_DERIVE
    assert chemin.is_file(), message(
        en=f"{PLAN_DERIVE} is missing. The drift is proven by a SAVED plan, "
        "then converted: `terraform plan -refresh-only -out=derive.tfplan` followed "
        f"by `terraform show -json derive.tfplan > {PLAN_DERIVE}`.",
        fr=f"{PLAN_DERIVE} est absent. La dérive se prouve par un plan ENREGISTRÉ, "
        "puis converti : `terraform plan -refresh-only -out=derive.tfplan` suivi "
        f"de `terraform show -json derive.tfplan > {PLAN_DERIVE}`.",
    )
    plan = _plan_json(projet, PLAN_DERIVE)

    derives = {c["address"] for c in plan.get("resource_drift", [])}
    assert "local_file.note" in derives, message(
        en=f"The plan reports no drift on `local_file.note`. Recorded: "
        f"{sorted(derives) or 'none'}. A plan taken BEFORE the file was "
        "modified, or AFTER it was reconciled, shows nothing.",
        fr=f"Le plan ne signale aucune dérive sur `local_file.note`. Relevé : "
        f"{sorted(derives) or 'aucune'}. Un plan pris AVANT la modification du "
        "fichier, ou APRÈS sa réconciliation, ne montre rien.",
    )

    changements = [
        c["address"]
        for c in plan.get("resource_changes", [])
        if c["change"]["actions"] != ["no-op"]
    ]
    assert not changements, message(
        en=f"`resource_changes` carries {changements}, it should be empty. That is the "
        "signature of an ORDINARY plan: it puts the same drift into "
        "`resource_changes`, where `-refresh-only` only describes the state's "
        "catch-up.",
        fr=f"`resource_changes` porte {changements}, il devrait être vide. C'est la "
        "signature d'un plan ORDINAIRE : il range la même dérive dans "
        "`resource_changes`, là où `-refresh-only` ne décrit que le rattrapage "
        "du state.",
    )


# --------------------------------------------------------------------------
# 2. Le state a ete reconcilie, et le fichier remis en conformite
# --------------------------------------------------------------------------

def test_le_state_colle_au_reel(projet: Path) -> None:
    plan = terraform("plan", "-refresh-only", "-input=false",
                     "-detailed-exitcode", "-no-color", cwd=projet)
    assert plan.returncode == 0, message(
        en=f"`plan -refresh-only -detailed-exitcode` returns {plan.returncode}, "
        "expected 0. The state still describes something other than reality: a "
        "drift remains to be reconciled with `terraform apply -refresh-only`.",
        fr=f"`plan -refresh-only -detailed-exitcode` rend {plan.returncode}, "
        "attendu 0. Le state décrit encore autre chose que la réalité : il "
        "reste une dérive à réconcilier par `terraform apply -refresh-only`.",
    )


def test_la_note_a_retrouve_le_contenu_declare(projet: Path) -> None:
    ressources = _ressources(projet)
    assert "local_file.note" in ressources, message(
        en=f"`local_file.note` has disappeared from the state. Managed addresses: "
        f"{sorted(ressources)}",
        fr=f"`local_file.note` a disparu du state. Adresses gérées : "
        f"{sorted(ressources)}",
    )
    attendu = ressources["local_file.note"]["values"]["content"]
    reel = (projet / NOTE).read_text(encoding="utf-8")
    assert reel == attendu, message(
        en=f"{NOTE} contains {reel!r}, while the state attributes {attendu!r} to it. "
        "Reconciling the state is not enough: the real object must then be brought "
        "back into line with the code.",
        fr=f"{NOTE} contient {reel!r}, alors que le state lui prête {attendu!r}. "
        "Réconcilier le state ne suffit pas : il faut ensuite remettre l'objet "
        "réel en conformité avec le code.",
    )


# --------------------------------------------------------------------------
# 3. Le jeton herite a ete adopte, pas regenere
# --------------------------------------------------------------------------

def test_le_jeton_herite_a_ete_adopte_tel_quel(projet: Path) -> None:
    ressources = _ressources(projet)
    assert "random_string.legacy" in ressources, message(
        en="`random_string.legacy` is not in the state. Was the `import` block "
        "uncommented and completed, then applied? Managed addresses: "
        f"{sorted(ressources)}",
        fr="`random_string.legacy` n'est pas dans le state. Le bloc `import` "
        "a-t-il été décommenté et complété, puis appliqué ? Adresses gérées : "
        f"{sorted(ressources)}",
    )
    attendu = (projet / JETON).read_text(encoding="utf-8").strip()
    obtenu = ressources["random_string.legacy"]["values"]["result"]
    assert obtenu == attendu, message(
        en=f"The state's token is {obtenu!r}, expected {attendu!r}. Terraform "
        "REGENERATED it instead of adopting it: when the declared attributes diverge "
        "from the imported object, the plan announces `must be replaced` with "
        "`Warning: this will destroy the imported resource`. The inherited token "
        "is known to a third-party service, it is not regenerated.",
        fr=f"Le jeton du state vaut {obtenu!r}, attendu {attendu!r}. Terraform l'a "
        "RÉGÉNÉRÉ au lieu de l'adopter : quand les attributs déclarés divergent "
        "de l'objet importé, le plan annonce `must be replaced` avec "
        "`Warning: this will destroy the imported resource`. Le jeton hérité "
        "est connu d'un service tiers, il ne se régénère pas.",
    )


def test_le_state_porte_exactement_les_deux_adresses(projet: Path) -> None:
    presentes = set(_ressources(projet))
    assert presentes == ADRESSES, message(
        en=f"The state carries {sorted(presentes)}, expected {sorted(ADRESSES)}.",
        fr=f"Le state porte {sorted(presentes)}, attendu {sorted(ADRESSES)}.",
    )


# --------------------------------------------------------------------------
# 4. Les deux codes de sortie a zero, en meme temps
# --------------------------------------------------------------------------

def test_plus_aucun_changement_en_attente(projet: Path) -> None:
    plan = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color",
                     cwd=projet)
    assert plan.returncode == 0, message(
        en=f"`plan -detailed-exitcode` returns {plan.returncode}, expected 0. A code 2 "
        "signals a pending change: either the real object still diverges from the "
        "code, or the adoption leaves a replacement to play, which the "
        f"`lifecycle` block must prevent.\n{plan.stdout[-900:]}",
        fr=f"`plan -detailed-exitcode` rend {plan.returncode}, attendu 0. Un code 2 "
        "signale un changement en attente : soit l'objet réel diverge encore du "
        "code, soit l'adoption laisse un remplacement à jouer, ce que le bloc "
        f"`lifecycle` doit empêcher.\n{plan.stdout[-900:]}",
    )
