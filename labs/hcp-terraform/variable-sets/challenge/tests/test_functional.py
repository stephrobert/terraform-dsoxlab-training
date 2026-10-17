"""Tests fonctionnels du lab « la precedence HCP Terraform a quinze niveaux ».

Quinze etages, et une inversion que presque personne ne voit : chez les variable
sets PRIORITY, le scope le plus LARGE gagne, alors que chez les sets normaux
c'est le plus ETROIT.

Releve a la source le 2026-09-25 :

    « When a variable set is priority, the values take precedence over any
    variables with the same key set at a more specific scope. »

## Le controle qui empeche d'ecrire la reponse cas par cas

Les six cas fournis se resolvent a la main en dix minutes, et une resolution qui
les nomme un par un passerait. Les tests rejouent donc la configuration avec
HUIT cas qu'ils generent eux-memes, que l'apprenant n'a jamais vus, dont deux
visent l'inversion.

Une resolution qui parcourt la table les traite tous. Une resolution ecrite cas
par cas n'en traite aucun.

## Ce que les tests ne lisent pas

Aucun `.tf` ni `.tfvars` de l'apprenant. Tout passe par `terraform output -json`
et par `planned_values` des plans, donc par ce que la configuration CALCULE.
"""

from __future__ import annotations

import json
import subprocess

import pytest

from conftest import exiger_workdir, message, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "hcp-terraform-variable-sets"

SOURCE = "https://developer.hashicorp.com/terraform/cloud-docs/workspaces/variables"

# La table officielle, du PLUS prioritaire au moins. Relevee a la source.
ORDRE_OFFICIEL = [
    "cli_var",
    "tf_var_env",
    "priority_global",
    "priority_org_project_scoped",
    "priority_org_workspace_scoped",
    "priority_project_project_scoped",
    "priority_project_workspace_scoped",
    "workspace",
    "set_project_workspace_scoped",
    "set_project_project_scoped",
    "set_org_workspace_scoped",
    "set_org_project_scoped",
    "set_global",
    "auto_tfvars",
    "terraform_tfvars",
]

SENTINELLE = "default_hcl"

REPONSES_ATTENDUES = {
    "set_prend_effet_au_prochain_run": (True, "un set applique prend effet au prochain run"),
    "mode_local_applique_les_variables": (
        True,
        "le mode local deporte l'EXECUTION, pas la configuration",
    ),
    "variable_hcl_attend_de_la_syntaxe": (
        True,
        "une variable HCL attend de la syntaxe HCL, pas une chaine brute",
    ),
    "variable_sensible_relisible": (
        False,
        "une variable sensible ne se relit pas, elle se remplace",
    ),
    "auto_tfvars_bat_terraform_tfvars": (
        True,
        "les *.auto.tfvars sont charges apres terraform.tfvars, et le dernier gagne",
    ),
}

# Huit cas que l'apprenant ne voit pas. Deux visent l'inversion, un est vide.
CAS_DE_CONTROLE = {
    "ctrl_inversion_priority": (
        {"priority_org_workspace_scoped": "large", "priority_project_project_scoped": "etroit"},
        "priority_org_workspace_scoped",
        "chez les sets PRIORITY, le proprietaire le plus large gagne",
    ),
    "ctrl_inversion_normaux": (
        {"set_project_project_scoped": "etroit", "set_org_workspace_scoped": "large"},
        "set_project_project_scoped",
        "chez les sets NORMAUX, c'est l'inverse : le plus etroit gagne",
    ),
    "ctrl_cli_bat_tout": (
        {"cli_var": "a", "priority_global": "b", "workspace": "c"},
        "cli_var",
        "rien ne bat la ligne de commande",
    ),
    "ctrl_env_bat_priority": (
        {"tf_var_env": "a", "priority_global": "b"},
        "tf_var_env",
        "TF_VAR_ bat tous les variable sets, y compris prioritaires",
    ),
    "ctrl_priority_bat_workspace": (
        {"priority_project_workspace_scoped": "a", "workspace": "b"},
        "priority_project_workspace_scoped",
        "le moins prioritaire des sets priority bat encore la variable de workspace",
    ),
    "ctrl_workspace_bat_sets_normaux": (
        {"workspace": "a", "set_project_workspace_scoped": "b"},
        "workspace",
        "une variable de workspace bat tous les sets normaux",
    ),
    "ctrl_fichiers_en_dernier": (
        {"set_global": "a", "auto_tfvars": "b", "terraform_tfvars": "c"},
        "set_global",
        "les fichiers sont EN BAS de la table, le moindre set les bat",
    ),
    "ctrl_vide": ({}, SENTINELLE, "un cas sans aucune source resout sur la sentinelle"),
}


