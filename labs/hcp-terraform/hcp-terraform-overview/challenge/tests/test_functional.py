"""Tests fonctionnels du lab « le workflow d'un run, joué puis qualifié ».

L'objectif 6 est evalue en QCM : aucun compte HCP Terraform, rien ne part en
execution distante. Ce lab fait donc deux choses que rien n'oblige a separer.

## 1. Il JOUE un run, en local, et c'est possible

Un run HCP Terraform est une division stricte entre un plan et un apply, ou
l'apply reprend le plan DEJA calcule au lieu d'en refaire un. Le plan enregistre
local reproduit exactement cela, et les tests s'appuient sur trois proprietes
mesurees le 2026-09-25 sur Terraform 1.16.1 :

    terraform apply <plan>            n'ouvre AUCUNE confirmation
    le meme plan rejoue               « Saved plan is stale »
    -var passe a l'apply d'un plan    « Can't change variable when applying a
                                        saved plan »

La deuxieme est le pendant local de la file de runs d'un workspace : « the new
run won't start until the current one has completely finished, because the
current run might change what a future run would do ». La troisieme est le
pendant du verrouillage d'un run sur sa configuration version et son jeu de
variables.

## 2. Il fait QUALIFIER six runs decrits

Ce que les tests lisent la, c'est `terraform output -json` : ce que la
configuration CALCULE, jamais ce qu'elle contient. Aucune reponse constante ne
passe, et chaque cas est assere separement pour que le message dise LEQUEL est
faux.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import exiger_workdir, output_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "hcp-terraform-hcp-terraform-overview"

RUN = "run"
ANALYSE = "analyse"

PREMIER = "premier-run"
SECOND = "second-run"

PLAN1 = "run1.tfplan"
PLAN2 = "run2.tfplan"
RAPPORT = "rapport.txt"

# Releves le 2026-09-25, sur Terraform 1.16.1, chacun sur un cas minimal.
PERIME = "Saved plan is stale"
VARIABLE_FIGEE = "Can't change variable when applying a saved plan"

# L'ordre officiel des etapes, lu le 2026-09-25 sur la page « Run states and
# stages » de HCP Terraform. Le point qui surprend est au milieu : la
# verification OPA precede l'estimation de cout, celle de Sentinel la suit.
ETAPES = [
    "pending",
    "fetching",
    "pre_plan",
    "plan",
    "post_plan",
    "opa_policy_check",
    "cost_estimation",
    "sentinel_policy_check",
    "pre_apply",
    "apply",
    "post_apply",
]

SOURCE_ETATS = "https://developer.hashicorp.com/terraform/cloud-docs/run/states"
SOURCE_RUNS = (
    "https://developer.hashicorp.com/terraform/cloud-docs/run/remote-operations"
)

VERDICTS_ATTENDUS = {
    "cas1_pull_request": (
        "plan_speculatif",
        "une pull request ne declenche qu'un plan speculatif, qui ne peut RIEN "
        "appliquer. Le reglage d'auto-apply du workspace n'y change rien",
    ),
    "cas2_commit_auto_apply": (
        "apply_automatique",
        "un commit sur la branche suivie, avec auto-apply et un auteur qui a la "
        "permission d'appliquer : le seul des six qui part sans confirmation",
    ),
    "cas3_commit_sans_auto_apply": (
        "attend_confirmation",
        "sans auto-apply, le run s'arrete apres le plan et attend qu'un "
        "utilisateur habilite tranche",
    ),
    "cas4_commit_plan_sans_changement": (
        "planned_and_finished",
        "« If a plan contains no changes, HCP Terraform does not attempt to "
        "apply it. » L'auto-apply ne s'applique pas a un plan vide",
    ),
    "cas5_cli_apply_mode_local": (
        "aucun_run_distant",
        "un workspace en mode d'execution `local` ne sert plus que de backend "
        "d'etat : l'execution a lieu sur le poste, HCP Terraform n'execute rien",
    ),
    "cas6_run_trigger_auto_apply": (
        "attend_confirmation",
        "« Some plans can't be auto-applied, like plans queued by run triggers "
        "or by users without permission to apply runs. » Le reglage est actif, "
        "le declencheur n'y donne pas droit",
    ),
}

VERDICTS_ADMIS = {
    "plan_speculatif",
    "planned_and_finished",
    "apply_automatique",
    "attend_confirmation",
    "aucun_run_distant",
}

FAITS_ATTENDUS = {
    "operations_qui_ne_bloquent_pas_la_file": (
        ["planification_des_saved_plan_runs", "runs_plan_only"],
        "deux operations echappent a la file, parce qu'elles ne touchent pas "
        "l'infrastructure : les runs plan-only et la PHASE DE PLANIFICATION "
        "des saved plan runs. L'apply d'un plan enregistre, lui, bloque la file "
        "comme n'importe quel autre",
    ),
    "etape_ou_un_echec_n_arrete_plus_le_run": (
        "post_apply",
        "a toutes les autres etapes, une run task en echec arrete le run. Apres "
        "l'apply, il n'y a plus rien a arreter : l'infrastructure est deja "
        "provisionnee",
    ),
    "ce_que_fournit_encore_un_workspace_local": (
        "le_stockage_du_state",
        "le mode `local` fait du workspace un backend d'etat, et rien de plus : "
        "ni Sentinel, ni estimation de cout, ni notifications, qui reposent "
        "toutes sur l'execution distante",
    ),
}


@pytest.fixture(scope="module")
def joue() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    return WORKDIR


# --------------------------------------------------------------------------
# 1. Le run joue en deux temps.
# --------------------------------------------------------------------------
def _plan_json(repertoire: Path, fichier: str) -> dict:
    """Le contenu structure d'un plan enregistre.

    `terraform show -json <plan>` exige un repertoire initialise, ce que le
    travail de l'apprenant a fait. On relance `init` par precaution : il est
    idempotent et ne touche a aucun plan.
    """
    chemin = repertoire / fichier
    assert chemin.is_file(), (
        f"`{RUN}/{fichier}` n'existe pas.\n\nUn run HCP est un plan puis un "
        "apply de CE plan. Ici, les deux plans doivent rester sur le disque : "
        "ce sont eux qui prouvent le travail."
    )

    terraform("init", "-input=false", "-no-color", cwd=repertoire)
    proc = terraform("show", "-json", fichier, cwd=repertoire)
    assert proc.returncode == 0, (
        f"`terraform show -json {fichier}` a echoue.\n{proc.stderr[-800:]}"
    )
    return json.loads(proc.stdout)


def test_le_premier_run_a_ete_applique(joue: Path) -> None:
    """L'apply est passe, et il a pose la valeur du PREMIER plan."""
    rapport = joue / RUN / RAPPORT
    assert rapport.is_file(), (
        f"`{RUN}/{RAPPORT}` n'existe pas : le premier run n'a pas ete applique.\n\n"
        "Un plan enregistre s'applique par `terraform apply <fichier>`, et cet "
        "apply n'ouvre aucune confirmation : le plan a deja tranche."
    )

    contenu = rapport.read_text(encoding="utf-8")
    assert contenu == PREMIER, (
        f"`{RUN}/{RAPPORT}` contient {contenu!r}, {PREMIER!r} attendu.\n\n"
        "C'est la valeur du PREMIER run. Si vous y lisez celle du second, le "
        "second plan a ete applique alors qu'il devait rester en attente."
    )


