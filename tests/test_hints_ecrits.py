"""Méta-tests du dépôt : les indices doivent avoir été écrits.

Le générateur de labs pose des indices provisoires, du genre « Nudge à écrire :
orienter vers le bon concept sans donner la méthode ». Ils sont encodés en
base64, comme les vrais, pour qu'un apprenant n'y accède pas en ouvrant le
fichier. C'est justement ce qui les a rendus invisibles : `grep` ne les trouve
pas, une relecture de PR non plus, et deux labs ont été livrés validés avec des
indices que personne n'avait écrits.

On les décode donc, et on refuse le gabarit.

La liste `DETTE` porte les labs qui n'ont pas encore été repris. Elle n'est PAS
une exemption commode : le test refuse aussi qu'un lab y reste alors que ses
indices ont été écrits. Sans cette seconde moitié, la liste ne décroîtrait
jamais et plus personne ne la regarderait.
"""

import base64
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
LABS = REPO / "labs"

# Formules que le générateur laisse derrière lui, dans les deux langues.
MARQUEURS = ("à écrire", "to write", "A_COMPLETER")

# Convention MESURÉE sur les 51 labs déjà écrits, le 2026-09-18 : trois indices
# aux coûts 10, 15 et 20. Le catalogue Kubernetes en recommande quatre ; c'est
# sa convention, pas celle de ce dépôt.
COUTS_ATTENDUS = [10, 15, 20]

# Labs dont les indices sont encore ceux du générateur, mesurés le 2026-09-18.
# Un lab repris se retire d'ici, et le test le vérifie.
DETTE = {
    "aws/sg-subnet-instance",
    "certifications/professional/capstone3-collaborative-workflows",
    "certifications/professional/capstone4-modules",
    "certifications/professional/capstone5-providers",
    "certifications/professional/capstone6-hcp",
    "certifications/professional/mock-pro",
    "environments/when-to-use-workspaces",
    "getting-started/terraform-project-structure",
    "hcp-terraform/hcp-terraform-overview",
    "hcp-terraform/hcp-workspaces",
    "hcp-terraform/policy-as-code",
    "hcp-terraform/projects-teams",
    "hcp-terraform/remote-runs",
    "hcp-terraform/shared-credentials",
    "hcp-terraform/variable-sets",
}


def labs_avec_indices() -> list[str]:
    return sorted(
        str(f.parent.parent.relative_to(LABS))
        for f in LABS.rglob("challenge/hints.yaml")
    )


def indices_en_clair(rel: str) -> list[dict]:
    """Les indices d'un lab, décodés. La liste peut être vide."""
    fichier = LABS / rel / "challenge" / "hints.yaml"
    contenu = yaml.safe_load(fichier.read_text(encoding="utf-8")) or {}
    clairs = []
    for h in contenu.get("hints") or []:
        clairs.append(
            {
                "cost": h.get("cost"),
                "fr": base64.b64decode(h.get("text_fr", "")).decode("utf-8", "replace"),
                "en": base64.b64decode(h.get("text_en", "")).decode("utf-8", "replace"),
            }
        )
    return clairs


def porte_le_gabarit(clairs: list[dict]) -> bool:
    return any(m in i[langue] for i in clairs for langue in ("fr", "en") for m in MARQUEURS)


@pytest.mark.parametrize("rel", labs_avec_indices())
def test_les_indices_ne_sont_pas_ceux_du_generateur(rel: str) -> None:
    clairs = indices_en_clair(rel)
    assert clairs, f"{rel} : hints.yaml ne porte aucun indice."

    if porte_le_gabarit(clairs):
        assert rel in DETTE, (
            f"{rel} : les indices sont encore ceux du générateur.\n"
            f"Premier indice décodé : {clairs[0]['fr']!r}\n\n"
            "Quatre indices bilingues de coût croissant, du plus vague au plus "
            "explicite, sans jamais donner le bloc complet. Ils sont en base64 "
            "pour qu'un apprenant n'y accède pas en ouvrant le fichier."
        )
        return

    assert rel not in DETTE, (
        f"{rel} : les indices ont été écrits, mais le lab figure encore dans "
        "DETTE. Retirez-le de la liste, sinon elle ne décroît jamais et plus "
        "personne ne la regarde."
    )


@pytest.mark.parametrize("rel", sorted(set(labs_avec_indices()) - DETTE))
def test_trois_indices_de_cout_croissant(rel: str) -> None:
    """Un lab repris porte trois indices, aux coûts attendus."""
    couts = [i["cost"] for i in indices_en_clair(rel)]
    assert couts == COUTS_ATTENDUS, (
        f"{rel} : les coûts des indices valent {couts}, attendu "
        f"{COUTS_ATTENDUS}. Trois paliers du plus vague au plus explicite."
    )


@pytest.mark.parametrize("rel", sorted(set(labs_avec_indices()) - DETTE))
def test_les_deux_langues_sont_renseignees(rel: str) -> None:
    """`text_fr` recopié de l'anglais signale une traduction jamais faite.

    L'égalité n'est pas fautive indice par indice : le dernier palier est
    parfois un extrait de HCL, identique dans les deux langues par nature. Ce
    qui est fautif, c'est que le lab ENTIER soit identique en français et en
    anglais, car alors personne n'a traduit.
    """
    clairs = indices_en_clair(rel)
    for rang, indice in enumerate(clairs, start=1):
        assert indice["fr"].strip(), f"{rel} : indice {rang} sans texte français."
        assert indice["en"].strip(), f"{rel} : indice {rang} sans texte anglais."

    assert any(i["fr"] != i["en"] for i in clairs), (
        f"{rel} : les trois indices portent le même texte en français et en "
        "anglais. `text_fr` est une copie de l'anglais tant que personne n'est "
        "passé."
    )


def test_la_dette_ne_designe_que_des_labs_existants() -> None:
    """Un lab renommé ou supprimé ne doit pas laisser une entrée fantôme."""
    fantomes = DETTE - set(labs_avec_indices())
    assert not fantomes, (
        f"DETTE désigne des labs qui n'existent pas : {sorted(fantomes)}."
    )
