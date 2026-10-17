"""Tests fonctionnels du lab « un backend, deux environnements, zero chemin en dur ».

Le test ORCHESTRE la migration : il applique d'abord avec le backend local
implicite (backend.tf mis de cote), capture le lineage, puis remet backend.tf et
migre avec -backend-config. Il prouve ensuite que le state a MIGRE (meme lineage)
et non ete recree, que le backend est resolu, et que le bloc est bien partiel.

Principe : on ne lit jamais un `.tf`. On lit ce que Terraform ecrit :
`.terraform/terraform.tfstate` (backend resolu), `state pull` (lineage/serial),
`show -json`, et des codes retour.

Faits verifies sur Terraform 1.15.4 (random + local, hors ligne) :
- une config partielle `backend "local" {}` resout `path` a null sans
  -backend-config, et au chemin fourni avec ;
- `init -migrate-state` preserve le lineage : c'est une migration, pas un apply
  neuf ;
- le bloc backend rejette une variable (voir le guide, non teste ici).
"""

import json
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, message, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "state-backends"
CONFIGS = ("versions.tf", "main.tf", "variables.tf", "backend.tf",
           "dev.local.tfbackend", "prod.local.tfbackend")


def _lineage(cwd: Path) -> str:
    pull = terraform("state", "pull", cwd=cwd)
    pull.check_returncode()
    return json.loads(pull.stdout)["lineage"]


@pytest.fixture(scope="module")
def applied() -> Iterator[tuple[Path, str]]:
    exiger_workdir(WORKDIR, LAB_ID)
    backend_tf = WORKDIR / "backend.tf"
    aside = WORKDIR / "backend.tf.aside"
    # 1. Appliquer avec le backend local IMPLICITE : on met backend.tf de cote.
    if backend_tf.exists():
        backend_tf.rename(aside)
    init0 = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init0.returncode != 0:
        pytest.fail(message(
            en=f"`terraform init` (implicit) failed.\n{init0.stderr[-1000:]}",
            fr=f"`terraform init` (implicite) a échoué.\n{init0.stderr[-1000:]}",
        ))
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(message(
            en=f"`terraform apply` failed.\n{app.stderr[-1200:]}",
            fr=f"`terraform apply` a échoué.\n{app.stderr[-1200:]}",
        ))
    lineage_initial = _lineage(WORKDIR)
    # 2. Remettre backend.tf et MIGRER vers le backend configure.
    if aside.exists():
        aside.rename(backend_tf)
    else:
        pytest.fail(message(
            en="backend.tf missing: add a `backend \"local\" {}` block.",
            fr="backend.tf absent : ajoutez un bloc `backend \"local\" {}`.",
        ))
    mig = terraform(
        "init", "-migrate-state", "-force-copy", "-input=false", "-no-color",
        "-backend-config=dev.local.tfbackend", cwd=WORKDIR,
    )
    if mig.returncode != 0:
        pytest.fail(
            message(
            en="The migration `init -migrate-state -backend-config=dev…` failed. "
            "A `???` in dev.local.tfbackend, or a backend block that is not partial?"
            f"\n{mig.stderr[-1200:]}",
            fr="La migration `init -migrate-state -backend-config=dev...` a échoué. "
            "Un `???` dans dev.local.tfbackend, ou un bloc backend non partiel ?"
            f"\n{mig.stderr[-1200:]}",
        )
        )
    yield WORKDIR, lineage_initial
    terraform("destroy", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)


def _backend_resolu(cwd: Path) -> dict:
    raw = (cwd / ".terraform" / "terraform.tfstate").read_text(encoding="utf-8")
    return json.loads(raw)["backend"]


# --------------------------------------------------------------------------
# 1. Le state a MIGRE (meme lineage), il n'a pas ete recree
# --------------------------------------------------------------------------

def test_migration_conserve_le_lineage(applied: tuple[Path, str]) -> None:
    cwd, lineage_initial = applied
    assert _lineage(cwd) == lineage_initial, message(
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

def test_backend_resolu_sur_dev(applied: tuple[Path, str]) -> None:
    cwd, _ = applied
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
# --------------------------------------------------------------------------

def test_config_partielle(applied: tuple[Path, str], tmp_path: Path) -> None:
    cwd, _ = applied
    copie = tmp_path / "copie"
    copie.mkdir()
    for f in CONFIGS:
        src = cwd / f
        if src.exists():
            shutil.copy2(src, copie / f)

    sans = terraform("init", "-input=false", "-no-color", cwd=copie)
    sans.check_returncode()
    assert _backend_resolu(copie)["config"].get("path") is None, message(
        en="Without -backend-config, a partial block must resolve path to null. A path "
        "hard-coded in backend.tf would show up here.",
        fr="Sans -backend-config, un bloc partiel doit résoudre path à null. Un chemin "
        "codé en dur dans backend.tf ressortirait ici.",
    )

    prod = terraform(
        "init", "-reconfigure", "-input=false", "-no-color",
        "-backend-config=prod.local.tfbackend", cwd=copie,
    )
    prod.check_returncode()
    assert _backend_resolu(copie)["config"].get("path") == "etat/prod/terraform.tfstate", message(
        en="The same backend block must resolve to etat/prod with the prod "
        "-backend-config: that is the proof that the configuration is partial.",
        fr="Le même bloc backend doit résoudre sur etat/prod avec le -backend-config "
        "prod : c'est la preuve que la config est partielle.",
    )


# --------------------------------------------------------------------------
# 4. Idempotence apres migration
# --------------------------------------------------------------------------

def test_idempotence(applied: tuple[Path, str]) -> None:
    cwd, _ = applied
    p = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=cwd)
    assert p.returncode == 0, message(
        en=f"plan -detailed-exitcode returns {p.returncode}, expected 0: the migrated state "
        "must describe reality.",
        fr=f"plan -detailed-exitcode rend {p.returncode}, attendu 0 : le state migré "
        "doit décrire la réalité.",
    )
