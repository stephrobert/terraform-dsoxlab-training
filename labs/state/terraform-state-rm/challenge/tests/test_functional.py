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

from conftest import exiger_workdir, message, show_json, terraform, workdir_lab

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
        pytest.fail(message(
            en=f"`terraform plan -out` failed.\n{plan.stderr[-900:]}",
            fr=f"`terraform plan -out` a échoué.\n{plan.stderr[-900:]}",
        ))
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
            message(
            en="`terraform init` failed. A leftover `???` in the `removed` block "
            f"you uncommented?\n{init.stderr[-1200:]}",
            fr="`terraform init` a échoué. Un `???` restant dans le bloc `removed` "
            f"que vous avez décommenté ?\n{init.stderr[-1200:]}",
        )
        )
    if "values" not in show_json(WORKDIR):
        pytest.fail(
            message(
            en="The state is empty: the project was never applied. Run "
            "`terraform apply` in challenge/work to lay down the starting state "
            "(four managed resources), then do both removals.",
            fr="Le state est vide : le projet n'a jamais été appliqué. Lancez "
            "`terraform apply` dans challenge/work pour poser l'état de départ "
            "(quatre ressources gérées), puis faites les deux retraits.",
        )
        )
    yield WORKDIR


# --------------------------------------------------------------------------
# 1. Les deux cibles ont quitte le state, les temoins y sont restes
# --------------------------------------------------------------------------

def test_les_deux_cibles_ont_quitte_le_state(applied: Path) -> None:
    presentes = _adresses_managees(applied)
    restantes = RETIREES & presentes
    assert not restantes, message(
        en=f"These resources are still managed: {sorted(restantes)}. They "
        "were supposed to come out of the state, one through `state rm`, the other through the "
        "`removed` block.",
        fr=f"Ces ressources sont encore gérées : {sorted(restantes)}. Elles "
        "devaient sortir du state, l'une par `state rm`, l'autre par le bloc "
        "`removed`.",
    )
    manquants = TEMOINS - presentes
    assert not manquants, message(
        en=f"These witnesses have disappeared from the state: {sorted(manquants)}. They were supposed "
        f"to stay managed. Current state: {sorted(presentes)}",
        fr=f"Ces témoins ont disparu du state : {sorted(manquants)}. Ils devaient "
        f"rester gérés. State actuel : {sorted(presentes)}",
    )
    assert presentes == TEMOINS, message(
        en=f"The state carries {sorted(presentes)}, exactly {sorted(TEMOINS)} expected.",
        fr=f"Le state porte {sorted(presentes)}, attendu exactement {sorted(TEMOINS)}.",
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
    assert not manquants, message(
        en=f"These files were DESTROYED: {manquants}. Taking a resource out of the "
        "state must not touch the real object. For the `removed` block, it is "
        "`destroy = false` that prevents it: without it, the default is to destroy.",
        fr=f"Ces fichiers ont été DÉTRUITS : {manquants}. Sortir une ressource du "
        "state ne doit pas toucher à l'objet réel. Pour le bloc `removed`, c'est "
        "`destroy = false` qui l'empêche : sans lui, le défaut est de détruire.",
    )
    assert not contenus_faux, message(
        en=f"These files were recreated instead of being kept: {contenus_faux}.",
        fr=f"Ces fichiers ont été recréés au lieu d'être conservés : {contenus_faux}.",
    )


# --------------------------------------------------------------------------
# 3. Le code et le state convergent
# --------------------------------------------------------------------------

def test_plus_aucun_changement_en_attente(applied: Path) -> None:
    plan = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color",
                     cwd=applied)
    assert plan.returncode == 0, message(
        en=f"plan -detailed-exitcode returns {plan.returncode}, expected 0. A code 2 "
        "signals either a `resource` block forgotten in the code (the resource "
        "removed from the state would be orphaned, and Terraform would want to RECREATE it), "
        f"or a `removed` block never applied.\n{plan.stdout[-1000:]}",
        fr=f"plan -detailed-exitcode rend {plan.returncode}, attendu 0. Un code 2 "
        "signale soit un bloc `resource` oublié dans le code (la ressource "
        "retirée du state serait orpheline, et Terraform voudrait la RECRÉER), "
        f"soit un bloc `removed` jamais appliqué.\n{plan.stdout[-1000:]}",
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
    assert actions.get("local_file.rapport") == ["create"], message(
        en="A resource present in the code but absent from the state should be "
        f"planned as `create`. Actions recorded: {actions}",
        fr="Une ressource présente dans le code mais absente du state devrait être "
        f"planifiée en `create`. Actions relevées : {actions}",
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
    assert actions.get("local_file.conserve") == ["delete"], message(
        en="Without `destroy = false`, the `removed` block should plan a "
        f"DESTRUCTION. Actions recorded: {actions}. If this test fails, "
        "Terraform's default behaviour has changed and the lab must be revised.",
        fr="Sans `destroy = false`, le bloc `removed` devrait planifier une "
        f"DESTRUCTION. Actions relevées : {actions}. Si ce test échoue, le "
        "comportement par défaut de Terraform a changé et le lab doit être revu.",
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
    assert actions.get("local_file.conserve") == ["forget"], message(
        en="With `destroy = false`, the expected action is `forget` (forget without "
        f"destroying). Actions recorded: {actions}",
        fr="Avec `destroy = false`, l'action attendue est `forget` (oublier sans "
        f"détruire). Actions relevées : {actions}",
    )