def test_le_second_plan_attend_toujours_son_apply(joue: Path) -> None:
    """Le pendant local d'un run arrete en « Needs Confirmation ».

    Deux moities, et la seconde est indispensable : un plan applyable ne prouve
    rien si son apply a deja eu lieu.
    """
    repertoire = joue / RUN
    plan = _plan_json(repertoire, PLAN2)

    assert plan.get("applyable") is True, (
        f"`{PLAN2}` porte `applyable: {plan.get('applyable')}`, `true` attendu.\n\n"
        "Un plan sans changement vaut `applyable: false`, et c'est exactement "
        "ce que HCP Terraform nomme « Planned and finished ». Ici le second run "
        "doit porter un changement."
    )

    valeur = (plan.get("variables") or {}).get("message", {}).get("value")
    assert valeur == SECOND, (
        f"`{PLAN2}` a ete calcule avec `message = {valeur!r}`, {SECOND!r} "
        "attendu.\n\nUn plan enregistre FIGE les valeurs qui lui ont ete "
        "donnees : c'est ce que HCP Terraform fait d'un run, verrouille sur sa "
        "configuration version et son jeu de variables."
    )

    contenu = (repertoire / RAPPORT).read_text(encoding="utf-8")
    assert contenu != SECOND, (
        f"`{RAPPORT}` porte deja la valeur du second run.\n\nLe second plan "
        "devait rester EN ATTENTE, comme un run arrete en « Needs "
        "Confirmation ». Un plan qu'on applique aussitot ne montre plus rien "
        "de la division entre le plan et l'apply."
    )


