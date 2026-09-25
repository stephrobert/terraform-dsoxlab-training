"""Tests fonctionnels du lab « le premier run distant, pour de vrai ».

C'est le SEUL lab du catalogue qui demande un compte HCP Terraform. Les sept
autres s'arrêtent volontairement avant l'authentification, et c'est ce qui les
rend jouables partout ; celui-ci va de l'autre côté de cette frontière, et il
est optionnel pour cette raison.

## Ce que les tests lisent, et pourquoi c'est l'API

Un state local ne prouverait rien : il dirait ce que l'apprenant a demandé, pas
ce que la plateforme a fait. Les tests interrogent donc l'API de HCP Terraform,
qui est la seule à savoir si un run a réellement tourné, sur quelle machine, et
avec quel résultat.

Le test central cherche un run à l'état `applied` sur le workspace créé. Rien,
en local, ne peut le fabriquer.

## Sans jeton, on skippe

Un apprenant qui n'a pas de compte ne doit pas voir une suite rouge : il doit
lire où trouver ce qui manque. Le message renvoie au guide, et le lab reste à
zéro sans pénaliser personne.

## Ce que le teardown détruit, et pourquoi

Tout ce que le lab a créé dans l'organisation. Laisser traîner un projet et un
workspace dans le compte de quelqu'un est pire que de lui demander de rejouer
deux `terraform apply` de trente secondes, et un lab qui ne range pas derrière
lui n'a pas sa place ici.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Iterator

import pytest

from conftest import exiger_workdir, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "hcp-terraform-premier-run-distant"

PLATEFORME = "plateforme"
APPLICATION = "application"

HOTE = "app.terraform.io"
GUIDE = "docs/hcp-token.fr.md"

# Ce que le lab impose, et que les tests vérifient côté plateforme.
PROJET_ATTENDU = "formation-terraform"
WORKSPACE_ATTENDU = "premier-run-distant"
VARIABLE_ATTENDUE = "message"


# ---------------------------------------------------------------------------
# Le jeton, et l'API.
# ---------------------------------------------------------------------------
def _jeton() -> str | None:
    """Le jeton, cherché là où Terraform le cherche, dans le même ordre.

    Repris de `scripts/diagnostic-jeton-hcp.py`, volontairement : un test qui
    chercherait ailleurs que l'outil de diagnostic donnerait deux verdicts
    contradictoires sur le même poste.
    """
    variable = "TF_TOKEN_" + HOTE.replace(".", "_")
    depuis_env = os.environ.get(variable)
    if depuis_env:
        return depuis_env

    fichier = Path.home() / ".terraform.d" / "credentials.tfrc.json"
    if not fichier.is_file():
        return None
    try:
        contenu = json.loads(fichier.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return ((contenu.get("credentials") or {}).get(HOTE) or {}).get("token")


def _api(chemin: str, jeton: str) -> dict[str, Any]:
    requete = urllib.request.Request(
        f"https://{HOTE}/api/v2{chemin}",
        headers={
            "Authorization": f"Bearer {jeton}",
            "Content-Type": "application/vnd.api+json",
        },
    )
    with urllib.request.urlopen(requete, timeout=30) as reponse:
        return json.loads(reponse.read().decode("utf-8"))


@pytest.fixture(scope="module")
def jeton() -> str:
    valeur = _jeton()
    if not valeur:
        pytest.skip(
            "Ce lab est le seul du catalogue qui demande un compte HCP "
            f"Terraform, et aucun jeton n'a été trouvé.\n\nVoir {GUIDE}, puis "
            "`python3 scripts/diagnostic-jeton-hcp.py --verifier`.\n\nLes sept "
            "autres labs `hcp-terraform` se jouent sans compte."
        )

    try:
        _api("/account/details", valeur)
    except urllib.error.HTTPError as erreur:
        if erreur.code == 401:
            pytest.skip(
                "Un jeton est en place mais l'API le refuse (401).\n\n"
                "`python3 scripts/diagnostic-jeton-hcp.py --verifier` dit "
                "pourquoi : le plus souvent, c'est le jeton OAuth de la GitHub "
                "App, affiché en permanence sur la page « Tokens », et non un "
                "jeton d'API."
            )
        raise
    except urllib.error.URLError as erreur:
        pytest.skip(f"L'API HCP Terraform est injoignable : {erreur.reason}")

    return valeur


# ---------------------------------------------------------------------------
# Le travail de l'apprenant, tel qu'il l'a laissé.
# ---------------------------------------------------------------------------
def _tf(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["terraform", *args], cwd=cwd, capture_output=True, text=True, check=False
    )


def _api_ecrire(chemin: str, jeton: str, methode: str, corps: dict | None = None):
    """Comme `_api`, mais tolérante : le ménage ne doit jamais casser la suite."""
    donnees = json.dumps(corps).encode() if corps is not None else None
    requete = urllib.request.Request(
        f"https://{HOTE}/api/v2{chemin}",
        data=donnees,
        method=methode,
        headers={
            "Authorization": f"Bearer {jeton}",
            "Content-Type": "application/vnd.api+json",
        },
    )
    try:
        with urllib.request.urlopen(requete, timeout=60) as reponse:
            texte = reponse.read().decode()
            return reponse.status, (json.loads(texte) if texte.strip() else {})
    except urllib.error.HTTPError as erreur:
        return erreur.code, {}
    except urllib.error.URLError:
        return 0, {}


def _ranger(organisation: str, jeton: str) -> None:
    """Détruit ce que le lab a créé, dans l'ordre que la plateforme impose.

    Trois choses mesurées le 2026-09-25 ont dicté cette fonction, et chacune a
    coûté un essai :

    1. **HCP refuse de supprimer un workspace qui gère des ressources.**

           409 conflict : Workspace is currently managing 1 resources. A destroy
           run must be applied to remove managed resources before the workspace
           can be safely deleted

       Il faut donc un run de destruction AVANT la suppression.

    2. **Un `terraform destroy` de la plateforme casse à mi-chemin.** Il détruit
       la variable du workspace, puis bute sur ce 409. Le workspace survit alors
       sans sa variable, et le run de destruction échoue à son tour sur « The
       root module input variable "message" is not set ». On repose donc la
       variable si elle manque, au lieu de supposer l'état sain.

    3. **Le state local ne survit pas au harnais**, qui réinitialise le workdir
       entre deux exécutions. Un ménage qui en dépendrait ne trouverait plus
       rien à détruire, alors que tout existe encore côté plateforme. Le ménage
       passe donc par l'API, qui n'a besoin que des noms.
    """
    statut, ws = _api_ecrire(
        f"/organizations/{organisation}/workspaces/{WORKSPACE_ATTENDU}", jeton, "GET"
    )
    if statut == 200 and ws:
        identifiant = ws["data"]["id"]

        if ws["data"]["attributes"].get("resource-count"):
            _, variables = _api_ecrire(f"/workspaces/{identifiant}/vars", jeton, "GET")
            presentes = [
                v["attributes"]["key"] for v in (variables or {}).get("data", [])
            ]
            if VARIABLE_ATTENDUE not in presentes:
                _api_ecrire(
                    f"/workspaces/{identifiant}/vars",
                    jeton,
                    "POST",
                    {
                        "data": {
                            "type": "vars",
                            "attributes": {
                                "key": VARIABLE_ATTENDUE,
                                "value": "reposee-pour-le-menage",
                                "category": "terraform",
                                "sensitive": True,
                            },
                        }
                    },
                )

            statut, run = _api_ecrire(
                "/runs",
                jeton,
                "POST",
                {
                    "data": {
                        "type": "runs",
                        "attributes": {
                            "is-destroy": True,
                            "auto-apply": True,
                            "message": "Ménage du lab premier-run-distant",
                        },
                        "relationships": {
                            "workspace": {
                                "data": {"type": "workspaces", "id": identifiant}
                            }
                        },
                    }
                },
            )
            if statut in (200, 201):
                for _ in range(60):
                    _, courant = _api_ecrire(f"/runs/{run['data']['id']}", jeton, "GET")
                    etat = (courant or {}).get("data", {}).get("attributes", {}).get(
                        "status"
                    )
                    if etat in (
                        "applied",
                        "errored",
                        "canceled",
                        "discarded",
                        "planned_and_finished",
                    ):
                        break
                    time.sleep(5)

        _api_ecrire(f"/workspaces/{identifiant}/actions/safe-delete", jeton, "POST")

    _, projets = _api_ecrire(f"/organizations/{organisation}/projects", jeton, "GET")
    for projet in (projets or {}).get("data", []):
        if projet["attributes"]["name"] == PROJET_ATTENDU:
            _api_ecrire(f"/projects/{projet['id']}", jeton, "DELETE")
            break


@pytest.fixture(scope="module")
def plateforme(jeton: str) -> Iterator[dict]:
    """Les sorties de `plateforme/`, et le ménage à la fin."""
    exiger_workdir(WORKDIR, LAB_ID)
    repertoire = WORKDIR / PLATEFORME

    proc = _tf("output", "-json", cwd=repertoire)
    if proc.returncode != 0 or not proc.stdout.strip() or proc.stdout.strip() == "{}":
        pytest.fail(
            f"`{PLATEFORME}/` n'a pas été appliqué.\n\nRenseignez votre "
            "organisation dans `organisation.auto.tfvars`, complétez les `???`, "
            "puis :\n\n    cd plateforme && terraform init && terraform apply\n\n"
            f"{proc.stderr[-600:]}"
        )

    sorties = {c: v["value"] for c, v in json.loads(proc.stdout).items()}
    yield sorties

    organisation = sorties.get("organisation")
    if organisation:
        _ranger(organisation, jeton)


@pytest.fixture(scope="module")
def workspace(plateforme: dict, jeton: str) -> dict:
    """Le workspace, tel que l'API le décrit."""
    organisation = plateforme.get("organisation")
    nom = plateforme.get("workspace")
    assert organisation and nom, (
        f"`{PLATEFORME}/` ne rend pas les sorties attendues : {sorted(plateforme)}"
    )

    try:
        reponse = _api(f"/organizations/{organisation}/workspaces/{nom}", jeton)
    except urllib.error.HTTPError as erreur:
        if erreur.code == 404:
            pytest.fail(
                f"Le workspace `{nom}` n'existe pas dans l'organisation "
                f"`{organisation}`.\n\nLes sorties locales le décrivent, mais "
                "l'API ne le connaît pas : l'apply a-t-il vraiment abouti ?"
            )
        raise
    return reponse["data"]


