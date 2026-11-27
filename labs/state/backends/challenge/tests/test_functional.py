"""Tests fonctionnels du lab « un backend, deux environnements, zero chemin en dur ».

Le test ORCHESTRE la migration : il applique d'abord avec le backend local
implicite (sans backend.tf), capture le lineage, puis ajoute backend.tf et
migre avec -backend-config. Il prouve ensuite que le state a MIGRE (meme
lineage) et non ete recree, que le backend est resolu, et que le bloc est bien
partiel.

Tout se joue dans une COPIE JETABLE de la configuration de l'apprenant
-------------------------------------------------------------------

`challenge/work` n'est jamais modifie : ni renomme, ni initialise, ni applique.
On copie ses `.tf`, ses `.tfbackend` et son `.terraform.lock.hcl` dans un
repertoire temporaire, et la migration se joue la. Le repertoire disparait a
la fin du module, y compris sur un echec ou un Ctrl-C.

Avant, la fixture renommait backend.tf dans le workdir, initialisait et
migrait sur place. Deux defauts en sortaient (mesures sur dsoxlab 0.11.2 et
Terraform 1.16.1) :

- une solution juste passait au premier check puis BLOQUAIT tous les suivants :
  `.terraform/terraform.tfstate` gardait le backend `etat/dev`, et l'`init`
  sans backend.tf tombait sur « Backend configuration changed » ;
- un echec avant le `yield` laissait backend.tf renomme en backend.tf.aside.

Un echec nomme son etape, il ne bloque pas
-----------------------------------------

Une etape qui echoue (init, apply, migration) n'est pas une erreur de fixture :
c'est la configuration de l'apprenant que Terraform refuse. Elle devient donc
un ECHEC des tests qui en dependent, avec un message qui nomme l'etape et la
reponse de Terraform. Une erreur de fixture s'affiche « non evalue » sans
aucun message, et l'apprenant ne sait pas quoi corriger.
`test_config_partielle` ne depend pas de la migration : il a sa propre copie,
et reste evalue quand la migration echoue.

Principe : on ne lit jamais un `.tf`. On lit ce que Terraform ecrit :
`.terraform/terraform.tfstate` (backend resolu), `state pull` (lineage/serial),
`show -json`, et des codes retour.

Faits verifies sur Terraform 1.16.1 (random + local, hors ligne) :
- une config partielle `backend "local" {}` resout `path` a null sans
  -backend-config, et au chemin fourni avec ;
- `init -migrate-state` preserve le lineage : c'est une migration, pas un apply
  neuf ;
- `path = var.chemin_state` fait echouer un `init` sans -backend-config sur
  « Variables not allowed ».
"""

import json
import shutil
import tempfile
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

from conftest import exiger_workdir, message, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "state-backends"
#: Ce que le test emprunte au workdir. Rien d'autre : ni `.terraform`, ni state,
#: ni `etat/`, qui sont les traces des essais de l'apprenant.
MOTIFS_DE_CONFIG = ("*.tf", "*.tfbackend", ".terraform.lock.hcl")


def _copier_la_config(vers: Path, *, avec_backend: bool = True) -> None:
    """Copie la configuration de l'apprenant, a plat, dans `vers`."""
    for motif in MOTIFS_DE_CONFIG:
        for src in WORKDIR.glob(motif):
            if src.is_file() and (avec_backend or src.name != "backend.tf"):
                shutil.copy2(src, vers / src.name)


def _sortie(proc) -> str:
    return (proc.stderr or proc.stdout or "").strip()[-1200:]


def _backend_resolu(cwd: Path) -> dict:
    raw = (cwd / ".terraform" / "terraform.tfstate").read_text(encoding="utf-8")
    return json.loads(raw)["backend"]


@dataclass
class Migration:
    """Le resultat de la migration jouee dans la copie."""

    cwd: Path
    lineage_initial: str | None = None
    echec: str | None = None


