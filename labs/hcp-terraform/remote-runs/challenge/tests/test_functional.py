"""Tests fonctionnels du lab « le flux d'un run, et les trois façons de le lancer ».

L'objectif 6 est evalue en QCM : aucun compte HCP Terraform. Mais ce qu'une CLI
recoit d'un run distant, « Running plan in HCP Terraform. Output will stream
here », est le flux structure que `terraform apply -json` produit aussi en local.
Ce lab fait donc produire ce flux, puis analyser.

## Pourquoi le run du lab echoue, et pourquoi c'est le sujet

Mesure du 2026-09-25, sur Terraform 1.16.1, sur la MEME configuration selon
qu'elle aboutit ou non :

    run qui aboutit    2 change_summary, `plan` puis `apply`
    run qui echoue     1 change_summary, `plan` SEUL

Autrement dit, sur un run interrompu, le seul resume que le flux porte est celui
que le plan ANNONCAIT. Il dit `add: 3` la ou deux ressources seulement ont ete
posees, et rien dans ce message ne le signale. Ce qui a reellement eu lieu ne se
lit que dans les `apply_complete`.

Un run qui reussit de bout en bout ne permettrait pas de mesurer cela : tout ce
qui est planifie aboutit, et les deux moities du flux racontent la meme chose.
La configuration fournie echoue donc volontairement sur sa troisieme ressource.

## Ce que les tests comparent, et pourquoi ce n'est pas une constante

La tentation serait d'ecrire les chiffres attendus dans les tests, `add: 3`,
`apply_complete: 2`. Ils seraient justes aujourd'hui et faux au premier
changement de la configuration ou de la version de Terraform.

Les tests RELISENT donc `flux/run.jsonl` et recalculent ce que l'analyse aurait
du rendre. Ce qui est compare, c'est l'analyse de l'apprenant a la verite de SON
flux.

## Le flux ne peut pas etre fabrique a la main

Un `run.jsonl` ecrit de toutes pieces passerait l'analyse. Les tests exigent donc
que l'etat du systeme corresponde : les deux fichiers poses existent, le
troisieme est absent, et le state porte exactement deux ressources.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from conftest import exiger_workdir, output_json, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "hcp-terraform-remote-runs"

FLUX = "flux"
ANALYSE = "analyse"
QUESTIONNAIRE = "questionnaire"

JOURNAL = "run.jsonl"

# Ce que la configuration fournie pose, et ce qu'elle ne peut pas poser.
POSES = ("socle.txt", "service.txt")
ABOUTIES = ("local_file.service", "local_file.socle")
EN_ECHEC = ("local_file.sonde",)

SOURCE_CLI = "https://developer.hashicorp.com/terraform/cloud-docs/run/cli"

REPONSES_ATTENDUES = {
    "workflow_sans_remote_apply": (
        "ui_vcs",
        "« You cannot run remote applies in workspaces that are linked to a VCS "
        "repository, since the repository serves as the workspace's source of "
        "truth. » Pour appliquer, on fusionne dans la branche suivie",
    ),
    "ce_qu_un_run_cli_envoie": (
        "une_archive_du_repertoire_local",
        "« CLI-driven runs upload an archive of your configuration directory to "
        "HCP Terraform. » Ce n'est pas un lien vers un depot : c'est le contenu "
        "du repertoire, envoye tel quel",
    ),
    "d_ou_viennent_les_variables_en_cli": (
        "du_workspace",
        "« Remote applies use the configuration code from the local working "
        "directory, but use the variable values from the specified workspace. » "
        "Le code vient du poste, les valeurs viennent du workspace",
    ),
    "workflow_pour_le_non_interactif": (
        "api",
        "« External systems cannot run the traditional apply workflow because "
        "Terraform requires console input from the user to approve plans. We "
        "recommend using the API-driven Run Workflow for non-interactive "
        "workflows when possible. »",
    ),
    "fichier_qui_exclut_de_l_upload": (
        ".terraformignore",
        "il se place dans le repertoire de configuration, et son support "
        "remonte a Terraform 0.12.11",
    ),
}


@pytest.fixture(scope="module")
def joue() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    return WORKDIR


@pytest.fixture(scope="module")
def messages(joue: Path) -> list[dict]:
    """Le flux du run, decode par les tests eux-memes.

    C'est la reference a laquelle l'analyse de l'apprenant est comparee.
    """
    journal = joue / FLUX / JOURNAL
    assert journal.is_file(), (
        f"`{FLUX}/{JOURNAL}` n'existe pas.\n\nLe run doit etre joue en "
        "enregistrant son flux :\n\n"
        "    terraform apply -auto-approve -json > run.jsonl\n\n"
        "C'est ce flux que la CLI recoit d'un run distant, un message JSON par "
        "ligne. Il rendra un code non nul : la troisieme ressource echoue, et "
        "c'est le sujet du lab."
    )

    lignes = [ligne for ligne in journal.read_text(encoding="utf-8").splitlines() if ligne.strip()]
    assert lignes, f"`{FLUX}/{JOURNAL}` est vide."

    decodes = []
    for rang, ligne in enumerate(lignes, start=1):
        try:
            decodes.append(json.loads(ligne))
        except json.JSONDecodeError as erreur:
            pytest.fail(
                f"La ligne {rang} de `{JOURNAL}` n'est pas du JSON : {erreur}\n\n"
                "Le flux s'obtient avec `-json`, et la sortie d'erreur ne s'y "
                "redirige pas : `> run.jsonl` suffit."
            )
    return decodes


# --------------------------------------------------------------------------
# 1. Le run a reellement eu lieu, et il a reellement echoue.
# --------------------------------------------------------------------------
def test_le_run_a_pose_deux_fichiers_et_pas_le_troisieme(joue: Path) -> None:
    """Sans cela, un `run.jsonl` ecrit a la main passerait tout le reste."""
    manquants = [f for f in POSES if not (joue / FLUX / f).is_file()]
    assert not manquants, (
        f"Ces fichiers n'ont pas ete poses : {manquants}\n\nLe run doit avoir "
        f"ete APPLIQUE dans `{FLUX}/`, pas seulement planifie."
    )

    impossible = joue / FLUX / "socle.txt" / "sonde.txt"
    assert not impossible.exists(), (
        f"`{impossible}` existe, ce qui ne devrait pas etre possible : "
        "`socle.txt` est un fichier. La configuration fournie a ete modifiee."
    )


def test_le_state_ne_porte_que_les_ressources_abouties(joue: Path) -> None:
    etat = show_json(joue / FLUX)
    adresses = sorted(
        r["address"]
        for r in (etat.get("values") or {}).get("root_module", {}).get("resources", [])
    )
    assert adresses == sorted(ABOUTIES), (
        f"Le state de `{FLUX}/` porte {adresses}, attendu {sorted(ABOUTIES)}.\n\n"
        "Une ressource qui a echoue n'entre pas dans le state : c'est bien "
        "pourquoi le resume du plan ne dit pas ce qui a eu lieu."
    )


def test_le_flux_est_celui_d_un_run_interrompu(messages: list[dict]) -> None:
    """Le flux doit etre celui d'un APPLY, et d'un apply qui a echoue.

    Un `terraform plan -json` produirait un flux credible mais sans aucun
    `apply_*`, et le lab entier porterait a faux.
    """
    types = Counter(m.get("type") for m in messages)

    for attendu in ("version", "planned_change", "change_summary", "apply_complete"):
        assert types.get(attendu), (
            f"Le flux ne porte aucun message `{attendu}`.\nTypes presents : "
            f"{dict(types)}\n\nLe flux attendu est celui d'un `apply`, pas celui "
            "d'un `plan`."
        )

    assert types.get("apply_errored"), (
        f"Le flux ne porte aucun message `apply_errored`.\nTypes presents : "
        f"{dict(types)}\n\nLa troisieme ressource DOIT echouer : c'est ce qui "
        "fait diverger ce que le plan annonce de ce qui a lieu. Si votre run "
        "aboutit, la configuration fournie a ete modifiee."
    )


# --------------------------------------------------------------------------
# 2. L'analyse, comparee a la verite du flux.
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def sorties(joue: Path) -> dict:
    repertoire = joue / ANALYSE

    init = terraform("init", "-input=false", "-no-color", cwd=repertoire)
    assert init.returncode == 0, f"`init` a echoue.\n{init.stderr[-800:]}"

    applique = terraform(
        "apply", "-auto-approve", "-input=false", "-no-color", cwd=repertoire
    )
    assert applique.returncode == 0, (
        f"`apply` a echoue dans `{ANALYSE}/`.\n\nUn `???` subsiste, ou une "
        "expression ne tient pas. Rappel : un fichier JSONL se decoupe en "
        "lignes AVANT d'etre decode, et sa derniere ligne est vide.\n"
        f"{applique.stderr[-1200:]}"
    )

    return {c: v["value"] for c, v in output_json(repertoire).items()}


def _entier(valeur: object) -> object:
    return int(valeur) if isinstance(valeur, (int, float)) else valeur


def test_le_compte_par_type_est_celui_du_flux(
    sorties: dict, messages: list[dict]
) -> None:
    attendu = dict(Counter(m.get("type") for m in messages))
    obtenu = sorties.get("par_type")

    assert isinstance(obtenu, dict), (
        f"`par_type` rend {type(obtenu).__name__}, une map attendue."
    )

    obtenu_entier = {t: int(n) for t, n in obtenu.items()}
    assert obtenu_entier == attendu, (
        f"`par_type` ne correspond pas au flux.\nObtenu  : {obtenu_entier}\n"
        f"Attendu : {attendu}\n\nCes chiffres sont recalcules depuis "
        f"`{FLUX}/{JOURNAL}` par le test lui-meme : ils suivent votre flux, ils "
        "ne sont pas geles."
    )


def test_le_resume_est_celui_que_le_flux_porte(
    sorties: dict, messages: list[dict]
) -> None:
    """Le piege du lab, et il se referme sur une habitude raisonnable.

    Chercher `operation == "apply"` est le reflexe juste sur un run qui
    aboutit. Sur un run interrompu, ce message n'existe pas, et le filtre rend
    `null`.
    """
    resumes = [m["changes"] for m in messages if m.get("type") == "change_summary"]
    assert len(resumes) == 1, (
        f"Le flux porte {len(resumes)} `change_summary`, un seul attendu sur un "
        "run interrompu. La configuration fournie a-t-elle ete modifiee ?"
    )
    attendu = {c: _entier(v) for c, v in resumes[0].items()}

    obtenu = sorties.get("resume_annonce")
    assert isinstance(obtenu, dict), (
        f"`resume_annonce` rend {obtenu!r}.\n\nUn filtre sur l'operation "
        "`apply` rend `null` ici : le flux d'un run INTERROMPU ne porte pas de "
        "resume d'apply. Le seul qu'il porte est celui du plan."
    )

    obtenu_normalise = {c: _entier(v) for c, v in obtenu.items()}
    assert obtenu_normalise == attendu, (
        f"`resume_annonce` ne correspond pas au flux.\nObtenu  : "
        f"{obtenu_normalise}\nAttendu : {attendu}"
    )

    assert obtenu.get("operation") == "plan", (
        f"`resume_annonce.operation` vaut {obtenu.get('operation')!r}, `plan` "
        "attendu."
    )


def test_les_adresses_abouties_et_en_echec(
    sorties: dict, messages: list[dict]
) -> None:
    abouties = sorted(
        m["hook"]["resource"]["addr"]
        for m in messages
        if m.get("type") == "apply_complete"
    )
    en_echec = sorted(
        m["hook"]["resource"]["addr"]
        for m in messages
        if m.get("type") == "apply_errored"
    )

    assert sorties.get("adresses_abouties") == abouties, (
        f"`adresses_abouties` vaut {sorties.get('adresses_abouties')}, attendu "
        f"{abouties}.\n\nLe message qui prouve qu'une ressource a abouti n'est "
        "pas celui qui annonce son changement : entre les deux, elle peut "
        "echouer."
    )
    assert sorties.get("adresses_en_echec") == en_echec, (
        f"`adresses_en_echec` vaut {sorties.get('adresses_en_echec')}, attendu "
        f"{en_echec}."
    )
    assert set(en_echec) == set(EN_ECHEC), (
        f"Le flux declare en echec {en_echec}, attendu {sorted(EN_ECHEC)}."
    )


def test_l_ecart_entre_ce_qui_est_annonce_et_ce_qui_a_eu_lieu(
    sorties: dict, messages: list[dict]
) -> None:
    """Le dernier test, et il exerce les deux cotes.

    Ce qui reste vrai : le plan annoncait trois ajouts, et le flux le dit
    encore. Ce qui est faux : en conclure que trois ressources existent. Un
    test qui ne verifierait que le resume, ou que les abouties, laisserait
    passer exactement la confusion que ce lab traite.
    """
    annonce = next(
        m["changes"]["add"] for m in messages if m.get("type") == "change_summary"
    )
    abouties = sum(1 for m in messages if m.get("type") == "apply_complete")
    attendu = int(annonce) - abouties

    obtenu = sorties.get("ecart_entre_annonce_et_abouti")
    assert obtenu is not None, "`ecart_entre_annonce_et_abouti` n'est pas rendu."
    assert int(obtenu) == attendu, (
        f"`ecart_entre_annonce_et_abouti` vaut {obtenu}, attendu {attendu}.\n\n"
        f"Le resume annonce {annonce} ajouts ; {abouties} ressources ont "
        "abouti. L'ecart est ce que le flux ne dit nulle part, et c'est "
        "pourtant ce qu'il faut savoir avant de relancer quoi que ce soit."
    )
    assert attendu > 0, (
        "L'ecart mesure est nul : le run a abouti entierement, alors que la "
        "configuration fournie doit echouer sur sa troisieme ressource."
    )


# --------------------------------------------------------------------------
# 3. Les trois workflows.
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def reponses(joue: Path) -> dict:
    repertoire = joue / QUESTIONNAIRE

    init = terraform("init", "-input=false", "-no-color", cwd=repertoire)
    assert init.returncode == 0, f"`init` a echoue.\n{init.stderr[-800:]}"

    applique = terraform(
        "apply", "-auto-approve", "-input=false", "-no-color", cwd=repertoire
    )
    assert applique.returncode == 0, (
        f"`apply` a echoue dans `{QUESTIONNAIRE}/`.\n\nUne reponse hors de "
        "l'enumere est refusee AU PLAN, et le message dit quoi ecrire.\n"
        f"{applique.stderr[-1200:]}"
    )

    return output_json(repertoire)["reponses"]["value"]


@pytest.mark.parametrize("question", sorted(REPONSES_ATTENDUES))
def test_chaque_reponse_sur_les_workflows(reponses: dict, question: str) -> None:
    attendue, pourquoi = REPONSES_ATTENDUES[question]
    obtenue = reponses.get(question)
    assert obtenue == attendue, (
        f"`{question}` vaut {obtenue!r}, {attendue!r} attendu.\n\n"
        f"{pourquoi.capitalize()}.\n\nSource : {SOURCE_CLI}"
    )