# ---------------------------------------------------------------------------
# 1. La plateforme est provisionnée, et bien réglée.
# ---------------------------------------------------------------------------
def test_le_projet_existe_dans_l_organisation(plateforme: dict, jeton: str) -> None:
    organisation = plateforme["organisation"]
    projets = _api(f"/organizations/{organisation}/projects", jeton)
    noms = [p["attributes"]["name"] for p in projets.get("data", [])]

    assert PROJET_ATTENDU in noms, (
        f"Le projet `{PROJET_ATTENDU}` n'existe pas dans `{organisation}`.\n"
        f"Projets trouvés : {noms}"
    )


def test_le_workspace_vit_dans_ce_projet(
    workspace: dict, plateforme: dict, jeton: str
) -> None:
    """Un workspace créé hors du projet fonctionne : c'est bien le piège.

    Rien ne le signale, et le lab demande explicitement le contraire.
    """
    assert workspace["attributes"]["name"] == WORKSPACE_ATTENDU, (
        f"Le workspace se nomme {workspace['attributes']['name']!r}, "
        f"{WORKSPACE_ATTENDU!r} attendu."
    )

    projet_id = (
        ((workspace.get("relationships") or {}).get("project") or {}).get("data") or {}
    ).get("id")
    assert projet_id, "L'API ne rattache le workspace à aucun projet."

    projet = _api(f"/projects/{projet_id}", jeton)
    nom = projet["data"]["attributes"]["name"]
    assert nom == PROJET_ATTENDU, (
        f"Le workspace vit dans le projet `{nom}`, et non dans "
        f"`{PROJET_ATTENDU}`.\n\nUn workspace créé sans `project_id` atterrit "
        "dans le projet par défaut de l'organisation, et rien ne le signale."
    )


