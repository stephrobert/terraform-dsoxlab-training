"""Tests fonctionnels du lab « publier et consommer des versions de module ».

Un module Git n'est pas versionne parce qu'on a ecrit `version` quelque part :
il l'est parce qu'une REFERENCE existe et qu'un consommateur pointe dessus. Les
tests lisent cette reference dans `.terraform/modules/modules.json`, ecrit par
Terraform a l'installation, et lisent le code REELLEMENT installe sous
`.terraform/modules/`, pas les fichiers de l'apprenant.

Faits verifies sur Terraform 1.15.4, depot Git local, hors ligne :
- une source Git n'a AUCUNE cle `Version` dans `modules.json` : cette cle est
  reservee aux modules de registre ;
- l'argument `version` a cote d'une source Git fait echouer l'init sur `Invalid
  registry module source address` ; un `modules.json` present prouve donc qu'il
  a ete retire ;
- un tag Git se DEPLACE (`git tag -f`) : seule une reference immuable, le SHA-1
  du commit, garantit le meme code d'un init a l'autre ;
- une version mineure reste consommable par une configuration ecrite pour la
  precedente, une version majeure ne l'est pas.

Ce lab se joue hors ligne : le depot de modules est local.
"""

import json
import re
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "modules-version-modules"

PROJETS = ("fige", "stable", "migre")
SHA1 = re.compile(r"^[0-9a-f]{40}$")


def _modules_json(projet: Path) -> dict[str, dict]:
    chemin = projet / ".terraform" / "modules" / "modules.json"
    if not chemin.is_file():
        pytest.fail(
            f"{projet.name}/.terraform/modules/modules.json est absent : "
            "`terraform init` n'a jamais abouti dans ce projet. Un `???` "
            "restant, un depot pas encore initialise, ou l'argument `version` "
            "encore present a cote d'une source Git ?"
        )
    document = json.loads(chemin.read_text(encoding="utf-8"))
    return {m["Key"]: m for m in document["Modules"] if m["Key"]}


def _reference(projet: Path) -> str:
    """Valeur du `?ref=` de la source installee, chaine vide si absent."""
    source = _modules_json(projet)["etiquette"]["Source"]
    marque = "?ref="
    if marque not in source:
        return ""
    return source.split(marque, 1)[1].split("&", 1)[0]


def _outputs(projet: Path) -> dict:
    sortie = terraform("output", "-json", cwd=projet)
    if sortie.returncode != 0:
        pytest.fail(
            f"`terraform output -json` a echoue dans {projet.name} : ce projet "
            f"n'a pas ete applique.\n{sortie.stderr[-600:]}"
        )
    return json.loads(sortie.stdout)


def _module_installe(projet: Path) -> str:
    """Contenu concatene des .tf du module tel que Terraform l'a installe."""
    racine = projet / ".terraform" / "modules" / "etiquette"
    fichiers = sorted(racine.rglob("*.tf"))
    if not fichiers:
        pytest.fail(
            f"Aucun fichier .tf installe sous {racine} : le module n'a pas ete "
            "telecharge dans ce projet."
        )
    return "\n".join(f.read_text(encoding="utf-8") for f in fichiers)


@pytest.fixture(scope="module")
def racine() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    yield WORKDIR


# --------------------------------------------------------------------------
# 1. Les trois projets consomment la bibliotheque locale par Git
# --------------------------------------------------------------------------

def test_les_trois_projets_consomment_le_depot_local(racine: Path) -> None:
    for nom in PROJETS:
        modules = _modules_json(racine / nom)
        assert "etiquette" in modules, (
            f"{nom} : aucune entree `etiquette` dans modules.json. "
            f"Cles : {sorted(modules)}"
        )
        source = modules["etiquette"]["Source"]
        assert source.startswith("git::file://"), (
            f"{nom} : `Source` vaut {source!r}. La bibliotheque est un depot "
            "Git LOCAL, la source doit donc etre une URL `git::file://`."
        )
        assert "//etiquette" in source, (
            f"{nom} : `Source` vaut {source!r}. Le module vise est le "
            "sous-repertoire `etiquette` du depot, designe par `//`."
        )


def test_une_source_git_n_a_pas_de_cle_version(racine: Path) -> None:
    for nom in PROJETS:
        entree = _modules_json(racine / nom)["etiquette"]
        assert "Version" not in entree, (
            f"{nom} : l'entree porte une cle `Version` ({entree.get('Version')!r}). "
            "Cette cle n'existe que pour un module de REGISTRE : une source Git "
            "se fige par `?ref=`, jamais par l'argument `version`."
        )


