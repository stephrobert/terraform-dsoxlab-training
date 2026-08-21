"""Tests fonctionnels du lab « contraintes de version et lock file ».

Principe : on ne lit jamais le CONTENU des `.tf` de l'apprenant pour l'asserer.
On lit `terraform version -json` (versions retenues), le fichier de lock genere
`.terraform.lock.hcl` (un artefact, pas du HCL de config), et des codes retour.

Faits verifies sur Terraform v1.15.4 :
- un `required_version` litteral satisfait par 1.15.4 laisse `init` reussir ; une
  variable dans le bloc `terraform` leve « Variables not allowed » ;
- un pin exact `= 2.5.1` resout le provider local a EXACTEMENT 2.5.1 ;
- `~> 3.6` resout random dans [3.6, 4.0) ;
- le lock file enregistre des empreintes `h1:` par provider.
"""

import json
import re
from pathlib import Path

import pytest

from conftest import exiger_workdir, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "write-code-version-constraints"


@pytest.fixture(scope="module")
def initialise() -> Path:
    """`init` seul suffit : c'est lui qui resout les contraintes et ecrit le lock."""
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(
            "`terraform init` a echoue. Un `???` restant, un required_version non "
            "litteral (Variables not allowed), ou une contrainte de provider "
            f"introuvable ?\n{init.stderr[-1500:]}"
        )
    return WORKDIR


def _selections(cwd: Path) -> dict:
    return json.loads(terraform("version", "-json", cwd=cwd).stdout).get("provider_selections", {})


# --------------------------------------------------------------------------
# 1. Pin exact du provider local
# --------------------------------------------------------------------------

def test_local_epingle_exactement(initialise: Path) -> None:
    v = _selections(initialise).get("registry.terraform.io/hashicorp/local")
    assert v == "2.5.1", (
        f"local resolu en {v!r}, attendu exactement 2.5.1. Utilisez l'operateur "
        "d'egalite : version = \"= 2.5.1\"."
    )


# --------------------------------------------------------------------------
# 2. Pessimiste sur random : 3.x, jamais 4.0
# --------------------------------------------------------------------------

def test_random_pessimiste_dans_la_plage(initialise: Path) -> None:
    v = _selections(initialise).get("registry.terraform.io/hashicorp/random", "")
    assert re.match(r"^3\.", v), (
        f"random resolu en {v!r}, attendu la serie 3.x. Utilisez ~> 3.6 pour "
        "autoriser 3.x sans jamais atteindre 4.0."
    )
    major, minor = (int(x) for x in v.split(".")[:2])
    assert (major, minor) >= (3, 6), f"random = {v}, attendu >= 3.6 (contrainte ~> 3.6)."


# --------------------------------------------------------------------------
# 3. Le lock file enregistre des empreintes h1
# --------------------------------------------------------------------------

def test_lock_file_avec_empreintes_h1(initialise: Path) -> None:
    lock = (initialise / ".terraform.lock.hcl").read_text(encoding="utf-8")
    assert lock.count("h1:") >= 2, (
        "Le lock file doit enregistrer des empreintes h1: pour local ET random. "
        "Il se genere a l'init et se COMMITTE."
    )
    assert '"2.5.1"' in lock, (
        "Le lock file doit enregistrer la version 2.5.1 retenue pour local."
    )


# --------------------------------------------------------------------------
# 4. Le required_version litteral laisse apply converger
# --------------------------------------------------------------------------

def test_apply_et_idempotence(initialise: Path) -> None:
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=initialise)
    assert app.returncode == 0, f"`terraform apply` a echoue.\n{app.stderr[-1000:]}"
    p = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=initialise)
    assert p.returncode == 0, (
        f"`plan -detailed-exitcode` rend {p.returncode} (2 = des changements "
        "restent planifies). Un apply doit converger."
    )
