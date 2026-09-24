"""Méta-tests du dépôt : un squelette ne doit jamais passer pour un lab.

Le défaut que ces tests ferment est subtil, et il rend `scripts/test-all.sh`
trompeur : **pytest considère un lab entièrement skippé comme une exécution
réussie**. Les labs squelettes portent

    pytestmark = pytest.mark.skip(reason="Lab squelette : tests à écrire")

donc la suite peut annoncer « tous les labs passent » alors que vingt-six labs
ne prouvent absolument rien. Le message est vrai au sens de pytest, et faux au
sens de ce que le catalogue promet.

## Pourquoi un statut DÉRIVÉ et non DÉCLARÉ

La première idée est d'ajouter `status: verified` dans `lab.yaml`. Deux raisons
de ne pas le faire, et la seconde est la vraie :

1. `dsoxlab validate-structure` REFUSE un champ inconnu du contrat. Mesuré le
   2026-09-23 : `status` fait sortir la validation en 1. Le contourner
   localement irait contre la règle du dépôt, qui veut qu'un défaut du moteur se
   corrige en amont ou se remonte, jamais qu'on passe à côté.

2. Surtout : **un statut déclaré peut mentir**. Rien n'empêche d'écrire
   `verified` sans avoir rien vérifié, et l'on retombe exactement sur le
   problème qu'on voulait résoudre. Un statut dérivé de l'état réel du dépôt,
   lui, ne diverge jamais.

La maturité se LIT donc : un lab est mûr quand son test n'est pas un squelette
et qu'une solution de référence existe. Aucune des deux moitiés ne suffit.

## Ce que la liste COQUILLES est, et n'est pas

Elle porte les labs dont le scénario est écrit mais dont le test reste à faire.
Ce n'est pas une exemption commode : le test refuse aussi qu'un lab y reste
alors qu'il a été écrit. Sans cette seconde moitié, la liste ne décroîtrait
jamais et plus personne ne la regarderait.
"""

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
LABS = REPO / "labs"
SOLUTIONS = REPO / "solution"

MARQUEUR_SQUELETTE = "tests non implémentés"

# Labs dont le test reste à écrire, mesurés le 2026-09-23. Un lab écrit se
# retire d'ici, et le test le vérifie.
COQUILLES = {
    "certifications/professional/capstone2-dynamic-config",
    "certifications/professional/capstone3-collaborative-workflows",
    "certifications/professional/capstone4-modules",
    "certifications/professional/capstone5-providers",
    "certifications/professional/capstone6-hcp",
    "certifications/professional/mock-pro",
    "getting-started/providers-resources-data-sources",
    "getting-started/terraform-project-structure",
    "hcp-terraform/hcp-terraform-overview",
    "hcp-terraform/hcp-workspaces",
    "hcp-terraform/policy-as-code",
    "hcp-terraform/projects-teams",
    "hcp-terraform/remote-runs",
    "hcp-terraform/shared-credentials",
    "hcp-terraform/variable-sets",
}


def tous_les_labs() -> list[str]:
    return sorted(str(c.parent.relative_to(LABS)) for c in LABS.rglob("lab.yaml"))


def est_un_squelette(rel: str) -> bool:
    suite = LABS / rel / "challenge" / "tests" / "test_functional.py"
    if not suite.is_file():
        return True
    return MARQUEUR_SQUELETTE in suite.read_text(encoding="utf-8")


def a_une_solution(rel: str) -> bool:
    dossier = SOLUTIONS / rel
    return dossier.is_dir() and any(f.is_file() for f in dossier.rglob("*"))


@pytest.mark.parametrize("rel", tous_les_labs())
def test_un_squelette_est_declare_comme_tel(rel: str) -> None:
    """Aucun lab ne doit être un squelette sans figurer dans la liste."""
    if est_un_squelette(rel):
        assert rel in COQUILLES, (
            f"{rel} porte un test squelette, entièrement skippé, et ne figure "
            "pas dans COQUILLES.\n\nUn lab dont toute la suite skippe fait "
            "passer `scripts/test-all.sh` au vert sans rien prouver. Soit le "
            "test est à écrire, et le lab s'ajoute à la liste ; soit il est "
            "écrit, et le marqueur de squelette doit disparaître."
        )
        return

    assert rel not in COQUILLES, (
        f"{rel} a un test écrit, mais figure encore dans COQUILLES. Retirez-le "
        "de la liste, sinon elle ne décroît jamais et plus personne ne la "
        "regarde."
    )


@pytest.mark.parametrize("rel", sorted(set(tous_les_labs()) - COQUILLES))
def test_un_lab_ecrit_porte_une_solution_de_reference(rel: str) -> None:
    """Un test sans solution ne peut pas être validé.

    C'est l'implication que le catalogue doit tenir :

        lab publié  =>  solution existe  =>  solution rejouable

    Sans solution, `scripts/test-all.sh` ne peut rien rejouer, et le lab n'a
    jamais été éprouvé dans le sens « 100 ». Il peut très bien être impossible
    à résoudre sans que personne ne le sache.
    """
    assert a_une_solution(rel), (
        f"{rel} a un test fonctionnel écrit, mais AUCUNE solution sous "
        f"solution/{rel}/.\n\nRien ne prouve alors que ses tests sont "
        "satisfaisables : ils peuvent exiger l'impossible, et seul un apprenant "
        "s'en apercevrait."
    )


def test_la_liste_des_coquilles_ne_designe_que_des_labs_existants() -> None:
    """Un lab renommé ou supprimé ne doit pas laisser une entrée fantôme."""
    fantomes = COQUILLES - set(tous_les_labs())
    assert not fantomes, (
        f"COQUILLES désigne des labs qui n'existent pas : {sorted(fantomes)}."
    )


def test_le_compte_de_coquilles_est_celui_qu_on_croit() -> None:
    """Un garde-fou contre la dérive silencieuse du catalogue.

    Ce test ne vérifie pas une propriété du code : il rend VISIBLE un chiffre
    qui, sans lui, ne se lit nulle part. Le voir bouger dans un diff est le seul
    moyen de remarquer qu'un lab a régressé à l'état de squelette.
    """
    squelettes = {rel for rel in tous_les_labs() if est_un_squelette(rel)}
    assert squelettes == COQUILLES, (
        f"Les squelettes réels sont {sorted(squelettes)}.\n"
        f"La liste en déclare {sorted(COQUILLES)}.\n\n"
        f"Apparus : {sorted(squelettes - COQUILLES)}\n"
        f"Disparus : {sorted(COQUILLES - squelettes)}"
    )
