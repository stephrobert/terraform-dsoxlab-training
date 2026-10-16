"""Tests fonctionnels du lab « variables : typage, validation et precedence ».

Principe : on ne lit jamais le CONTENU des `.tf` de l'apprenant, seulement
`terraform validate -json`, `show -json`, `output -json` et des codes retour.

Faits verifies sur Terraform v1.15.4 :
- `map(object({ ... optional(x, defaut) }))` complete une entree partielle du
  fichier de valeurs avec les defauts des `optional()` ;
- un `null` explicite pose par terraform.tfvars retombe sur le `default` quand
  `nullable = false` ;
- un `*.auto.tfvars` l'emporte sur `terraform.tfvars` ET sur `TF_VAR_...`, et
  cede devant `-var` ;
- `sensitive = true` masque l'AFFICHAGE mais la valeur reste EN CLAIR dans le
  state (`show -json` / `output -json` la rendent) ;
- une `validation` rejette la valeur au plan, avant tout provider.
"""

import json
import os
import subprocess
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
LAB_ID = "write-code-variables"


def _plan_exitcode(cwd: Path, *var: str, env: dict | None = None) -> int:
    """Code retour de `plan -detailed-exitcode` (0 stable, 2 des changements)."""
    return subprocess.run(
        ["terraform", "plan", "-input=false", "-detailed-exitcode", "-no-color", *var],
        cwd=cwd, env=env or dict(os.environ), capture_output=True, text=True, check=False,
    ).returncode


@pytest.fixture(scope="module")
def prepared() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(message(
            en=f"`terraform init` failed.\n{init.stderr[-1200:]}",
            fr=f"`terraform init` a échoué.\n{init.stderr[-1200:]}",
        ))
    return WORKDIR


@pytest.fixture(scope="module")
def applied(prepared: Path) -> Path:
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=prepared)
    if app.returncode != 0:
        pytest.fail(message(
            en=f"`terraform apply` failed. A leftover `???`?\n{app.stderr[-1500:]}",
            fr=f"`terraform apply` a échoué. Un `???` restant ?\n{app.stderr[-1500:]}",
        ))
    return prepared


# --------------------------------------------------------------------------
# 1. La configuration est valide une fois les trous completes
# --------------------------------------------------------------------------

def test_validate_valide(prepared: Path) -> None:
    p = terraform("validate", "-json", cwd=prepared)
    data = json.loads(p.stdout)
    assert data.get("valid") is True, message(
        en=f"`terraform validate` fails: {data.get('error_count')} error(s). "
        "A `???` remains in variables.tf.",
        fr=f"`terraform validate` échoue : {data.get('error_count')} erreur(s). "
        "Un `???` subsiste dans variables.tf.",
    )


# --------------------------------------------------------------------------
# 2. Type complexe : les optional() completent l'entree partielle
# --------------------------------------------------------------------------

def test_nodes_optional_completes(applied: Path) -> None:
    nodes = output_json(applied)["nodes"]["value"]
    assert set(nodes) == {"web", "db"}, message(
        en=f"nodes keys = {sorted(nodes)}, expected web/db.",
        fr=f"clés nodes = {sorted(nodes)}, attendu web/db.",
    )
    assert nodes["web"] == {"size": "small", "replicas": 1, "public": False}, message(
        en=f"nodes.web = {nodes['web']!r}. The attributes `replicas` (default 1) and "
        "`public` (default false) must be completed by optional(). "
        "Expected type: map(object({ size=string, replicas=optional(number,1), "
        "public=optional(bool,false) })).",
        fr=f"nodes.web = {nodes['web']!r}. Les attributs `replicas` (défaut 1) et "
        "`public` (défaut false) doivent être complétés par optional(). "
        "Type attendu : map(object({ size=string, replicas=optional(number,1), "
        "public=optional(bool,false) })).",
    )
    assert nodes["db"]["replicas"] == 2 and nodes["db"]["public"] is True, message(
        en=f"nodes.db = {nodes['db']!r}, expected replicas=2, public=true (values provided).",
        fr=f"nodes.db = {nodes['db']!r}, attendu replicas=2, public=true (valeurs fournies).",
    )


# --------------------------------------------------------------------------
# 3. nullable = false : le null explicite retombe sur le defaut
# --------------------------------------------------------------------------

def test_retention_nullable_false(applied: Path) -> None:
    v = output_json(applied)["retention_days"]["value"]
    assert v == 7, message(
        en=f"`retention_days` = {v!r}, expected 7. terraform.tfvars sets "
        "`retention_days = null`: without `nullable = false`, that null overwrites the "
        "default and propagates. `nullable = false` falls back on the default.",
        fr=f"`retention_days` = {v!r}, attendu 7. terraform.tfvars pose "
        "`retention_days = null` : sans `nullable = false`, ce null écrase le "
        "défaut et se propage. `nullable = false` fait retomber sur le défaut.",
    )


# --------------------------------------------------------------------------
# 4. sensitive masque l'affichage, mais le state garde le clair
# --------------------------------------------------------------------------

