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

from conftest import exiger_workdir, message, workdir_lab

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
        ["terraform", *args], cwd=cwd, capture_output=True, text=True, env=env,
        check=False,
    )


def _racine(travail: Path, nom: str) -> Path:
    chemin = travail / nom
    if not chemin.is_dir():
        pytest.fail(message(
            en=f"The {nom}/ directory is missing from challenge/work.",
            fr=f"Le répertoire {nom}/ est absent de challenge/work.",
        ))
    return chemin


def _etat(travail: Path, nom: str, workspace: str | None = None) -> dict:
    montre = _tf("show", "-json", cwd=_racine(travail, nom), workspace=workspace)
    if montre.returncode != 0:
        pytest.fail(
            message(
            en=f"`terraform show -json` fails in {nom}/. Has the configuration "
            f"been initialised and applied?\n{montre.stderr[-700:]}",
            fr=f"`terraform show -json` échoue dans {nom}/. La configuration "
            f"a-t-elle été initialisée et appliquée ?\n{montre.stderr[-700:]}",
        )
        )
    return json.loads(montre.stdout or "{}")


def _ressources(etat: dict) -> list[dict]:
    return list(etat.get("values", {}).get("root_module", {}).get("resources", []))


def _sorties(travail: Path, nom: str, workspace: str | None = None) -> dict:
    rendu = _tf("output", "-json", cwd=_racine(travail, nom), workspace=workspace)
    if rendu.returncode != 0:
        pytest.fail(
            message(
            en=f"`terraform output -json` fails in {nom}/.\n{rendu.stderr[-700:]}",
            fr=f"`terraform output -json` échoue dans {nom}/.\n{rendu.stderr[-700:]}",
        )
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
                    message(
                    en=f"`terraform init` fails in {nom}/.\n{init.stderr[-800:]}",
                    fr=f"`terraform init` échoue dans {nom}/.\n{init.stderr[-800:]}",
                )
                )
    yield WORKDIR


# ── 1. Le socle est applique et expose son contrat ──────────────────────────


def test_le_socle_est_applique_et_expose_deux_sorties(travail: Path) -> None:
    gerees = [
        r for r in _ressources(_etat(travail, "socle")) if r.get("mode") == "managed"
    ]
    assert gerees, message(
        en="The foundation tracks no resource: it was not applied.",
        fr="Le socle ne suit aucune ressource : il n'a pas été appliqué.",
    )

    sorties = _sorties(travail, "socle")
    for attendu in ("identifiant_socle", "cidr_reseau"):
        assert attendu in sorties, message(
            en=f"The foundation does not expose `{attendu}`. Its two outputs are its "
            "CONTRACT: nothing else crosses the boundary between root modules.",
            fr=f"Le socle n'expose pas `{attendu}`. Ses deux outputs sont son "
            "CONTRAT : rien d'autre ne traverse la frontière entre racines.",
        )
        valeur = sorties[attendu].get("value")
        assert valeur not in (None, ""), message(
            en=f"The foundation's `{attendu}` output is empty.",
            fr=f"L'output `{attendu}` du socle est vide.",
        )


# ── 2. L'application lit l'etat du socle ────────────────────────────────────


def test_l_application_lit_l_etat_distant_du_socle(travail: Path) -> None:
    donnees = [r for r in _ressources(_etat(travail, "app")) if r.get("mode") == "data"]
    assert donnees, message(
        en="The state of `app` contains no data source. Yet the only "
        "gateway between two root modules is reading the other's remote "
        "state.",
        fr="L'état de `app` ne contient aucune source de données. Or la seule "
        "passerelle entre deux racines est la lecture de l'état distant de "
        "l'autre.",
    )
    distants = [d for d in donnees if d.get("type") == "terraform_remote_state"]
    assert distants, message(
        en="No `terraform_remote_state` source in the state of `app`: "
        f"types found = {[d.get('type') for d in donnees]}.",
        fr="Aucune source `terraform_remote_state` dans l'état de `app` : "
        f"types trouvés = {[d.get('type') for d in donnees]}.",
    )


