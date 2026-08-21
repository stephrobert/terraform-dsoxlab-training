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

from conftest import exiger_workdir, output_json, show_json, terraform, workdir_lab

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
        pytest.fail(f"`terraform init` a echoue.\n{init.stderr[-1200:]}")
    return WORKDIR


@pytest.fixture(scope="module")
def applied(prepared: Path) -> Path:
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=prepared)
    if app.returncode != 0:
        pytest.fail(f"`terraform apply` a echoue. Un `???` restant ?\n{app.stderr[-1500:]}")
    return prepared


# --------------------------------------------------------------------------
# 1. La configuration est valide une fois les trous completes
# --------------------------------------------------------------------------

def test_validate_valide(prepared: Path) -> None:
    p = terraform("validate", "-json", cwd=prepared)
    data = json.loads(p.stdout)
    assert data.get("valid") is True, (
        f"`terraform validate` echoue : {data.get('error_count')} erreur(s). "
        "Un `???` subsiste dans variables.tf."
    )


# --------------------------------------------------------------------------
# 2. Type complexe : les optional() completent l'entree partielle
# --------------------------------------------------------------------------

def test_nodes_optional_completes(applied: Path) -> None:
    nodes = output_json(applied)["nodes"]["value"]
    assert set(nodes) == {"web", "db"}, f"cles nodes = {sorted(nodes)}, attendu web/db."
    assert nodes["web"] == {"size": "small", "replicas": 1, "public": False}, (
        f"nodes.web = {nodes['web']!r}. Les attributs `replicas` (defaut 1) et "
        "`public` (defaut false) doivent etre completes par optional(). "
        "Type attendu : map(object({ size=string, replicas=optional(number,1), "
        "public=optional(bool,false) }))."
    )
    assert nodes["db"]["replicas"] == 2 and nodes["db"]["public"] is True, (
        f"nodes.db = {nodes['db']!r}, attendu replicas=2, public=true (valeurs fournies)."
    )


# --------------------------------------------------------------------------
# 3. nullable = false : le null explicite retombe sur le defaut
# --------------------------------------------------------------------------

def test_retention_nullable_false(applied: Path) -> None:
    v = output_json(applied)["retention_days"]["value"]
    assert v == 7, (
        f"`retention_days` = {v!r}, attendu 7. terraform.tfvars pose "
        "`retention_days = null` : sans `nullable = false`, ce null ecrase le "
        "defaut et se propage. `nullable = false` fait retomber sur le defaut."
    )


# --------------------------------------------------------------------------
# 4. sensitive masque l'affichage, mais le state garde le clair
# --------------------------------------------------------------------------

def test_sensitive_est_un_masque_pas_une_protection(applied: Path) -> None:
    outs = show_json(applied).get("values", {}).get("outputs", {})
    assert outs.get("db_password", {}).get("sensitive") is True, (
        "La sortie `db_password` n'est pas marquee sensible. La variable "
        "`db_password` doit porter `sensitive = true`."
    )
    assert outs.get("db_password", {}).get("value") == "changeme-please", (
        "La valeur sensible devrait apparaitre EN CLAIR dans `show -json` : "
        "`sensitive` masque l'affichage humain, pas le fichier d'etat."
    )


# --------------------------------------------------------------------------
# 5. Precedence : auto.tfvars > terraform.tfvars et > TF_VAR_ ; -var au-dessus
# --------------------------------------------------------------------------

def test_precedence_auto_tfvars_et_var(applied: Path) -> None:
    assert output_json(applied)["env"]["value"] == "staging", (
        "`env` devrait valoir 'staging' : un *.auto.tfvars l'emporte sur "
        "terraform.tfvars (qui pose 'dev')."
    )
    code_tfvar = _plan_exitcode(applied, env=dict(os.environ, TF_VAR_env="prod"))
    assert code_tfvar == 0, (
        "Avec TF_VAR_env=prod, le plan devrait rester stable (code 0) : un "
        "*.auto.tfvars a une precedence SUPERIEURE a TF_VAR_, donc env reste 'staging'."
    )
    code_var = _plan_exitcode(applied, "-var", "env=prod")
    assert code_var == 2, (
        "Avec -var env=prod, le plan devrait proposer un changement (code 2) : "
        "-var l'emporte sur toutes les autres sources."
    )


# --------------------------------------------------------------------------
# 6. La validation rejette une valeur interdite, accepte une valeur permise
# --------------------------------------------------------------------------

def test_validation_env(applied: Path) -> None:
    interdit = terraform("plan", "-input=false", "-no-color", "-var", "env=chaos", cwd=applied)
    assert interdit.returncode != 0, (
        "Un `env` hors de dev/staging/prod devrait faire ECHOUER le plan "
        "(bloc validation). Il a reussi."
    )
    permis = terraform("plan", "-input=false", "-no-color", "-var", "env=prod", cwd=applied)
    assert permis.returncode == 0, (
        f"`env=prod` est autorise, le plan ne devrait pas echouer.\n{permis.stderr[-600:]}"
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
    assert data["env"] == "staging"
    assert data["retention_days"] == 7
    assert data["nodes"]["web"]["replicas"] == 1


# --------------------------------------------------------------------------
# 8. Idempotence
# --------------------------------------------------------------------------

def test_configuration_stable_apres_apply(applied: Path) -> None:
    assert _plan_exitcode(applied) == 0, (
        "`plan -detailed-exitcode` ne rend pas 0 apres apply (2 = des changements "
        "restent planifies). Un apply doit converger."
    )
