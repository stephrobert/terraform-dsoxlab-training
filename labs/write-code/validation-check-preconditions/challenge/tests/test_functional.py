"""Tests fonctionnels du lab « quatre niveaux de validation ».

Principe : on ne lit jamais le CONTENU des `.tf` de l'apprenant, seulement
`terraform show -json` (dont le tableau `checks` de premier niveau), des sorties
JSON et des codes retour.

Faits verifies sur Terraform 1.15.4 (providers random + local, hors ligne) :
- le tableau `checks` de show -json porte les QUATRE niveaux (address.kind :
  var, resource, output_value, check) ;
- les trois premiers passent, le bloc `check` echoue MAIS n'a pas bloque l'apply
  (exit 0) : il surveille sans arreter ;
- une precondition bloque le plan (exit != 0) ;
- `validate -json` declare valide (valid: true) une valeur que le `plan` refuse
  (validation croisee) : validate ne juge pas ce que le plan refuse ;
- `plan -detailed-exitcode` rend 2 sur une config convergee, car le data source
  scope dans le `check` est relu a chaque plan (seule entree non no-op : read).
"""

from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "write-code-validation-check-preconditions"


def _kinds(cwd: Path) -> dict[str, str]:
    checks = show_json(cwd).get("checks", [])
    return {c["address"]["kind"]: c["status"] for c in checks}


@pytest.fixture(scope="module")
def applied() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(f"`terraform init` a echoue.\n{init.stderr[-1200:]}")
    # L'apply DOIT reussir malgre le bloc check en echec : un check ne bloque pas.
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(
            "`terraform apply` a echoue. Un `???` restant, ou une condition "
            "(validation/precondition/postcondition) fausse sur l'etat par defaut ?"
            f"\n{app.stderr[-1500:]}"
        )
    yield WORKDIR
    terraform("destroy", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)


# --------------------------------------------------------------------------
# 1. Les QUATRE niveaux sont visibles dans le tableau checks
# --------------------------------------------------------------------------

def test_les_quatre_niveaux_presents(applied: Path) -> None:
    kinds = _kinds(applied)
    attendus = {"var", "resource", "output_value", "check"}
    assert attendus <= set(kinds), (
        f"Le tableau checks ne porte pas les 4 niveaux. Vu : {kinds}. Attendu au "
        "moins var (validation), resource (pre/postcondition), output_value "
        "(precondition d'output) et check."
    )


# --------------------------------------------------------------------------
# 2. Trois passent, le check echoue (sans avoir bloque l'apply, deja prouve)
# --------------------------------------------------------------------------

def test_check_echoue_les_autres_passent(applied: Path) -> None:
    kinds = _kinds(applied)
    assert kinds.get("var") == "pass"
    assert kinds.get("resource") == "pass"
    assert kinds.get("output_value") == "pass"
    assert kinds.get("check") == "fail", (
        f"Le bloc check devrait etre en fail (assert volontairement faux) : {kinds}."
    )
    # Le message redige par l'apprenant remonte dans instances[].problems[].
    checks = show_json(applied)["checks"]
    check = next(c for c in checks if c["address"]["kind"] == "check")
    messages = [
        p["message"]
        for inst in check.get("instances", [])
        for p in inst.get("problems", [])
    ]
    assert messages and all(isinstance(m, str) and m for m in messages), (
        f"Le check en echec doit porter un error_message non vide : {messages}."
    )


# --------------------------------------------------------------------------
# 3. Une precondition BLOQUE le plan
# --------------------------------------------------------------------------

def test_precondition_bloque_le_plan(applied: Path) -> None:
    # taille_max=20 viole la precondition (garde-fou <= 10), instances presentes.
    p = terraform("plan", "-input=false", "-no-color", "-var", "taille_max=20", cwd=applied)
    assert p.returncode != 0, (
        "Un plan qui viole la precondition doit echouer. Il a reussi : la "
        "precondition ne garde pas le bon invariant."
    )
    assert "recondition" in (p.stdout + p.stderr), (
        "L'echec attendu est une precondition de ressource."
    )


# --------------------------------------------------------------------------
# 4. validate dit valide ce que le plan refuse (validation croisee)
# --------------------------------------------------------------------------

def test_validate_permissif_plan_strict(applied: Path) -> None:
    import json
    v = terraform("validate", "-json", cwd=applied)
    v.check_returncode()
    assert json.loads(v.stdout)["valid"] is True, (
        "terraform validate -json devrait rendre valid: true : il ne connait pas "
        "les valeurs des variables et ne joue pas les validations croisees."
    )
    # taille_lot=10 > taille_max=5 : le plan, lui, refuse.
    p = terraform("plan", "-input=false", "-no-color", "-var", "taille_lot=10", cwd=applied)
    assert p.returncode != 0, (
        "Le plan doit refuser taille_lot=10 (validation croisee taille_lot <= "
        "taille_max), la ou validate le declarait valide."
    )


# --------------------------------------------------------------------------
# 5. Le piege : plan -detailed-exitcode = 2 sur une config convergee
# --------------------------------------------------------------------------

def test_check_data_source_relu_chaque_plan(applied: Path) -> None:
    import json
    code = terraform(
        "plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=applied
    ).returncode
    assert code == 2, (
        f"`plan -detailed-exitcode` rend {code}, attendu 2. Le data source scope "
        "dans le check est relu a chaque plan : il produit toujours un diff."
    )
    # La preuve : la seule entree non no-op du plan est ce data source, en read.
    terraform("plan", "-input=false", "-no-color", "-out=tfplan", cwd=applied).check_returncode()
    plan = terraform("show", "-json", "tfplan", cwd=applied)
    plan.check_returncode()
    changes = json.loads(plan.stdout).get("resource_changes", [])
    non_noop = [r for r in changes if r["change"]["actions"] != ["no-op"]]
    assert non_noop and all(
        r["mode"] == "data" and r["change"]["actions"] == ["read"] for r in non_noop
    ), (
        "La seule entree non no-op du plan doit etre le data source du check, en "
        f"action read : {[(r['address'], r['change']['actions']) for r in non_noop]}."
    )
