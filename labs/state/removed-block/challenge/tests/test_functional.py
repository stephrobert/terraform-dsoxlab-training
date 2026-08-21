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

from conftest import exiger_workdir, show_json, terraform, workdir_lab

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
        "`random_pet.jeton` a disparu du state. Il devait rester gere du debut "
        "a la fin : c'est lui qui nomme les fichiers du lot."
    )


def _changements(cwd: Path, nom: str) -> dict[str, list[str]]:
    """Actions non `no-op` d'un plan enregistre, par adresse."""
    plan = terraform("plan", "-input=false", "-no-color", f"-out={nom}", cwd=cwd)
    if plan.returncode != 0:
        pytest.fail(f"`terraform plan -out` a echoue.\n{plan.stderr[-900:]}")
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
            "`terraform init` a echoue. Un `???` restant dans un bloc `removed` "
            f"que vous avez decommente ?\n{init.stderr[-1200:]}"
        )
    if "values" not in show_json(WORKDIR):
        pytest.fail(
            "Le state est vide : le projet n'a jamais ete applique. Lancez "
            "`terraform apply` dans challenge/work pour poser l'etat de depart "
            "(huit adresses, sept fichiers), puis menez la migration."
        )
    yield WORKDIR


# --------------------------------------------------------------------------
# 1. Ce qui reste gere, et rien d'autre
# --------------------------------------------------------------------------

def test_le_state_ne_porte_plus_que_les_quatre_adresses(applied: Path) -> None:
    presentes = _adresses_managees(applied)
    assert presentes == GEREES, (
        f"Le state porte {sorted(presentes)}.\nAttendu exactement "
        f"{sorted(GEREES)}. Les rapports et le cache devaient en sortir "
        "entierement, les bacs seulement pour la cle `beta`."
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
    assert not manquants, (
        f"Ces fichiers ont ete DETRUITS : {sorted(manquants)}. Un bloc `removed` "
        "ne conserve l'objet reel que s'il porte `destroy = false` : sans lui, le "
        "defaut est de detruire."
    )
    assert not contenus_faux, (
        f"Ces fichiers ont ete RECREES au lieu d'etre conserves : "
        f"{sorted(contenus_faux)}. Leur contenu ne porte plus le jeton "
        f"`{jeton}` du state, donc ils ne sont plus ceux de l'apply d'origine."
    )


# --------------------------------------------------------------------------
# 3. Detruit : le meme bloc, sans le garde-fou
# --------------------------------------------------------------------------

def test_le_cache_a_bien_ete_detruit(applied: Path) -> None:
    assert not (applied / DETRUIT).exists(), (
        f"{DETRUIT} est encore la. Le cache devait disparaitre AVEC son fichier, "
        "ce qu'un bloc `removed` fait par defaut, sans `destroy = false`."
    )
    assert "local_file.cache" not in _adresses_managees(applied), (
        "`local_file.cache` est encore gere : son bloc `removed` n'a pas ete "
        "applique."
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
    assert not concernant_bacs, (
        f"Le plan porte encore des changements sur les bacs : {concernant_bacs}. "
        "Un `create` signifie que la cle retiree du state est toujours dans le "
        "`for_each` : Terraform la recreerait et ecraserait le fichier legue."
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
    assert changements == {"local_file.journaux": ["forget"]}, (
        f"Le plan devait porter exactement un changement, `forget` sur "
        f"`local_file.journaux`. Releve : {changements}. Un plan vide signifie "
        "que le bloc `removed` manque ou a deja ete applique, un `delete` qu'il "
        "lui manque `destroy = false`."
    )
    plan = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color",
                     cwd=applied)
    assert plan.returncode == 2, (
        f"plan -detailed-exitcode rend {plan.returncode}, attendu 2 : la "
        "migration des journaux doit rester EN ATTENTE. C'est tout l'interet du "
        "bloc `removed` : l'operation se relit en revue avant d'etre jouee."
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
    assert plan.returncode != 0, (
        "Un `removed` visant une cle d'instance devrait echouer. Si ce test "
        "passe, Terraform a change et le lab doit etre revu."
    )
    assert "Resource instance keys not allowed" in plan.stderr, (
        "L'erreur attendue est `Resource instance keys not allowed`. Relevee :\n"
        f"{plan.stderr[-800:]}"
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
    assert actions == attendu, (
        "Sans `destroy = false`, le bloc `removed` devrait planifier une "
        f"DESTRUCTION par instance. Actions relevees : {actions}"
    )
