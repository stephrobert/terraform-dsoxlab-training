"""Méta-tests du dépôt : aucun secret ne doit entrer dans l'historique.

## Pourquoi ce contrôle existe

Le catalogue explique désormais comment créer un jeton HCP Terraform
(`docs/hcp-token.md`), et le lab optionnel qui s'en sert demande à l'apprenant
d'en poser un sur son poste. Dès qu'un secret circule autour d'un dépôt, la
question n'est plus « est-ce que quelqu'un le committera » mais « qu'est-ce qui
l'en empêchera ».

Un `.gitignore` n'en empêche rien : il protège les chemins qu'on a pensé à
nommer, et un fichier ajouté avec `git add -f` passe outre. Ce test regarde le
CONTENU, ce qui couvre aussi le fichier qu'on n'avait pas prévu.

## Ce qu'il cherche

Les formes qu'un vrai jeton prend, et qui ne se rencontrent pas par hasard :

- un jeton d'API HCP Terraform, `<14 caractères>.atlasv1.<au moins 60>` ;
- une clé d'accès AWS, `AKIA` suivi de 16 caractères, sauf l'exemple que
  HashiCorp et AWS emploient dans toute leur documentation ;
- un bloc `credentials` de fichier `.tfrc` portant un `token`.

## Ce qu'il ne peut pas faire

Il lit les fichiers du dépôt, pas l'historique : un jeton committé puis retiré
resterait dans les objets git. C'est une raison de plus pour révoquer plutôt que
pour retirer, et le guide le dit.

Il a été éprouvé dans les deux sens, en posant un faux jeton à la forme exacte
dans un fichier temporaire du dépôt : le test le voit et le nomme.
"""

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent

# Un jeton d'API HCP Terraform : un identifiant, `atlasv1`, puis la partie
# secrète. La longueur est ce qui distingue un vrai jeton d'une illustration.
JETON_HCP = re.compile(r"\b[A-Za-z0-9]{14}\.atlasv1\.[A-Za-z0-9_-]{60,}")

# Une clé d'accès AWS. `AKIAIOSFODNN7EXAMPLE` est l'exemple officiel, employé
# par AWS comme par HashiCorp, et le lab `shared-credentials` s'en sert
# justement pour montrer ce qu'il ne faut pas faire.
CLE_AWS = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
EXEMPLES_ADMIS = {"AKIAIOSFODNN7EXAMPLE"}

# Un bloc de credentials Terraform portant un jeton non vide.
BLOC_CREDENTIALS = re.compile(
    r'credentials\s+"[^"]+"\s*\{[^}]*token\s*=\s*"(?!<)(?!\s*")[^"]{20,}"',
    re.DOTALL,
)

# Les fichiers de credentials n'ont rien à faire ici, quel que soit leur contenu.
NOMS_INTERDITS = {"credentials.tfrc.json", "credentials.tfrc", ".terraformrc"}

# Ce qu'on ne lit pas : ce qui n'est pas du texte suivi, ou ce que git ignore.
REPERTOIRES_IGNORES = {
    ".git",
    ".venv",
    "__pycache__",
    ".terraform",
    ".pytest_cache",
    "node_modules",
}
SUFFIXES_IGNORES = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz", ".lock"}


def fichiers_du_depot() -> list[Path]:
    trouves = []
    for chemin in REPO.rglob("*"):
        if not chemin.is_file():
            continue
        if set(chemin.relative_to(REPO).parts) & REPERTOIRES_IGNORES:
            continue
        if chemin.suffix in SUFFIXES_IGNORES:
            continue
        trouves.append(chemin)
    return sorted(trouves)


FICHIERS = fichiers_du_depot()


def lire(chemin: Path) -> str:
    try:
        return chemin.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