def test_la_valeur_traverse_les_deux_etats(travail: Path) -> None:
    du_socle = _sorties(travail, "socle")["identifiant_socle"]["value"]
    de_l_app = _sorties(travail, "app")

    assert "reseau_consomme" in de_l_app, message(
        en="`app` does not expose `reseau_consomme`.",
        fr="`app` n'expose pas `reseau_consomme`.",
    )
    assert de_l_app["reseau_consomme"]["value"] == du_socle, message(
        en=f"`app` exposes {de_l_app['reseau_consomme']['value']!r} while the "
        f"foundation produces {du_socle!r}. The value must COME from the foundation.",
        fr=f"`app` expose {de_l_app['reseau_consomme']['value']!r} alors que le "
        f"socle produit {du_socle!r}. La valeur doit VENIR du socle.",
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
    assert rejoue.returncode == 0, message(
        en=f"The foundation cannot be replayed.\n{rejoue.stderr[-700:]}",
        fr=f"Le socle ne se rejoue pas.\n{rejoue.stderr[-700:]}",
    )

    nouveau_cidr = _sorties(copie, "socle")["cidr_reseau"]["value"]
    assert nouveau_cidr == "10.9.9.0/24", message(
        en=f"The foundation still exposes {nouveau_cidr!r} after being replayed with "
        "another value: its output does not follow its variable.",
        fr=f"Le socle expose encore {nouveau_cidr!r} après avoir été rejoué avec "
        "une autre valeur : son output ne suit pas sa variable.",
    )

    suivi = _tf(
        "apply", "-auto-approve", "-input=false", "-no-color", cwd=copie / "app"
    )
    assert suivi.returncode == 0, message(
        en=f"The application cannot be replayed.\n{suivi.stderr[-700:]}",
        fr=f"L'application ne se rejoue pas.\n{suivi.stderr[-700:]}",
    )
    apres = _sorties(copie, "socle")["identifiant_socle"]["value"]
    assert _sorties(copie, "app")["reseau_consomme"]["value"] == apres, message(
        en="After replaying the foundation, `app` no longer exposes the same value as "
        "it: the data was COPIED instead of being read from the remote state.",
        fr="Après avoir rejoué le socle, `app` n'expose plus la même valeur que "
        "lui : la donnée a été RECOPIÉE au lieu d'être lue dans l'état distant.",
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
    assert not commun, message(
        en=f"Both root modules manage the same resources: {sorted(commun)}. "
        "A split that leaves a resource in both states produces two "
        "owners for a single object.",
        fr=f"Les deux racines gèrent les mêmes ressources : {sorted(commun)}. "
        "Une découpe qui laisse une ressource dans les deux états produit deux "
        "propriétaires pour un seul objet.",
    )


def test_les_racines_n_utilisent_aucun_workspace(travail: Path) -> None:
    for nom in RACINES:
        # TEMOIN : sans lui, ce test passerait sur un `challenge/work` intact,
        # ou aucun repertoire terraform.tfstate.d n'existe encore. Constater une
        # absence ne prouve rien tant que le travail n'a pas eu lieu.
        gerees = [
            r for r in _ressources(_etat(travail, nom)) if r.get("mode") == "managed"
        ]
        assert gerees, message(
            en=f"{nom}/ tracks no resource: it was not applied, so "
            "the absence of a workspace proves nothing.",
            fr=f"{nom}/ ne suit aucune ressource : il n'a pas été appliqué, donc "
            "l'absence de workspace ne prouve rien.",
        )

        dossier = _racine(travail, nom) / "terraform.tfstate.d"
        assert not dossier.is_dir(), message(
            en=f"{nom}/terraform.tfstate.d exists: the split was made with "
            "WORKSPACES. But that is precisely what this case does not allow, "
            "since the workspaces of one directory share a single backend.",
            fr=f"{nom}/terraform.tfstate.d existe : la découpe a été faite avec "
            "des WORKSPACES. Or c'est précisément ce que ce cas ne permet pas, "
            "puisque les workspaces d'un répertoire partagent un seul backend.",
        )


# ── 4. Le bac a sable : les workspaces restent legitimes ────────────────────


def test_le_bac_a_sable_a_ses_deux_workspaces(travail: Path) -> None:
    dossier = _racine(travail, BAC) / "terraform.tfstate.d"
    assert dossier.is_dir(), message(
        en=f"{BAC}/terraform.tfstate.d does not exist: no workspace other than "
        "`default` was created. This case does belong to workspaces, though.",
        fr=f"{BAC}/terraform.tfstate.d n'existe pas : aucun workspace autre que "
        "`default` n'a été créé. Ce cas-là relève pourtant bien des workspaces.",
    )
    trouves = {p.name for p in dossier.iterdir() if p.is_dir()}
    assert trouves >= set(TAILLES), message(
        en=f"Workspaces found: {sorted(trouves)}. At least "
        f"{sorted(TAILLES)} expected.",
        fr=f"Workspaces trouvés : {sorted(trouves)}. Attendu au moins "
        f"{sorted(TAILLES)}.",
    )


def test_la_taille_suit_le_workspace(travail: Path) -> None:
    for workspace, attendu in TAILLES.items():
        sorties = _sorties(travail, BAC, workspace=workspace)
        assert "taille" in sorties, message(
            en=f"`taille` is not exposed in workspace {workspace!r}.",
            fr=f"`taille` n'est pas exposé dans le workspace {workspace!r}.",
        )
        obtenu = sorties["taille"]["value"]
        assert obtenu == attendu, message(
            en=f"In workspace {workspace!r}, `taille` is {obtenu!r}, "
            f"expected {attendu}. The map must be indexed by "
            "`terraform.workspace`, with a fallback on the `default` entry.",
            fr=f"Dans le workspace {workspace!r}, `taille` vaut {obtenu!r}, "
            f"attendu {attendu}. La map doit être indexée par "
            "`terraform.workspace`, avec un repli sur l'entrée `default`.",
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
        assert plan.returncode == 0, message(
            en=f"{etiquette}: `plan -detailed-exitcode` returns {plan.returncode}, "
            f"expected 0.\n{(plan.stdout + plan.stderr)[-600:]}",
            fr=f"{etiquette} : `plan -detailed-exitcode` rend {plan.returncode}, "
            f"attendu 0.\n{(plan.stdout + plan.stderr)[-600:]}",
        )