def _tf(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["terraform", *args], cwd=WORKDIR, capture_output=True, text=True, check=False
    )


@pytest.fixture(scope="module")
def sorties() -> dict:
    exiger_workdir(WORKDIR, LAB_ID)

    init = _tf("init", "-input=false", "-no-color")
    assert init.returncode == 0, message(
        en=f"`terraform init` failed.\n{init.stderr[-1000:]}",
        fr=f"`terraform init` a échoué.\n{init.stderr[-1000:]}",
    )

    applique = _tf("apply", "-auto-approve", "-input=false", "-no-color")
    assert applique.returncode == 0, message(
        en=f"`terraform apply` failed: a `???` remains, or an expression does not "
        f"hold.\n{applique.stderr[-1200:]}",
        fr=f"`terraform apply` a échoué : un `???` subsiste, ou une expression ne "
        f"tient pas.\n{applique.stderr[-1200:]}",
    )

    proc = _tf("output", "-json")
    proc.check_returncode()
    return {c: v["value"] for c, v in json.loads(proc.stdout or "{}").items()}


def _resolutions_avec(cas: dict) -> dict:
    """Ce que la configuration resout sur des cas qu'elle n'a jamais vus.

    Le plan est lu plutot qu'applique : on interroge une configuration, on ne
    modifie pas l'etat de l'apprenant.
    """
    plan = _tf(
        "plan", "-input=false", "-no-color", "-out=controle.tfplan",
        "-var", f"cas={json.dumps(cas)}",
    )
    assert plan.returncode == 0, message(
        en=f"The control plan failed.\n\nA resolution assuming that every case "
        f"carries at least one source falls over here: the empty case is one of them.\n"
        f"{plan.stderr[-1200:]}",
        fr=f"Le plan de contrôle a échoué.\n\nUne résolution qui suppose qu'un cas "
        f"porte au moins une source tombe ici : le cas vide en fait partie.\n"
        f"{plan.stderr[-1200:]}",
    )
    montre = _tf("show", "-json", "controle.tfplan")
    montre.check_returncode()
    return json.loads(montre.stdout)["planned_values"]["outputs"]["resolutions"]["value"]


# --------------------------------------------------------------------------
# 1. La table, position par position.
# --------------------------------------------------------------------------
def test_la_table_de_precedence_est_complete_et_sans_doublon(sorties: dict) -> None:
    ordre = sorties.get("ordre_precedence")
    assert isinstance(ordre, list), message(
        en=f"`ordre_precedence` returns {type(ordre).__name__}, a list was expected.",
        fr=f"`ordre_precedence` rend {type(ordre).__name__}, une liste attendue.",
    )
    assert len(ordre) == 15, message(
        en=f"The table carries {len(ordre)} entries, fifteen expected.",
        fr=f"La table porte {len(ordre)} entrées, quinze attendues.",
    )
    assert len(set(ordre)) == 15, message(
        en=f"The table carries duplicates: "
        f"{sorted({s for s in ordre if ordre.count(s) > 1})}.",
        fr=f"La table porte des doublons : "
        f"{sorted({s for s in ordre if ordre.count(s) > 1})}.",
    )
    inconnus = set(ordre) - set(ORDRE_OFFICIEL)
    assert not inconnus, message(
        en=f"These identifiers do not appear in `VOCABULAIRE.md`: "
        f"{sorted(inconnus)}.",
        fr=f"Ces identifiants ne figurent pas dans `VOCABULAIRE.md` : "
        f"{sorted(inconnus)}.",
    )


def test_la_table_est_dans_l_ordre_officiel(sorties: dict) -> None:
    """Comparee position par position : une seule inversion fait echouer.

    Le message nomme la premiere divergence plutot que de rendre les deux
    listes : sur quinze entrees, un diff brut ne se lit pas.
    """
    ordre = sorties["ordre_precedence"]
    # `strict=True` : si la table de l'apprenant n'a pas le bon nombre de rangs,
    # `zip` s'arrêterait en silence sur la plus courte et le test passerait
    # sur une table tronquée. On veut que cela échoue.
    for rang, (obtenu, attendu) in enumerate(
        zip(ordre, ORDRE_OFFICIEL, strict=True), start=1
    ):
        assert obtenu == attendu, message(
            en=f"At rank {rang}, the table carries {obtenu!r}, {attendu!r} expected.\n\n"
            "A reminder of the inversion: with PRIORITY sets the BROADEST "
            "scope wins (global, then project, then workspace), whereas with "
            "normal sets it is the NARROWEST (workspace, then project, "
            "then global).\n\n"
            f"Source: {SOURCE}",
            fr=f"Au rang {rang}, la table porte {obtenu!r}, {attendu!r} attendu.\n\n"
            "Rappel de l'inversion : chez les sets PRIORITY le scope le plus "
            "LARGE gagne (global, puis projet, puis workspace), alors que chez "
            "les sets normaux c'est le plus ÉTROIT (workspace, puis projet, "
            "puis global).\n\n"
            f"Source : {SOURCE}",
        )


