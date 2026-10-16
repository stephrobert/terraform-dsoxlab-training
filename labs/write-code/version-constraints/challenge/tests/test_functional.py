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

from conftest import exiger_workdir, message, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "write-code-version-constraints"


@pytest.fixture(scope="module")
def initialise() -> Path:
    """`init` seul suffit : c'est lui qui resout les contraintes et ecrit le lock."""
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(
            message(
            en="`terraform init` failed. A leftover `???`, a non-literal "
            "required_version (Variables not allowed), or a provider constraint "
            f"that cannot be found?\n{init.stderr[-1500:]}",
            fr="`terraform init` a échoué. Un `???` restant, un required_version non "
            "littéral (Variables not allowed), ou une contrainte de provider "
            f"introuvable ?\n{init.stderr[-1500:]}",
        )
        )
    return WORKDIR


def _selections(cwd: Path) -> dict:
    return json.loads(terraform("version", "-json", cwd=cwd).stdout).get("provider_selections", {})


# --------------------------------------------------------------------------
# 1. Pin exact du provider local
# --------------------------------------------------------------------------

def test_local_epingle_exactement(initialise: Path) -> None:
    v = _selections(initialise).get("registry.terraform.io/hashicorp/local")
    assert v == "2.5.1", message(
        en=f"local resolved to {v!r}, exactly 2.5.1 expected. Use the equality "
        "operator: version = \"= 2.5.1\".",
        fr=f"local résolu en {v!r}, attendu exactement 2.5.1. Utilisez l'opérateur "
        "d'égalité : version = \"= 2.5.1\".",
    )


# --------------------------------------------------------------------------
# 2. Pessimiste sur random : 3.x, jamais 4.0
# --------------------------------------------------------------------------

def test_random_pessimiste_dans_la_plage(initialise: Path) -> None:
    v = _selections(initialise).get("registry.terraform.io/hashicorp/random", "")
    assert re.match(r"^3\.", v), message(
        en=f"random resolved to {v!r}, the 3.x series was expected. Use ~> 3.6 to "
        "allow 3.x without ever reaching 4.0.",
        fr=f"random résolu en {v!r}, attendu la série 3.x. Utilisez ~> 3.6 pour "
        "autoriser 3.x sans jamais atteindre 4.0.",
    )
    major, minor = (int(x) for x in v.split(".")[:2])
    assert (major, minor) >= (3, 6), message(
        en=f"random = {v}, >= 3.6 expected (constraint ~> 3.6).",
        fr=f"random = {v}, attendu >= 3.6 (contrainte ~> 3.6).",
    )


# --------------------------------------------------------------------------
# 3. Le lock file enregistre des empreintes h1
# --------------------------------------------------------------------------

def test_lock_file_avec_empreintes_h1(initialise: Path) -> None:
    lock = (initialise / ".terraform.lock.hcl").read_text(encoding="utf-8")
    assert lock.count("h1:") >= 2, message(
        en="The lock file must record h1: checksums for local AND random. "
        "It is generated at init time and COMMITTED.",
        fr="Le lock file doit enregistrer des empreintes h1: pour local ET random. "
        "Il se génère à l'init et se COMMITTE.",
    )
    assert '"2.5.1"' in lock, message(
        en="The lock file must record the version 2.5.1 kept for local.",
        fr="Le lock file doit enregistrer la version 2.5.1 retenue pour local.",
    )


# --------------------------------------------------------------------------
# 4. Le required_version litteral laisse apply converger
# --------------------------------------------------------------------------

def test_apply_et_idempotence(initialise: Path) -> None:
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=initialise)
    assert app.returncode == 0, message(
        en=f"`terraform apply` failed.\n{app.stderr[-1000:]}",
        fr=f"`terraform apply` a échoué.\n{app.stderr[-1000:]}",
    )
    p = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=initialise)
    assert p.returncode == 0, message(
        en=f"`plan -detailed-exitcode` returns {p.returncode} (2 = changes "
        "remain planned). An apply must converge.",
        fr=f"`plan -detailed-exitcode` rend {p.returncode} (2 = des changements "
        "restent planifiés). Un apply doit converger.",
    )
