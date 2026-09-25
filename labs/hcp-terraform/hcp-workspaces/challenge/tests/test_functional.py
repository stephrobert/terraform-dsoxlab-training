"""Tests fonctionnels du lab « deux mots workspace, deux strategies ».

L'objectif 6 est evalue en QCM : aucun compte HCP Terraform, rien ne part en
execution distante.

## La frontiere du lab, assumee et mesuree

Une configuration `cloud` correcte ne s'initialise pas sans jeton : elle s'arrete
sur `Required token could not be found`. C'est justement ce qui en fait un
critere utilisable sans compte :

    configuration FAUSSE   ->  init echoue sur la faute
    configuration JUSTE    ->  init echoue sur le JETON

Les tests verifient donc que l'init s'arrete sur le jeton, et qu'aucun des
messages de faute n'apparait. Une configuration cassee ne peut pas atteindre ce
point.

## Ce que ce lab fait constater, et qui surprend

Mesure du 2026-09-25 : `terraform validate` repond « Success! The configuration
is valid. » sur deux des trois fautes de `nomme/`, `organization = var.x` comme
`name` + `tags` ensemble. Il n'attrape QUE le conflit entre `cloud` et `backend`.

Un `validate` vert ne dit donc rien du rattachement : seule l'initialisation du
backend le voit.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

import pytest

from conftest import exiger_workdir, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "hcp-terraform-hcp-workspaces"

NOMME = "nomme"
ETIQUETE = "etiquete"
QUESTIONNAIRE = "questionnaire"

ORGANISATION = "atelier-dsoxlab"
WORKSPACE = "app-prod"

# Ce qu'une configuration juste rend quand il ne manque que le jeton. Releve
# le 2026-09-25 sur Terraform 1.16.1.
FRONTIERE = "Required token could not be found"

# Les messages qui signent une configuration encore fautive, releves de la meme
# facon, un cas minimal par faute.
#
# Cette liste n'est pas un confort : elle est INDISPENSABLE. Mesure du meme
# jour, sur un cas `backend` + `cloud` et sur un cas a deux blocs `cloud`,
# `init` rend « Required token could not be found » EN PLUS de la faute. La
# marque de frontiere, seule, declarerait donc justes deux configurations
# fautives.
FAUTES = {
    "Conflicting 'cloud' and 'backend'": "un bloc `backend` cohabite avec le bloc `cloud`",
    "Invalid workspaces configuration": "`name` et `tags` figurent ensemble",
    "Variables not allowed": "le bloc `cloud` reference une valeur nommee",
    "Duplicate HCP Terraform configurations": "deux blocs `cloud` sont declares",
    # Le filet : toute faute de configuration non enumeree ci-dessus.
    "problems during initialisation": "la configuration porte une faute que "
    "l'initialisation refuse",
}

REPONSES_ATTENDUES = {
    "ce_que_nomme_un_workspace_cli": (
        "un_state",
        "`terraform workspace new` cree un etat de plus dans le meme "
        "repertoire : ni variables, ni droits, ni execution",
    ),
    "ce_que_nomme_un_workspace_hcp": (
        "une_execution",
        "un workspace HCP Terraform est une unite d'execution, avec ses "
        "variables, ses droits et son historique",
    ),
    "ou_vivent_les_variables": (
        "le_workspace_hcp",
        "avec HCP Terraform, les variables d'entree d'un run vivent dans le "
        "workspace, pas dans un fichier du depot",
    ),
    "ce_qui_exclut_name_et_tags": (
        "deux_strategies",
        "l'un nomme un workspace unique, l'autre en selectionne un ensemble : "
        "ce sont deux strategies de rattachement",
    ),
    "ce_que_validate_attrape": (
        "le_conflit_backend_seul",
        "mesure du 2026-09-25 : validate repond « Success » sur les deux autres "
        "fautes",
    ),
}


COMMENTAIRE = re.compile(r"(#|//).*$", re.MULTILINE)

# Un fichier de configuration CLI vide, hors du lab : voir `_sans_jeton`.
TFRC_VIDE = Path(tempfile.gettempdir()) / "dsoxlab-hcp-workspaces-vide.tfrc"
TFRC_VIDE.touch()


def _tf(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["terraform", *args], cwd=cwd, capture_output=True, text=True, check=False
    )


def _sans_commentaires(source: str) -> str:
    """Le HCL depouille de ses commentaires.

    Sans cela, un test qui cherche `tags` trouverait le commentaire qui
    EXPLIQUE pourquoi il ne faut pas de `tags`, et recalerait une correction
    juste. C'est arrive assez souvent pour valoir une fonction.
    """
    return COMMENTAIRE.sub("", source)


def _blocs_cloud(source: str) -> list[str]:
    """Le corps de chaque bloc `cloud`, accolades equilibrees.

    Un `split("cloud")` suffirait tant que la configuration est bien formee,
    et se tromperait des qu'elle ne l'est pas : c'est exactement le cas que ce
    lab met en scene.
    """
    nu = _sans_commentaires(source)
    corps: list[str] = []
    for debut in re.finditer(r"\bcloud\b\s*\{", nu):
        profondeur, i = 0, debut.end() - 1
        while i < len(nu):
            if nu[i] == "{":
                profondeur += 1
            elif nu[i] == "}":
                profondeur -= 1
                if profondeur == 0:
                    corps.append(nu[debut.end() : i])
                    break
            i += 1
    return corps


@pytest.fixture(scope="module")
def joue() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    return WORKDIR


def _sans_jeton() -> dict[str, str]:
    """Un environnement ou Terraform ne peut trouver aucun jeton.

    Mesure du 2026-09-25, sur la MEME configuration juste :

        poste sans jeton              -> « Required token could not be found »
        poste ayant fait `login`      -> « Failed to read organization ... »
        jeton par TF_TOKEN_...        -> « Failed to read organization ... »

    Un apprenant qui utilise HCP Terraform par ailleurs serait donc recale
    pour un travail juste. Deux gardes suffisent a rendre la mesure identique
    partout : un fichier de configuration CLI vide, qui neutralise le fichier
    de credentials, et le retrait des jetons portes par l'environnement.
    """
    env = {c: v for c, v in os.environ.items() if not c.startswith("TF_TOKEN_")}
    env["TF_CLI_CONFIG_FILE"] = str(TFRC_VIDE)
    return env


def _init(repertoire: Path) -> str:
    """La sortie d'un `init`, erreurs comprises, sur un poste sans jeton."""
    proc = subprocess.run(
        ["terraform", "init", "-input=false", "-no-color"],
        cwd=repertoire,
        env=_sans_jeton(),
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout + proc.stderr


def _atteint_la_frontiere(sortie: str, repertoire: str) -> None:
    """L'init doit s'arreter au jeton, et sur rien d'autre."""
    restantes = {
        message: raison for message, raison in FAUTES.items() if message in sortie
    }
    assert not restantes, (
        f"`{repertoire}/` porte encore des fautes de configuration :\n"
        + "\n".join(f"  - {r}" for r in restantes.values())
        + "\n\nCes messages viennent de l'initialisation du backend, et non de "
        "`validate` : mesure du 2026-09-25, `validate` repond « Success » sur "
        "deux d'entre eux."
    )

    assert FRONTIERE in sortie, (
        f"`{repertoire}/` ne s'arrete pas au jeton.\n\nUne configuration `cloud` "
        "correcte va jusqu'a la demande d'authentification, et c'est la "
        "frontiere de ce lab : il ne requiert aucun compte. Le test neutralise "
        "d'ailleurs tout jeton du poste, pour que la mesure soit la meme "
        "partout.\n\nSortie obtenue :\n\n" + sortie[-1200:]
    )


# --------------------------------------------------------------------------
# 1. Les deux rattachements vont jusqu'au jeton.
# --------------------------------------------------------------------------
def test_le_rattachement_par_nom_est_correct(joue: Path) -> None:
    _atteint_la_frontiere(_init(joue / NOMME), NOMME)


def test_le_rattachement_par_etiquettes_est_correct(joue: Path) -> None:
    _atteint_la_frontiere(_init(joue / ETIQUETE), ETIQUETE)


# --------------------------------------------------------------------------
# 2. Chaque repertoire emploie LA strategie qu'on lui demande.
# --------------------------------------------------------------------------
def test_chaque_repertoire_emploie_la_strategie_attendue(joue: Path) -> None:
    """Le seul test de ce lab qui ouvre un fichier, et c'est assume.

    Une configuration `cloud` ne s'initialise pas sans compte : ni le state ni
    le plan n'existent, donc aucune sortie structuree ne dit par quelle
    strategie le repertoire se rattache. Le fichier est la seule source.

    Les tests cherchent la presence d'arguments, jamais une mise en forme : un
    espacement different ou un ordre different passent.
    """
    nomme = _blocs_cloud((joue / NOMME / "main.tf").read_text(encoding="utf-8"))
    etiquete = _blocs_cloud((joue / ETIQUETE / "main.tf").read_text(encoding="utf-8"))

    assert len(nomme) == 1, (
        f"`{NOMME}/main.tf` declare {len(nomme)} blocs `cloud`, un attendu."
    )
    assert len(etiquete) == 1, (
        f"`{ETIQUETE}/main.tf` declare {len(etiquete)} blocs `cloud`. Il n'en "
        "existe qu'UN par configuration : le second n'ajoute pas un second "
        "rattachement, il rend la configuration invalide."
    )

    par_nom, par_etiquettes = nomme[0], etiquete[0]

    assert re.search(rf'\bname\b\s*=\s*"{WORKSPACE}"', par_nom), (
        f"`{NOMME}/` ne se rattache pas par NOM au workspace `{WORKSPACE}`."
    )
    assert not re.search(r"\btags\b", par_nom), (
        f"`{NOMME}/` porte encore des `tags`. Les deux strategies s'excluent : "
        "ce repertoire se rattache par nom SEUL."
    )
    assert re.search(rf'\borganization\b\s*=\s*"{ORGANISATION}"', par_nom), (
        f"`{NOMME}/` ne porte pas l'organisation `{ORGANISATION}` en chaine "
        "litterale.\n\nUn bloc `cloud` est resolu avant toute evaluation "
        "d'expression : il ne peut referencer aucune valeur nommee, pas meme "
        "une variable avec une valeur par defaut."
    )

    assert re.search(r"\btags\b\s*=", par_etiquettes), (
        f"`{ETIQUETE}/` ne se rattache pas par ETIQUETTES."
    )
    assert re.search(r"\bproject\b\s*=", par_etiquettes), (
        f"`{ETIQUETE}/` ne declare pas de `project`. Le rattachement attendu "
        "restreint la selection a un projet."
    )
    assert not re.search(r"\bname\b\s*=", par_etiquettes), (
        f"`{ETIQUETE}/` porte un `name` : les deux strategies s'excluent."
    )


# --------------------------------------------------------------------------
# 3. Le questionnaire.
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def reponses(joue: Path) -> dict:
    repertoire = joue / QUESTIONNAIRE

    init = _tf("init", "-input=false", "-no-color", cwd=repertoire)
    assert init.returncode == 0, (
        f"`init` a echoue dans `{QUESTIONNAIRE}/`.\n{init.stderr[-800:]}"
    )

    applique = _tf("apply", "-auto-approve", "-input=false", "-no-color", cwd=repertoire)
    assert applique.returncode == 0, (
        f"`apply` a echoue dans `{QUESTIONNAIRE}/`.\n\nUne reponse hors de "
        "l'enumere est refusee AU PLAN, et le message dit quoi ecrire.\n"
        f"{applique.stderr[-1200:]}"
    )

    proc = _tf("output", "-json", cwd=repertoire)
    proc.check_returncode()
    return json.loads(proc.stdout)["reponses"]["value"]


@pytest.mark.parametrize("question", sorted(REPONSES_ATTENDUES))
def test_chaque_reponse_du_questionnaire(reponses: dict, question: str) -> None:
    attendue, pourquoi = REPONSES_ATTENDUES[question]
    obtenue = reponses.get(question)
    assert obtenue == attendue, (
        f"`{question}` vaut {obtenue!r}, {attendue!r} attendu.\n\n"
        f"{pourquoi.capitalize()}."
    )
