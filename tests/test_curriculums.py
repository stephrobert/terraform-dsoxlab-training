"""Méta-tests du dépôt : un objectif d'examen cité doit exister dans SA grille.

## Le défaut que ces tests ferment

Deux grilles d'objectifs coexistent dans ce catalogue, et elles se ressemblent
assez pour qu'on les confonde sans s'en apercevoir :

    Associate 004                    Pro (Authoring and Operations)
    1b = avantages de l'IaC          1b = générer un plan d'exécution
    3d = générer un plan             3d = partager des données entre configs

Un code emprunté à la mauvaise grille reste un code **valide**. Il ne casse
rien, ne lève aucune erreur, et désigne simplement autre chose. C'est
exactement le genre de faux qu'aucun test d'exécution n'attrape.

Mesuré le 2026-09-24 : `certifications/associate/essential-commands`, livré le
jour même, annonçait « Associate 004 » et citait `1b` pour un lab qui fait
générer et lire un plan. Le chiffre venait de la grille Pro, où il est juste.

## La règle de rattachement, et pourquoi elle est explicite

Le rattachement se lit dans le **chemin** du lab, pas dans son texte :

    labs/certifications/associate/...  ->  grille Associate 004
    tout le reste                      ->  grille Professional

Ce n'est pas arbitraire, c'est ce que le catalogue fait déjà : les 26 autres
labs qui citent un objectif utilisent tous la grille Professional, et les deux
labs sous `certifications/associate/` visent l'Associate. Une règle lisible dans
l'arborescence vaut mieux qu'une heuristique sur le texte, qui se tromperait le
jour où un lab cite l'autre examen en passant.

## Deux contrôles, et pourquoi le premier ne suffisait pas

Le premier écrit vérifiait que le code **existe** dans la grille du lab. Il est
passé au vert sur le défaut qui l'avait motivé : `1b` existe dans les deux
grilles. Un test qui ne tombe pas sur le cas qui l'a fait naître ne mesure rien,
il rassure.

Le second compare donc le **libellé** que le lab accole à son code aux fragments
que `curriculums.yml` associe à ce code. C'est lui qui attrape un code emprunté
à l'autre grille, et c'est lui qui a trouvé quatre autres labs dans ce cas.

Ce qu'ils ne font pas : juger la qualité d'une traduction. Les fragments sont
courts et comparés sans accents, de sorte qu'un libellé formulé autrement passe.
Le test refuse une **contradiction**, il ne note pas la rédaction. Un libellé
juste que les fragments ne couvrent pas encore se corrige dans
`curriculums.yml`, et le message d'échec le dit.
"""

import re
import unicodedata
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
LABS = REPO / "labs"
SOURCE = REPO / "curriculums.yml"

# « Sous-objectif d'examen visé : 1b », « Objectif d'examen visé : **1** », et
# leurs formes anglaises. Le code est capturé sans les astérisques de gras.
CITATION = re.compile(
    r"(?:[Ss]ous-)?[Oo]bjectifs? d'examen visé\s*:\s*\*{0,2}(\d[a-z]?)"
    r"|(?:[Ee]xam )?objectives? targeted\s*:\s*\*{0,2}(\d[a-z]?)",
)

FICHIERS_LUS = ("scenario.fr.md", "scenario.md", "README.fr.md", "README.md")

# La même citation, avec le libellé qui la suit : entre parenthèses, ou après
# une virgule jusqu'à la fin de la phrase.
CITATION_LIBELLE = re.compile(
    r"(?:[Ss]ous-)?[Oo]bjectifs? d'examen visé\s*:\s*\*{0,2}(?P<code>\d[a-z]?)"
    r"(?:\s*\((?P<paren>[^)]{1,120})\)|\s*,\s*(?P<virgule>[^.\n*]{1,120}))?",
)


def curriculums() -> dict:
    return yaml.safe_load(SOURCE.read_text(encoding="utf-8"))["curriculums"]


def mots_cles() -> dict:
    return yaml.safe_load(SOURCE.read_text(encoding="utf-8"))["mots_cles"]