def test_le_workspace_execute_a_distance_et_attend_une_confirmation(
    workspace: dict,
) -> None:
    """Les deux réglages qui font de ce lab autre chose qu'un backend distant."""
    attributs = workspace["attributes"]

    assert attributs.get("execution-mode") == "remote", (
        f"Le mode d'exécution vaut {attributs.get('execution-mode')!r}, "
        "`remote` attendu.\n\nEn mode `local`, HCP Terraform ne serait plus "
        "qu'un stockage d'état : aucun run ne tournerait chez lui, et ce lab "
        "n'aurait plus d'objet.\n\nCe réglage se pose dans "
        "`tfe_workspace_settings` : l'attribut `execution_mode` de "
        "`tfe_workspace` est déprécié et disparaîtra."
    )

    assert attributs.get("auto-apply") is False, (
        f"`auto-apply` vaut {attributs.get('auto-apply')!r}, `false` attendu.\n\n"
        "Le lab veut un run qu'un humain confirme, ce qui est le réglage par "
        "défaut et le plus sûr."
    )


def test_la_variable_du_workspace_existe_et_est_sensible(
    workspace: dict, jeton: str
) -> None:
    variables = _api(f"/workspaces/{workspace['id']}/vars", jeton)
    par_nom = {
        v["attributes"]["key"]: v["attributes"] for v in variables.get("data", [])
    }

    assert VARIABLE_ATTENDUE in par_nom, (
        f"La variable `{VARIABLE_ATTENDUE}` n'existe pas dans le workspace.\n"
        f"Variables trouvées : {sorted(par_nom)}"
    )

    variable = par_nom[VARIABLE_ATTENDUE]
    assert variable["category"] == "terraform", (
        f"`{VARIABLE_ATTENDUE}` est de catégorie {variable['category']!r}, "
        "`terraform` attendu.\n\nUne variable d'environnement sert à configurer "
        "un provider ; celle-ci est une entrée de la configuration."
    )
    assert variable["sensitive"] is True, (
        f"`{VARIABLE_ATTENDUE}` n'est pas marquée sensible.\n\nUne variable "
        "sensible n'est plus lisible dans l'interface après son enregistrement, "
        "ce qui est le minimum pour une valeur qu'on refuse de mettre dans le "
        "dépôt."
    )


