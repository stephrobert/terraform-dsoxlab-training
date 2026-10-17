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

from conftest import exiger_workdir, message, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "modules-version-modules"

PROJETS = ("fige", "stable", "migre")
SHA1 = re.compile(r"^[0-9a-f]{40}$")


def _modules_json(projet: Path) -> dict[str, dict]:
    chemin = projet / ".terraform" / "modules" / "modules.json"
    if not chemin.is_file():
        pytest.fail(
            message(
            en=f"{projet.name}/.terraform/modules/modules.json is missing: "
            "`terraform init` never succeeded in this project. A leftover "
            "`???`, a repository not yet initialised, or the `version` argument "
            "still present next to a Git source?",
            fr=f"{projet.name}/.terraform/modules/modules.json est absent : "
            "`terraform init` n'a jamais abouti dans ce projet. Un `???` "
            "restant, un dépôt pas encore initialisé, ou l'argument `version` "
            "encore présent à côté d'une source Git ?",
        )
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
            message(
            en=f"`terraform output -json` failed in {projet.name}: that project "
            f"was not applied.\n{sortie.stderr[-600:]}",
            fr=f"`terraform output -json` a échoué dans {projet.name} : ce projet "
            f"n'a pas été appliqué.\n{sortie.stderr[-600:]}",
        )
        )
    return json.loads(sortie.stdout)


