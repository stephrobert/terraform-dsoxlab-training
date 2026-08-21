"""Tests fonctionnels du lab « la faute de frappe qui ne casse rien ».

Principe : on ne lit jamais le CONTENU des `.tf` de l'apprenant, seulement
`terraform output -json` et des codes retour.

Faits verifies sur Terraform v1.15.4 :
- une variable non declaree dans un `.tfvars` ne fait qu'un AVERTISSEMENT : le
  plan reussit, mais la vraie variable reste a son defaut (piege de la faute de
  frappe) ;
- `terraform.tfvars.json` l'emporte sur `terraform.tfvars` (niveau de precedence
  distinct).
"""

import json
from pathlib import Path

import pytest

from conftest import exiger_workdir, output_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "write-code-tfvars-files"


@pytest.fixture(scope="module")
def applied() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(f"`terraform init` a echoue.\n{init.stderr[-1200:]}")
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(f"`terraform apply` a echoue.\n{app.stderr[-1500:]}")
    return WORKDIR


# --------------------------------------------------------------------------
# 1. La faute de frappe est corrigee : bucket vaut "prod", pas le defaut
# --------------------------------------------------------------------------

def test_bucket_prend_la_valeur(applied: Path) -> None:
    v = output_json(applied)["bucket"]["value"]
    assert v == "prod", (
        f"`bucket` = {v!r}, attendu 'prod'. Le terraform.tfvars fourni ecrit "
        "`bukcet = \"prod\"` (faute de frappe) : une variable non declaree dans un "
        ".tfvars ne fait qu'un warning, bucket reste alors a son defaut "
        "'app-defaut'. Corrigez le nom en `bucket`."
    )


def test_region_depuis_tfvars(applied: Path) -> None:
    assert output_json(applied)["region"]["value"] == "eu-west-3", (
        "`region` devrait valoir 'eu-west-3' (fourni par terraform.tfvars)."
    )


# --------------------------------------------------------------------------
# 2. tfvars.json l'emporte sur tfvars : replicas = 5, pas 2
# --------------------------------------------------------------------------

def test_replicas_depuis_json(applied: Path) -> None:
    v = output_json(applied)["replicas"]["value"]
    assert v == 5, (
        f"`replicas` = {v!r}, attendu 5. terraform.tfvars pose replicas = 2 ; "
        "creez un terraform.tfvars.json posant replicas = 5 : la variante JSON "
        "l'emporte sur terraform.tfvars."
    )
    assert isinstance(v, (int, float)) and not isinstance(v, bool), (
        "`replicas` doit rester un nombre."
    )


# --------------------------------------------------------------------------
# 3. Idempotence
# --------------------------------------------------------------------------

def test_configuration_stable_apres_apply(applied: Path) -> None:
    p = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=applied)
    assert p.returncode == 0, (
        f"`plan -detailed-exitcode` rend {p.returncode} (2 = des changements "
        "restent planifies). Un apply doit converger."
    )