def test_sensitive_est_un_masque_pas_une_protection(applied: Path) -> None:
    outs = show_json(applied).get("values", {}).get("outputs", {})
    assert outs.get("db_password", {}).get("sensitive") is True, message(
        en="The `db_password` output is not marked sensitive. The "
        "`db_password` variable must carry `sensitive = true`.",
        fr="La sortie `db_password` n'est pas marquée sensible. La variable "
        "`db_password` doit porter `sensitive = true`.",
    )
    assert outs.get("db_password", {}).get("value") == "changeme-please", message(
        en="The sensitive value should appear IN CLEAR in `show -json`: "
        "`sensitive` hides the human display, not the state file.",
        fr="La valeur sensible devrait apparaître EN CLAIR dans `show -json` : "
        "`sensitive` masque l'affichage humain, pas le fichier d'état.",
    )


# --------------------------------------------------------------------------
# 5. Precedence : auto.tfvars > terraform.tfvars et > TF_VAR_ ; -var au-dessus
# --------------------------------------------------------------------------

def test_precedence_auto_tfvars_et_var(applied: Path) -> None:
    assert output_json(applied)["env"]["value"] == "staging", message(
        en="`env` should be 'staging': a *.auto.tfvars wins over "
        "terraform.tfvars (which sets 'dev').",
        fr="`env` devrait valoir 'staging' : un *.auto.tfvars l'emporte sur "
        "terraform.tfvars (qui pose 'dev').",
    )
    code_tfvar = _plan_exitcode(applied, env=dict(os.environ, TF_VAR_env="prod"))
    assert code_tfvar == 0, message(
        en="With TF_VAR_env=prod, the plan should stay stable (code 0): a "
        "*.auto.tfvars has a HIGHER precedence than TF_VAR_, so env stays 'staging'.",
        fr="Avec TF_VAR_env=prod, le plan devrait rester stable (code 0) : un "
        "*.auto.tfvars a une précédence SUPÉRIEURE à TF_VAR_, donc env reste 'staging'.",
    )
    code_var = _plan_exitcode(applied, "-var", "env=prod")
    assert code_var == 2, message(
        en="With -var env=prod, the plan should propose a change (code 2): "
        "-var wins over every other source.",
        fr="Avec -var env=prod, le plan devrait proposer un changement (code 2) : "
        "-var l'emporte sur toutes les autres sources.",
    )


# --------------------------------------------------------------------------
# 6. La validation rejette une valeur interdite, accepte une valeur permise
# --------------------------------------------------------------------------

def test_validation_env(applied: Path) -> None:
    interdit = terraform("plan", "-input=false", "-no-color", "-var", "env=chaos", cwd=applied)
    assert interdit.returncode != 0, message(
        en="An `env` outside dev/staging/prod should make the plan FAIL "
        "(a validation block). It succeeded.",
        fr="Un `env` hors de dev/staging/prod devrait faire ÉCHOUER le plan "
        "(bloc validation). Il a réussi.",
    )
    permis = terraform("plan", "-input=false", "-no-color", "-var", "env=prod", cwd=applied)
    assert permis.returncode == 0, message(
        en=f"`env=prod` is allowed, the plan should not fail.\n{permis.stderr[-600:]}",
        fr=f"`env=prod` est autorisé, le plan ne devrait pas échouer.\n{permis.stderr[-600:]}",
    )


# --------------------------------------------------------------------------
# 7. Les valeurs ont traverse la config (contenu du local_file)
# --------------------------------------------------------------------------

def test_manifest_reprend_les_variables(applied: Path) -> None:
    state = show_json(applied)
    contenu = next(
        r["values"]["content"]
        for r in state["values"]["root_module"]["resources"]
        if r.get("type") == "local_file"
    )
    data = json.loads(contenu)
    # Le fichier produit doit porter les valeurs EFFECTIVES, celles que les
    # trois tests precedents ont etablies : un fichier qui en porte d'autres
    # vient d'une expression ecrite a part, qui divergera.
    ecart = message(
        en="The file written does not carry the effective values: env=staging, "
        "retention_days=7 and nodes.web.replicas=1. It must derive from the "
        "variables, not from a separate expression.",
        fr="Le fichier écrit ne porte pas les valeurs effectives : env=staging, "
        "retention_days=7 et nodes.web.replicas=1. Il doit dériver des "
        "variables, pas d'une expression écrite à part.",
    )
    assert data["env"] == "staging", ecart
    assert data["retention_days"] == 7, ecart
    assert data["nodes"]["web"]["replicas"] == 1, ecart


# --------------------------------------------------------------------------
# 8. Idempotence
# --------------------------------------------------------------------------

def test_configuration_stable_apres_apply(applied: Path) -> None:
    assert _plan_exitcode(applied) == 0, message(
        en="`plan -detailed-exitcode` does not return 0 after the apply (2 = changes "
        "remain planned). An apply must converge.",
        fr="`plan -detailed-exitcode` ne rend pas 0 après apply (2 = des changements "
        "restent planifiés). Un apply doit converger.",
    )
