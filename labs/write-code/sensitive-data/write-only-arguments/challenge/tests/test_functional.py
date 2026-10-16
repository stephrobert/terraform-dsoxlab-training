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

from conftest import (
    exiger_workdir,
    message,
    output_json,
    show_json,
    terraform,
    workdir_lab,
)

WORKDIR = workdir_lab(__file__)
LAB_ID = "write-code-sensitive-data-write-only-arguments"

# Sentinelle posee par fixtures/terraform.tfvars. Le secret ne doit jamais
# apparaitre dans le state : on la cherche dans terraform.tfstate.
SENTINELLE = "WO-SENTINELLE-NE-DOIT-PAS-FUITER"

# Floci est publie sur le port 4566 de l'hote (cf. runtime.services du lab et
# la valeur par defaut de var.floci_endpoint).
FLOCI_HOST = "127.0.0.1"
FLOCI_PORT = 14566


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
        absence = message(
            en=f"Floci unreachable on {FLOCI_HOST}:{FLOCI_PORT}. The lab needs it "
            "for the SSM API. `dsoxlab run/check` starts it on its own "
            "(runtime.services).",
            fr=f"Floci injoignable sur {FLOCI_HOST}:{FLOCI_PORT}. Le lab en a besoin "
            "pour l'API SSM. `dsoxlab run/check` le démarre tout seul "
            "(runtime.services).",
        )
        if os.environ.get("LAB_WORKDIR"):
            pytest.fail(absence)
        pytest.skip(absence)
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
            en="`terraform apply` failed. A leftover `???`, or `value_wo` without its "
            f"`value_wo_version` (the pair is mandatory)?\n{app.stderr[-1500:]}",
            fr="`terraform apply` a échoué. Un `???` restant, ou `value_wo` sans son "
            f"`value_wo_version` (le couple est obligatoire) ?\n{app.stderr[-1500:]}",
        )
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
    assert len(params) == 1, message(
        en=f"{len(params)} aws_ssm_parameter in the state, 1 expected.",
        fr=f"{len(params)} aws_ssm_parameter dans le state, attendu 1.",
    )
    return params[0]


# --------------------------------------------------------------------------
# 1. Le parametre existe et value_wo ne round-trip PAS dans le state
# --------------------------------------------------------------------------

def test_value_wo_absent_du_state(applied: Path) -> None:
    values = _param(applied)["values"]
    assert values["value_wo"] is None, message(
        en=f"`value_wo` = {values['value_wo']!r} in the state, expected null. A "
        "write-only argument is passed to the provider but never persisted: if it "
        "carries a value here, then an ordinary argument (`value`) was "
        "used, and the secret leaks.",
        fr=f"`value_wo` = {values['value_wo']!r} dans le state, attendu null. Un "
        "argument write-only est transmis au provider mais jamais persisté : s'il "
        "porte une valeur ici, c'est un argument ordinaire (`value`) qui a été "
        "utilisé, et le secret fuite.",
    )


# --------------------------------------------------------------------------
# 2. La sentinelle du secret n'est NULLE PART dans terraform.tfstate
# --------------------------------------------------------------------------

def test_secret_absent_du_fichier_state(applied: Path) -> None:
    tfstate = applied / "terraform.tfstate"
    assert tfstate.is_file(), message(
        en="terraform.tfstate missing after the apply.",
        fr="terraform.tfstate absent après apply.",
    )
    contenu = tfstate.read_text(encoding="utf-8")
    assert SENTINELLE not in contenu, message(
        en="The secret's value appears in clear in terraform.tfstate. That is "
        "exactly what a write-only argument must prevent: the secret must "
        "never touch the state.",
        fr="La valeur du secret apparaît en clair dans terraform.tfstate. C'est "
        "exactement ce qu'un argument write-only doit empêcher : le secret ne "
        "doit jamais toucher le state.",
    )


# --------------------------------------------------------------------------
# 3. value_wo_version EST persiste (il pilote le renvoi de la valeur)
# --------------------------------------------------------------------------

def test_version_wo_persistee(applied: Path) -> None:
    values = _param(applied)["values"]
    assert values.get("value_wo_version") == 1, message(
        en=f"`value_wo_version` = {values.get('value_wo_version')!r}, expected 1. That "
        "number, on the other hand, is stored in the state: it is what tells Terraform "
        "when to send the value back to the service.",
        fr=f"`value_wo_version` = {values.get('value_wo_version')!r}, attendu 1. Ce "
        "numéro, lui, est stocké dans le state : c'est ce qui dit à Terraform "
        "quand renvoyer la valeur au service.",
    )
    version_output = output_json(applied).get("value_wo_version", {}).get("value")
    assert version_output == 1, message(
        en=f"output value_wo_version = {version_output!r}, expected 1.",
        fr=f"output value_wo_version = {version_output!r}, attendu 1.",
    )


# --------------------------------------------------------------------------
# 4. Idempotence
# --------------------------------------------------------------------------

def test_configuration_stable_apres_apply(applied: Path) -> None:
    p = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=applied)
    assert p.returncode == 0, message(
        en=f"`plan -detailed-exitcode` returns {p.returncode} (2 = changes "
        "remain planned). As long as value_wo_version does not change, no resending "
        f"of the value is planned and the plan must be empty.\n{p.stdout[-800:]}",
        fr=f"`plan -detailed-exitcode` rend {p.returncode} (2 = des changements "
        "restent planifiés). Tant que value_wo_version ne change pas, aucun renvoi "
        f"de la valeur n'est prévu et le plan doit être vide.\n{p.stdout[-800:]}",
    )