def test_rejouer_le_premier_plan_est_refuse(joue: Path) -> None:
    """Ce qui est interdit, et la raison pour laquelle un workspace fait la queue.

    Ce test ne peut pas passer avant le travail : sans apply, le premier plan
    n'est pas perime, et sans premier plan il n'y a rien a rejouer.
    """
    repertoire = joue / RUN
    assert (repertoire / PLAN1).is_file(), (
        f"`{RUN}/{PLAN1}` n'existe pas : gardez le plan du premier run."
    )

    proc = terraform("apply", "-no-color", "-input=false", PLAN1, cwd=repertoire)
    sortie = proc.stdout + proc.stderr

    assert PERIME in sortie, (
        f"Rejouer `{PLAN1}` n'a pas ete refuse pour cause de plan perime.\n\n"
        f"Attendu : « {PERIME} ». Obtenu :\n\n{sortie[-1000:]}\n\n"
        "Ce refus est le pendant local de la file de runs d'un workspace : un "
        "run en cours peut changer ce qu'un run suivant ferait, donc le suivant "
        "attend. Si ce message n'apparait pas, c'est que le premier plan n'a "
        f"jamais ete applique.\n\nSource : {SOURCE_RUNS}"
    )


def test_un_plan_enregistre_verrouille_ses_variables(joue: Path) -> None:
    """Le dernier test du run, et il exerce les deux cotes.

    Ce qui reste permis : appliquer le plan tel qu'il a ete calcule. Ce qui est
    interdit : lui passer une autre valeur au moment de l'apply. Un test qui
    n'exercerait que le refus laisserait passer un plan vide ou illisible.
    """
    repertoire = joue / RUN
    plan = _plan_json(repertoire, PLAN2)

    changements = {
        c["address"]: c["change"] for c in plan.get("resource_changes", [])
    }
    assert "local_file.rapport" in changements, (
        "Le second plan ne porte aucun changement sur `local_file.rapport` : "
        f"{sorted(changements)}."
    )
    apres = changements["local_file.rapport"]["after"].get("content")
    assert apres == SECOND, (
        f"Le second plan ecrirait {apres!r}, {SECOND!r} attendu."
    )

    proc = terraform(
        "apply",
        "-no-color",
        "-input=false",
        "-var",
        "message=passee-a-l-apply",
        PLAN2,
        cwd=repertoire,
    )
    sortie = proc.stdout + proc.stderr

    assert VARIABLE_FIGEE in sortie, (
        "Passer `-var` a l'apply d'un plan enregistre aurait du etre refuse.\n\n"
        f"Attendu : « {VARIABLE_FIGEE} ». Obtenu :\n\n{sortie[-1000:]}\n\n"
        "C'est la meme propriete que HCP Terraform applique a un run : « If you "
        "change variables or commit new code before the run finishes, it will "
        "only affect future runs. »"
    )