def codes_connus(examen: str) -> set[str]:
    """Tous les codes de la grille : les objectifs et leurs sous-objectifs."""
    grille = curriculums()[examen]["objectifs"]
    codes = {str(numero) for numero in grille}
    for objectif in grille.values():
        codes |= set(objectif["sous_objectifs"])
    return codes


def tous_les_labs() -> list[str]:
    return sorted(str(c.parent.relative_to(LABS)) for c in LABS.rglob("lab.yaml"))


def examen_du_lab(rel: str) -> str:
    """La grille à laquelle un lab se rattache, lue dans son chemin."""
    return "associate" if rel.startswith("certifications/associate/") else "professional"


def citations(rel: str) -> list[tuple[str, str]]:
    """Les codes d'objectif cités par un lab, avec le fichier qui les porte."""
    trouvees = []
    for nom in FICHIERS_LUS:
        chemin = LABS / rel / nom
        if not chemin.is_file():
            continue
        for brut in CITATION.findall(chemin.read_text(encoding="utf-8")):
            code = brut[0] or brut[1]
            if code:
                trouvees.append((nom, code))
    return trouvees


# --------------------------------------------------------------------------
# 1. L'intégrité de la source elle-même.
# --------------------------------------------------------------------------
def test_la_source_porte_les_deux_grilles_et_leur_provenance() -> None:
    """Une grille sans URL ni date de vérification ne se confronte pas.

    C'est la moitié que le catalogue Kubernetes a payée : un chiffre « vérifié
    sur le site officiel » sans commande qui le montre vaut zéro.
    """
    data = curriculums()
    assert set(data) == {"associate", "professional"}, (
        f"Grilles déclarées : {sorted(data)}. Attendu associate et professional."
    )
    for nom, grille in data.items():
        assert grille["source"].startswith("https://developer.hashicorp.com/"), (
            f"La grille {nom} ne cite pas sa source officielle."
        )
        assert grille["derniere_verification"], (
            f"La grille {nom} ne dit pas quand elle a été confrontée au publié."
        )


def test_les_grilles_ont_le_nombre_d_objectifs_publies() -> None:
    """Un garde-fou contre une grille tronquée par une édition malheureuse.

    Relevé le 2026-09-24 sur les deux pages officielles : 8 objectifs pour
    l'Associate 004, 6 pour le Professional.
    """
    attendus = {"associate": 8, "professional": 6}
    for nom, combien in attendus.items():
        objectifs = curriculums()[nom]["objectifs"]
        assert len(objectifs) == combien, (
            f"La grille {nom} déclare {len(objectifs)} objectifs, {combien} publiés.\n"
            f"Présents : {sorted(objectifs)}."
        )


def test_chaque_sous_objectif_porte_le_numero_de_son_objectif() -> None:
    """`3d` doit vivre sous l'objectif 3, sinon la table ment sur elle-même."""
    for nom, grille in curriculums().items():
        for numero, objectif in grille["objectifs"].items():
            for code in objectif["sous_objectifs"]:
                assert code.startswith(str(numero)), (
                    f"{nom} : le sous-objectif {code} est rangé sous l'objectif "
                    f"{numero}."
                )


# --------------------------------------------------------------------------
# 2. Ce que les labs citent.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("rel", tous_les_labs())
def test_un_lab_ne_cite_que_des_objectifs_de_sa_grille(rel: str) -> None:
    examen = examen_du_lab(rel)
    connus = codes_connus(examen)
    grille = curriculums()[examen]

    for fichier, code in citations(rel):
        assert code in connus, (
            f"{rel}/{fichier} cite l'objectif `{code}`, qui n'existe pas dans la "
            f"grille {grille['nom']}.\n\n"
            "Ce lab se rattache à cette grille par son chemin. Deux causes "
            "possibles, et la seconde est la plus fréquente :\n"
            "  - le code est inventé ou périmé ;\n"
            "  - le code est emprunté à l'AUTRE grille, où il existe et désigne "
            "autre chose.\n\n"
            f"Codes valides : {sorted(connus)}\n"
            f"Source : {grille['source']}"
        )