# --------------------------------------------------------------------------
# 2. Les six cas fournis.
# --------------------------------------------------------------------------
def test_chaque_cas_fourni_est_resolu(sorties: dict) -> None:
    resolutions = sorties.get("resolutions")
    assert isinstance(resolutions, dict) and resolutions, message(
        en="`resolutions` is empty or is not a map.",
        fr="`resolutions` est vide ou n'est pas une map.",
    )
    for nom, resolu in resolutions.items():
        assert set(resolu) >= {"source", "valeur"}, message(
            en=f"`{nom}` returns {sorted(resolu)}, at least `source` and "
            "`valeur` were expected.",
            fr=f"`{nom}` rend {sorted(resolu)}, attendu au moins `source` et "
            "`valeur`.",
        )
        assert resolu["source"] in [*ORDRE_OFFICIEL, SENTINELLE], message(
            en=f"`{nom}` names the source {resolu['source']!r}, which does not exist.",
            fr=f"`{nom}` désigne la source {resolu['source']!r}, qui n'existe pas.",
        )


# --------------------------------------------------------------------------
# 3. LE controle : huit cas que l'apprenant n'a jamais vus.
# --------------------------------------------------------------------------
def test_la_resolution_tient_sur_des_cas_inconnus(sorties: dict) -> None:
    """Le seul test qu'une resolution ecrite cas par cas ne passe pas.

    Les six cas fournis se resolvent a la main. Ceux-ci sont generes ici, et
    deux d'entre eux visent l'inversion, celle qu'on croit connaitre.
    """
    cas = {nom: sources for nom, (sources, _, _) in CAS_DE_CONTROLE.items()}
    obtenu = _resolutions_avec(cas)

    assert set(obtenu) == set(CAS_DE_CONTROLE), message(
        en=f"The resolution returns {sorted(obtenu)}, expected {sorted(CAS_DE_CONTROLE)}."
        "\n\nIt therefore does not follow the variable: some cases are named by hand.",
        fr=f"La résolution rend {sorted(obtenu)}, attendu {sorted(CAS_DE_CONTROLE)}."
        "\n\nElle ne suit donc pas la variable : des cas sont nommés en dur.",
    )

    for nom, (sources, attendue, pourquoi) in CAS_DE_CONTROLE.items():
        assert obtenu[nom]["source"] == attendue, message(
            en=f"`{nom}` resolves on {obtenu[nom]['source']!r}, {attendue!r} "
            f"expected.\n\nSources filled in: {sorted(sources) or 'none'}\n"
            f"Because {pourquoi}.\n\nSource: {SOURCE}",
            fr=f"`{nom}` résout sur {obtenu[nom]['source']!r}, {attendue!r} "
            f"attendu.\n\nSources renseignées : {sorted(sources) or 'aucune'}\n"
            f"Parce que {pourquoi}.\n\nSource : {SOURCE}",
        )
        if sources:
            assert obtenu[nom]["valeur"] == sources[attendue], message(
                en=f"`{nom}` names the right source but returns the value "
                f"{obtenu[nom]['valeur']!r}, {sources[attendue]!r} expected.",
                fr=f"`{nom}` désigne la bonne source mais rend la valeur "
                f"{obtenu[nom]['valeur']!r}, {sources[attendue]!r} attendue.",
            )


