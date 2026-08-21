"""Tests fonctionnels du lab « workspaces ou configurations separees ».

Les tests n'ouvrent jamais un `.tf` de l'apprenant : ils interrogent l'etat
structure, `terraform show -json` et `terraform output -json`.

Faits verifies sur Terraform 1.15.4, hors ligne, providers `local` et `random` :

- un bloc `backend` refuse toute valeur nommee (`Error: Variables not allowed`),
  la ou un bloc `provider` accepte les expressions : c'est ce qui rend le
  backend, donc l'etat et ses droits, impossible a faire varier par workspace ;
- la seule passerelle entre deux racines est la lecture de l'ETAT distant par
  ses outputs declares, ce que prouve une entree `mode: data` de type
  `terraform_remote_state` ;
- les workspaces non `default` d'un backend local rangent leur etat sous
  `terraform.tfstate.d/<nom>/`.
"""

import json
import os
import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "environments-when-to-use-workspaces"

RACINES = ("socle", "app")
BAC = "bac-a-sable"
TAILLES = {"dev": 2, "prod": 8}


# ── Helpers ─────────────────────────────────────────────────────────────────


def _tf(
    *args: str, cwd: Path, workspace: str | None = None
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if workspace:
        env["TF_WORKSPACE"] = workspace
    return subprocess.run(
        ["terraform", *args], cwd=cwd, capture_output=True, text=True, env=env
    )


def _racine(travail: Path, nom: str) -> Path:
    chemin = travail / nom
    if not chemin.is_dir():
        pytest.fail(f"Le repertoire {nom}/ est absent de challenge/work.")
    return chemin


def _etat(travail: Path, nom: str, workspace: str | None = None) -> dict:
    montre = _tf("show", "-json", cwd=_racine(travail, nom), workspace=workspace)
    if montre.returncode != 0:
        pytest.fail(
            f"`terraform show -json` echoue dans {nom}/. La configuration "
            f"a-t-elle ete initialisee et appliquee ?\n{montre.stderr[-700:]}"
        )
    return json.loads(montre.stdout or "{}")


def _ressources(etat: dict) -> list[dict]:
    return list(etat.get("values", {}).get("root_module", {}).get("resources", []))


def _sorties(travail: Path, nom: str, workspace: str | None = None) -> dict:
    rendu = _tf("output", "-json", cwd=_racine(travail, nom), workspace=workspace)
    if rendu.returncode != 0:
        pytest.fail(
            f"`terraform output -json` echoue dans {nom}/.\n{rendu.stderr[-700:]}"
        )
    return json.loads(rendu.stdout or "{}")


@pytest.fixture(scope="module")
def travail() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    # Les plugins ne sont pas le travail de l'apprenant : on les remet dans
    # CHACUNE des trois racines si besoin. Sans cela, un rejeu de solution dans
    # un repertoire temporaire n'a aucun provider et echoue sur le schema.
    for nom in (*RACINES, BAC):
        racine = WORKDIR / nom
        if racine.is_dir() and not (racine / ".terraform" / "providers").is_dir():
            init = _tf("init", "-input=false", "-no-color", cwd=racine)
            if init.returncode != 0:
                pytest.fail(
                    f"`terraform init` echoue dans {nom}/.\n{init.stderr[-800:]}"
                )
    yield WORKDIR


# ── 1. Le socle est applique et expose son contrat ──────────────────────────


def test_le_socle_est_applique_et_expose_deux_sorties(travail: Path) -> None:
    gerees = [
        r for r in _ressources(_etat(travail, "socle")) if r.get("mode") == "managed"
    ]
    assert gerees, "Le socle ne suit aucune ressource : il n'a pas ete applique."

    sorties = _sorties(travail, "socle")
    for attendu in ("identifiant_socle", "cidr_reseau"):
        assert attendu in sorties, (
            f"Le socle n'expose pas `{attendu}`. Ses deux outputs sont son "
            "CONTRAT : rien d'autre ne traverse la frontiere entre racines."
        )
        valeur = sorties[attendu].get("value")
        assert valeur not in (None, ""), f"L'output `{attendu}` du socle est vide."


# ── 2. L'application lit l'etat du socle ────────────────────────────────────


def test_l_application_lit_l_etat_distant_du_socle(travail: Path) -> None:
    donnees = [r for r in _ressources(_etat(travail, "app")) if r.get("mode") == "data"]
    assert donnees, (
        "L'etat de `app` ne contient aucune source de donnees. Or la seule "
        "passerelle entre deux racines est la lecture de l'etat distant de "
        "l'autre."
    )
    distants = [d for d in donnees if d.get("type") == "terraform_remote_state"]
    assert distants, (
        "Aucune source `terraform_remote_state` dans l'etat de `app` : "
        f"types trouves = {[d.get('type') for d in donnees]}."
    )


def test_la_valeur_traverse_les_deux_etats(travail: Path) -> None:
    du_socle = _sorties(travail, "socle")["identifiant_socle"]["value"]
    de_l_app = _sorties(travail, "app")

    assert "reseau_consomme" in de_l_app, "`app` n'expose pas `reseau_consomme`."
    assert de_l_app["reseau_consomme"]["value"] == du_socle, (
        f"`app` expose {de_l_app['reseau_consomme']['value']!r} alors que le "
        f"socle produit {du_socle!r}. La valeur doit VENIR du socle."
    )


def test_la_valeur_n_est_pas_recopiee_en_dur(travail: Path, tmp_path: Path) -> None:
    """Le controle qui distingue une lecture d'une copie.

    On rejoue le socle avec une AUTRE entree, dans une copie, et on exige que
    l'application suive. Une valeur recopiee en dur resterait figee.
    """
    copie = tmp_path / "derive"
    shutil.copytree(travail, copie, symlinks=True)

    rejoue = _tf(
        "apply", "-auto-approve", "-input=false", "-no-color",
        "-var", "cidr=10.9.9.0/24",
        cwd=copie / "socle",
    )
    assert rejoue.returncode == 0, f"Le socle ne se rejoue pas.\n{rejoue.stderr[-700:]}"

    nouveau_cidr = _sorties(copie, "socle")["cidr_reseau"]["value"]
    assert nouveau_cidr == "10.9.9.0/24", (
        f"Le socle expose encore {nouveau_cidr!r} apres avoir ete rejoue avec "
        "une autre valeur : son output ne suit pas sa variable."
    )

    suivi = _tf(
        "apply", "-auto-approve", "-input=false", "-no-color", cwd=copie / "app"
    )
    assert suivi.returncode == 0, (
        f"L'application ne se rejoue pas.\n{suivi.stderr[-700:]}"
    )
    apres = _sorties(copie, "socle")["identifiant_socle"]["value"]
    assert _sorties(copie, "app")["reseau_consomme"]["value"] == apres, (
        "Apres avoir rejoue le socle, `app` n'expose plus la meme valeur que "
        "lui : la donnee a ete RECOPIEE au lieu d'etre lue dans l'etat distant."
    )


# ── 3. Les deux racines sont bien disjointes ────────────────────────────────


def test_les_deux_racines_sont_disjointes(travail: Path) -> None:
    adresses = {}
    for nom in RACINES:
        adresses[nom] = {
            r["address"]
            for r in _ressources(_etat(travail, nom))
            if r.get("mode") == "managed"
        }
    commun = adresses["socle"] & adresses["app"]
    assert not commun, (
        f"Les deux racines gerent les memes ressources : {sorted(commun)}. "
        "Une decoupe qui laisse une ressource dans les deux etats produit deux "
        "proprietaires pour un seul objet."
    )


def test_les_racines_n_utilisent_aucun_workspace(travail: Path) -> None:
    for nom in RACINES:
        # TEMOIN : sans lui, ce test passerait sur un `challenge/work` intact,
        # ou aucun repertoire terraform.tfstate.d n'existe encore. Constater une
        # absence ne prouve rien tant que le travail n'a pas eu lieu.
        gerees = [
            r for r in _ressources(_etat(travail, nom)) if r.get("mode") == "managed"
        ]
        assert gerees, (
            f"{nom}/ ne suit aucune ressource : il n'a pas ete applique, donc "
            "l'absence de workspace ne prouve rien."
        )

        dossier = _racine(travail, nom) / "terraform.tfstate.d"
        assert not dossier.is_dir(), (
            f"{nom}/terraform.tfstate.d existe : la decoupe a ete faite avec "
            "des WORKSPACES. Or c'est precisement ce que ce cas ne permet pas, "
            "puisque les workspaces d'un repertoire partagent un seul backend."
        )


# ── 4. Le bac a sable : les workspaces restent legitimes ────────────────────


def test_le_bac_a_sable_a_ses_deux_workspaces(travail: Path) -> None:
    dossier = _racine(travail, BAC) / "terraform.tfstate.d"
    assert dossier.is_dir(), (
        f"{BAC}/terraform.tfstate.d n'existe pas : aucun workspace autre que "
        "`default` n'a ete cree. Ce cas-la releve pourtant bien des workspaces."
    )
    trouves = {p.name for p in dossier.iterdir() if p.is_dir()}
    assert trouves >= set(TAILLES), (
        f"Workspaces trouves : {sorted(trouves)}. Attendu au moins "
        f"{sorted(TAILLES)}."
    )


def test_la_taille_suit_le_workspace(travail: Path) -> None:
    for workspace, attendu in TAILLES.items():
        sorties = _sorties(travail, BAC, workspace=workspace)
        assert "taille" in sorties, (
            f"`taille` n'est pas expose dans le workspace {workspace!r}."
        )
        obtenu = sorties["taille"]["value"]
        assert obtenu == attendu, (
            f"Dans le workspace {workspace!r}, `taille` vaut {obtenu!r}, "
            f"attendu {attendu}. La map doit etre indexee par "
            "`terraform.workspace`, avec un repli sur l'entree `default`."
        )


# ── 5. Tout a converge ──────────────────────────────────────────────────────


def test_les_quatre_etats_sont_stables(travail: Path) -> None:
    cibles = [("socle", None), ("app", None), (BAC, "dev"), (BAC, "prod")]
    for nom, workspace in cibles:
        plan = _tf(
            "plan", "-input=false", "-detailed-exitcode", "-no-color",
            cwd=_racine(travail, nom), workspace=workspace,
        )
        etiquette = f"{nom}" + (f" [{workspace}]" if workspace else "")
        assert plan.returncode == 0, (
            f"{etiquette} : `plan -detailed-exitcode` rend {plan.returncode}, "
            f"attendu 0.\n{(plan.stdout + plan.stderr)[-600:]}"
        )