def test_au_moins_un_lab_cite_chaque_grille() -> None:
    """Sans cela, une grille pourrait pourrir sans que rien ne la relise.

    Ce test ne juge pas la couverture du blueprint, il constate seulement que
    les deux grilles servent. Une grille que plus aucun lab ne cite est soit à
    retirer, soit le signe qu'une section entière a perdu ses références.
    """
    par_examen: dict[str, int] = {"associate": 0, "professional": 0}
    for rel in tous_les_labs():
        if citations(rel):
            par_examen[examen_du_lab(rel)] += 1

    for examen, combien in par_examen.items():
        assert combien, (
            f"Aucun lab ne cite d'objectif de la grille {examen}. Soit la grille "
            "ne sert plus, soit les citations ont disparu des scénarios."
        )


# --------------------------------------------------------------------------
# 3. Le LIBELLÉ accolé au code, seule vérification qui attrape le vrai défaut.
# --------------------------------------------------------------------------
def _sans_accents(texte: str) -> str:
    decompose = unicodedata.normalize("NFD", texte.lower())
    return "".join(c for c in decompose if unicodedata.category(c) != "Mn")


def libelles(rel: str) -> list[tuple[str, str, str]]:
    """Les couples (fichier, code, libellé) que le lab accole à ses citations.

    Un libellé suit soit entre parenthèses, `4c (refactorer un module)`, soit
    après une virgule, `2d, les meta-arguments`. Un code seul, `4a.`, n'est pas
    contrôlable et n'est pas rendu.
    """
    trouves = []
    for nom in FICHIERS_LUS:
        chemin = LABS / rel / nom
        if not chemin.is_file():
            continue
        for m in CITATION_LIBELLE.finditer(chemin.read_text(encoding="utf-8")):
            code = m.group("code")
            libelle = m.group("paren") or m.group("virgule") or ""
            if libelle.strip():
                trouves.append((nom, code, libelle.strip()))
    return trouves


@pytest.mark.parametrize("rel", tous_les_labs())
def test_le_libelle_cite_ne_contredit_pas_la_grille(rel: str) -> None:
    """Ce test est la raison d'être du fichier, et il a fallu deux essais.

    Le premier se contentait de vérifier que le code EXISTE dans la grille. Il
    passait au vert sur le défaut qu'il devait fermer : `1b` existe dans les
    deux grilles. Un test qui ne tombe pas sur le cas qui l'a motivé ne mesure
    rien, il rassure.

    Celui-ci compare le libellé que le lab accole à son code aux fragments que
    `curriculums.yml` associe à ce code. Un libellé qui n'en contient aucun
    signale un code emprunté à l'autre grille, ou un lab qui a dérivé de
    l'objectif qu'il annonce.
    """
    examen = examen_du_lab(rel)
    table = mots_cles()[examen]
    grille = curriculums()[examen]

    for fichier, code, libelle in libelles(rel):
        if code not in table:
            continue  # un objectif de premier niveau, sans mots-clés propres
        normalise = _sans_accents(libelle)
        attendus = table[code]
        assert any(_sans_accents(f) in normalise for f in attendus), (
            f"{rel}/{fichier} cite `{code}` avec le libellé « {libelle} », qui "
            f"ne correspond à rien de ce que ce code désigne.\n\n"
            f"Grille {grille['nom']} :\n"
            f"  {code} = {grille['objectifs'][int(code[0])]['sous_objectifs'][code]}\n\n"
            f"Fragments attendus dans le libellé : {attendus}\n\n"
            "Trois causes, par ordre de fréquence :\n"
            "  - le code vient de l'AUTRE grille, où il désigne bien ce libellé ;\n"
            "  - le lab a dérivé et ne vise plus l'objectif qu'il annonce ;\n"
            "  - le libellé est une traduction que les fragments ne couvrent "
            "pas encore, et c'est `curriculums.yml` qu'il faut enrichir.\n\n"
            f"Source : {grille['source']}"
        )
