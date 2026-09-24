"""Méta-tests du dépôt : un lab écrit ne doit pas se déclarer non écrit.

Le défaut que ces tests ferment a échappé à tous les autres, et il est du même
genre que ceux qu'ils attrapent : **le lab était bon, sa présentation mentait**.

Mesuré le 2026-09-24 : `first-infra/clean-destroy`, livré et validé dans les
deux sens, portait toujours

    > **Squelette.** Ce lab n'est pas encore écrit.

en tête de son `README.fr.md`, et « This lab is not written yet » en tête de son
`README.md`. Vingt-huit labs sur soixante-dix étaient dans ce cas, pour
soixante-dix-neuf fichiers.

## Pourquoi rien ne l'avait vu

`test_maturite_des_labs.py` dérive la maturité du **test fonctionnel**, ce qui
est le bon critère pour savoir si un lab prouve quelque chose. Mais un lab ne se
réduit pas à sa suite : un apprenant lit d'abord son README. Les deux
descriptions du lab, celle qui s'exécute et celle qui se lit, n'étaient
comparées par rien.

C'est exactement le trou du catalogue Kubernetes entre `lab.yaml` et `meta.yml` :
deux descriptions justes chacune de son côté, et personne pour les confronter.

## La langue officielle est l'anglais

Le fichier **sans suffixe** porte l'anglais, le `.fr.md` la traduction
française. Un lab écrit doit avoir les deux : livrer le français seul laisse la
version officielle annoncer que le lab n'existe pas.

## Ce que la liste DETTE est, et n'est pas

Elle porte les labs écrits dont la rédaction reste à faire, et elle décroît. Le
test refuse aussi qu'un lab y reste alors que ses fichiers sont écrits : sans
cette seconde moitié, une liste d'exemptions ne se vide jamais.
"""

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
LABS = REPO / "labs"

MARQUEUR_SQUELETTE = "tests non implémentés"

# Les tournures que laisse `dsoxlab new lab`, dans les deux langues. Un fichier
# qui en porte une n'a pas été relu par un humain.
MARQUEURS_DE_GABARIT = (
    "is not written yet",
    "n'est pas encore écrit",
    "TODO: describe",
    "TODO : décrire",
    "TODO: state what",
    "TODO : énoncer",
    "(skeleton)",
    "(squelette)",
)

# Ce qu'un lab écrit doit porter, dans les deux langues.
FICHIERS_DE_LECTURE = (
    "README.md",
    "README.fr.md",
    "scenario.md",
    "scenario.fr.md",
    "challenge/README.md",
    "challenge/README.fr.md",
    "lab.yaml",
    "lab.fr.yaml",
)

# Labs écrits dont la rédaction reste à faire.
#
# Mesuré le 2026-09-24 : 27 labs, 79 fichiers, 62 en anglais et 17 en
# français. `first-infra` et `aws` rédigés le jour même, il en reste 15.
DETTE = {
    "getting-started/cli-terraform",
    "getting-started/install-terraform",
    "modules/create-modules",
    "state/backends",
    "state/understand-state",
    "write-code/conditionals",
    "write-code/data-sources",
    "write-code/declare-resources",
    "write-code/depends-on",
    "write-code/dynamic-blocks",
    "write-code/for-each",
    "write-code/for-loops",
    "write-code/functions",
    "write-code/lifecycle",
    "write-code/locals",
}


def tous_les_labs() -> list[str]:
    return sorted(str(c.parent.relative_to(LABS)) for c in LABS.rglob("lab.yaml"))


def est_un_squelette(rel: str) -> bool:
    suite = LABS / rel / "challenge" / "tests" / "test_functional.py"
    if not suite.is_file():
        return True
    return MARQUEUR_SQUELETTE in suite.read_text(encoding="utf-8")


def fichiers_au_gabarit(rel: str) -> list[str]:
    """Les fichiers de lecture qui portent encore une tournure du générateur."""
    restes = []
    for nom in FICHIERS_DE_LECTURE:
        chemin = LABS / rel / nom
        if not chemin.is_file():
            restes.append(f"{nom} (absent)")
            continue
        texte = chemin.read_text(encoding="utf-8")
        if any(m in texte for m in MARQUEURS_DE_GABARIT):
            restes.append(nom)
    return restes


LABS_ECRITS = [rel for rel in tous_les_labs() if not est_un_squelette(rel)]


@pytest.mark.parametrize("rel", LABS_ECRITS)
def test_un_lab_ecrit_ne_se_declare_pas_non_ecrit(rel: str) -> None:
    """Les deux descriptions d'un lab doivent dire la même chose.

    Celle qui s'exécute, c'est `test_functional.py`. Celle qui se lit, c'est le
    README. Quand la première prouve huit choses et que la seconde annonce
    « ce lab n'est pas encore écrit », c'est la seconde que l'apprenant croit.
    """
    restes = fichiers_au_gabarit(rel)
    if restes:
        assert rel in DETTE, (
            f"{rel} a un test fonctionnel écrit, mais ces fichiers portent "
            f"encore le gabarit du générateur : {restes}.\n\n"
            "Un apprenant qui ouvre ce lab lit qu'il n'existe pas. Soit la "
            "rédaction est à faire, et le lab s'ajoute à DETTE ; soit elle est "
            "faite, et les tournures du générateur doivent disparaître.\n\n"
            "Rappel : le fichier SANS suffixe porte l'anglais, langue "
            "officielle du dépôt ; le `.fr.` porte la traduction."
        )
        return

    assert rel not in DETTE, (
        f"{rel} est entièrement rédigé, mais figure encore dans DETTE. "
        "Retirez-le de la liste, sinon elle ne décroît jamais et plus personne "
        "ne la regarde."
    )


def test_la_dette_ne_designe_que_des_labs_existants() -> None:
    fantomes = DETTE - set(tous_les_labs())
    assert not fantomes, f"DETTE désigne des labs qui n'existent pas : {sorted(fantomes)}."


def test_le_compte_de_fichiers_a_rediger_est_celui_qu_on_croit() -> None:
    """Rend visible un chiffre qui, sinon, ne se lit nulle part.

    Le voir bouger dans un diff est le seul moyen de remarquer qu'un lab a
    perdu sa rédaction, ou qu'un nouveau est arrivé sans la sienne.
    """
    reste = {rel: fichiers_au_gabarit(rel) for rel in LABS_ECRITS}
    reste = {rel: f for rel, f in reste.items() if f}
    assert set(reste) == DETTE, (
        f"Labs à rédiger réellement : {sorted(reste)}.\n"
        f"DETTE en déclare : {sorted(DETTE)}.\n\n"
        f"Apparus : {sorted(set(reste) - DETTE)}\n"
        f"Disparus : {sorted(DETTE - set(reste))}"
    )