def _migrer(cwd: Path) -> Migration:
    """Joue les quatre etapes ; s'arrete a la premiere qui echoue, et la nomme."""
    if not (WORKDIR / "backend.tf").is_file():
        return Migration(cwd, echec=message(
            en="backend.tf missing from challenge/work: the migration needs a "
            "`backend \"local\"` block to migrate to.",
            fr="backend.tf est absent de challenge/work : la migration a besoin d'un "
            "bloc `backend \"local\"` vers lequel migrer.",
        ))

    # 1. Appliquer avec le backend local IMPLICITE : sans backend.tf.
    _copier_la_config(cwd, avec_backend=False)
    init0 = terraform("init", "-input=false", "-no-color", cwd=cwd)
    if init0.returncode != 0:
        return Migration(cwd, echec=message(
            en="Step 1, `terraform init` without backend.tf, failed: the rest of the "
            f"configuration does not initialise.\n{_sortie(init0)}",
            fr="Étape 1, `terraform init` sans backend.tf, a échoué : le reste de la "
            f"configuration ne s'initialise pas.\n{_sortie(init0)}",
        ))
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=cwd)
    if app.returncode != 0:
        return Migration(cwd, echec=message(
            en=f"Step 2, `terraform apply` without backend.tf, failed.\n{_sortie(app)}",
            fr=f"Étape 2, `terraform apply` sans backend.tf, a échoué.\n{_sortie(app)}",
        ))
    pull = terraform("state", "pull", cwd=cwd)
    lineage_initial = json.loads(pull.stdout)["lineage"] if pull.returncode == 0 else None

    # 2. Ajouter backend.tf et MIGRER vers le backend configure.
    shutil.copy2(WORKDIR / "backend.tf", cwd / "backend.tf")
    mig = terraform(
        "init", "-migrate-state", "-force-copy", "-input=false", "-no-color",
        "-backend-config=dev.local.tfbackend", cwd=cwd,
    )
    if mig.returncode != 0:
        return Migration(cwd, lineage_initial, echec=message(
            en="Step 3, the migration `terraform init -migrate-state "
            "-backend-config=dev.local.tfbackend`, failed. A `???` left in "
            f"dev.local.tfbackend, or a backend block that is not partial?\n{_sortie(mig)}",
            fr="Étape 3, la migration `terraform init -migrate-state "
            "-backend-config=dev.local.tfbackend`, a échoué. Un `???` resté dans "
            f"dev.local.tfbackend, ou un bloc backend non partiel ?\n{_sortie(mig)}",
        ))
    return Migration(cwd, lineage_initial)


@pytest.fixture(scope="module")
def migration() -> Iterator[Migration]:
    exiger_workdir(WORKDIR, LAB_ID)
    with tempfile.TemporaryDirectory(prefix="state-backends-") as repertoire:
        # Les ressources (random_pet, local_file sous path.module) vivent dans
        # la copie : retirer le repertoire suffit, aucun destroy n'est utile.
        yield _migrer(Path(repertoire))


def _exiger_la_migration(m: Migration) -> Path:
    if m.echec:
        pytest.fail(m.echec)
    return m.cwd


# --------------------------------------------------------------------------
# 1. Le state a MIGRE (meme lineage), il n'a pas ete recree
# --------------------------------------------------------------------------

def test_migration_conserve_le_lineage(migration: Migration) -> None:
    cwd = _exiger_la_migration(migration)
    pull = terraform("state", "pull", cwd=cwd)
    lineage = json.loads(pull.stdout)["lineage"] if pull.returncode == 0 else None
    assert lineage is not None and lineage == migration.lineage_initial, message(
        en="The lineage changed: the state was recreated, not migrated. A fresh `apply` "
        "would have made a different lineage.",
        fr="Le lineage a changé : le state a été recréé, pas migré. Un `apply` neuf "
        "aurait fabriqué un lineage différent.",
    )
    managed = [r for r in show_json(cwd)["values"]["root_module"]["resources"]
               if r.get("mode") == "managed"]
    assert len(managed) == 2, message(
        en=f"{len(managed)} managed resources, 2 expected.",
        fr=f"{len(managed)} ressources managed, attendu 2.",
    )


# --------------------------------------------------------------------------
# 2. Le backend est resolu sur l'emplacement dev
# --------------------------------------------------------------------------

