"""Tests fonctionnels du lab « cesser de gerer sans detruire ».

Deux voies pour sortir une ressource du state, et un enjeu commun : aucune des
deux ne doit toucher le fichier sur le disque. Les tests verifient donc les deux
cotes, le state ET le disque, puis prouvent par execution le defaut qui coute
cher : dans un bloc `removed`, ne pas ecrire `destroy = false` DETRUIT l'objet.

Faits verifies sur Terraform 1.15.4 (local + random, hors ligne) :
- `terraform state rm` repond `Removed <adresse>` puis `Successfully removed 1
  resource instance(s).`, et le fichier reste sur le disque ;
- une ressource retiree du state mais toujours dans le code devient orpheline :
  le plan suivant veut la RECREER (`actions == ["create"]`) ;
- un bloc `removed` avec `destroy = false` produit l'action **`forget`**, un plan
  « 0 to add, 0 to change, 0 to destroy », et l'objet survit ;
- un bloc `removed` SANS `lifecycle` est accepte sans le moindre avertissement,
  planifie `delete` et DETRUIT le fichier a l'apply. Le defaut est donc la
  destruction, ce qui rend `destroy = false` indispensable.
"""

import json
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "state-terraform-state-rm"

RETIREES = {"local_file.rapport", "local_file.archive"}
TEMOINS = {"local_file.conserve", "random_pet.identifiant"}
FICHIERS_SURVIVANTS = {
    "rapport.txt": "rapport-origine\n",
    "archive.txt": "archive-origine\n",
}


def _adresses_managees(cwd: Path) -> set[str]:
    racine = show_json(cwd)["values"]["root_module"]
    return {
        r["address"] for r in racine.get("resources", []) if r.get("mode") == "managed"
    }


def _actions_du_plan(cwd: Path, nom: str) -> dict[str, list[str]]:
    """Enregistre un plan et rend, par adresse, la liste de ses actions."""
    plan = terraform("plan", "-input=false", "-no-color", f"-out={nom}", cwd=cwd)
    if plan.returncode != 0:
        pytest.fail(f"`terraform plan -out` a echoue.\n{plan.stderr[-900:]}")
    montre = terraform("show", "-json", nom, cwd=cwd)
    montre.check_returncode()
    return {
        c["address"]: c["change"]["actions"]
        for c in json.loads(montre.stdout).get("resource_changes", [])
    }


def _sans_le_bloc(contenu: str, nom: str) -> str:
    """Retire du code le bloc `resource "local_file" "<nom>"`."""
    debut = contenu.index(f'resource "local_file" "{nom}"')
    fin = contenu.index("}\n", contenu.index("content", debut)) + 2
    return contenu[:debut] + contenu[fin:]


@pytest.fixture(scope="module")
def applied() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(
            "`terraform init` a echoue. Un `???` restant dans le bloc `removed` "
            f"que vous avez decommente ?\n{init.stderr[-1200:]}"
        )
    if "values" not in show_json(WORKDIR):
        pytest.fail(
            "Le state est vide : le projet n'a jamais ete applique. Lancez "
            "`terraform apply` dans challenge/work pour poser l'etat de depart "
            "(quatre ressources gerees), puis faites les deux retraits."
        )
    yield WORKDIR


# --------------------------------------------------------------------------
# 1. Les deux cibles ont quitte le state, les temoins y sont restes
# --------------------------------------------------------------------------

def test_les_deux_cibles_ont_quitte_le_state(applied: Path) -> None:
    presentes = _adresses_managees(applied)
    restantes = RETIREES & presentes
    assert not restantes, (
        f"Ces ressources sont encore gerees : {sorted(restantes)}. Elles "
        "devaient sortir du state, l'une par `state rm`, l'autre par le bloc "
        "`removed`."
    )
    manquants = TEMOINS - presentes
    assert not manquants, (
        f"Ces temoins ont disparu du state : {sorted(manquants)}. Ils devaient "
        f"rester geres. State actuel : {sorted(presentes)}"
    )
    assert presentes == TEMOINS, (
        f"Le state porte {sorted(presentes)}, attendu exactement {sorted(TEMOINS)}."
    )


# --------------------------------------------------------------------------
# 2. Aucun fichier n'a ete detruit : c'est tout l'enjeu
# --------------------------------------------------------------------------

