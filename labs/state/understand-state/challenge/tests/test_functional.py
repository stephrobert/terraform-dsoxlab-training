"""Tests fonctionnels du lab « le state sait tout, y compris ce qu'il ne devrait pas ».

Principe : on ne lit jamais le CONTENU des `.tf` de l'apprenant. On pilote
Terraform et on n'exploite que `show -json`, `state pull`, des codes retour, et
la fixture du mot de passe existant (la reference attendue).

Faits verifies sur Terraform 1.15.4 (providers random + local, hors ligne) :
- un bloc `import` rattache le mot de passe existant SANS le regenerer ;
- le secret est EN CLAIR dans `state pull`, tout en etant marque
  `sensitive_attributes` (la marque existe, la protection non) ;
- une derive hors Terraform est vue par `plan` (exit 2) mais pas par
  `plan -refresh=false` (exit 0) : la detection vient du rafraichissement ;
- `terraform state push` refuse un state de serial anterieur, et refuse un
  state de lineage different, avec deux messages distincts.
"""

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "state-understand-state"


def _mot_de_passe(cwd: Path) -> str:
    return (cwd / "mot-de-passe-existant.txt").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def applied() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(f"`terraform init` a echoue.\n{init.stderr[-1200:]}")
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(
            "`terraform apply` a echoue. Un `???` restant, ou le bloc import "
            f"manquant/mal ecrit ?\n{app.stderr[-1500:]}"
        )
    yield WORKDIR
    terraform("destroy", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)


def _resources(cwd: Path) -> list[dict]:
    return show_json(cwd)["values"]["root_module"]["resources"]


# --------------------------------------------------------------------------
# 1. Reprise sans regeneration : le secret existant a ete rattache
# --------------------------------------------------------------------------

def test_reprise_sans_regeneration(applied: Path) -> None:
    attendu = _mot_de_passe(applied)
    res = {r["address"]: r["values"] for r in _resources(applied)}
    assert res["random_password.db"]["result"] == attendu, (
        "random_password.db.result n'est pas le mot de passe existant : un simple "
        "`apply` en a tire un neuf. Il fallait un bloc import."
    )
    # Comparaison apres decodage JSON (Terraform echappe < et > en \\u003c/\\u003e).
    assert attendu in res["local_file.configuration"]["content"], (
        "app.conf ne contient pas le mot de passe rattache."
    )


# --------------------------------------------------------------------------
# 2. Le secret est EN CLAIR dans le state, malgre la marque sensitive
# --------------------------------------------------------------------------

def test_secret_en_clair_dans_le_state(applied: Path) -> None:
    attendu = _mot_de_passe(applied)
    pull = terraform("state", "pull", cwd=applied)
    pull.check_returncode()
    state = json.loads(pull.stdout)
    inst = next(
        i for r in state["resources"] if r["type"] == "random_password"
        for i in r["instances"]
    )
    assert inst["attributes"]["result"] == attendu, (
        "Le mot de passe devrait etre EN CLAIR dans le state (c'est le probleme)."
    )
    assert any("result" in json.dumps(s) for s in inst.get("sensitive_attributes", [])), (
        "result devrait figurer dans sensitive_attributes : la marque existe, mais "
        "elle ne cache rien du contenu du state."
    )


# --------------------------------------------------------------------------
# 3. Derive vue par refresh, pas par le state seul
# --------------------------------------------------------------------------

def test_derive_detectee_par_refresh(applied: Path) -> None:
    log = applied / "service.log"
    original = log.read_text(encoding="utf-8")
    log.write_text(original + "\nligne ajoutee hors terraform\n", encoding="utf-8")
    try:
        avec = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=applied)
        assert avec.returncode == 2, (
            f"plan (avec refresh) rend {avec.returncode}, attendu 2 : la derive du "
            "fichier doit etre vue."
        )
        sans = terraform(
            "plan", "-input=false", "-refresh=false", "-detailed-exitcode", "-no-color",
            cwd=applied,
        )
        assert sans.returncode == 0, (
            f"plan -refresh=false rend {sans.returncode}, attendu 0 : sans "
            "rafraichissement, le state seul ne voit pas la derive."
        )
    finally:
        terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=applied)
    apres = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=applied)
    assert apres.returncode == 0, "apply doit retablir la convergence."


# --------------------------------------------------------------------------
# 4. state push refuse un serial anterieur, et un lineage different
# --------------------------------------------------------------------------

def test_state_push_refuse_etat_anterieur(applied: Path, tmp_path: Path) -> None:
    pull = terraform("state", "pull", cwd=applied)
    pull.check_returncode()
    courant = json.loads(pull.stdout)
    serial_courant = courant["serial"]

    vieux = dict(courant)
    vieux["serial"] = max(0, serial_courant - 1)
    f_vieux = tmp_path / "etat-anterieur.tfstate"
    f_vieux.write_text(json.dumps(vieux), encoding="utf-8")
    r1 = terraform("state", "push", str(f_vieux), cwd=applied)
    assert r1.returncode != 0, "state push d'un serial anterieur doit etre refuse."
    assert "serial" in (r1.stdout + r1.stderr).lower()

    autre = dict(courant)
    autre["lineage"] = "00000000-0000-0000-0000-000000000000"
    f_autre = tmp_path / "autre-lineage.tfstate"
    f_autre.write_text(json.dumps(autre), encoding="utf-8")
    r2 = terraform("state", "push", str(f_autre), cwd=applied)
    assert r2.returncode != 0, "state push d'un lineage different doit etre refuse."
    assert "lineage" in (r2.stdout + r2.stderr).lower(), (
        "Le refus d'un lineage different doit porter un message distinct."
    )

    apres = json.loads(terraform("state", "pull", cwd=applied).stdout)
    assert apres["serial"] == serial_courant, (
        "Le serial courant ne doit pas avoir bouge malgre les tentatives refusees."
    )


# --------------------------------------------------------------------------
# 5. Idempotence et perimetre : exactement 3 ressources managed, 0 data
# --------------------------------------------------------------------------

def test_idempotence_et_perimetre(applied: Path) -> None:
    res = _resources(applied)
    managed = [r for r in res if r.get("mode") == "managed"]
    assert len(managed) == 3, f"{len(managed)} ressources managed, attendu 3."
    assert all(r.get("mode") != "data" for r in res), "Aucune data source attendue."
    p = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=applied)
    assert p.returncode == 0, f"plan -detailed-exitcode rend {p.returncode}, attendu 0."
