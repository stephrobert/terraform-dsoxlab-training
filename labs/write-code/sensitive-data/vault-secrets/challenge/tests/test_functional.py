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

from conftest import exiger_workdir, output_json, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "write-code-sensitive-data-vault-secrets"

VAULT_ADDR = "http://127.0.0.1:8200"
VAULT_TOKEN = "root"
# Valeur sentinelle du secret source, posee par le seed. Le test verifie
# qu'elle n'apparait NULLE PART cote Terraform.
SENTINELLE = "VAULT-SENTINELLE-NE-DOIT-PAS-FUITER"


def _vault(method: str, path: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        f"{VAULT_ADDR}/v1/{path}",
        data=data,
        method=method,
        headers={"X-Vault-Token": VAULT_TOKEN},
    )
    with urllib.request.urlopen(req, timeout=5) as resp:  # noqa: S310 (URL locale fixe)
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
        message = (
            f"Vault injoignable sur {VAULT_ADDR}. Le lab en a besoin. "
            "`dsoxlab run/check` le demarre tout seul (runtime.services)."
        )
        if os.environ.get("LAB_WORKDIR"):
            pytest.fail(message)
        pytest.skip(message)
    _seed()
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(f"`terraform init` a echoue.\n{init.stderr[-1200:]}")
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(
            "`terraform apply` a echoue. Un `???` restant, un bloc `ephemeral` mal "
            f"ecrit, ou data_json_wo sans sa version ?\n{app.stderr[-1500:]}"
        )
    yield WORKDIR
    terraform("destroy", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)


def _replique(cwd: Path) -> dict:
    res = show_json(cwd)["values"]["root_module"]["resources"]
    reps = [r for r in res if r.get("type") == "vault_kv_secret_v2"]
    assert len(reps) == 1, f"{len(reps)} vault_kv_secret_v2 dans le state, attendu 1."
    return reps[0]


# --------------------------------------------------------------------------
# 1. L'ephemere ne laisse rien : aucun mode data, secret write-only null
# --------------------------------------------------------------------------

def test_ephemere_et_write_only_absents_du_state(applied: Path) -> None:
    res = show_json(applied)["values"]["root_module"]["resources"]
    assert all(r.get("mode") != "data" for r in res), (
        "Aucune entree mode: data ne doit subsister : le secret source se lit par "
        "un bloc ephemeral, pas par une data source."
    )
    v = _replique(applied)["values"]
    assert v.get("data_json_wo") is None, f"data_json_wo devrait etre null : {v.get('data_json_wo')!r}"
    assert v.get("data_json") is None, f"data_json devrait etre null : {v.get('data_json')!r}"
    assert v.get("data") == {}, f"data devrait etre vide : {v.get('data')!r}"
    assert v.get("data_json_wo_version") == 1, (
        f"data_json_wo_version devrait valoir 1 : {v.get('data_json_wo_version')!r}"
    )


# --------------------------------------------------------------------------
# 2. Le secret source n'apparait NULLE PART cote Terraform
# --------------------------------------------------------------------------

def test_secret_absent_du_state(applied: Path) -> None:
    doc = json.dumps(show_json(applied))
    assert SENTINELLE not in doc, "Le secret source apparait dans show -json."
    tfstate = (applied / "terraform.tfstate").read_text(encoding="utf-8")
    assert SENTINELLE not in tfstate, "Le secret source apparait dans terraform.tfstate."


# --------------------------------------------------------------------------
# 3. La replique dans Vault contient bien le meme secret
# --------------------------------------------------------------------------

def test_replique_dans_vault(applied: Path) -> None:
    rep = _vault("GET", "kvv2/data/app/db-replique")
    assert rep["data"]["data"]["password"] == SENTINELLE, (
        "La replique dans Vault doit contenir le meme mot de passe que la source : "
        "le secret a bien transite pendant l'operation, sans etre persiste."
    )
    chemin = output_json(applied).get("chemin", {}).get("value")
    assert chemin == "kvv2/app/db-replique", f"output chemin = {chemin!r}."


# --------------------------------------------------------------------------
# 4. Idempotence, et rotation par copie_version
# --------------------------------------------------------------------------

def test_idempotence_et_rotation(applied: Path) -> None:
    p0 = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=applied)
    assert p0.returncode == 0, (
        f"plan -detailed-exitcode rend {p0.returncode}, attendu 0 apres apply."
    )
    # Changer le secret source sans toucher la version : toujours aucun plan.
    _vault("POST", "kvv2/data/app/db", {"data": {"password": SENTINELLE + "-v2", "username": "app"}})
    p1 = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=applied)
    assert p1.returncode == 0, (
        "Changer le secret source sans incrementer copie_version ne doit produire "
        "aucun plan : Terraform ne suit pas ce qu'il ne stocke pas."
    )
    # Incrementer la version : un plan non vide, puis la replique recoit le neuf.
    p2 = terraform(
        "plan", "-input=false", "-detailed-exitcode", "-no-color",
        "-var", "copie_version=2", cwd=applied,
    )
    assert p2.returncode == 2, (
        f"plan -var copie_version=2 rend {p2.returncode}, attendu 2 (rotation)."
    )
    apply2 = terraform(
        "apply", "-auto-approve", "-input=false", "-no-color",
        "-var", "copie_version=2", cwd=applied,
    )
    apply2.check_returncode()
    rep = _vault("GET", "kvv2/data/app/db-replique")
    assert rep["data"]["data"]["password"] == SENTINELLE + "-v2", (
        "Apres rotation, la replique doit porter le nouveau mot de passe source."
    )
