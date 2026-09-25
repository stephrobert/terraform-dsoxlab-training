"""Les liens relatifs des Markdown pointent vers un fichier qui existe.

Un lien interne cassé ne fait échouer aucun test fonctionnel : il ne casse que
la navigation de l'apprenant, en silence. C'est exactement ce qu'un test attrape
mieux qu'une relecture, et le catalogue Ansible jumeau en a relevé 150 d'un coup
le jour où le contrôle y a été écrit, dont 112 qui pointaient un niveau trop
haut.

Ce dépôt a deux raisons de plus d'en avoir besoin :

1. **la table des README est générée** par `scripts/gen_catalog.py` et renvoie
   vers les répertoires de labs. Un lab renommé y laisserait un renvoi mort sans
   que rien ne le dise ;
2. **les labs sont rangés sur deux ou trois niveaux** (`labs/<section>/<lab>/`,
   parfois `labs/write-code/sensitive-data/<lab>/`). Le nombre de `../` pour
   remonter à la racine n'est donc pas le même partout, ce qui est une source
   d'erreur mécanique. Mesuré le 2026-09-25 : depuis `challenge/README.md` d'un
   lab, `docs/hcp-token.md` est à quatre niveaux et non trois, et
   `dsoxlab validate-structure` l'a signalé avant ce test.

Aucun réseau, donc rapide et déterministe. Les URL absolues ne sont pas du
ressort de ce module : le moteur les contrôle avec
`dsoxlab validate-structure --check-urls`, que la CI lance.

    pytest tests/test_liens_internes.py -v
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).parent.parent.resolve()
LABS = RACINE / "labs"
DOCS = RACINE / "docs"

# [libellé](cible) où la cible est relative (commence par ./ ou ../).
LIEN_RELATIF = re.compile(r"\[[^\]]*\]\((\.\.?/[^)]+)\)")


def _fichiers_markdown() -> list[Path]:
    """Les Markdown des labs, de `docs/`, et ceux de la racine."""
    return (
        sorted(LABS.rglob("*.md"))
        + sorted(DOCS.rglob("*.md") if DOCS.is_dir() else [])
        + sorted(RACINE.glob("*.md"))
    )


def _liens_casses(fichier: Path) -> list[str]:
    """Cibles relatives introuvables depuis ce fichier.

    L'ancre (`#section`) est retirée avant de tester le chemin : elle est
    résolue par le lecteur Markdown, pas par le système de fichiers.
    """
    contenu = fichier.read_text(encoding="utf-8", errors="ignore")
    casses = []
    for cible in LIEN_RELATIF.findall(contenu):
        chemin = (fichier.parent / cible.split("#")[0]).resolve()
        if not chemin.exists():
            casses.append(cible)
    return casses


def test_il_y_a_des_markdown_a_verifier() -> None:
    """Garde-fou : sans lui, un glob cassé rendrait la suite verte à vide."""
    trouves = _fichiers_markdown()
    assert len(trouves) > 200, (
        f"Seulement {len(trouves)} fichier(s) .md trouvé(s) : le glob est "
        "probablement cassé, et la suite deviendrait verte sans rien mesurer."
    )


@pytest.mark.parametrize(
    "fichier",
    _fichiers_markdown(),
    ids=lambda p: str(p.relative_to(RACINE)),
)
def test_les_liens_relatifs_pointent_vers_un_fichier_existant(fichier: Path) -> None:
    casses = _liens_casses(fichier)

    assert not casses, (
        f"{fichier.relative_to(RACINE)} contient {len(casses)} lien(s) mort(s) :\n"
        + "\n".join(f"  - {c}" for c in casses)
        + "\n\nComptez les niveaux depuis le fichier qui porte le lien : depuis "
        "`labs/<section>/<lab>/README.md`, la racine est à trois `../` ; depuis "
        "`labs/<section>/<lab>/challenge/README.md`, elle est à quatre."
    )
