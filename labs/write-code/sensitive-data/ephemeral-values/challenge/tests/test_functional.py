"""Tests fonctionnels du lab « la valeur qui ne touche jamais le state ».

Principe : on ne lit jamais le CONTENU des `.tf` de l'apprenant, seulement
`terraform show -json` (state), `output -json` et des codes retour.

Faits verifies sur Terraform v1.15.4 avec random >= 3.7 :
- une ressource `ephemeral "random_password"` n'apparait JAMAIS dans le state ;
- un `random_password` ordinaire y stocke son `result` en clair ;
- une valeur ephemere exposee au root leve « Ephemeral value not allowed » ;
  `ephemeralasnull()` la rend null hors contexte ephemere ;
- une valeur ephemere dans un attribut persiste leve « Invalid use of ephemeral
  value ».
"""

from pathlib import Path

import pytest

from conftest import exiger_workdir, output_json, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "write-code-sensitive-data-ephemeral-values"


@pytest.fixture(scope="module")
def applied() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(f"`terraform init` a echoue.\n{init.stderr[-1200:]}")
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(
            "`terraform apply` a echoue. Un `???` restant, un output ephemere non "
            f"passe par ephemeralasnull(), ou un jeton persiste ?\n{app.stderr[-1500:]}"
        )
    return WORKDIR


def _resources(cwd: Path) -> list[dict]:
    return show_json(cwd)["values"]["root_module"]["resources"]


# --------------------------------------------------------------------------
# 1. Le random_password ORDINAIRE est persiste en clair
# --------------------------------------------------------------------------

def test_persistant_est_dans_le_state(applied: Path) -> None:
    passwords = [r for r in _resources(applied) if r.get("type") == "random_password"]
    assert len(passwords) == 1, (
        f"{len(passwords)} random_password dans le state, attendu 1 (le seul "
        "persistant). Le jeton doit etre EPHEMERE, donc absent du state : si vous "
        "en voyez deux, le bloc jeton est declare `resource` au lieu de `ephemeral`."
    )
    assert passwords[0]["name"] == "persistant"
    assert isinstance(passwords[0]["values"].get("result"), str) and \
        len(passwords[0]["values"]["result"]) == 20, (
        "Le random_password persistant doit exposer son `result` en clair dans le "
        "state (c'est justement ce que l'ephemere evite)."
    )


# --------------------------------------------------------------------------
# 2. Le jeton ephemere n'est NULLE PART dans le state
# --------------------------------------------------------------------------

def test_ephemere_absent_du_state(applied: Path) -> None:
    state = show_json(applied)
    adresses = [r["address"] for r in state["values"]["root_module"]["resources"]]
    assert not any("ephemeral" in a for a in adresses), (
        f"Une adresse ephemere apparait dans le state : {adresses}. Une valeur "
        "ephemere ne doit jamais y figurer."
    )
    assert all(r.get("mode") == "managed" for r in state["values"]["root_module"]["resources"])


# --------------------------------------------------------------------------
# 3. ephemeralasnull rend la valeur ephemere null au root
# --------------------------------------------------------------------------

def test_jeton_masque_est_null(applied: Path) -> None:
    val = output_json(applied).get("jeton_masque", {}).get("value")
    assert val is None, (
        f"`jeton_masque` = {val!r}, attendu null. `ephemeralasnull()` rend null "
        "toute valeur ephemere hors contexte ephemere. Une valeur NON ephemere "
        "ressortirait telle quelle : ce null prouve que le jeton est bien ephemere."
    )


# --------------------------------------------------------------------------
# 4. Idempotence
# --------------------------------------------------------------------------

def test_configuration_stable_apres_apply(applied: Path) -> None:
    p = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=applied)
    assert p.returncode == 0, (
        f"`plan -detailed-exitcode` rend {p.returncode} (2 = des changements "
        "restent planifies). Un apply doit converger. Note : une valeur ephemere "
        "est regeneree a chaque run, mais elle ne cree pas de diff dans le state."
    )
