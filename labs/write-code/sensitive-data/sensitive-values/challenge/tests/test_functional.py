"""Tests fonctionnels du lab « la sensibilite qui casse for_each ».

Principe : on ne lit jamais le CONTENU des `.tf` de l'apprenant, seulement
`terraform show -json` (state, dont sensitive_values), `output -json` et des
codes retour.

Faits verifies sur Terraform v1.15.4 :
- une valeur sensible ne peut PAS servir de cle for_each (« Invalid for_each
  argument ») : il faut iterer sur un ensemble NON sensible ;
- un attribut de ressource alimente par une valeur sensible est marque dans
  `sensitive_values` du state ;
- le sha256 d'un secret reste sensible : `nonsensitive()` le declassifie pour
  l'exposer dans un output non sensible.
"""

import json
from pathlib import Path

import pytest

from conftest import exiger_workdir, output_json, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "write-code-sensitive-data-sensitive-values"


@pytest.fixture(scope="module")
def applied() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(f"`terraform init` a echoue.\n{init.stderr[-1200:]}")
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(
            "`terraform apply` a echoue. Un `???` restant, une valeur SENSIBLE "
            f"utilisee en cle for_each (Invalid for_each argument) ?\n{app.stderr[-1500:]}"
        )
    return WORKDIR


def _confs(cwd: Path) -> list[dict]:
    return [r for r in show_json(cwd)["values"]["root_module"]["resources"]
            if r.get("type") == "local_file" and r.get("name") == "conf"]


# --------------------------------------------------------------------------
# 1. for_each keye par des cles NON sensibles (services)
# --------------------------------------------------------------------------

def test_for_each_sur_cles_non_sensibles(applied: Path) -> None:
    confs = _confs(applied)
    assert confs, "Aucune instance conf : le for_each a-t-il abouti ?"
    indices = {r.get("index") for r in confs}
    assert indices == {"web", "db"}, (
        f"Cles conf = {sorted(indices)}, attendu web/db. Iterez sur var.services "
        "(NON sensible) : une valeur sensible en cle for_each est refusee."
    )


# --------------------------------------------------------------------------
# 2. L'attribut content est contamine (marque dans sensitive_values)
# --------------------------------------------------------------------------

def test_content_marque_sensible(applied: Path) -> None:
    for r in _confs(applied):
        sv = r.get("sensitive_values", {})
        assert sv.get("content") is True, (
            f"conf[{r.get('index')!r}] : content n'est pas marque sensible dans "
            "sensitive_values. Un attribut alimente par une valeur sensible doit "
            "l'etre : c'est la trace de la contamination."
        )


# --------------------------------------------------------------------------
# 3. empreinte : declassifiee, non sensible, aucun secret
# --------------------------------------------------------------------------

def test_empreinte_declassifiee(applied: Path) -> None:
    out = output_json(applied).get("empreinte", {})
    assert out.get("sensitive") is False, (
        "`empreinte` ne doit pas etre sensible : le sha256 d'un secret reste "
        "sensible, utilisez nonsensitive() pour l'exposer."
    )
    v = out.get("value")
    assert isinstance(v, str) and len(v) == 64, (
        f"`empreinte` = {v!r}, attendu un sha256 (64 hex)."
    )


# --------------------------------------------------------------------------
# 4. Idempotence
# --------------------------------------------------------------------------

def test_configuration_stable_apres_apply(applied: Path) -> None:
    p = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=applied)
    assert p.returncode == 0, (
        f"`plan -detailed-exitcode` rend {p.returncode} (2 = des changements "
        "restent planifies). Un apply doit converger."
    )