# --------------------------------------------------------------------------
# 2. Les six runs qualifies.
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
        f"`apply` a echoue dans `{ANALYSE}/`.\n\nLa configuration ne calcule "
        f"pas : un `???` subsiste, ou une expression ne tient pas.\n"
        f"{applique.stderr[-1200:]}"
    )

    return {c: v["value"] for c, v in output_json(repertoire).items()}


def test_les_six_runs_sont_tous_qualifies(sorties: dict) -> None:
    verdicts = sorties.get("verdicts")
    assert isinstance(verdicts, dict), (
        f"La sortie `verdicts` rend {type(verdicts).__name__}, une map attendue."
    )
    assert set(verdicts) == set(VERDICTS_ATTENDUS), (
        f"Runs qualifies : {sorted(verdicts)}.\nAttendu les six : "
        f"{sorted(VERDICTS_ATTENDUS)}."
    )

    hors_vocabulaire = {
        nom: v for nom, v in verdicts.items() if v not in VERDICTS_ADMIS
    }
    assert not hors_vocabulaire, (
        f"Ces verdicts ne sont pas dans le vocabulaire admis : "
        f"{hors_vocabulaire}.\nAdmis : {sorted(VERDICTS_ADMIS)}."
    )


@pytest.mark.parametrize("cas", sorted(VERDICTS_ATTENDUS))
def test_chaque_run_recoit_le_bon_verdict(sorties: dict, cas: str) -> None:
    attendu, pourquoi = VERDICTS_ATTENDUS[cas]
    obtenu = sorties["verdicts"].get(cas)

    assert obtenu == attendu, (
        f"`{cas}` vaut {obtenu!r}, attendu {attendu!r}.\n\n{pourquoi.capitalize()}.\n\n"
        f"Source : {SOURCE_RUNS}"
    )


# --------------------------------------------------------------------------
# 3. Ce qui se lit, et ne se devine pas.
# --------------------------------------------------------------------------
def test_les_onze_etapes_dans_l_ordre(sorties: dict) -> None:
    obtenues = sorties.get("etapes_du_run")
    assert isinstance(obtenues, list), (
        f"`etapes_du_run` rend {type(obtenues).__name__}, une liste attendue."
    )

    assert set(obtenues) == set(ETAPES), (
        f"Les etapes citees ne sont pas les onze attendues.\n"
        f"En trop : {sorted(set(obtenues) - set(ETAPES))}\n"
        f"Manquantes : {sorted(set(ETAPES) - set(obtenues))}"
    )

    assert obtenues == ETAPES, (
        f"L'ordre n'est pas celui de la documentation.\nObtenu  : {obtenues}\n"
        f"Attendu : {ETAPES}\n\nLe point qui surprend est au milieu : la "
        "verification OPA precede l'estimation de cout, celle de Sentinel la "
        "suit. C'est ce qui fait qu'une regle Sentinel peut lire un cout "
        f"estime, et qu'une regle OPA ne le peut pas.\n\nSource : {SOURCE_ETATS}"
    )


@pytest.mark.parametrize("fait", sorted(FAITS_ATTENDUS))
def test_chaque_fait_etabli(sorties: dict, fait: str) -> None:
    faits = sorties.get("faits")
    assert isinstance(faits, dict), (
        f"`faits` rend {type(faits).__name__}, une map attendue."
    )

    attendu, pourquoi = FAITS_ATTENDUS[fait]
    obtenu = faits.get(fait)
    if isinstance(attendu, list) and isinstance(obtenu, list):
        obtenu = sorted(obtenu)

    assert obtenu == attendu, (
        f"`{fait}` vaut {obtenu!r}, attendu {attendu!r}.\n\n"
        f"{pourquoi.capitalize()}.\n\nSources : {SOURCE_ETATS} et {SOURCE_RUNS}"
    )