@pytest.mark.parametrize("chemin", FICHIERS, ids=lambda c: str(c.relative_to(REPO)))
def test_aucun_fichier_ne_porte_de_jeton(chemin: Path) -> None:
    rel = chemin.relative_to(REPO)
    contenu = lire(chemin)

    assert chemin.name not in NOMS_INTERDITS, (
        f"{rel} est un fichier de credentials Terraform.\n\nCes fichiers vivent "
        "dans le répertoire personnel, jamais dans un dépôt. Retirez-le, puis "
        "RÉVOQUEZ le jeton qu'il portait : un fichier retiré reste dans "
        "l'historique git."
    )

    trouve = JETON_HCP.search(contenu)
    assert trouve is None, (
        f"{rel} porte ce qui ressemble à un jeton d'API HCP Terraform, à la "
        f"ligne {contenu[: trouve.start()].count(chr(10)) + 1}.\n\nRévoquez-le "
        "immédiatement sur app.terraform.io, User settings puis Tokens : le "
        "retirer du fichier ne suffit pas, il reste dans l'historique git.\n\n"
        "Voir docs/hcp-token.md."
    )

    cles = {c for c in CLE_AWS.findall(contenu)} - EXEMPLES_ADMIS
    assert not cles, (
        f"{rel} porte une clé d'accès AWS qui n'est pas l'exemple officiel : "
        f"{sorted(cles)}.\n\nSeul `AKIAIOSFODNN7EXAMPLE` est admis, et "
        "uniquement pour montrer ce qu'il ne faut pas faire."
    )

    bloc = BLOC_CREDENTIALS.search(contenu)
    assert bloc is None, (
        f"{rel} porte un bloc `credentials` avec un jeton renseigné.\n\nDans la "
        "documentation, ce bloc s'écrit avec un `<votre-jeton>` explicite, "
        "jamais avec une valeur."
    )


def test_le_controle_lit_bien_quelque_chose() -> None:
    """Un balayage qui ne trouve plus aucun fichier serait vert et muet."""
    assert len(FICHIERS) >= 300, (
        f"Seuls {len(FICHIERS)} fichiers sont examinés, ce qui est trop peu pour "
        "ce dépôt : les exclusions ont probablement trop mangé."
    )


def test_les_motifs_reconnaissent_un_vrai_jeton() -> None:
    """Le contrôle doit VOIR ce qu'il prétend voir.

    Sans ce test, une expression régulière cassée rendrait tout le fichier vert,
    et c'est la forme la plus discrète de faux vert : plus rien n'est détecté,
    tout passe.

    Les valeurs ci-dessous ont la forme exacte d'un vrai secret, et n'en sont
    pas : elles ne sont acceptées par aucun service.
    """
    faux_jeton = "Ab3dEf6hIj9kLm.atlasv1." + "x" * 64
    assert JETON_HCP.search(f'token = "{faux_jeton}"'), (
        "Le motif ne reconnaît plus un jeton HCP Terraform."
    )
    assert JETON_HCP.search("atlasv1") is None, (
        "Le motif se déclenche sur une simple mention du mot."
    )

    # Construite, et non écrite : sinon ce fichier se dénoncerait lui-même, ce
    # qu'il a fait au premier essai. La seule autre issue aurait été d'exclure
    # ce fichier du balayage, c'est-à-dire d'ouvrir un trou dans le contrôle
    # pour que le contrôle passe.
    fausse_cle = "AKIA" + "Z" * 16
    assert CLE_AWS.findall(fausse_cle) == [fausse_cle]
    assert not (set(CLE_AWS.findall("AKIA" + "IOSFODNN7EXAMPLE")) - EXEMPLES_ADMIS), (
        "L'exemple officiel doit rester admis, sinon le lab shared-credentials "
        "ne peut plus montrer ce qu'il faut éviter."
    )

    bloc = (
        'credentials "app.terraform.io" {\n'
        f'  token = "{faux_jeton}"\n'
        "}\n"
    )
    assert BLOC_CREDENTIALS.search(bloc), "Le motif ne voit plus un bloc renseigné."
    assert BLOC_CREDENTIALS.search(
        'credentials "app.terraform.io" {\n  token = "<votre-jeton>"\n}\n'
    ) is None, "Le motif se déclenche sur la forme documentaire, qui est un exemple."
