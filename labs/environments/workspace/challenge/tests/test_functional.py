"""Tests fonctionnels du lab « un seul repertoire, trois etats ».

Ces tests n'ouvrent aucun `.tf`. Ils interrogent chaque workspace SANS toucher a
la selection de l'apprenant, en posant `TF_WORKSPACE` sur la commande : mesure
sur Terraform 1.15.4, cette variable change le workspace vu par la commande et
laisse `.terraform/environment` intact.

Faits verifies sur 1.15.4, hors ligne, providers `local` et `random` :

- l'inventaire des workspaces se lit dans `terraform.tfstate.d/`, ecrit par
  Terraform, jamais dans une sortie humaine ;
- le workspace selectionne se lit dans `.terraform/environment`, fichier local
  jamais partage ;
- supprimer un workspace ne detruit rien : `terraform workspace delete` refuse
  tant qu'il suit des ressources (`Error: Workspace is not empty`), et `-force`
  supprime l'etat en LAISSANT les objets sur le disque.
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
LAB_ID = "environments-workspace"

# workspace -> (ressources gerees attendues, fichiers produits attendus)
ENVIRONNEMENTS = {"dev": (2, 1), "prod": (4, 3)}
HERITE = "bac-a-sable"
FICHIER_HERITE = "sorties/app-bac-a-sable-0.conf"


# ── Helpers ─────────────────────────────────────────────────────────────────


def _tf(
    *args: str, cwd: Path, workspace: str | None = None
) -> subprocess.CompletedProcess[str]:
    """Lance terraform, eventuellement DANS un workspace donne.

    `TF_WORKSPACE` selectionne le workspace pour cette commande seulement : la
    selection locale de l'apprenant n'est pas modifiee.
    """
    env = os.environ.copy()
    if workspace:
        env["TF_WORKSPACE"] = workspace
    return subprocess.run(
        ["terraform", *args], cwd=cwd, capture_output=True, text=True, env=env
    )


def _workspaces(racine: Path) -> set[str]:
    """Inventaire ecrit par Terraform, `default` etant implicite."""
    dossier = racine / "terraform.tfstate.d"
    trouves = {"default"}
    if dossier.is_dir():
        trouves |= {p.name for p in dossier.iterdir() if p.is_dir()}
    return trouves


def _ressources_gerees(racine: Path, workspace: str) -> list[dict]:
    montre = _tf("show", "-json", cwd=racine, workspace=workspace)
    montre.check_returncode()
    etat = json.loads(montre.stdout or "{}")
    valeurs = etat.get("values", {}).get("root_module", {})
    return [r for r in valeurs.get("resources", []) if r.get("mode") == "managed"]


def _sorties(racine: Path, workspace: str) -> dict:
    rendu = _tf("output", "-json", cwd=racine, workspace=workspace)
    if rendu.returncode != 0:
        pytest.fail(
            f"`terraform output` echoue pour le workspace {workspace!r}.\n"
            f"{rendu.stderr[-700:]}"
        )
    return json.loads(rendu.stdout or "{}")


@pytest.fixture(scope="module")
def travail() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    if not (WORKDIR / ".terraform" / "providers").is_dir():
        init = _tf("init", "-input=false", "-no-color", cwd=WORKDIR)
        if init.returncode != 0:
            pytest.fail(f"`terraform init` echoue.\n{init.stderr[-900:]}")
    yield WORKDIR


# ── 1. L'inventaire des workspaces ──────────────────────────────────────────


def _hors_rejeu_de_solution(quoi: str) -> None:
    """Abstention explicite quand le harnais vient de reposer les fixtures.

    `scripts/verify-solutions.py` recopie TOUTES les fixtures puis depose la
    solution par-dessus. Il ne sait pas SUPPRIMER : le workspace herite et son
    fichier reapparaissent donc systematiquement. Une preuve de RETRAIT ne peut
    pas etre faite dans ce mode, et la tordre pour qu'elle passe la viderait de
    son sens. Elle est faite, entiere, sur le parcours apprenant.
    """
    if os.environ.get("LAB_WORKDIR"):
        pytest.skip(
            f"Rejeu de solution : les fixtures viennent d'etre reposees, donc "
            f"{quoi} est de retour. Ce controle n'est probant que sur le "
            "parcours apprenant (`dsoxlab check`), ou il est joue."
        )


def test_les_trois_workspaces_attendus(travail: Path) -> None:
    _hors_rejeu_de_solution("le workspace herite")
    trouves = _workspaces(travail)
    assert HERITE not in trouves, (
        f"Le workspace herite {HERITE!r} existe encore. Il devait etre detruit "
        "puis supprime."
    )
    assert trouves == {"default", "dev", "prod"}, (
        f"Workspaces presents : {sorted(trouves)}. Attendu exactement "
        "default, dev et prod."
    )


def test_le_workspace_selectionne_est_default(travail: Path) -> None:
    """La selection courante se lit dans un fichier local, pas dans une sortie."""
    marqueur = travail / ".terraform" / "environment"
    # Absent = jamais bascule depuis `default`, ce qui convient aussi.
    courant = marqueur.read_text(encoding="utf-8").strip() if marqueur.is_file() else "default"
    assert courant == "default", (
        f".terraform/environment porte {courant!r} : le travail doit se terminer "
        "sur `default`, pour ne pas laisser la prochaine commande s'appliquer "
        "au mauvais etat."
    )


# ── 2. default reste vide ───────────────────────────────────────────────────


def test_default_ne_suit_aucune_ressource(travail: Path) -> None:
    gerees = _ressources_gerees(travail, "default")
    assert not gerees, (
        f"Le workspace `default` suit {len(gerees)} ressource(s) "
        f"({[r['address'] for r in gerees]}). Il doit rester vide : les "
        "environnements vivent dans `dev` et `prod`."
    )


# ── 3. Chaque environnement a son compte ────────────────────────────────────


def test_chaque_environnement_a_son_compte(travail: Path) -> None:
    for workspace, (ressources, fichiers) in ENVIRONNEMENTS.items():
        gerees = _ressources_gerees(travail, workspace)
        assert len(gerees) == ressources, (
            f"Le workspace {workspace!r} suit {len(gerees)} ressource(s), "
            f"attendu {ressources}. Adresses : {[r['address'] for r in gerees]}"
        )
        sorties = _sorties(travail, workspace)
        assert sorties["replicas"]["value"] == fichiers, (
            f"{workspace!r} produit {sorties['replicas']['value']} fichier(s), "
            f"attendu {fichiers}."
        )


def test_chaque_fichier_porte_le_nom_de_son_workspace(travail: Path) -> None:
    for workspace in ENVIRONNEMENTS:
        sorties = _sorties(travail, workspace)
        produit = str(sorties["fichier_produit"]["value"])
        assert workspace in produit, (
            f"Le workspace {workspace!r} produit {produit!r}, qui ne porte pas "
            "son nom. Le nom doit etre derive de `terraform.workspace`."
        )
        assert sorties["workspace_actif"]["value"] == workspace, (
            f"`workspace_actif` vaut {sorties['workspace_actif']['value']!r} "
            f"dans le workspace {workspace!r}."
        )


def test_les_deux_environnements_ont_converge(travail: Path) -> None:
    for workspace in ENVIRONNEMENTS:
        plan = _tf(
            "plan", "-input=false", "-detailed-exitcode", "-no-color",
            cwd=travail, workspace=workspace,
        )
        assert plan.returncode == 0, (
            f"`plan -detailed-exitcode` rend {plan.returncode} dans "
            f"{workspace!r}, attendu 0.\n{(plan.stdout + plan.stderr)[-700:]}"
        )


# ── 4. Le workspace herite a ete DETRUIT, pas seulement supprime ────────────


def test_le_fichier_herite_a_disparu(travail: Path) -> None:
    """Un `delete -force` aurait laisse ce fichier orphelin sur le disque."""
    _hors_rejeu_de_solution("le fichier herite")
    orphelin = travail / FICHIER_HERITE
    assert not orphelin.exists(), (
        f"{FICHIER_HERITE} existe encore. Le workspace {HERITE!r} a donc ete "
        "supprime SANS avoir ete detruit, probablement avec `-force` : "
        "l'etat a disparu, le fichier est reste, et plus rien ne le gere. "
        "L'ordre correct est `terraform destroy` PUIS "
        "`terraform workspace delete`."
    )


# ── 5. Aucune valeur litterale d'environnement dans la configuration ────────


def test_le_nommage_suit_un_workspace_inconnu(travail: Path, tmp_path: Path) -> None:
    """Le controle qui distingue `terraform.workspace` d'une valeur en dur.

    On cree un workspace que l'apprenant n'a jamais vu, dans une COPIE, et on
    applique. Une configuration qui code `dev`/`prod` en dur, ou qui s'appuie
    sur la variable `nom_env`, produit ici le mauvais nom.
    """
    copie = tmp_path / "controle"
    shutil.copytree(travail, copie, symlinks=True)

    cree = _tf(
        "workspace", "select", "-or-create", "controle", "-no-color", cwd=copie
    )
    assert cree.returncode == 0, (
        f"`workspace select -or-create` echoue.\n{cree.stderr[-700:]}"
    )

    applique = _tf("apply", "-auto-approve", "-input=false", "-no-color", cwd=copie)
    assert applique.returncode == 0, (
        f"`terraform apply` echoue dans le workspace temoin.\n"
        f"{applique.stderr[-900:]}"
    )

    sorties = _sorties(copie, "controle")
    produit = str(sorties["fichier_produit"]["value"])
    assert "controle" in produit, (
        f"Dans un workspace nomme `controle`, le fichier produit est "
        f"{produit!r}. Le nom ne suit donc pas `terraform.workspace` : il vient "
        "d'une valeur en dur ou de la variable `nom_env`, qui ne change pas "
        "avec le workspace."
    )
    assert sorties["replicas"]["value"] == 1, (
        f"Le workspace temoin produit {sorties['replicas']['value']} fichiers, "
        "attendu 1 : seul `prod` en produit trois."
    )
