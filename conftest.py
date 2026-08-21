"""
Configuration pytest globale pour le repo terraform-training.

Tous les labs sont de type `shell` : ils s'exécutent dans `challenge/work` sur
la machine de l'apprenant, où `terraform` (ou `tofu`) est sur le PATH. Il n'y a
NI control node NI VM à provisionner (pas de `dsoxlab provision`), donc pas de
testinfra ni de ssh_config ici — un test de lab pilote directement terraform
dans son workdir et assère l'état via la sortie JSON structurée.

Helpers communs exposés aux tests : `terraform(*args, cwd=...)`, `show_json()`,
`output_json()` et `workdir_lab()`.

Le suivi d'avancement est assuré par la CLI dsoxlab externe
(`uv tool install dsoxlab`), qui enregistre les résultats de `dsoxlab check`
dans `<repo>/.dsoxlab.db`.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent
LABS_ROOT = REPO_ROOT / "labs"
SOLUTIONS_ROOT = REPO_ROOT / "solution"
VAULT_PASS = REPO_ROOT / ".vault-pass"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "no_replay: le lab s'orchestre lui-même, ne pas rejouer la solution "
        "de référence avant ses tests (voir la fixture _apply_lab_state).",
    )


def workdir_lab(fichier_test: str | Path) -> Path:
    """Workdir du lab auquel appartient un fichier de test.

    Par défaut `<lab>/challenge/work`. La variable d'environnement
    `LAB_WORKDIR` la surcharge, ce dont se sert `scripts/verify-solutions.py`
    pour rejouer les mêmes tests contre la solution de référence.
    """
    surcharge = os.environ.get("LAB_WORKDIR")
    if surcharge:
        return Path(surcharge)
    return Path(fichier_test).resolve().parents[2] / "challenge" / "work"


def exiger_workdir(workdir: Path, lab_id: str) -> None:
    """Arrête proprement le test quand le workdir n'existe pas.

    La distinction est volontaire, et c'est elle qui rend la suite lisible :

    - **lab simplement pas joué** : on SKIPPE. Un `pytest` lancé à la racine du
      dépôt ne doit pas afficher des erreurs rouges pour des labs que personne
      n'a ouverts.
    - **workdir surchargé par `LAB_WORKDIR`** : on ÉCHOUE. Dans ce cas le
      répertoire devait être matérialisé par l'appelant, son absence est un
      vrai défaut et non un lab au repos.
    """
    if workdir.is_dir():
        return
    if os.environ.get("LAB_WORKDIR"):
        pytest.fail(
            f"LAB_WORKDIR pointe sur {workdir}, qui n'existe pas. "
            "L'appelant devait matérialiser ce répertoire avant de lancer les "
            "tests."
        )
    pytest.skip(
        f"Lab non joué : {workdir} est absent. "
        f"Lancez `dsoxlab run {lab_id}` pour poser l'état de départ."
    )


def terraform(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    """Lance `terraform <args>` dans `cwd` et rend le process terminé.

    N'échoue pas tout seul (check=False) : c'est au test de décider si un code
    retour non nul est une erreur ou le résultat attendu (ex. `plan -detailed
    -exitcode`).
    """
    return subprocess.run(
        ["terraform", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def show_json(cwd: Path) -> dict:
    """État Terraform courant, structuré : `terraform show -json`.

    À préférer TOUJOURS au parsing de la sortie humaine pour assérer un état.
    """
    proc = terraform("show", "-json", cwd=cwd)
    proc.check_returncode()
    return json.loads(proc.stdout)


def output_json(cwd: Path) -> dict:
    """Outputs racine, structurés : `terraform output -json`."""
    proc = terraform("output", "-json", cwd=cwd)
    proc.check_returncode()
    return json.loads(proc.stdout)


# ── Rejeu de la solution de référence avant les tests (mode formateur) ───────
#
# Même mécanisme que le dépôt ansible-training : une fixture autouse pose l'état
# de départ de chaque lab (fixtures + solution déchiffrée) dans `challenge/work`
# AVANT ses tests, de sorte que `pytest labs/` (via scripts/test-all.sh) joue
# réellement TOUS les labs au lieu de tous les skipper. Adapté à Terraform :
# « poser la solution » = copier les fixtures à plat puis déchiffrer la solution
# par-dessus (le test lance ensuite `terraform apply` lui-même).


def _dechiffrer(fichier: Path) -> bytes:
    """Contenu en clair d'un fichier de solution chiffré par ansible-vault."""
    proc = subprocess.run(
        ["ansible-vault", "view", "--vault-password-file", str(VAULT_PASS), str(fichier)],
        capture_output=True, check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Déchiffrement impossible pour {fichier.name} : "
            f"{proc.stderr.decode(errors='replace').strip()}"
        )
    return proc.stdout


def _materialiser_solution(lab_root: Path) -> None:
    """Copie les fixtures puis déchiffre la solution dans `challenge/work`.

    Reproduit à l'identique l'aplatissement du runtime shell de dsoxlab et le
    comportement de scripts/verify-solutions.py, mais dans le workdir réel.
    """
    work = lab_root / "challenge" / "work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    fixtures = lab_root / "fixtures"
    if fixtures.is_dir():
        for fichier in sorted(fixtures.rglob("*")):
            if fichier.is_file():
                cible = work / fichier.relative_to(fixtures)
                cible.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(fichier, cible)

    lab_rel = lab_root.relative_to(LABS_ROOT)
    sol_dir = SOLUTIONS_ROOT / lab_rel
    for chiffre in sorted(sol_dir.rglob("*")):
        if chiffre.is_file():
            cible = work / chiffre.relative_to(sol_dir)
            cible.parent.mkdir(parents=True, exist_ok=True)
            cible.write_bytes(_dechiffrer(chiffre))


@pytest.fixture(scope="module", autouse=True)
def _apply_lab_state(request: pytest.FixtureRequest) -> None:
    """Pose la solution de référence du lab avant ses tests (mode formateur).

    Désactivée dans trois cas, à ne pas confondre :

    - `LAB_NO_REPLAY=1` : mode APPRENANT, posé par `dsoxlab check`. On note le
      travail de l'apprenant, on ne rejoue rien par-dessus.
    - `LAB_WORKDIR` défini : `scripts/verify-solutions.py` matérialise déjà la
      solution dans son propre répertoire temporaire, il ne faut pas toucher au
      `challenge/work` de l'apprenant en parallèle.
    - marqueur `@pytest.mark.no_replay` : le lab s'orchestre lui-même.

    No-op quand le lab n'a pas de solution de référence sous `solution/` (labs
    squelette) : leurs tests skippent d'eux-mêmes.
    """
    if os.environ.get("LAB_NO_REPLAY") == "1":
        return
    if os.environ.get("LAB_WORKDIR"):
        return
    if request.node.get_closest_marker("no_replay"):
        return

    test_path = Path(str(request.fspath)).resolve()
    # <lab>/challenge/tests/test_*.py → parents[2] == <lab>
    lab_root = test_path.parents[2]
    if not (lab_root / "lab.yaml").is_file():
        return
    if not (SOLUTIONS_ROOT / lab_root.relative_to(LABS_ROOT)).is_dir():
        return  # lab sans solution de référence : le test skippe de lui-même

    if not VAULT_PASS.is_file():
        pytest.skip(
            ".vault-pass absent : la solution chiffrée ne peut pas être rejouée."
        )
    _materialiser_solution(lab_root)
