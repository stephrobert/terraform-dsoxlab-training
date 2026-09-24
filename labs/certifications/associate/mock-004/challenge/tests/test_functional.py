"""Tests fonctionnels du lab « examen blanc Associate 004 ».

Un QCM corrige a la main ne prouve rien et se triche tout seul. Ici les reponses
voyagent dans un fichier de variables, Terraform les corrige lui-meme, et quatre
questions n'ont de reponse qu'apres avoir construit une infrastructure.

## Ce que les tests lisent, et ce qu'ils ne lisent pas

Rien n'est code en dur cote reponses : les tests ne detiennent que des `sha256`,
exactement comme le bareme. Ils ne peuvent donc pas servir de corrige.

La preuve centrale est un CROISEMENT : les quatre dernieres questions portent
sur l'etat de `atelier/`, et les tests recalculent ces quatre valeurs depuis cet
etat avant de les confronter aux reponses fournies. Repondre sans construire
echoue sur l'etat ; construire sans repondre echoue sur le score.

## Une mesure faite en ecrivant le lab

`terraform output -json` d'un output marque `sensitive` rend bien sa valeur :
c'est `terraform output` SANS `-json` qui masque. Le lab s'appuie sur ce fait
plutot que sur l'idee, repandue, qu'une valeur sensible serait illisible.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from conftest import exiger_workdir, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "certifications-associate-mock-004"

EXAMEN = "examen"
ATELIER = "atelier"

SEL = "dsoxlab-mock-004"

# Le score minimal, et le plancher par objectif. Un candidat peut rater un
# objectif entier et rester au-dessus de 80 % global : le plancher existe pour
# que le lab ne valide pas une impasse sur un pan du programme.
SCORE_MINIMAL = 80
PLANCHER_PAR_OBJECTIF = 50

QUESTIONS_ATTENDUES = 40
OBJECTIFS_ATTENDUS = {"1", "2", "3", "4", "5", "6", "7", "8"}

# Les quatre questions dont la reponse se relit dans l'etat de l'atelier.
Q_OBJETS_GERES = "q37"
Q_ADRESSE_DATA = "q38"
Q_CODE_PLAN = "q39"
Q_SENSIBLE_EN_CLAIR = "q40"


def _tf(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["terraform", *args], cwd=cwd, capture_output=True, text=True, check=False
    )


def _empreinte(reponse: str) -> str:
    return hashlib.sha256(f"{SEL}:{reponse}".encode()).hexdigest()


@pytest.fixture(scope="module")
def joue() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    return WORKDIR


@pytest.fixture(scope="module")
def sorties_examen(joue: Path) -> dict:
    proc = _tf("output", "-json", cwd=joue / EXAMEN)
    assert proc.returncode == 0, (
        "`terraform output -json` a echoue dans `examen/`.\n\nLe bareme n'a pas "
        "ete applique : lancez `terraform init` puis `terraform apply` dans ce "
        f"repertoire.\n{proc.stderr[-800:]}"
    )
    return {cle: valeur["value"] for cle, valeur in json.loads(proc.stdout or "{}").items()}


@pytest.fixture(scope="module")
def etat_atelier(joue: Path) -> dict:
    proc = _tf("show", "-json", cwd=joue / ATELIER)
    assert proc.returncode == 0, (
        f"`terraform show -json` a echoue dans `atelier/`.\n{proc.stderr[-800:]}"
    )
    return json.loads(proc.stdout)


def _ressources(etat: dict) -> list[dict]:
    return etat.get("values", {}).get("root_module", {}).get("resources", [])


# --------------------------------------------------------------------------
# 1. L'atelier existe, avec exactement ce que les questions interrogent.
# --------------------------------------------------------------------------
def test_l_atelier_porte_quatre_objets_geres_et_un_seul_bloc_data(
    etat_atelier: dict,
) -> None:
    ressources = _ressources(etat_atelier)
    assert ressources, (
        "`atelier/` n'a aucune ressource dans son etat.\n\nCommencez par lui : "
        "les quatre dernieres questions de l'examen portent sur ce qu'il produit "
        "et n'ont pas de reponse avant."
    )

    geres = sorted(r["address"] for r in ressources if r["mode"] == "managed")
    lues = sorted(r["address"] for r in ressources if r["mode"] == "data")

    assert len(geres) == 4, (
        f"L'atelier porte {len(geres)} objets en `mode: managed`, quatre attendus."
        f"\nPresents : {geres}"
    )
    assert len(lues) == 1, (
        f"L'atelier porte {len(lues)} blocs en `mode: data`, un seul attendu.\n"
        f"Presents : {lues}\n\nUn bloc `data` LIT, il ne cree pas : recopier le "
        "contenu dans une ressource le ferait passer en `managed`."
    )


def test_la_dependance_explicite_et_le_remplacement_sont_declares(joue: Path) -> None:
    """Deux exigences que seul le plan JSON expose, et qu'aucune sortie ne dit.

    La configuration est lue dans `configuration.root_module`, ou Terraform
    rend ce qu'il a compris : les `depends_on` de chaque bloc, et non le texte
    des fichiers.
    """
    plan = _tf("plan", "-out=verif.tfplan", "-input=false", "-no-color", cwd=joue / ATELIER)
    assert plan.returncode == 0, f"Le plan a echoue dans `atelier/`.\n{plan.stderr[-800:]}"

    montre = _tf("show", "-json", "verif.tfplan", cwd=joue / ATELIER)
    montre.check_returncode()
    config = json.loads(montre.stdout)["configuration"]["root_module"]

    avec_depends_on = [
        r["address"] for r in config.get("resources", []) if r.get("depends_on")
    ]
    assert avec_depends_on, (
        "Aucune ressource de `atelier/` ne porte de `depends_on`.\n\nUne des "
        "ressources depend du COMPORTEMENT d'une autre sans utiliser aucune de "
        "ses donnees : aucune reference ne peut exprimer ce lien."
    )


def test_le_bloc_check_avertit_sans_bloquer(etat_atelier: dict) -> None:
    """Un `check` est le seul des cinq mecanismes qui n'arrete pas Terraform.

    Sa presence se lit dans le tableau `checks`, ou son `kind` vaut `check`,
    la precondition et la postcondition portant `resource`.
    """
    genres = {c["address"]["kind"] for c in etat_atelier.get("checks", [])}
    assert "check" in genres, (
        f"Aucun bloc `check` dans l'etat de `atelier/`. Genres presents : "
        f"{sorted(genres) or 'aucun'}.\n\nUn bloc `check` se declare au niveau "
        "RACINE, jamais dans une ressource."
    )
    assert "resource" in genres, (
        "Aucune `precondition` ni `postcondition` dans l'etat de `atelier/` : "
        f"genres presents {sorted(genres)}.\n\nCes deux controles vivent dans le "
        "bloc `lifecycle` de la ressource, et portent `kind: resource`."
    )


def test_la_valeur_sensible_est_masquee_a_l_ecran_et_en_clair_dans_le_state(
    joue: Path,
) -> None:
    """Les deux cotes, et c'est la question q40 qui les croise.

    Mesure faite en ecrivant le lab : `terraform output -json` rend la valeur
    d'un output sensible. Seul `terraform output` sans `-json` la masque.
    """
    humaine = _tf("output", "-no-color", cwd=joue / ATELIER)
    assert humaine.returncode == 0, f"`terraform output` a echoue.\n{humaine.stderr}"
    ligne = next(
        (l for l in humaine.stdout.splitlines() if l.startswith("jeton_expose")), ""
    )
    assert "<sensitive>" in ligne, (
        f"L'affichage rend {ligne!r} : la sortie `jeton_expose` n'est pas marquee "
        "sensible. Terraform aurait d'ailleurs refuse de planifier."
    )

    etat = json.loads((joue / ATELIER / "terraform.tfstate").read_text(encoding="utf-8"))
    valeur = etat["outputs"]["jeton_expose"]["value"]
    assert valeur, (
        "La valeur sensible ne figure pas dans `terraform.tfstate`. Elle devrait : "
        "`sensitive` cache un affichage, il ne chiffre rien."
    )


# --------------------------------------------------------------------------
# 2. Le questionnaire.
# --------------------------------------------------------------------------
def test_le_bareme_n_a_pas_ete_retouche(sorties_examen: dict) -> None:
    """Le bareme est fourni : le modifier serait la facon la plus simple de tricher.

    Les tests ne detiennent aucune reponse, seulement le nombre de questions et
    la forme des empreintes. Une table tronquee ou reecrite se voit.
    """
    empreintes = sorties_examen.get("empreintes")
    assert isinstance(empreintes, dict), (
        "La sortie `empreintes` est absente de `examen/`. Le bareme a ete modifie "
        "ou remplace."
    )
    assert len(empreintes) == QUESTIONS_ATTENDUES, (
        f"Le bareme porte {len(empreintes)} questions, {QUESTIONS_ATTENDUES} "
        "attendues."
    )
    mauvaises = [q for q, h in empreintes.items() if len(h) != 64 or not set(h) <= set("0123456789abcdef")]
    assert not mauvaises, (
        f"Ces entrees ne sont pas des empreintes sha256 : {sorted(mauvaises)}."
    )


def test_aucune_question_n_est_laissee_sans_reponse(sorties_examen: dict) -> None:
    sans = sorties_examen.get("sans_reponse")
    assert sans == [], (
        f"{len(sans)} question(s) sans reponse : {sans}\n\nUne entree laissee a "
        "`???` compte comme une absence. L'examen se passe en entier."
    )


def test_le_score_global_atteint_le_seuil(sorties_examen: dict) -> None:
    score = sorties_examen.get("score")
    assert isinstance(score, (int, float)), "La sortie `score` est absente."
    assert score >= SCORE_MINIMAL, (
        f"Score global : {score} %, seuil {SCORE_MINIMAL} %.\n\nLe detail par "
        f"objectif est dans `terraform output score_par_objectif`, et le detail "
        "par question dans `terraform output corrige`."
    )


def test_aucun_objectif_n_est_sous_le_plancher(sorties_examen: dict) -> None:
    """Un score global flatteur peut cacher un objectif entierement rate.

    C'est le defaut d'un QCM note globalement : quarante questions permettent de
    compenser. Le plancher par objectif interdit l'impasse.
    """
    par_objectif = sorties_examen.get("score_par_objectif")
    assert isinstance(par_objectif, dict), "La sortie `score_par_objectif` est absente."
    assert set(par_objectif) == OBJECTIFS_ATTENDUS, (
        f"Objectifs notes : {sorted(par_objectif)}.\nAttendu les huit du "
        f"programme : {sorted(OBJECTIFS_ATTENDUS)}."
    )

    faibles = {n: s for n, s in par_objectif.items() if s < PLANCHER_PAR_OBJECTIF}
    assert not faibles, (
        f"Ces objectifs sont sous le plancher de {PLANCHER_PAR_OBJECTIF} % : "
        f"{faibles}\n\nUn score global suffisant peut cacher un pan entier du "
        "programme jamais revise."
    )


# --------------------------------------------------------------------------
# 3. Le croisement : les deux moities se repondent l'une a l'autre.
# --------------------------------------------------------------------------
def test_les_quatre_dernieres_reponses_concordent_avec_l_etat_reel(
    joue: Path, sorties_examen: dict, etat_atelier: dict
) -> None:
    """La preuve qui empeche de deviner, et celle qui empeche de bacler.

    Les tests recalculent ces quatre valeurs depuis l'etat de `atelier/`, puis
    les confrontent aux empreintes du bareme. Ils ne detiennent aucune reponse :
    ils la DEDUISENT de l'infrastructure construite, et le hachage les compare.

    Consequence voulue : un atelier different produirait d'autres reponses, et
    le bareme les refuserait. Les deux moities du lab se tiennent.
    """
    ressources = _ressources(etat_atelier)
    geres = [r["address"] for r in ressources if r["mode"] == "managed"]
    lues = [r["address"] for r in ressources if r["mode"] == "data"]

    plan = _tf("plan", "-detailed-exitcode", "-input=false", "-no-color", cwd=joue / ATELIER)

    etat_fichier = json.loads(
        (joue / ATELIER / "terraform.tfstate").read_text(encoding="utf-8")
    )
    en_clair = bool(etat_fichier["outputs"]["jeton_expose"]["value"])

    releve = {
        Q_OBJETS_GERES: str(len(geres)),
        Q_ADRESSE_DATA: lues[0] if lues else "",
        Q_CODE_PLAN: str(plan.returncode),
        Q_SENSIBLE_EN_CLAIR: "v" if en_clair else "f",
    }

    empreintes = sorties_examen["empreintes"]
    corrige = sorties_examen["corrige"]

    for question, valeur in releve.items():
        attendue = _empreinte(valeur.lower().strip())
        assert empreintes[question] == attendue, (
            f"La reponse attendue pour {question} ne correspond pas a ce que votre "
            f"atelier produit.\n\nL'etat reel donne : {valeur!r}\n\nSoit l'atelier "
            "n'est pas celui que le lab demande, soit il n'a pas ete applique. "
            "Les quatre dernieres questions portent sur SON etat."
        )
        assert corrige[question], (
            f"{question} est fausse alors que votre atelier repond {valeur!r}.\n\n"
            "Relevez la valeur dans l'etat plutot que de la deviner : c'est tout "
            "l'objet de ces quatre questions."
        )


def test_les_deux_repertoires_sont_stables(joue: Path) -> None:
    """Les deux cotes, et celui de gauche serait vrai d'un repertoire vide.

    Accole a la convergence de l'examen, il dit autre chose : les deux moities
    ont ete appliquees, et aucune ne derive. Un `check` mal place, interrogeant
    une donnee relue a chaque plan, ramenerait un code 2 ici.
    """
    for nom in (ATELIER, EXAMEN):
        plan = _tf("plan", "-detailed-exitcode", "-input=false", "-no-color", cwd=joue / nom)
        assert plan.returncode == 0, (
            f"`plan -detailed-exitcode` rend {plan.returncode} dans `{nom}/`, "
            "attendu 0.\n\n"
            + (
                "Un code 2 signale un changement en attente : le repertoire n'a "
                "pas ete applique, ou quelque chose derive.\n"
                if plan.returncode == 2
                else "Un code 1 signale une erreur.\n"
            )
            + plan.stdout[-800:]
        )