# ---------------------------------------------------------------------------
# 2. Un run a réellement tourné chez HCP Terraform.
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def runs(workspace: dict, jeton: str) -> list[dict]:
    return _api(f"/workspaces/{workspace['id']}/runs", jeton).get("data", [])


def test_un_run_a_ete_applique_sur_ce_workspace(runs: list[dict]) -> None:
    """Le cœur du lab, et rien en local ne peut le fabriquer.

    Ce test lit l'historique des runs du workspace chez HCP Terraform. Un
    `terraform apply` joué sur le poste, sans rattachement, n'y laisse aucune
    trace : seul un run distant en produit une.
    """
    assert runs, (
        "Aucun run n'a jamais tourné sur ce workspace.\n\nLe rattachement de "
        f"`{APPLICATION}/` est-il écrit, et l'`apply` a-t-il été lancé ?\n\n"
        "    cd application && terraform init && terraform apply"
    )

    etats = [r["attributes"]["status"] for r in runs]
    assert "applied" in etats, (
        f"Aucun run appliqué. États trouvés : {etats}\n\nUn run `planned` s'est "
        "arrêté avant l'apply : c'est le comportement attendu d'un workspace "
        "sans auto-apply, et il faut le confirmer. `terraform apply` le fait "
        "depuis la CLI ; l'interface le fait avec le bouton « Confirm & "
        "Apply »."
    )


