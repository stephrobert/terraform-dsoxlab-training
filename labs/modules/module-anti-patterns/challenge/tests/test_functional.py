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

from conftest import exiger_workdir, message, terraform, workdir_lab

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
        pytest.fail(message(
            en=f"The {PROJET}/ directory is missing from challenge/work.",
            fr=f"Le répertoire {PROJET}/ est absent de challenge/work.",
        ))
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
        pytest.fail(message(
            en=f"`terraform plan` failed.\n{plan.stderr[-1100:]}",
            fr=f"`terraform plan` a échoué.\n{plan.stderr[-1100:]}",
        ))
    montre = terraform("show", "-json", "analyse.tfplan", cwd=projet)
    montre.check_returncode()
    return json.loads(montre.stdout)


@pytest.fixture(scope="module")
def racine() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=_projet(WORKDIR))
    if init.returncode != 0:
        pytest.fail(message(
            en=f"`terraform init` failed.\n{init.stderr[-1100:]}",
            fr=f"`terraform init` a échoué.\n{init.stderr[-1100:]}",
        ))
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
            message(
            en="No resource in the state lives inside a module: the refactoring "
            "did not happen, so keeping the identifiers proves nothing.",
            fr="Aucune ressource du state ne vit dans un module : le refactoring "
            "n'a pas eu lieu, et conserver les identifiants ne prouve donc rien.",
        )
        )
    yield racine


# --------------------------------------------------------------------------
# 1. Le copier-colle a disparu au profit d'un module appele deux fois
# --------------------------------------------------------------------------

def test_la_ressource_vit_dans_un_module(racine: Path) -> None:
    adresses = sorted(_ressources(racine))
    assert adresses, message(
        en="The state contains no resource.",
        fr="Le state ne contient aucune ressource.",
    )
    restees = [a for a in adresses if not a.startswith("module.")]
    assert not restees, message(
        en=f"{restees} are still declared at the project's root. The resource "
        "must live inside a module, written ONCE only.",
        fr=f"{restees} sont encore déclarées à la racine du projet. La ressource "
        "doit vivre dans un module, écrite UNE seule fois.",
    )
    assert len(adresses) == 2 * len(ETIQUETTES), message(
        en=f"The state contains {adresses}: the plate AND its token were expected for "
        f"each of the {len(ETIQUETTES)} labels.",
        fr=f"Le state contient {adresses} : attendu la plaque ET son jeton pour "
        f"chacune des {len(ETIQUETTES)} étiquettes.",
    )


def test_un_seul_appel_produit_les_deux_plaques(racine: Path) -> None:
    appels = _plan(racine)["configuration"]["root_module"].get("module_calls", {})
    assert len(appels) == 1, message(
        en=f"The project declares {sorted(appels)}: a SINGLE `module` block must "
        "produce both plates. Two copied calls are the same "
        "copy-paste as before, one level down.",
        fr=f"Le projet déclare {sorted(appels)} : un SEUL bloc `module` doit "
        "produire les deux plaques. Deux appels recopiés, c'est le même "
        "copier-coller qu'avant, un étage plus bas.",
    )
    nom, appel = next(iter(appels.items()))
    references = {
        ref
        for expression in appel.get("expressions", {}).values()
        for ref in expression.get("references", [])
    }
    assert any(r.startswith(("each.", "count.")) for r in references), message(
        en=f"The call `{nom}` references neither `each` nor `count`: references "
        f"found {sorted(references)}.",
        fr=f"L'appel `{nom}` ne référence ni `each` ni `count` : références "
        f"trouvées {sorted(references)}.",
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
    assert valeurs, message(
        en="No `random_pet` in the state: the module must carry the token, "
        "as the project used to.",
        fr="Aucun `random_pet` dans le state : le module doit porter le jeton, "
        "comme le projet le faisait.",
    )
    for etiquette, jeton in JETONS_DE_DEPART.items():
        assert jeton in valeurs, message(
            en=f"The token of plate `{etiquette}` ({jeton}) is no longer in the "
            f"state, which carries {sorted(valeurs)}. The resource was DESTROYED "
            "and then recreated: a change of address is declared, it is not guessed.",
            fr=f"Le jeton de la plaque `{etiquette}` ({jeton}) n'est plus dans le "
            f"state, qui porte {sorted(valeurs)}. La ressource a été DÉTRUITE "
            "puis recréée : un déplacement d'adresse se déclare, il ne se devine "
            "pas.",
        )


def test_le_plan_ne_propose_plus_rien(refactore: Path) -> None:
    plan = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color",
                     cwd=_projet(refactore))
    assert plan.returncode == 0, message(
        en=f"plan -detailed-exitcode returns {plan.returncode}, expected 0. A "
        "successful refactoring leaves no pending change."
        f"\n{plan.stdout[-800:]}",
        fr=f"plan -detailed-exitcode rend {plan.returncode}, attendu 0. Un "
        "refactoring réussi ne laisse aucun changement en attente."
        f"\n{plan.stdout[-800:]}",
    )


