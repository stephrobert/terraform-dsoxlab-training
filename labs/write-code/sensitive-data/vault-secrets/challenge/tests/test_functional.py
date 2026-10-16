"""Tests fonctionnels du lab « le secret vient de Vault, le state n'en saura rien ».

Principe : on ne lit jamais le CONTENU des `.tf` de l'apprenant, seulement
`terraform show -json`, le fichier de state brut, des codes retour, et l'etat
reel de Vault via son API HTTP.

Faits verifies sur Terraform 1.15.4, provider hashicorp/vault 5.x, contre un
Vault dev (kv-v2 sur kvv2, secret source app/db) :
- le secret source est lu par un bloc `ephemeral` : aucune entree `mode: data`
  ni le secret dans le state ;
- la replique est un `vault_kv_secret_v2` dont `data_json_wo` et `data_json`
  valent null, `data` est vide, et `data_json_wo_version` porte un nombre ;
- la valeur du secret source n'apparait nulle part dans show -json ni le state ;
- la replique dans Vault contient pourtant le meme mot de passe ;
- idempotence, et rotation pilotee par copie_version.

Prerequis Vault : sous `dsoxlab run/check`, `runtime.services` demarre le
serveur Vault dev. Hors dsoxlab (pytest nu), le test SKIPPE si Vault est
injoignable, sauf sous `LAB_WORKDIR` (verify-solutions) ou son absence ECHOUE.
"""

import json
import os
import urllib.error
import urllib.request
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
LAB_ID = "write-code-sensitive-data-vault-secrets"

VAULT_ADDR = "http://127.0.0.1:8200"
VAULT_TOKEN = "root"  # noqa: S105 - jeton du Vault de dev du lab, pas un secret
# Valeur sentinelle du secret source, posee par le seed. Le test verifie
# qu'elle n'apparait NULLE PART cote Terraform.
SENTINELLE = "VAULT-SENTINELLE-NE-DOIT-PAS-FUITER"


def _vault(method: str, path: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    # S310 vise les deux appels, la requête comme son ouverture : l'adresse est
    # la constante VAULT_ADDR, en http://127.0.0.1, et non une entrée.
    req = urllib.request.Request(
        f"{VAULT_ADDR}/v1/{path}",
        data=data,
        method=method,
        headers={"X-Vault-Token": VAULT_TOKEN},
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        body = resp.read()
    return json.loads(body) if body else {}


def _vault_up() -> bool:
    try:
        _vault("GET", "sys/health")
        return True
    except (urllib.error.URLError, OSError):
        return False


def _seed() -> None:
    """Monte kvv2 (si absent) et depose le secret source app/db."""
    try:
        _vault("POST", "sys/mounts/kvv2", {"type": "kv", "options": {"version": "2"}})
    except urllib.error.HTTPError as e:
        if e.code != 400:  # 400 = deja monte, acceptable
            raise
    _vault("POST", "kvv2/data/app/db",
           {"data": {"password": SENTINELLE, "username": "app"}})


@pytest.fixture(scope="module")
def applied() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    if not _vault_up():
        explication = message(
            en=f"Vault cannot be reached at {VAULT_ADDR}. The lab needs it. "
            "`dsoxlab run/check` starts it on its own (runtime.services).",
            fr=f"Vault injoignable sur {VAULT_ADDR}. Le lab en a besoin. "
            "`dsoxlab run/check` le démarre tout seul (runtime.services).",
        )
        if os.environ.get("LAB_WORKDIR"):
            pytest.fail(explication)
        pytest.skip(explication)
    _seed()
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
            en="`terraform apply` failed. A leftover `???`, a badly written `ephemeral` "
            f"block, or data_json_wo without its version?\n{app.stderr[-1500:]}",
            fr="`terraform apply` a échoué. Un `???` restant, un bloc `ephemeral` mal "
            f"écrit, ou data_json_wo sans sa version ?\n{app.stderr[-1500:]}",
        )
        )
    yield WORKDIR
    terraform("destroy", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)


def _replique(cwd: Path) -> dict:
    res = show_json(cwd)["values"]["root_module"]["resources"]
    reps = [r for r in res if r.get("type") == "vault_kv_secret_v2"]
    assert len(reps) == 1, message(
        en=f"{len(reps)} vault_kv_secret_v2 in the state, 1 expected.",
        fr=f"{len(reps)} vault_kv_secret_v2 dans le state, attendu 1.",
    )
    return reps[0]


# --------------------------------------------------------------------------
# 1. L'ephemere ne laisse rien : aucun mode data, secret write-only null
# --------------------------------------------------------------------------