# Les sources qu'un run du lab peut légitimement porter. Relevées le
# 2026-09-25, et la première a coûté un cycle : j'avais SUPPOSÉ l'énumération
# (`tfe-cli`, `tfe-api`, `tfe-ui`) au lieu de la mesurer, et un run déclenché
# par `terraform apply` avec un bloc `cloud` porte en réalité `terraform+cloud`.
# Le test passait pour un défaut du travail de l'apprenant alors qu'il ne
# mesurait que mon hypothèse.
SOURCES_ADMISES = {
    "terraform+cloud",  # `terraform apply` avec un bloc `cloud`, le cas du lab
    "tfe-api",  # l'API, pour qui automatise
    "tfe-ui",  # le bouton de l'interface
    "tfe-cli",  # forme historique
}


def test_le_run_a_ete_execute_par_la_plateforme(runs: list[dict]) -> None:
    """Le run doit venir d'un déclenchement légitime, et pouvoir appliquer.

    Un plan spéculatif ne prouverait rien : il ne peut, par construction, rien
    appliquer.
    """
    applique = next(
        (r for r in runs if r["attributes"]["status"] == "applied"), None
    )
    assert applique is not None, "Aucun run appliqué à examiner."

    attributs = applique["attributes"]
    source = attributs.get("source")
    assert source in SOURCES_ADMISES, (
        f"Le run vient de {source!r}, ce qui n'est pas une source attendue.\n"
        f"Sources admises : {sorted(SOURCES_ADMISES)}\n\nUn `terraform apply` "
        "lancé depuis un répertoire portant un bloc `cloud` produit "
        "`terraform+cloud`."
    )

    assert attributs.get("plan-only") is not True, (
        "Le run retenu est un plan spéculatif : il ne peut rien appliquer, et "
        "ne prouve donc pas qu'un apply a eu lieu."
    )


def test_le_state_distant_porte_la_ressource(
    workspace: dict, jeton: str
) -> None:
    """Le dernier test, et il exerce les deux côtés.

    Ce qui est exigé : que la ressource existe. Où elle existe : dans le state
    que HCP Terraform détient, et non dans un fichier du poste. Les deux
    ensemble prouvent que le calcul a bien eu lieu de l'autre côté.
    """
    versions = _api(
        f"/workspaces/{workspace['id']}/current-state-version?include=outputs",
        jeton,
    )

    inclus = versions.get("included") or []
    sorties = {
        o["attributes"]["name"]: o["attributes"] for o in inclus
    }

    assert "preuve_du_run" in sorties, (
        f"Le state distant ne porte pas la sortie `preuve_du_run`.\n"
        f"Sorties trouvées : {sorted(sorties)}\n\nLe state d'un workspace "
        "rattaché vit CHEZ HCP Terraform : si cette sortie n'y est pas, le run "
        "n'a pas produit ce qu'il devait, ou il a tourné ailleurs."
    )

    valeur = sorties["preuve_du_run"].get("value")
    assert isinstance(valeur, str) and "-" in valeur, (
        f"`preuve_du_run` vaut {valeur!r} : un nom tiré au sort par "
        "`random_pet` est attendu, de la forme `mot-mot-mot`."
    )

    assert sorties.get("empreinte_du_message", {}).get("sensitive") is True, (
        "`empreinte_du_message` n'est pas marquée sensible côté HCP.\n\n"
        "Terraform propage la sensibilité à travers les fonctions sans regarder "
        "ce qu'elles font : une empreinte dérivée d'une variable sensible reste "
        "sensible, et l'annotation est obligatoire."
    )