def test_un_cas_sans_source_resout_sur_la_sentinelle(sorties: dict) -> None:
    """Et le PLAN doit tenir : une erreur ici ferait tomber tous les cas.

    Une indexation `[0]` sur une liste vide echoue, et sans protection c'est la
    configuration entiere qui s'arrete, pas seulement ce cas.
    """
    obtenu = _resolutions_avec({"seul_cas_vide": {}})
    assert obtenu["seul_cas_vide"]["source"] == SENTINELLE, message(
        en=f"An empty case resolves on {obtenu['seul_cas_vide']['source']!r}, "
        f"{SENTINELLE!r} expected.\n\nNeither `null` nor a plan error: a "
        "sentinel says \"nothing filled in\" instead of interrupting.",
        fr=f"Un cas vide résout sur {obtenu['seul_cas_vide']['source']!r}, "
        f"{SENTINELLE!r} attendu.\n\nNi `null`, ni une erreur de plan : une "
        "sentinelle dit « rien de renseigné » au lieu d'interrompre.",
    )


# --------------------------------------------------------------------------
# 4. Le duel lexical, et les cinq affirmations.
# --------------------------------------------------------------------------
def test_le_duel_se_tranche_par_points_de_code(sorties: dict) -> None:
    """Une map HCL n'a pas d'ordre d'insertion.

    S'appuyer sur l'ordre du fichier marcherait par hasard. Le test impose un
    jeu ou majuscules et chiffres precedent les minuscules en Unicode, ce qui
    ne correspond a aucun ordre d'ecriture naturel.
    """
    assert sorties.get("gagnant_lexical") == "equipe-donnees", message(
        en=f"`gagnant_lexical` is {sorties.get('gagnant_lexical')!r}, "
        "`equipe-donnees` expected on the default set.",
        fr=f"`gagnant_lexical` vaut {sorties.get('gagnant_lexical')!r}, "
        "`equipe-donnees` attendu sur le jeu par défaut.",
    )

    duel = {"zeta": "z", "Alpha": "A", "9beta": "9"}
    plan = _tf(
        "plan", "-input=false", "-no-color", "-out=lexical.tfplan",
        "-var", f"duel_lexical={json.dumps(duel)}",
    )
    assert plan.returncode == 0, message(
        en=f"The lexical plan failed.\n{plan.stderr[-800:]}",
        fr=f"Le plan lexical a échoué.\n{plan.stderr[-800:]}",
    )

    montre = _tf("show", "-json", "lexical.tfplan")
    montre.check_returncode()
    gagnant = json.loads(montre.stdout)["planned_values"]["outputs"]["gagnant_lexical"]["value"]
    assert gagnant == "9beta", message(
        en=f"On `zeta`, `Alpha` and `9beta`, the announced winner is {gagnant!r}, "
        "`9beta` expected.\n\nThe ordering is by Unicode CODE POINTS: "
        "digits come before capitals, which come before lower case. "
        "A sort ignoring case, or the writing order in the map, gives "
        "something else.",
        fr=f"Sur `zeta`, `Alpha` et `9beta`, le gagnant annoncé est {gagnant!r}, "
        "`9beta` attendu.\n\nLe classement se fait par POINTS DE CODE Unicode : "
        "les chiffres précèdent les majuscules, qui précèdent les minuscules. "
        "Un tri qui ignore la casse, ou l'ordre d'écriture dans la map, donne "
        "autre chose.",
    )


@pytest.mark.parametrize("affirmation", sorted(REPONSES_ATTENDUES))
def test_chaque_affirmation_est_tranchee(sorties: dict, affirmation: str) -> None:
    attendue, pourquoi = REPONSES_ATTENDUES[affirmation]
    reponses = sorties.get("reponses")
    assert isinstance(reponses, dict), message(
        en="`reponses` is not a map.",
        fr="`reponses` n'est pas une map.",
    )

    assert affirmation in reponses, message(
        en=f"`{affirmation}` is not settled. Present: {sorted(reponses)}.",
        fr=f"`{affirmation}` n'est pas tranchée. Présentes : {sorted(reponses)}.",
    )
    assert reponses[affirmation] is attendue, message(
        en=f"`{affirmation}` is {reponses[affirmation]!r}, {attendue!r} "
        f"expected.\n\nBecause {pourquoi}.\n\nSource: {SOURCE}",
        fr=f"`{affirmation}` vaut {reponses[affirmation]!r}, {attendue!r} "
        f"attendu.\n\nParce que {pourquoi}.\n\nSource : {SOURCE}",
    )


def test_la_configuration_converge(sorties: dict) -> None:
    plan = _tf("plan", "-detailed-exitcode", "-input=false", "-no-color")
    assert plan.returncode == 0, message(
        en=f"`plan -detailed-exitcode` returns {plan.returncode}, expected 0.\n"
        + plan.stdout[-800:],
        fr=f"`plan -detailed-exitcode` rend {plan.returncode}, attendu 0.\n"
        + plan.stdout[-800:],
    )