def test_aucune_destruction_n_est_planifiee(refactore: Path) -> None:
    changements = _plan(refactore).get("resource_changes", [])
    fautifs = {
        c["address"]: c["change"]["actions"]
        for c in changements
        if set(c["change"]["actions"]) & {"delete", "create"}
    }
    assert not fautifs, message(
        en=f"The plan still intends {fautifs}. Both files already exist: "
        "recreating them is not a refactoring.",
        fr=f"Le plan prévoit encore {fautifs}. Les deux fichiers existent déjà : "
        "les recréer n'est pas un refactoring.",
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
    assert variables, message(
        en="The module declares no variable.",
        fr="Le module ne déclare aucune variable.",
    )
    assert sorties, message(
        en="The module declares no output.",
        fr="Le module ne déclare aucune sortie.",
    )

    muettes = [
        nom
        for nom, declaration in {**variables, **sorties}.items()
        if not (declaration.get("description") or "").strip()
    ]
    assert not muettes, message(
        en=f"{sorted(muettes)} have no `description`. It is the only "
        "documentation a caller reads before using the module, and the "
        "only one tooling can extract.",
        fr=f"{sorted(muettes)} n'ont pas de `description`. C'est la seule "
        "documentation qu'un appelant lit avant d'employer le module, et la "
        "seule que l'outillage sache extraire.",
    )


def test_la_sortie_du_projet_n_a_pas_change(refactore: Path) -> None:
    chemins = _etat(refactore)["values"]["outputs"]["chemins"]["value"]
    assert sorted(chemins) == sorted(ETIQUETTES), message(
        en=f"The `chemins` output carries {sorted(chemins)}, expected "
        f"{sorted(ETIQUETTES)}: its contract was not to move.",
        fr=f"La sortie `chemins` porte {sorted(chemins)}, attendu "
        f"{sorted(ETIQUETTES)} : son contrat ne devait pas bouger.",
    )
    for etiquette, chemin in chemins.items():
        assert chemin.endswith(f"plaques/{etiquette}.txt"), message(
            en=f"The plate `{etiquette}` points at {chemin!r}: the refactoring was "
            "not supposed to move the files.",
            fr=f"La plaque `{etiquette}` pointe {chemin!r} : le refactoring ne "
            "devait pas déplacer les fichiers.",
        )


# --------------------------------------------------------------------------
# 4. L'arbre reste plat
# --------------------------------------------------------------------------

def test_l_arbre_des_modules_reste_plat(racine: Path) -> None:
    appel = next(
        iter(_plan(racine)["configuration"]["root_module"]["module_calls"].values())
    )
    imbriques = appel["module"].get("module_calls", {})
    assert not imbriques, message(
        en=f"The module itself calls {sorted(imbriques)}. The documentation is "
        "clear: \"we strongly recommend keeping the module tree flat, with only "
        "one level of child modules\".",
        fr=f"Le module appelle lui-même {sorted(imbriques)}. La documentation est "
        "nette : « we strongly recommend keeping the module tree flat, with only "
        "one level of child modules ».",
    )