def test_ephemere_et_write_only_absents_du_state(applied: Path) -> None:
    res = show_json(applied)["values"]["root_module"]["resources"]
    assert all(r.get("mode") != "data" for r in res), message(
        en="No mode: data entry must remain: the source secret is read through "
        "an ephemeral block, not through a data source.",
        fr="Aucune entrée mode: data ne doit subsister : le secret source se lit par "
        "un bloc ephemeral, pas par une data source.",
    )
    v = _replique(applied)["values"]
    assert v.get("data_json_wo") is None, message(
        en=f"data_json_wo should be null: {v.get('data_json_wo')!r}",
        fr=f"data_json_wo devrait être null : {v.get('data_json_wo')!r}",
    )
    assert v.get("data_json") is None, message(
        en=f"data_json should be null: {v.get('data_json')!r}",
        fr=f"data_json devrait être null : {v.get('data_json')!r}",
    )
    assert v.get("data") == {}, message(
        en=f"data should be empty: {v.get('data')!r}",
        fr=f"data devrait être vide : {v.get('data')!r}",
    )
    assert v.get("data_json_wo_version") == 1, message(
        en=f"data_json_wo_version should be 1: {v.get('data_json_wo_version')!r}",
        fr=f"data_json_wo_version devrait valoir 1 : {v.get('data_json_wo_version')!r}",
    )


# --------------------------------------------------------------------------
# 2. Le secret source n'apparait NULLE PART cote Terraform
# --------------------------------------------------------------------------

def test_secret_absent_du_state(applied: Path) -> None:
    doc = json.dumps(show_json(applied))
    assert SENTINELLE not in doc, message(
        en="The source secret appears in show -json.",
        fr="Le secret source apparaît dans show -json.",
    )
    tfstate = (applied / "terraform.tfstate").read_text(encoding="utf-8")
    assert SENTINELLE not in tfstate, message(
        en="The source secret appears in terraform.tfstate.",
        fr="Le secret source apparaît dans terraform.tfstate.",
    )


# --------------------------------------------------------------------------
# 3. La replique dans Vault contient bien le meme secret
# --------------------------------------------------------------------------

def test_replique_dans_vault(applied: Path) -> None:
    rep = _vault("GET", "kvv2/data/app/db-replique")
    assert rep["data"]["data"]["password"] == SENTINELLE, message(
        en="The replica in Vault must contain the same password as the source: "
        "the secret did pass through during the operation, without being persisted.",
        fr="La réplique dans Vault doit contenir le même mot de passe que la source : "
        "le secret a bien transité pendant l'opération, sans être persisté.",
    )
    chemin = output_json(applied).get("chemin", {}).get("value")
    assert chemin == "kvv2/app/db-replique", message(
        en=f"output chemin = {chemin!r}.",
        fr=f"output chemin = {chemin!r}.",
    )


# --------------------------------------------------------------------------
# 4. Idempotence, et rotation par copie_version
# --------------------------------------------------------------------------

def test_idempotence_et_rotation(applied: Path) -> None:
    p0 = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=applied)
    assert p0.returncode == 0, message(
        en=f"plan -detailed-exitcode returns {p0.returncode}, expected 0 after the apply.",
        fr=f"plan -detailed-exitcode rend {p0.returncode}, attendu 0 après apply.",
    )
    # Changer le secret source sans toucher la version : toujours aucun plan.
    _vault("POST", "kvv2/data/app/db", {"data": {"password": SENTINELLE + "-v2", "username": "app"}})
    p1 = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=applied)
    assert p1.returncode == 0, message(
        en="Changing the source secret without incrementing copie_version must produce "
        "no plan: Terraform does not track what it does not store.",
        fr="Changer le secret source sans incrémenter copie_version ne doit produire "
        "aucun plan : Terraform ne suit pas ce qu'il ne stocke pas.",
    )
    # Incrementer la version : un plan non vide, puis la replique recoit le neuf.
    p2 = terraform(
        "plan", "-input=false", "-detailed-exitcode", "-no-color",
        "-var", "copie_version=2", cwd=applied,
    )
    assert p2.returncode == 2, message(
        en=f"plan -var copie_version=2 returns {p2.returncode}, expected 2 (rotation).",
        fr=f"plan -var copie_version=2 rend {p2.returncode}, attendu 2 (rotation).",
    )
    apply2 = terraform(
        "apply", "-auto-approve", "-input=false", "-no-color",
        "-var", "copie_version=2", cwd=applied,
    )
    apply2.check_returncode()
    rep = _vault("GET", "kvv2/data/app/db-replique")
    assert rep["data"]["data"]["password"] == SENTINELLE + "-v2", message(
        en="After the rotation, the replica must carry the new source password.",
        fr="Après rotation, la réplique doit porter le nouveau mot de passe source.",
    )
