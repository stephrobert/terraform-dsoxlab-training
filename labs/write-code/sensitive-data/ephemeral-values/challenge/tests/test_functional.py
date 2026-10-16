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

from conftest import (
    exiger_workdir,
    message,
    output_json,
    show_json,
    terraform,
    workdir_lab,
)

WORKDIR = workdir_lab(__file__)
LAB_ID = "write-code-sensitive-data-ephemeral-values"


@pytest.fixture(scope="module")
def applied() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(message(
            en=f"`terraform init` failed.\n{init.stderr[-1200:]}",
            fr=f"`terraform init` a échoué.\n{init.stderr[-1200:]}",
        ))
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(
            message(
            en="`terraform apply` failed. A leftover `???`, an ephemeral output not "
            f"passed through ephemeralasnull(), or a persisted token?\n{app.stderr[-1500:]}",
            fr="`terraform apply` a échoué. Un `???` restant, un output éphémère non "
            f"passé par ephemeralasnull(), ou un jeton persisté ?\n{app.stderr[-1500:]}",
        )
        )
    return WORKDIR


def _resources(cwd: Path) -> list[dict]:
    return show_json(cwd)["values"]["root_module"]["resources"]


# --------------------------------------------------------------------------
# 1. Le random_password ORDINAIRE est persiste en clair
# --------------------------------------------------------------------------

def test_persistant_est_dans_le_state(applied: Path) -> None:
    passwords = [r for r in _resources(applied) if r.get("type") == "random_password"]
    assert len(passwords) == 1, message(
        en=f"{len(passwords)} random_password in the state, 1 expected (the only "
        "persistent one). The token must be EPHEMERAL, hence absent from the state: if you "
        "see two, the token block is declared `resource` instead of `ephemeral`.",
        fr=f"{len(passwords)} random_password dans le state, attendu 1 (le seul "
        "persistant). Le jeton doit être ÉPHÉMÈRE, donc absent du state : si vous "
        "en voyez deux, le bloc jeton est déclaré `resource` au lieu de `ephemeral`.",
    )
    assert passwords[0]["name"] == "persistant", message(
        en=f"The random_password in the state is named {passwords[0]['name']!r}, "
        "`persistant` expected: the ephemeral one must not be there.",
        fr=f"Le random_password du state s'appelle {passwords[0]['name']!r}, "
        "`persistant` attendu : l'éphémère ne doit pas y figurer.",
    )
    assert isinstance(passwords[0]["values"].get("result"), str) and \
        len(passwords[0]["values"]["result"]) == 20, message(
        en="The persistent random_password must expose its `result` in clear in the "
        "state (that is precisely what the ephemeral one avoids).",
        fr="Le random_password persistant doit exposer son `result` en clair dans le "
        "state (c'est justement ce que l'éphémère évite).",
    )


# --------------------------------------------------------------------------
# 2. Le jeton ephemere n'est NULLE PART dans le state
# --------------------------------------------------------------------------

def test_ephemere_absent_du_state(applied: Path) -> None:
    state = show_json(applied)
    adresses = [r["address"] for r in state["values"]["root_module"]["resources"]]
    assert not any("ephemeral" in a for a in adresses), message(
        en=f"An ephemeral address appears in the state: {adresses}. An ephemeral "
        "value must never appear there.",
        fr=f"Une adresse éphémère apparaît dans le state : {adresses}. Une valeur "
        "éphémère ne doit jamais y figurer.",
    )
    assert all(
        r.get("mode") == "managed" for r in state["values"]["root_module"]["resources"]
    ), message(
        en="Every resource in the state must be in `managed` mode: an ephemeral "
        "block produces nothing there.",
        fr="Toutes les ressources du state doivent être en mode `managed` : un "
        "bloc éphémère n'y produit rien.",
    )


# --------------------------------------------------------------------------
# 3. ephemeralasnull rend la valeur ephemere null au root
# --------------------------------------------------------------------------

def test_jeton_masque_est_null(applied: Path) -> None:
    val = output_json(applied).get("jeton_masque", {}).get("value")
    assert val is None, message(
        en=f"`jeton_masque` = {val!r}, expected null. `ephemeralasnull()` returns null "
        "for any ephemeral value outside an ephemeral context. A NON-ephemeral value "
        "would come back as it is: that null proves the token really is ephemeral.",
        fr=f"`jeton_masque` = {val!r}, attendu null. `ephemeralasnull()` rend null "
        "toute valeur éphémère hors contexte éphémère. Une valeur NON éphémère "
        "ressortirait telle quelle : ce null prouve que le jeton est bien éphémère.",
    )


# --------------------------------------------------------------------------
# 4. Idempotence
# --------------------------------------------------------------------------

def test_configuration_stable_apres_apply(applied: Path) -> None:
    p = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=applied)
    assert p.returncode == 0, message(
        en=f"`plan -detailed-exitcode` returns {p.returncode} (2 = changes "
        "remain planned). An apply must converge. Note: an ephemeral value "
        "is regenerated at every run, but it creates no diff in the state.",
        fr=f"`plan -detailed-exitcode` rend {p.returncode} (2 = des changements "
        "restent planifiés). Un apply doit converger. Note : une valeur éphémère "
        "est régénérée à chaque run, mais elle ne crée pas de diff dans le state.",
    )
