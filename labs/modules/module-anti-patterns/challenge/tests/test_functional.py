"""Tests fonctionnels du lab « refactorer sans rien detruire ».

L'anti-pattern traite ici n'est pas une faute de style : c'est le copier-coller
qui interdit toute reutilisation, et le refactoring qui, mal fait, DETRUIT ce qui
tournait. Les tests comparent donc les identifiants du state d'arrivee a ceux du
state de depart, livre en fixture.

Faits verifies sur Terraform 1.15.4, hors ligne, provider `local` :
- deplacer une ressource change son ADRESSE, et Terraform ne le devine pas : sans
  bloc `moved`, le plan propose une destruction suivie d'une creation ;
- avec les blocs `moved`, l'identifiant du state est CONSERVE, et le plan suivant
  n'annonce plus aucun changement ;
- un `moved` ne corrige QUE des adresses : ni une variable non typee, ni une
  configuration de provider, ni une ressource geree changee en source de donnees.
"""

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "modules-module-anti-patterns"

PROJET = "projet"
ETIQUETTES = ("nord", "sud")

# Jetons du state de depart, livre en fixture : ce sont eux qui doivent survivre
# au refactoring. Un `random_pet` est REGENERE des qu'il est detruit, contrairement
# a l'id d'un `local_file`, qui n'est qu'un hachage de son contenu : c'est donc lui
# qui distingue un deplacement d'une destruction suivie d'une recreation.
JETONS_DE_DEPART = {
    "nord": "becoming-gull",
    "sud": "stirring-porpoise",
}


def _projet(racine: Path) -> Path:
    chemin = racine / PROJET
    if not chemin.is_dir():
        pytest.fail(f"Le repertoire {PROJET}/ est absent de challenge/work.")
    return chemin


def _etat(racine: Path) -> dict:
    montre = terraform("show", "-json", cwd=_projet(racine))
    montre.check_returncode()
    return json.loads(montre.stdout)


def _ressources(racine: Path) -> dict[str, dict]:
    """Toutes les ressources du state, racine et modules enfants confondus."""
    etat = _etat(racine)["values"]["root_module"]
    trouvees = {r["address"]: r for r in etat.get("resources", [])}
    for enfant in etat.get("child_modules", []):
        for ressource in enfant.get("resources", []):
            trouvees[ressource["address"]] = ressource
    return trouvees


def _plan(racine: Path) -> dict:
    projet = _projet(racine)
    plan = terraform("plan", "-input=false", "-no-color", "-out=analyse.tfplan",
                     cwd=projet)
    if plan.returncode != 0:
        pytest.fail(f"`terraform plan` a echoue.\n{plan.stderr[-1100:]}")
    montre = terraform("show", "-json", "analyse.tfplan", cwd=projet)
    montre.check_returncode()
    return json.loads(montre.stdout)


@pytest.fixture(scope="module")
def racine() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=_projet(WORKDIR))
    if init.returncode != 0:
        pytest.fail(f"`terraform init` a echoue.\n{init.stderr[-1100:]}")
    yield WORKDIR


@pytest.fixture(scope="module")
def refactore(racine: Path) -> Iterator[Path]:
    """Le refactoring a eu lieu : sans lui, ne rien detruire ne prouve rien.

    Un `challenge/work` intact satisfait deja « aucune destruction planifiee » et
    « la sortie n'a pas change » : c'est justement l'etat de depart. Ces tests
    n'ont de sens qu'une fois les ressources passees dans un module.
    """
    dans_un_module = [
        adresse for adresse in _ressources(racine) if adresse.startswith("module.")
    ]
    if not dans_un_module:
        pytest.fail(
            "Aucune ressource du state ne vit dans un module : le refactoring "
            "n'a pas eu lieu, et conserver les identifiants ne prouve donc rien."
        )
    yield racine


# --------------------------------------------------------------------------
# 1. Le copier-colle a disparu au profit d'un module appele deux fois
# --------------------------------------------------------------------------

def test_la_ressource_vit_dans_un_module(racine: Path) -> None:
    adresses = sorted(_ressources(racine))
    assert adresses, "Le state ne contient aucune ressource."
    restees = [a for a in adresses if not a.startswith("module.")]
    assert not restees, (
        f"{restees} sont encore declarees a la racine du projet. La ressource "
        "doit vivre dans un module, ecrite UNE seule fois."
    )
    assert len(adresses) == 2 * len(ETIQUETTES), (
        f"Le state contient {adresses} : attendu la plaque ET son jeton pour "
        f"chacune des {len(ETIQUETTES)} etiquettes."
    )