def _module_installe(projet: Path) -> str:
    """Contenu concatene des .tf du module tel que Terraform l'a installe."""
    racine = projet / ".terraform" / "modules" / "etiquette"
    fichiers = sorted(racine.rglob("*.tf"))
    if not fichiers:
        pytest.fail(
            message(
            en=f"No .tf file installed under {racine}: the module was not "
            "downloaded in this project.",
            fr=f"Aucun fichier .tf installé sous {racine} : le module n'a pas été "
            "téléchargé dans ce projet.",
        )
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
        assert "etiquette" in modules, message(
            en=f"{nom}: no `etiquette` entry in modules.json. "
            f"Keys: {sorted(modules)}",
            fr=f"{nom} : aucune entrée `etiquette` dans modules.json. "
            f"Clés : {sorted(modules)}",
        )
        source = modules["etiquette"]["Source"]
        assert source.startswith("git::file://"), message(
            en=f"{nom}: `Source` is {source!r}. The library is a LOCAL Git "
            "repository, so the source must be a `git::file://` URL.",
            fr=f"{nom} : `Source` vaut {source!r}. La bibliothèque est un dépôt "
            "Git LOCAL, la source doit donc être une URL `git::file://`.",
        )
        assert "//etiquette" in source, message(
            en=f"{nom}: `Source` is {source!r}. The module targeted is the "
            "`etiquette` sub-directory of the repository, named with `//`.",
            fr=f"{nom} : `Source` vaut {source!r}. Le module visé est le "
            "sous-répertoire `etiquette` du dépôt, désigné par `//`.",
        )


def test_une_source_git_n_a_pas_de_cle_version(racine: Path) -> None:
    for nom in PROJETS:
        entree = _modules_json(racine / nom)["etiquette"]
        assert "Version" not in entree, message(
            en=f"{nom}: the entry carries a `Version` key ({entree.get('Version')!r}). "
            "That key only exists for a REGISTRY module: a Git source "
            "is pinned with `?ref=`, never with the `version` argument.",
            fr=f"{nom} : l'entrée porte une clé `Version` ({entree.get('Version')!r}). "
            "Cette clé n'existe que pour un module de REGISTRE : une source Git "
            "se fige par `?ref=`, jamais par l'argument `version`.",
        )


# --------------------------------------------------------------------------
# 2. Trois references, trois natures differentes
# --------------------------------------------------------------------------

def test_le_projet_fige_pointe_une_reference_immuable(racine: Path) -> None:
    reference = _reference(racine / "fige")
    assert reference, message(
        en="fige: the source carries no `?ref=`. With no reference, Terraform "
        "follows the repository's default branch, which is the opposite of pinning.",
        fr="fige : la source ne porte aucun `?ref=`. Sans référence, Terraform "
        "suit la branche par défaut du dépôt, ce qui est l'inverse du figeage.",
    )
    assert SHA1.match(reference), message(
        en=f"fige: the reference is {reference!r}. A tag MOVES "
        "(`git tag -f`): only a commit's SHA-1 is immutable, and that is "
        "what is expected here.",
        fr=f"fige : la référence vaut {reference!r}. Un tag se DÉPLACE "
        "(`git tag -f`) : seul le SHA-1 d'un commit est immuable, et c'est lui "
        "qui est attendu ici.",
    )


def test_stable_et_migre_pointent_leurs_tags(racine: Path) -> None:
    assert _reference(racine / "stable") == "v1.1.0", message(
        en=f"stable: the reference is {_reference(racine / 'stable')!r}, expected "
        "`v1.1.0`.",
        fr=f"stable : la référence vaut {_reference(racine / 'stable')!r}, attendu "
        "`v1.1.0`.",
    )
    assert _reference(racine / "migre") == "v2.0.0", message(
        en=f"migre: the reference is {_reference(racine / 'migre')!r}, expected "
        "`v2.0.0`.",
        fr=f"migre : la référence vaut {_reference(racine / 'migre')!r}, attendu "
        "`v2.0.0`.",
    )


# --------------------------------------------------------------------------
# 3. Chaque projet a resolu la version qu'il visait
# --------------------------------------------------------------------------

def test_chaque_projet_expose_la_version_attendue(racine: Path) -> None:
    attendu = {"fige": "1.0.0", "stable": "1.1.0", "migre": "2.0.0"}
    for nom, version in attendu.items():
        sorties = _outputs(racine / nom)
        obtenu = sorties["version_module"]["value"]
        assert obtenu == version, message(
            en=f"{nom}: `version_module` is {obtenu!r}, expected {version!r}. "
            "That value comes from the module Terraform resolved, it cannot "
            "be written from the root.",
            fr=f"{nom} : `version_module` vaut {obtenu!r}, attendu {version!r}. "
            "Cette valeur vient du module résolu par Terraform, elle ne peut "
            "pas être écrite depuis la racine.",
        )


def test_la_version_mineure_apporte_le_suffixe(racine: Path) -> None:
    etiquette = _outputs(racine / "stable")["etiquette"]["value"]
    assert etiquette == "atelier-nord", message(
        en=f"stable: `etiquette` is {etiquette!r}, expected `atelier-nord`. "
        "1.1.0 adds an optional suffix, and this project must use it.",
        fr=f"stable : `etiquette` vaut {etiquette!r}, attendu `atelier-nord`. La "
        "1.1.0 ajoute un suffixe facultatif, et ce projet doit s'en servir.",
    )


def test_la_version_majeure_a_renomme_l_entree(racine: Path) -> None:
    etiquette = _outputs(racine / "migre")["etiquette"]["value"]
    assert etiquette == "chantier", message(
        en=f"migre: `etiquette` is {etiquette!r}, expected `chantier`. 2.0.0 "
        "renames the input variable, so the call must have been adapted.",
        fr=f"migre : `etiquette` vaut {etiquette!r}, attendu `chantier`. La 2.0.0 "
        "renomme la variable d'entrée, l'appel doit avoir été adapté.",
    )
    fige = _outputs(racine / "fige")["etiquette"]["value"]
    assert fige == "socle", message(
        en=f"fige: `etiquette` is {fige!r}, expected `socle`.",
        fr=f"fige : `etiquette` vaut {fige!r}, attendu `socle`.",
    )


# --------------------------------------------------------------------------
# 4. Le code installe prouve la nature de chaque version
# --------------------------------------------------------------------------

def test_la_mineure_reste_retrocompatible(racine: Path) -> None:
    code = _module_installe(racine / "stable")
    assert 'variable "prefixe"' in code, message(
        en="stable: the module installed at 1.1.0 no longer declares `prefixe`. A "
        "MINOR version neither removes nor renames an existing input.",
        fr="stable : le module installé en 1.1.0 ne déclare plus `prefixe`. Une "
        "version MINEURE ne supprime ni ne renomme une entrée existante.",
    )
    assert 'variable "suffixe"' in code, message(
        en="stable: the module installed at 1.1.0 does not declare `suffixe`. That is "
        "the novelty this version brings.",
        fr="stable : le module installé en 1.1.0 ne déclare pas `suffixe`. C'est "
        "la nouveauté que cette version apporte.",
    )
    assert re.search(r'variable "suffixe"[^}]*default', code, re.S), message(
        en="stable: the `suffixe` variable of 1.1.0 has no `default`. Without a "
        "default, it would be REQUIRED, and the version would stop being "
        "backwards compatible.",
        fr="stable : la variable `suffixe` de la 1.1.0 n'a pas de `default`. Sans "
        "défaut, elle serait OBLIGATOIRE, et la version cesserait d'être "
        "rétrocompatible.",
    )


def test_la_majeure_est_bien_incompatible(racine: Path) -> None:
    code = _module_installe(racine / "migre")
    assert 'variable "nom_projet"' in code, message(
        en="migre: the module installed at 2.0.0 does not declare `nom_projet`. The "
        "expected breaking change is that rename.",
        fr="migre : le module installé en 2.0.0 ne déclare pas `nom_projet`. Le "
        "changement incompatible attendu est ce renommage.",
    )
    assert 'variable "prefixe"' not in code, message(
        en="migre: the module installed at 2.0.0 still declares `prefixe`. A "
        "rename that keeps the old name is not a major change, "
        "it is an addition.",
        fr="migre : le module installé en 2.0.0 déclare encore `prefixe`. Un "
        "renommage qui garde l'ancien nom n'est pas un changement majeur, "
        "c'est un ajout.",
    )
    fige = _module_installe(racine / "fige")
    assert 'variable "prefixe"' in fige and 'variable "nom_projet"' not in fige, message(
        en="fige: the module installed is not the one from 1.0.0. Its immutable "
        "reference was supposed to protect it from versions published afterwards.",
        fr="fige : le module installé n'est pas celui de la 1.0.0. Sa référence "
        "immuable devait le protéger des versions publiées ensuite.",
    )