# --------------------------------------------------------------------------
# 2. Trois references, trois natures differentes
# --------------------------------------------------------------------------

def test_le_projet_fige_pointe_une_reference_immuable(racine: Path) -> None:
    reference = _reference(racine / "fige")
    assert reference, (
        "fige : la source ne porte aucun `?ref=`. Sans reference, Terraform "
        "suit la branche par defaut du depot, ce qui est l'inverse du figeage."
    )
    assert SHA1.match(reference), (
        f"fige : la reference vaut {reference!r}. Un tag se DEPLACE "
        "(`git tag -f`) : seul le SHA-1 d'un commit est immuable, et c'est lui "
        "qui est attendu ici."
    )


def test_stable_et_migre_pointent_leurs_tags(racine: Path) -> None:
    assert _reference(racine / "stable") == "v1.1.0", (
        f"stable : la reference vaut {_reference(racine / 'stable')!r}, attendu "
        "`v1.1.0`."
    )
    assert _reference(racine / "migre") == "v2.0.0", (
        f"migre : la reference vaut {_reference(racine / 'migre')!r}, attendu "
        "`v2.0.0`."
    )


# --------------------------------------------------------------------------
# 3. Chaque projet a resolu la version qu'il visait
# --------------------------------------------------------------------------

def test_chaque_projet_expose_la_version_attendue(racine: Path) -> None:
    attendu = {"fige": "1.0.0", "stable": "1.1.0", "migre": "2.0.0"}
    for nom, version in attendu.items():
        sorties = _outputs(racine / nom)
        obtenu = sorties["version_module"]["value"]
        assert obtenu == version, (
            f"{nom} : `version_module` vaut {obtenu!r}, attendu {version!r}. "
            "Cette valeur vient du module resolu par Terraform, elle ne peut "
            "pas etre ecrite depuis la racine."
        )


def test_la_version_mineure_apporte_le_suffixe(racine: Path) -> None:
    etiquette = _outputs(racine / "stable")["etiquette"]["value"]
    assert etiquette == "atelier-nord", (
        f"stable : `etiquette` vaut {etiquette!r}, attendu `atelier-nord`. La "
        "1.1.0 ajoute un suffixe facultatif, et ce projet doit s'en servir."
    )


def test_la_version_majeure_a_renomme_l_entree(racine: Path) -> None:
    etiquette = _outputs(racine / "migre")["etiquette"]["value"]
    assert etiquette == "chantier", (
        f"migre : `etiquette` vaut {etiquette!r}, attendu `chantier`. La 2.0.0 "
        "renomme la variable d'entree, l'appel doit avoir ete adapte."
    )
    fige = _outputs(racine / "fige")["etiquette"]["value"]
    assert fige == "socle", (
        f"fige : `etiquette` vaut {fige!r}, attendu `socle`."
    )


# --------------------------------------------------------------------------
# 4. Le code installe prouve la nature de chaque version
# --------------------------------------------------------------------------

def test_la_mineure_reste_retrocompatible(racine: Path) -> None:
    code = _module_installe(racine / "stable")
    assert 'variable "prefixe"' in code, (
        "stable : le module installe en 1.1.0 ne declare plus `prefixe`. Une "
        "version MINEURE ne supprime ni ne renomme une entree existante."
    )
    assert 'variable "suffixe"' in code, (
        "stable : le module installe en 1.1.0 ne declare pas `suffixe`. C'est "
        "la nouveaute que cette version apporte."
    )
    assert re.search(r'variable "suffixe"[^}]*default', code, re.S), (
        "stable : la variable `suffixe` de la 1.1.0 n'a pas de `default`. Sans "
        "defaut, elle serait OBLIGATOIRE, et la version cesserait d'etre "
        "retrocompatible."
    )


def test_la_majeure_est_bien_incompatible(racine: Path) -> None:
    code = _module_installe(racine / "migre")
    assert 'variable "nom_projet"' in code, (
        "migre : le module installe en 2.0.0 ne declare pas `nom_projet`. Le "
        "changement incompatible attendu est ce renommage."
    )
    assert 'variable "prefixe"' not in code, (
        "migre : le module installe en 2.0.0 declare encore `prefixe`. Un "
        "renommage qui garde l'ancien nom n'est pas un changement majeur, "
        "c'est un ajout."
    )
    fige = _module_installe(racine / "fige")
    assert 'variable "prefixe"' in fige and 'variable "nom_projet"' not in fige, (
        "fige : le module installe n'est pas celui de la 1.0.0. Sa reference "
        "immuable devait le proteger des versions publiees ensuite."
    )
