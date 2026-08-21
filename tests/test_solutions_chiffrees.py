"""Méta-tests du dépôt : aucune solution ne doit partir en clair.

Ces tests ne jouent aucun lab. Ils vérifient une propriété du dépôt lui-même,
et tournent sans `.vault-pass` : ils sont donc jouables en CI par n'importe qui.
"""

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SOLUTIONS = REPO / "solution"

ENTETE_VAULT = b"$ANSIBLE_VAULT"
# Fichiers de service, non chiffrés par nature.
EXEMPTS = {"verified-with.json", "README.md"}


def fichiers_de_solution() -> list[Path]:
    if not SOLUTIONS.is_dir():
        return []
    return sorted(
        f for f in SOLUTIONS.rglob("*")
        if f.is_file() and f.name not in EXEMPTS
    )


def test_dossier_solution_present() -> None:
    """Le dépôt doit porter ses solutions de référence."""
    assert SOLUTIONS.is_dir(), (
        "Le dossier solution/ est absent : aucune solution de référence ne peut "
        "être rejouée après une montée de version de Terraform."
    )


@pytest.mark.parametrize(
    "fichier", fichiers_de_solution(), ids=lambda p: str(p.relative_to(REPO))
)
def test_solution_chiffree(fichier: Path) -> None:
    """Chaque fichier de solution est chiffré par ansible-vault."""
    debut = fichier.read_bytes()[: len(ENTETE_VAULT)]
    assert debut == ENTETE_VAULT, (
        f"{fichier.relative_to(REPO)} n'est pas chiffré. "
        "Chiffrez-le avec : ansible-vault encrypt "
        "--vault-password-file .vault-pass <fichier>"
    )


def test_vault_pass_jamais_versionne() -> None:
    """Le mot de passe ne doit jamais entrer dans l'index git."""
    import subprocess

    proc = subprocess.run(
        ["git", "ls-files", "--error-unmatch", ".vault-pass"],
        cwd=REPO, capture_output=True, text=True, check=False,
    )
    assert proc.returncode != 0, (
        ".vault-pass est suivi par git. Retirez-le immédiatement de l'index "
        "(git rm --cached .vault-pass) et changez le mot de passe."
    )
