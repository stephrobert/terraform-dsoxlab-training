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

from conftest import exiger_workdir, message, workdir_lab

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
    assert proc.returncode == 0, message(
        en="`terraform output -json` failed in `examen/`.\n\nThe marking scheme was not "
        "applied: run `terraform init` then `terraform apply` in that "
        f"directory.\n{proc.stderr[-800:]}",
        fr="`terraform output -json` a échoué dans `examen/`.\n\nLe barème n'a pas "
        "été appliqué : lancez `terraform init` puis `terraform apply` dans ce "
        f"répertoire.\n{proc.stderr[-800:]}",
    )
    return {cle: valeur["value"] for cle, valeur in json.loads(proc.stdout or "{}").items()}


@pytest.fixture(scope="module")
def etat_atelier(joue: Path) -> dict:
    proc = _tf("show", "-json", cwd=joue / ATELIER)
    assert proc.returncode == 0, message(
        en=f"`terraform show -json` failed in `atelier/`.\n{proc.stderr[-800:]}",
        fr=f"`terraform show -json` a échoué dans `atelier/`.\n{proc.stderr[-800:]}",
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
    assert ressources, message(
        en="`atelier/` has no resource in its state.\n\nStart with it: "
        "the last four questions of the exam are about what it produces "
        "and have no answer before that.",
        fr="`atelier/` n'a aucune ressource dans son état.\n\nCommencez par lui : "
        "les quatre dernières questions de l'examen portent sur ce qu'il produit "
        "et n'ont pas de réponse avant.",
    )

    geres = sorted(r["address"] for r in ressources if r["mode"] == "managed")
    lues = sorted(r["address"] for r in ressources if r["mode"] == "data")

    assert len(geres) == 4, message(
        en=f"The workshop carries {len(geres)} objects in `mode: managed`, four expected."
        f"\nPresent: {geres}",
        fr=f"L'atelier porte {len(geres)} objets en `mode: managed`, quatre attendus."
        f"\nPrésents : {geres}",
    )
    assert len(lues) == 1, message(
        en=f"The workshop carries {len(lues)} blocks in `mode: data`, a single one expected.\n"
        f"Present: {lues}\n\nA `data` block READS, it does not create: copying the "
        "content into a resource would make it `managed`.",
        fr=f"L'atelier porte {len(lues)} blocs en `mode: data`, un seul attendu.\n"
        f"Présents : {lues}\n\nUn bloc `data` LIT, il ne crée pas : recopier le "
        "contenu dans une ressource le ferait passer en `managed`.",
    )


def test_la_dependance_explicite_et_le_remplacement_sont_declares(joue: Path) -> None:
    """Deux exigences que seul le plan JSON expose, et qu'aucune sortie ne dit.

    La configuration est lue dans `configuration.root_module`, ou Terraform
    rend ce qu'il a compris : les `depends_on` de chaque bloc, et non le texte
    des fichiers.
    """
    plan = _tf("plan", "-out=verif.tfplan", "-input=false", "-no-color", cwd=joue / ATELIER)
    assert plan.returncode == 0, message(
        en=f"The plan failed in `atelier/`.\n{plan.stderr[-800:]}",
        fr=f"Le plan a échoué dans `atelier/`.\n{plan.stderr[-800:]}",
    )

    montre = _tf("show", "-json", "verif.tfplan", cwd=joue / ATELIER)
    montre.check_returncode()
    config = json.loads(montre.stdout)["configuration"]["root_module"]

    avec_depends_on = [
        r["address"] for r in config.get("resources", []) if r.get("depends_on")
    ]
    assert avec_depends_on, message(
        en="No resource in `atelier/` carries a `depends_on`.\n\nOne of the "
        "resources depends on the BEHAVIOUR of another without using any of "
        "its data: no reference can express that link.",
        fr="Aucune ressource de `atelier/` ne porte de `depends_on`.\n\nUne des "
        "ressources dépend du COMPORTEMENT d'une autre sans utiliser aucune de "
        "ses données : aucune référence ne peut exprimer ce lien.",
    )


def test_le_bloc_check_avertit_sans_bloquer(etat_atelier: dict) -> None:
    """Un `check` est le seul des cinq mecanismes qui n'arrete pas Terraform.

    Sa presence se lit dans le tableau `checks`, ou son `kind` vaut `check`,
    la precondition et la postcondition portant `resource`.
    """
    genres = {c["address"]["kind"] for c in etat_atelier.get("checks", [])}
    assert "check" in genres, message(
        en=f"No `check` block in the state of `atelier/`. Kinds present: "
        f"{sorted(genres) or 'none'}.\n\nA `check` block is declared at the "
        "ROOT level, never inside a resource.",
        fr=f"Aucun bloc `check` dans l'état de `atelier/`. Genres présents : "
        f"{sorted(genres) or 'aucun'}.\n\nUn bloc `check` se déclare au niveau "
        "RACINE, jamais dans une ressource.",
    )
    assert "resource" in genres, message(
        en="No `precondition` or `postcondition` in the state of `atelier/`: "
        f"kinds present {sorted(genres)}.\n\nThose two checks live in the "
        "resource's `lifecycle` block, and carry `kind: resource`.",
        fr="Aucune `precondition` ni `postcondition` dans l'état de `atelier/` : "
        f"genres présents {sorted(genres)}.\n\nCes deux contrôles vivent dans le "
        "bloc `lifecycle` de la ressource, et portent `kind: resource`.",
    )


def test_la_valeur_sensible_est_masquee_a_l_ecran_et_en_clair_dans_le_state(
    joue: Path,
) -> None:
    """Les deux cotes, et c'est la question q40 qui les croise.

    Mesure faite en ecrivant le lab : `terraform output -json` rend la valeur
    d'un output sensible. Seul `terraform output` sans `-json` la masque.
    """
    humaine = _tf("output", "-no-color", cwd=joue / ATELIER)
    assert humaine.returncode == 0, message(
        en=f"`terraform output` failed.\n{humaine.stderr}",
        fr=f"`terraform output` a échoué.\n{humaine.stderr}",
    )
    ligne = next(
        (ligne for ligne in humaine.stdout.splitlines() if ligne.startswith("jeton_expose")),
        "",
    )
    assert "<sensitive>" in ligne, message(
        en=f"The display returns {ligne!r}: the `jeton_expose` output is not marked "
        "sensitive. Terraform would in fact have refused to plan.",
        fr=f"L'affichage rend {ligne!r} : la sortie `jeton_expose` n'est pas marquée "
        "sensible. Terraform aurait d'ailleurs refusé de planifier.",
    )

    etat = json.loads((joue / ATELIER / "terraform.tfstate").read_text(encoding="utf-8"))
    valeur = etat["outputs"]["jeton_expose"]["value"]
    assert valeur, message(
        en="The sensitive value does not appear in `terraform.tfstate`. It should: "
        "`sensitive` hides a display, it encrypts nothing.",
        fr="La valeur sensible ne figure pas dans `terraform.tfstate`. Elle devrait : "
        "`sensitive` cache un affichage, il ne chiffre rien.",
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
    assert isinstance(empreintes, dict), message(
        en="The `empreintes` output is missing from `examen/`. The marking scheme was modified "
        "or replaced.",
        fr="La sortie `empreintes` est absente de `examen/`. Le barème a été modifié "
        "ou remplacé.",
    )
    assert len(empreintes) == QUESTIONS_ATTENDUES, message(
        en=f"The marking scheme carries {len(empreintes)} questions, {QUESTIONS_ATTENDUES} "
        "expected.",
        fr=f"Le barème porte {len(empreintes)} questions, {QUESTIONS_ATTENDUES} "
        "attendues.",
    )
    mauvaises = [q for q, h in empreintes.items() if len(h) != 64 or not set(h) <= set("0123456789abcdef")]
    assert not mauvaises, message(
        en=f"These entries are not sha256 fingerprints: {sorted(mauvaises)}.",
        fr=f"Ces entrées ne sont pas des empreintes sha256 : {sorted(mauvaises)}.",
    )


def test_aucune_question_n_est_laissee_sans_reponse(sorties_examen: dict) -> None:
    sans = sorties_examen.get("sans_reponse")
    assert sans == [], message(
        en=f"{len(sans)} unanswered question(s): {sans}\n\nAn entry left at "
        "`???` counts as an absence. The exam is taken in full.",
        fr=f"{len(sans)} question(s) sans réponse : {sans}\n\nUne entrée laissée à "
        "`???` compte comme une absence. L'examen se passe en entier.",
    )


def test_le_score_global_atteint_le_seuil(sorties_examen: dict) -> None:
    score = sorties_examen.get("score")
    assert isinstance(score, (int, float)), message(
        en="The `score` output is missing.",
        fr="La sortie `score` est absente.",
    )
    assert score >= SCORE_MINIMAL, message(
        en=f"Overall score: {score}%, threshold {SCORE_MINIMAL}%.\n\nThe detail per "
        f"objective is in `terraform output score_par_objectif`, and the detail "
        "per question in `terraform output corrige`.",
        fr=f"Score global : {score} %, seuil {SCORE_MINIMAL} %.\n\nLe détail par "
        f"objectif est dans `terraform output score_par_objectif`, et le détail "
        "par question dans `terraform output corrige`.",
    )


def test_aucun_objectif_n_est_sous_le_plancher(sorties_examen: dict) -> None:
    """Un score global flatteur peut cacher un objectif entierement rate.

    C'est le defaut d'un QCM note globalement : quarante questions permettent de
    compenser. Le plancher par objectif interdit l'impasse.
    """
    par_objectif = sorties_examen.get("score_par_objectif")
    assert isinstance(par_objectif, dict), message(
        en="The `score_par_objectif` output is missing.",
        fr="La sortie `score_par_objectif` est absente.",
    )
    assert set(par_objectif) == OBJECTIFS_ATTENDUS, message(
        en=f"Objectives graded: {sorted(par_objectif)}.\nThe eight of the "
        f"syllabus were expected: {sorted(OBJECTIFS_ATTENDUS)}.",
        fr=f"Objectifs notés : {sorted(par_objectif)}.\nAttendu les huit du "
        f"programme : {sorted(OBJECTIFS_ATTENDUS)}.",
    )

    faibles = {n: s for n, s in par_objectif.items() if s < PLANCHER_PAR_OBJECTIF}
    assert not faibles, message(
        en=f"These objectives are below the {PLANCHER_PAR_OBJECTIF}% floor: "
        f"{faibles}\n\nA sufficient overall score can hide a whole part of the "
        "syllabus that was never revised.",
        fr=f"Ces objectifs sont sous le plancher de {PLANCHER_PAR_OBJECTIF} % : "
        f"{faibles}\n\nUn score global suffisant peut cacher un pan entier du "
        "programme jamais révisé.",
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
        assert empreintes[question] == attendue, message(
            en=f"The expected answer for {question} does not match what your "
            f"workshop produces.\n\nThe real state gives: {valeur!r}\n\nEither the workshop "
            "is not the one the lab asks for, or it was not applied. "
            "The last four questions are about ITS state.",
            fr=f"La réponse attendue pour {question} ne correspond pas à ce que votre "
            f"atelier produit.\n\nL'état réel donne : {valeur!r}\n\nSoit l'atelier "
            "n'est pas celui que le lab demande, soit il n'a pas été appliqué. "
            "Les quatre dernières questions portent sur SON état.",
        )
        assert corrige[question], message(
            en=f"{question} is wrong although your workshop answers {valeur!r}.\n\n"
            "Take the value from the state rather than guessing it: that is the whole "
            "point of these four questions.",
            fr=f"{question} est fausse alors que votre atelier répond {valeur!r}.\n\n"
            "Relevez la valeur dans l'état plutôt que de la deviner : c'est tout "
            "l'objet de ces quatre questions.",
        )


def test_les_deux_repertoires_sont_stables(joue: Path) -> None:
    """Les deux cotes, et celui de gauche serait vrai d'un repertoire vide.

    Accole a la convergence de l'examen, il dit autre chose : les deux moities
    ont ete appliquees, et aucune ne derive. Un `check` mal place, interrogeant
    une donnee relue a chaque plan, ramenerait un code 2 ici.
    """
    for nom in (ATELIER, EXAMEN):
        plan = _tf("plan", "-detailed-exitcode", "-input=false", "-no-color", cwd=joue / nom)
        assert plan.returncode == 0, message(
            en=f"`plan -detailed-exitcode` returns {plan.returncode} in `{nom}/`, "
            "expected 0.\n\n"
            + (
                "A code 2 signals a pending change: the directory was "
                "not applied, or something has drifted.\n"
                if plan.returncode == 2
                else "A code 1 signals an error.\n"
            )
            + plan.stdout[-800:],
            fr=f"`plan -detailed-exitcode` rend {plan.returncode} dans `{nom}/`, "
            "attendu 0.\n\n"
            + (
                "Un code 2 signale un changement en attente : le répertoire n'a "
                "pas été appliqué, ou quelque chose dérive.\n"
                if plan.returncode == 2
                else "Un code 1 signale une erreur.\n"
            )
            + plan.stdout[-800:],
        )
