"""Vérifie que l'outillage du dépôt est cohérent avec lui-même.

Ce module existe à cause d'un défaut mesuré ici même, le 2026-09-25. Le dépôt
portait **neuf vérificateurs** dans `tests/`, et **un seul était câblé à un
hook**. Les huit autres ne tournaient que si quelqu'un lançait `pytest tests/`
à la main, c'est-à-dire jamais pendant un commit.

C'est pire que de ne pas les avoir : on les croit en poste. Un test débranché ne
proteste pas, et sa suite reste verte, puisqu'elle ne mesure que ce qu'on lui
demande de mesurer.

Ce module rend l'incohérence détectable, sur trois points :

1. tout hook local qui lance un test pointe vers un fichier qui existe ;
2. tout vérificateur de `tests/` est soit câblé en pre-commit, soit
   explicitement recensé comme « hors pre-commit », avec sa raison ;
3. le contrat du catalogue est vérifié au push.

Le deuxième point est le plus utile, et c'est celui qui aurait crié le
2026-09-25.

    pytest tests/test_outillage_coherent.py -v
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_TESTS = RACINE / "tests"
PRE_COMMIT = RACINE / ".pre-commit-config.yaml"

#: Vérificateurs délibérément NON câblés en pre-commit, avec leur raison.
#:
#: Rien n'y figure aujourd'hui. Le candidat naturel serait un contrôle des
#: `doc_url` en ligne, qui ralentirait chaque commit et le casserait hors
#: connexion : il n'est pas un test de ce dépôt, le moteur le rend avec
#: `dsoxlab validate-structure --check-urls`, et c'est la CI qui le joue.
HORS_PRE_COMMIT: dict[str, str] = {}


def _hooks_locaux() -> list[dict]:
    configuration = yaml.safe_load(PRE_COMMIT.read_text(encoding="utf-8"))
    hooks: list[dict] = []
    for depot in configuration.get("repos", []):
        if depot.get("repo") == "local":
            hooks.extend(depot.get("hooks", []))
    return hooks


HOOKS = _hooks_locaux()


def test_le_pre_commit_declare_des_hooks_locaux() -> None:
    """Garde-fou : un parsing cassé rendrait les tests suivants verts à vide."""
    assert HOOKS, "aucun hook local trouvé dans .pre-commit-config.yaml"


@pytest.mark.parametrize(
    "hook",
    [h for h in HOOKS if "pytest tests/" in str(h.get("entry", ""))],
    ids=lambda h: str(h.get("id", "?")),
)
def test_le_hook_pointe_un_test_existant(hook: dict) -> None:
    cible = re.search(r"pytest (tests/[\w.]+\.py)", str(hook["entry"]))
    assert cible, f"entry inattendue pour le hook {hook['id']} : {hook['entry']}"
    chemin = RACINE / cible.group(1)

    assert chemin.is_file(), (
        f"Le hook `{hook['id']}` lance {cible.group(1)}, qui n'existe pas.\n"
        "Soit le fichier a été supprimé et le hook doit suivre, soit il a "
        "disparu accidentellement et il faut le restaurer."
    )


@pytest.mark.parametrize(
    "fichier_de_test",
    sorted(p.name for p in DOSSIER_TESTS.glob("test_*.py")),
)
def test_le_verificateur_est_cable_ou_recense(fichier_de_test: str) -> None:
    """Un vérificateur présent mais débranché ne protège plus rien, en silence.

    C'est ce test qui aurait crié le 2026-09-25, sur huit fichiers d'un coup.
    """
    if fichier_de_test in HORS_PRE_COMMIT:
        pytest.skip(f"hors pre-commit assumé : {HORS_PRE_COMMIT[fichier_de_test]}")

    cable = any(fichier_de_test in str(hook.get("entry", "")) for hook in HOOKS)

    assert cable, (
        f"{fichier_de_test} existe dans tests/ mais aucun hook pre-commit ne le "
        "lance : il ne protège donc plus rien, sans que rien ne le signale.\n\n"
        "Soit ajoutez un hook local dans .pre-commit-config.yaml, soit "
        "inscrivez-le dans HORS_PRE_COMMIT (dans ce fichier) avec la raison."
    )


def test_le_contrat_est_verifie_au_push() -> None:
    """`dsoxlab validate-structure` rend des contrôles qu'aucun test d'ici ne refait.

    Liens relatifs cassés, fixtures déclarées présentes, cohérence des cibles
    avec `meta.yml` : le débrancher retirerait ces contrôles sans que la suite
    locale baisse d'un test, puisqu'elle ne les porte pas.
    """
    entrees = " ".join(str(hook.get("entry", "")) for hook in HOOKS)

    assert "validate-structure" in entrees, (
        "Aucun hook ne lance `dsoxlab validate-structure`. C'est le moteur qui "
        "vérifie le contrat déclaratif, les liens relatifs et les fixtures : "
        "aucun test de tests/ ne refait ce travail, et le retirer ouvrirait un "
        "trou qui ne se verrait nulle part."
    )


def test_le_catalogue_est_verifie_au_push() -> None:
    """Le même raisonnement pour la table des README, qui est générée.

    Un catalogue périmé annonce des labs qui n'existent plus, ou tait ceux qui
    viennent d'arriver. Rien dans `tests/` ne le voit.
    """
    entrees = " ".join(str(hook.get("entry", "")) for hook in HOOKS)

    assert "gen_catalog.py --check" in entrees, (
        "Aucun hook ne vérifie la fraîcheur du catalogue des README."
    )