def test_backend_resolu_sur_dev(migration: Migration) -> None:
    cwd = _exiger_la_migration(migration)
    be = _backend_resolu(cwd)
    assert be["type"] == "local", message(
        en=f"backend type = {be['type']}, expected local.",
        fr=f"backend type = {be['type']}, attendu local.",
    )
    assert be["config"].get("path") == "etat/dev/terraform.tfstate", message(
        en=f"resolved path = {be['config'].get('path')!r}, expected etat/dev/…: the "
        "-backend-config did not feed the partial configuration.",
        fr=f"path résolu = {be['config'].get('path')!r}, attendu etat/dev/... : le "
        "-backend-config n'a pas alimenté la config partielle.",
    )
    assert (cwd / "etat" / "dev" / "terraform.tfstate").is_file(), message(
        en="The state must exist under etat/dev/terraform.tfstate.",
        fr="Le state doit exister sous etat/dev/terraform.tfstate.",
    )


# --------------------------------------------------------------------------
# 3. La config est PARTIELLE : null sans -backend-config, prod avec
#    Independant de la migration : sa propre copie, sans state.
# --------------------------------------------------------------------------

def test_config_partielle(tmp_path: Path) -> None:
    exiger_workdir(WORKDIR, LAB_ID)
    assert (WORKDIR / "backend.tf").is_file(), message(
        en="backend.tf missing from challenge/work: add a `backend \"local\"` block.",
        fr="backend.tf est absent de challenge/work : ajoutez un bloc `backend \"local\"`.",
    )
    copie = tmp_path / "copie"
    copie.mkdir()
    _copier_la_config(copie)

    sans = terraform("init", "-input=false", "-no-color", cwd=copie)
    assert sans.returncode == 0, message(
        en="`terraform init` without -backend-config failed. A partial block must "
        f"initialise on its own; a variable in the backend block cannot.\n{_sortie(sans)}",
        fr="`terraform init` sans -backend-config a échoué. Un bloc partiel doit "
        "s'initialiser seul ; une variable dans le bloc backend, non.\n"
        f"{_sortie(sans)}",
    )
    assert _backend_resolu(copie)["config"].get("path") is None, message(
        en="Without -backend-config, a partial block must resolve path to null. A path "
        "hard-coded in backend.tf would show up here.",
        fr="Sans -backend-config, un bloc partiel doit résoudre path à null. Un chemin "
        "codé en dur dans backend.tf ressortirait ici.",
    )

    assert (copie / "prod.local.tfbackend").is_file(), message(
        en="prod.local.tfbackend missing: the prod environment needs its own file.",
        fr="prod.local.tfbackend est absent : l'environnement prod a besoin de son "
        "propre fichier.",
    )
    prod = terraform(
        "init", "-reconfigure", "-input=false", "-no-color",
        "-backend-config=prod.local.tfbackend", cwd=copie,
    )
    assert prod.returncode == 0, message(
        en=f"`terraform init -backend-config=prod.local.tfbackend` failed.\n{_sortie(prod)}",
        fr=f"`terraform init -backend-config=prod.local.tfbackend` a échoué.\n{_sortie(prod)}",
    )
    assert _backend_resolu(copie)["config"].get("path") == "etat/prod/terraform.tfstate", message(
        en="The same backend block must resolve to etat/prod with the prod "
        "-backend-config: that is the proof that the configuration is partial.",
        fr="Le même bloc backend doit résoudre sur etat/prod avec le -backend-config "
        "prod : c'est la preuve que la config est partielle.",
    )


# --------------------------------------------------------------------------
# 4. Idempotence apres migration
# --------------------------------------------------------------------------

def test_idempotence(migration: Migration) -> None:
    cwd = _exiger_la_migration(migration)
    p = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=cwd)
    assert p.returncode == 0, message(
        en=f"plan -detailed-exitcode returns {p.returncode}, expected 0: the migrated state "
        "must describe reality.",
        fr=f"plan -detailed-exitcode rend {p.returncode}, attendu 0 : le state migré "
        "doit décrire la réalité.",
    )
