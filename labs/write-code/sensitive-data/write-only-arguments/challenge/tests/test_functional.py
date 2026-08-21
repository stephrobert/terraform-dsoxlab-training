"""Tests fonctionnels du lab « le secret qui ne touche jamais le state ».

Principe : on ne lit jamais le CONTENU des `.tf` de l'apprenant, seulement
`terraform show -json` (state), `output -json`, le fichier `terraform.tfstate`
brut et des codes retour.

Faits verifies sur Terraform v1.15.4, provider AWS 6.x, contre Floci 1.6.0 :
- un `aws_ssm_parameter` avec `value_wo` s'applique bien contre Floci (SSM) ;
- son `value_wo` vaut `null` dans le state : la valeur ne round-trip jamais ;
- la valeur sentinelle du secret n'apparait NULLE PART dans terraform.tfstate ;
- `value_wo_version` EST persiste (c'est lui qui pilote le renvoi de la valeur) ;
- la configuration est idempotente (`plan -detailed-exitcode` rend 0).

Prerequis Floci : sous `dsoxlab run/check`, le mecanisme `runtime.services`
demarre Floci automatiquement. Hors dsoxlab (pytest nu), le test SKIPPE si Floci
est injoignable, sauf sous `LAB_WORKDIR` (contexte verify-solutions), ou son
absence est un vrai defaut et fait ECHOUER.
"""

import os
import socket
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, output_json, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "write-code-sensitive-data-write-only-arguments"

# Sentinelle posee par fixtures/terraform.tfvars. Le secret ne doit jamais
# apparaitre dans le state : on la cherche dans terraform.tfstate.
SENTINELLE = "WO-SENTINELLE-NE-DOIT-PAS-FUITER"

# Floci est publie sur le port 4566 de l'hote (cf. runtime.services du lab et
# la valeur par defaut de var.floci_endpoint).
FLOCI_HOST = "127.0.0.1"
FLOCI_PORT = 4566


def _floci_joignable() -> bool:
    try:
        with socket.create_connection((FLOCI_HOST, FLOCI_PORT), timeout=2):
            return True
    except OSError:
        return False


@pytest.fixture(scope="module")
def applied() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    if not _floci_joignable():
        message = (
            f"Floci injoignable sur {FLOCI_HOST}:{FLOCI_PORT}. Le lab en a besoin "
            "pour l'API SSM. `dsoxlab run/check` le demarre tout seul (runtime."
            "services)."
        )
        if os.environ.get("LAB_WORKDIR"):
            pytest.fail(message)
        pytest.skip(message)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(f"`terraform init` a echoue.\n{init.stderr[-1200:]}")
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(
            "`terraform apply` a echoue. Un `???` restant, ou `value_wo` sans son "
            f"`value_wo_version` (le couple est obligatoire) ?\n{app.stderr[-1500:]}"
        )
    yield WORKDIR
    # Teardown : Floci est un etat EXTERNE partage (memoire, long-vecu sous
    # test-all). Sans destroy, le parametre SSM survit a l'apply et un run
    # ulterieur avec un state neuf casse sur ParameterAlreadyExists. On nettoie
    # donc cote Floci, pour que le lab soit rejouable indefiniment.
    terraform("destroy", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)


def _param(cwd: Path) -> dict:
    resources = show_json(cwd)["values"]["root_module"]["resources"]
    params = [r for r in resources if r.get("type") == "aws_ssm_parameter"]
    assert len(params) == 1, (
        f"{len(params)} aws_ssm_parameter dans le state, attendu 1."
    )
    return params[0]


# --------------------------------------------------------------------------
# 1. Le parametre existe et value_wo ne round-trip PAS dans le state
# --------------------------------------------------------------------------

def test_value_wo_absent_du_state(applied: Path) -> None:
    values = _param(applied)["values"]
    assert values["value_wo"] is None, (
        f"`value_wo` = {values['value_wo']!r} dans le state, attendu null. Un "
        "argument write-only est transmis au provider mais jamais persiste : s'il "
        "porte une valeur ici, c'est un argument ordinaire (`value`) qui a ete "
        "utilise, et le secret fuite."
    )


# --------------------------------------------------------------------------
# 2. La sentinelle du secret n'est NULLE PART dans terraform.tfstate
# --------------------------------------------------------------------------

def test_secret_absent_du_fichier_state(applied: Path) -> None:
    tfstate = applied / "terraform.tfstate"
    assert tfstate.is_file(), "terraform.tfstate absent apres apply."
    contenu = tfstate.read_text(encoding="utf-8")
    assert SENTINELLE not in contenu, (
        "La valeur du secret apparait en clair dans terraform.tfstate. C'est "
        "exactement ce qu'un argument write-only doit empecher : le secret ne "
        "doit jamais toucher le state."
    )


# --------------------------------------------------------------------------
# 3. value_wo_version EST persiste (il pilote le renvoi de la valeur)
# --------------------------------------------------------------------------

def test_version_wo_persistee(applied: Path) -> None:
    values = _param(applied)["values"]
    assert values.get("value_wo_version") == 1, (
        f"`value_wo_version` = {values.get('value_wo_version')!r}, attendu 1. Ce "
        "numero, lui, est stocke dans le state : c'est ce qui dit a Terraform "
        "quand renvoyer la valeur au service."
    )
    version_output = output_json(applied).get("value_wo_version", {}).get("value")
    assert version_output == 1, (
        f"output value_wo_version = {version_output!r}, attendu 1."
    )


# --------------------------------------------------------------------------
# 4. Idempotence
# --------------------------------------------------------------------------

def test_configuration_stable_apres_apply(applied: Path) -> None:
    p = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=applied)
    assert p.returncode == 0, (
        f"`plan -detailed-exitcode` rend {p.returncode} (2 = des changements "
        "restent planifies). Tant que value_wo_version ne change pas, aucun renvoi "
        f"de la valeur n'est prevu et le plan doit etre vide.\n{p.stdout[-800:]}"
    )