def test_les_fichiers_ont_survecu(applied: Path) -> None:
    manquants, contenus_faux = [], []
    for nom, attendu in FICHIERS_SURVIVANTS.items():
        chemin = applied / nom
        if not chemin.is_file():
            manquants.append(nom)
        elif chemin.read_text(encoding="utf-8") != attendu:
            contenus_faux.append(nom)
    assert not manquants, (
        f"Ces fichiers ont ete DETRUITS : {manquants}. Sortir une ressource du "
        "state ne doit pas toucher a l'objet reel. Pour le bloc `removed`, c'est "
        "`destroy = false` qui l'empeche : sans lui, le defaut est de detruire."
    )
    assert not contenus_faux, (
        f"Ces fichiers ont ete recrees au lieu d'etre conserves : {contenus_faux}."
    )


# --------------------------------------------------------------------------
# 3. Le code et le state convergent
# --------------------------------------------------------------------------

def test_plus_aucun_changement_en_attente(applied: Path) -> None:
    plan = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color",
                     cwd=applied)
    assert plan.returncode == 0, (
        f"plan -detailed-exitcode rend {plan.returncode}, attendu 0. Un code 2 "
        "signale soit un bloc `resource` oublie dans le code (la ressource "
        "retiree du state serait orpheline, et Terraform voudrait la RECREER), "
        f"soit un bloc `removed` jamais applique.\n{plan.stdout[-1000:]}"
    )


# --------------------------------------------------------------------------
# 4. Le piege de la voie imperative, prouve par execution
# --------------------------------------------------------------------------

def test_une_ressource_orpheline_serait_recreee(applied: Path, tmp_path: Path) -> None:
    """`state rm` sans nettoyer le code laisse une orpheline que le plan recree."""
    copie = tmp_path / "orpheline"
    shutil.copytree(applied, copie)
    (copie / "orpheline.tf").write_text(
        'resource "local_file" "rapport" {\n'
        '  filename = "${path.root}/rapport.txt"\n'
        '  content  = "rapport-origine\\n"\n'
        "}\n",
        encoding="utf-8",
    )
    actions = _actions_du_plan(copie, "orpheline.tfplan")
    assert actions.get("local_file.rapport") == ["create"], (
        "Une ressource presente dans le code mais absente du state devrait etre "
        f"planifiee en `create`. Actions relevees : {actions}"
    )


# --------------------------------------------------------------------------
# 5. Le piege de la voie declarative : sans destroy = false, ca detruit
# --------------------------------------------------------------------------

def test_sans_destroy_false_le_bloc_removed_detruit(applied: Path, tmp_path: Path) -> None:
    """Le defaut d'un bloc `removed` est de DETRUIRE, et rien ne l'annonce."""
    copie = tmp_path / "sans-garde-fou"
    shutil.copytree(applied, copie)
    main = copie / "main.tf"
    main.write_text(
        _sans_le_bloc(main.read_text(encoding="utf-8"), "conserve"), encoding="utf-8"
    )
    (copie / "cobaye.tf").write_text(
        "removed {\n  from = local_file.conserve\n}\n", encoding="utf-8"
    )
    actions = _actions_du_plan(copie, "cobaye.tfplan")
    assert actions.get("local_file.conserve") == ["delete"], (
        "Sans `destroy = false`, le bloc `removed` devrait planifier une "
        f"DESTRUCTION. Actions relevees : {actions}. Si ce test echoue, le "
        "comportement par defaut de Terraform a change et le lab doit etre revu."
    )


def test_avec_destroy_false_l_action_est_forget(applied: Path, tmp_path: Path) -> None:
    """Le meme cobaye, avec le garde-fou : l'action devient `forget`."""
    copie = tmp_path / "avec-garde-fou"
    shutil.copytree(applied, copie)
    main = copie / "main.tf"
    main.write_text(
        _sans_le_bloc(main.read_text(encoding="utf-8"), "conserve"), encoding="utf-8"
    )
    (copie / "cobaye.tf").write_text(
        "removed {\n  from = local_file.conserve\n\n"
        "  lifecycle {\n    destroy = false\n  }\n}\n",
        encoding="utf-8",
    )
    actions = _actions_du_plan(copie, "cobaye.tfplan")
    assert actions.get("local_file.conserve") == ["forget"], (
        "Avec `destroy = false`, l'action attendue est `forget` (oublier sans "
        f"detruire). Actions relevees : {actions}"
    )