def test_un_seul_appel_produit_les_deux_plaques(racine: Path) -> None:
    appels = _plan(racine)["configuration"]["root_module"].get("module_calls", {})
    assert len(appels) == 1, (
        f"Le projet declare {sorted(appels)} : un SEUL bloc `module` doit "
        "produire les deux plaques. Deux appels recopies, c'est le meme "
        "copier-coller qu'avant, un etage plus bas."
    )
    nom, appel = next(iter(appels.items()))
    references = {
        ref
        for expression in appel.get("expressions", {}).values()
        for ref in expression.get("references", [])
    }
    assert any(r.startswith(("each.", "count.")) for r in references), (
        f"L'appel `{nom}` ne reference ni `each` ni `count` : references "
        f"trouvees {sorted(references)}."
    )


# --------------------------------------------------------------------------
# 2. Rien n'a ete detruit : les identifiants ont survecu
# --------------------------------------------------------------------------

def test_les_jetons_du_state_ont_survecu(refactore: Path) -> None:
    """La preuve du refactoring : meme objet, autre adresse."""
    valeurs = {
        str(r["values"].get("id"))
        for r in _ressources(refactore).values()
        if r.get("type") == "random_pet"
    }
    assert valeurs, (
        "Aucun `random_pet` dans le state : le module doit porter le jeton, "
        "comme le projet le faisait."
    )
    for etiquette, jeton in JETONS_DE_DEPART.items():
        assert jeton in valeurs, (
            f"Le jeton de la plaque `{etiquette}` ({jeton}) n'est plus dans le "
            f"state, qui porte {sorted(valeurs)}. La ressource a ete DETRUITE "
            "puis recreee : un deplacement d'adresse se declare, il ne se devine "
            "pas."
        )


def test_le_plan_ne_propose_plus_rien(refactore: Path) -> None:
    plan = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color",
                     cwd=_projet(refactore))
    assert plan.returncode == 0, (
        f"plan -detailed-exitcode rend {plan.returncode}, attendu 0. Un "
        "refactoring reussi ne laisse aucun changement en attente."
        f"\n{plan.stdout[-800:]}"
    )


def test_aucune_destruction_n_est_planifiee(refactore: Path) -> None:
    changements = _plan(refactore).get("resource_changes", [])
    fautifs = {
        c["address"]: c["change"]["actions"]
        for c in changements
        if set(c["change"]["actions"]) & {"delete", "create"}
    }
    assert not fautifs, (
        f"Le plan prevoit encore {fautifs}. Les deux fichiers existent deja : "
        "les recreer n'est pas un refactoring."
    )


# --------------------------------------------------------------------------
# 3. L'interface du module est typee, et la sortie n'a pas bouge
# --------------------------------------------------------------------------

def test_l_interface_du_module_est_documentee(racine: Path) -> None:
    """Le JSON du plan expose la `description` de chaque variable et sortie.

    Il n'expose pas leur `type` : le typage se verifie donc a l'usage, pas ici.
    Ce qu'on controle est l'autre moitie du contrat, celle que la Standard Module
    Structure impose : « All variables and outputs should have one or two
    sentence descriptions. »
    """
    appel = next(
        iter(_plan(racine)["configuration"]["root_module"]["module_calls"].values())
    )
    variables = appel["module"].get("variables", {})
    sorties = appel["module"].get("outputs", {})
    assert variables, "Le module ne declare aucune variable."
    assert sorties, "Le module ne declare aucune sortie."

    muettes = [
        nom
        for nom, declaration in {**variables, **sorties}.items()
        if not (declaration.get("description") or "").strip()
    ]
    assert not muettes, (
        f"{sorted(muettes)} n'ont pas de `description`. C'est la seule "
        "documentation qu'un appelant lit avant d'employer le module, et la "
        "seule que l'outillage sache extraire."
    )


def test_la_sortie_du_projet_n_a_pas_change(refactore: Path) -> None:
    chemins = _etat(refactore)["values"]["outputs"]["chemins"]["value"]
    assert sorted(chemins) == sorted(ETIQUETTES), (
        f"La sortie `chemins` porte {sorted(chemins)}, attendu "
        f"{sorted(ETIQUETTES)} : son contrat ne devait pas bouger."
    )
    for etiquette, chemin in chemins.items():
        assert chemin.endswith(f"plaques/{etiquette}.txt"), (
            f"La plaque `{etiquette}` pointe {chemin!r} : le refactoring ne "
            "devait pas deplacer les fichiers."
        )


# --------------------------------------------------------------------------
# 4. L'arbre reste plat
# --------------------------------------------------------------------------

def test_l_arbre_des_modules_reste_plat(racine: Path) -> None:
    appel = next(
        iter(_plan(racine)["configuration"]["root_module"]["module_calls"].values())
    )
    imbriques = appel["module"].get("module_calls", {})
    assert not imbriques, (
        f"Le module appelle lui-meme {sorted(imbriques)}. La documentation est "
        "nette : « we strongly recommend keeping the module tree flat, with only "
        "one level of child modules »."
    )
