"""Tests fonctionnels du lab « les permissions s'additionnent, elles ne s'écrasent pas ».

L'objectif 6b couvre les workspaces HCP Terraform et leurs options de
configuration, gestion des acces comprise. Il est evalue en QCM, et ce lab fait
donc ECRIRE la regle plutot que la reciter : une regle fausse se voit sur six
cas, une phrase apprise par coeur ne se voit pas.

## Le piege, et il vient d'une habitude solide

Partout ailleurs, une permission posee au niveau le plus specifique l'emporte.
Ici, non :

    « Each permission is additive, granting a user the highest level of
      permissions possible, regardless of which scope set that permission. »

Les deux exemples de la documentation encadrent exactement la regle, et le lab
les reprend comme cas 1 et cas 2 : `Manage all workspaces` au niveau
organisation l'emporte sur un `Read` de workspace, tandis que `View all
workspaces` ne l'emporte PAS sur un `Write` de workspace.

## Les deux echelles ne sont pas la meme

Lu a la source le 2026-09-25, sur les pages des permissions de workspace et de
projet :

    workspace   Read < Plan  < Write     < Admin
    projet      Read < Write < Maintain  < Admin

`plan` n'existe qu'au niveau workspace, `maintenance` qu'au niveau projet, et
les deux ne tombent pas au meme endroit de l'echelle. C'est ce qui interdit de
comparer deux niveaux « au jugé ».

## Ce que les tests lisent

`terraform output -json`, donc ce que la configuration CALCULE. Aucun `.tf`
n'est relu, et chaque cas est assere separement pour que le message dise lequel
est faux.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import exiger_workdir, message, output_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "hcp-terraform-projects-teams"

ACCES = "acces"
QUESTIONNAIRE = "questionnaire"

SOURCE_PERMISSIONS = (
    "https://developer.hashicorp.com/terraform/cloud-docs/users-teams-organizations/"
    "permissions"
)

ACCES_ATTENDUS = {
    "cas1_org_gestion_et_workspace_lecture": (
        "gestion_de_tous_les_workspaces",
        "c'est l'exemple meme de la documentation : « a team has Manage all "
        "workspaces permission for an organization, and the Read role in a "
        "workspace, then the team has Manage all workspaces permissions for the "
        "workspace ». Le droit le plus large l'emporte, meme pose au niveau le "
        "plus lointain",
    ),
    "cas2_org_vue_et_workspace_ecriture": (
        "ecriture",
        "le contre-exemple de la documentation : « the View all workspaces "
        "permission set for an organization does not override the Write role "
        "set on a specific workspace ». Additif ne veut pas dire que "
        "l'organisation gagne ; cela veut dire que le PLUS PERMISSIF gagne",
    ),
    "cas3_projet_maintenance_et_workspace_lecture": (
        "maintenance",
        "le role de projet `maintenance` se situe au-dessus de l'ecriture, donc "
        "bien au-dessus d'une lecture de workspace",
    ),
    "cas4_workspace_plan_seul": (
        "plan",
        "un seul niveau porte quelque chose, et c'est celui-la qui s'applique",
    ),
    "cas5_lecture_partout_sauf_workspace": (
        "lecture",
        "`vue_de_tous_les_workspaces` vaut une lecture, et deux lectures ne "
        "font pas une ecriture : additif ne veut pas dire cumulatif",
    ),
    "cas6_rien_nulle_part": (
        "aucun",
        "aucune equipe ne recoit d'acces par defaut",
    ),
}

NIVEAUX_ADMIS = {
    "aucun",
    "lecture",
    "plan",
    "ecriture",
    "maintenance",
    "administration",
    "gestion_de_tous_les_workspaces",
}

# Appliquer demande au moins l'ecriture : `plan` propose, il ne pose pas.
PEUVENT_APPLIQUER = [
    "cas1_org_gestion_et_workspace_lecture",
    "cas2_org_vue_et_workspace_ecriture",
    "cas3_projet_maintenance_et_workspace_lecture",
]

REPONSES_ATTENDUES = {
    "ce_qui_tranche_entre_deux_niveaux": (
        "le_plus_permissif",
        "et c'est l'inverse de l'habitude : ailleurs, le plus specifique "
        "l'emporte. Ici les permissions s'additionnent, « regardless of which "
        "scope set that permission »",
    ),
    "qui_peut_declencher_un_plan_vcs": (
        "quiconque_peut_fusionner_dans_la_branche",
        "« anyone who can merge changes to that repository's main branch can "
        "indirectly queue plans in that workspace, regardless of whether they "
        "have explicit permission to queue plans or are even a member of your "
        "HCP Terraform organization ». Le systeme integre delegue l'acces qu'on "
        "lui a donne",
    ),
    "duree_de_vie_du_jeton_run_task": (
        "dix_minutes",
        "« All access tokens created for run tasks have a lifetime of 10 "
        "minutes »",
    ),
    "role_entre_lecture_et_ecriture": (
        "plan",
        "l'echelle des roles de WORKSPACE est Read, Plan, Write, Admin. `plan` "
        "laisse proposer un changement sans pouvoir le poser",
    ),
    "role_entre_ecriture_et_admin": (
        "maintenance",
        "l'echelle des roles de PROJET est Read, Write, Maintain, Admin. "
        "`maintenance` n'existe pas au niveau workspace, et `plan` n'existe pas "
        "au niveau projet : les deux echelles ne sont pas la meme",
    ),
}


@pytest.fixture(scope="module")
def joue() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    return WORKDIR


def _applique(repertoire: Path, ou: str) -> dict:
    init = terraform("init", "-input=false", "-no-color", cwd=repertoire)
    assert init.returncode == 0, message(
        en=f"`init` failed in `{ou}/`.\n{init.stderr[-800:]}",
        fr=f"`init` a échoué dans `{ou}/`.\n{init.stderr[-800:]}",
    )

    applique = terraform(
        "apply", "-auto-approve", "-input=false", "-no-color", cwd=repertoire
    )
    assert applique.returncode == 0, message(
        en=f"`apply` failed in `{ou}/`.\n\nA `???` remains, or an expression "
        f"does not hold.\n{applique.stderr[-1200:]}",
        fr=f"`apply` a échoué dans `{ou}/`.\n\nUn `???` subsiste, ou une expression "
        f"ne tient pas.\n{applique.stderr[-1200:]}",
    )
    return {c: v["value"] for c, v in output_json(repertoire).items()}


@pytest.fixture(scope="module")
def sorties(joue: Path) -> dict:
    return _applique(joue / ACCES, ACCES)


# --------------------------------------------------------------------------
# 1. L'acces effectif, equipe par equipe.
# --------------------------------------------------------------------------
def test_les_six_equipes_sont_toutes_qualifiees(sorties: dict) -> None:
    acces = sorties.get("acces_effectif")
    assert isinstance(acces, dict), message(
        en=f"`acces_effectif` returns {type(acces).__name__}, a map was expected.",
        fr=f"`acces_effectif` rend {type(acces).__name__}, une map attendue.",
    )
    assert set(acces) == set(ACCES_ATTENDUS), message(
        en=f"Teams classified: {sorted(acces)}.\nAll six were expected: "
        f"{sorted(ACCES_ATTENDUS)}.",
        fr=f"Équipes qualifiées : {sorted(acces)}.\nAttendu les six : "
        f"{sorted(ACCES_ATTENDUS)}.",
    )

    hors_vocabulaire = {n: v for n, v in acces.items() if v not in NIVEAUX_ADMIS}
    assert not hors_vocabulaire, message(
        en=f"These levels are not on the scale: {hors_vocabulaire}.\n"
        f"Accepted: {sorted(NIVEAUX_ADMIS)}.",
        fr=f"Ces niveaux ne sont pas dans l'échelle : {hors_vocabulaire}.\n"
        f"Admis : {sorted(NIVEAUX_ADMIS)}.",
    )


@pytest.mark.parametrize("equipe", sorted(ACCES_ATTENDUS))
def test_chaque_equipe_recoit_le_bon_acces(sorties: dict, equipe: str) -> None:
    attendu, pourquoi = ACCES_ATTENDUS[equipe]
    obtenu = sorties["acces_effectif"].get(equipe)

    assert obtenu == attendu, message(
        en=f"`{equipe}` is {obtenu!r}, expected {attendu!r}.\n\n"
        f"{pourquoi.capitalize()}.\n\nA reminder of the rule: permissions "
        "ADD UP, and the effective access is the most permissive of the three "
        "levels. Which level set it does not come into play.\n\n"
        f"Source: {SOURCE_PERMISSIONS}",
        fr=f"`{equipe}` vaut {obtenu!r}, attendu {attendu!r}.\n\n"
        f"{pourquoi.capitalize()}.\n\nRappel de la règle : les permissions "
        "s'ADDITIONNENT, et l'accès effectif est le plus permissif des trois "
        "niveaux. Le niveau qui l'a posé n'entre pas en ligne de compte.\n\n"
        f"Source : {SOURCE_PERMISSIONS}",
    )


def test_seules_les_equipes_qui_ecrivent_peuvent_appliquer(sorties: dict) -> None:
    """Le test qui exerce les deux cotes de l'echelle.

    Il ne suffit pas de classer : il faut que le classement DECIDE de quelque
    chose. Une equipe qui en reste au plan doit etre exclue, et les trois qui
    ecrivent ou davantage doivent etre incluses. Une reponse qui prendrait
    « tout le monde sauf ceux qui n'ont rien » inclurait le cas 4, qui plane
    sans pouvoir appliquer ; une reponse trop stricte exclurait le cas 2, qui
    ecrit.
    """
    obtenu = sorties.get("equipes_qui_peuvent_appliquer")
    assert isinstance(obtenu, list), message(
        en=f"`equipes_qui_peuvent_appliquer` returns {type(obtenu).__name__}, a "
        "list was expected.",
        fr=f"`equipes_qui_peuvent_appliquer` rend {type(obtenu).__name__}, une "
        "liste attendue.",
    )

    assert sorted(obtenu) == sorted(PEUVENT_APPLIQUER), message(
        en=f"Teams able to apply: {sorted(obtenu)}\n"
        f"Expected: {sorted(PEUVENT_APPLIQUER)}\n\n"
        "Applying requires at least write. The `plan` role allows one to "
        "propose a change, never to make it, and that is precisely what "
        "makes it useful: it opens the review without opening production.",
        fr=f"Équipes pouvant appliquer : {sorted(obtenu)}\n"
        f"Attendu : {sorted(PEUVENT_APPLIQUER)}\n\n"
        "Appliquer demande au moins l'écriture. Le rôle `plan` permet de "
        "proposer un changement, jamais de le poser, et c'est précisément ce "
        "qui le rend utile : il ouvre la revue sans ouvrir la production.",
    )


# --------------------------------------------------------------------------
# 2. Ce qui se lit, et ne se devine pas.
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def reponses(joue: Path) -> dict:
    return _applique(joue / QUESTIONNAIRE, QUESTIONNAIRE)["reponses"]


@pytest.mark.parametrize("question", sorted(REPONSES_ATTENDUES))
def test_chaque_reponse_sur_les_acces(reponses: dict, question: str) -> None:
    attendue, pourquoi = REPONSES_ATTENDUES[question]
    obtenue = reponses.get(question)
    assert obtenue == attendue, message(
        en=f"`{question}` is {obtenue!r}, {attendue!r} expected.\n\n"
        f"{pourquoi.capitalize()}.\n\nSource: {SOURCE_PERMISSIONS}",
        fr=f"`{question}` vaut {obtenue!r}, {attendue!r} attendu.\n\n"
        f"{pourquoi.capitalize()}.\n\nSource : {SOURCE_PERMISSIONS}",
    )
