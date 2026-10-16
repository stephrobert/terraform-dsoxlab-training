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
LAB_ID = "write-code-sensitive-data-sensitive-values"


@pytest.fixture(scope="module")
def applied() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
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
            en="`terraform apply` failed. A leftover `???`, a SENSITIVE value "
            f"used as a for_each key (Invalid for_each argument)?\n{app.stderr[-1500:]}",
            fr="`terraform apply` a échoué. Un `???` restant, une valeur SENSIBLE "
            f"utilisée en clé for_each (Invalid for_each argument) ?\n{app.stderr[-1500:]}",
        )
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
    assert confs, message(
        en="No conf instance: did the for_each succeed?",
        fr="Aucune instance conf : le for_each a-t-il abouti ?",
    )
    indices = {r.get("index") for r in confs}
    assert indices == {"web", "db"}, message(
        en=f"conf keys = {sorted(indices)}, expected web/db. Iterate over var.services "
        "(NOT sensitive): a sensitive value as a for_each key is refused.",
        fr=f"Clés conf = {sorted(indices)}, attendu web/db. Itérez sur var.services "
        "(NON sensible) : une valeur sensible en clé for_each est refusée.",
    )


# --------------------------------------------------------------------------
# 2. L'attribut content est contamine (marque dans sensitive_values)
# --------------------------------------------------------------------------

def test_content_marque_sensible(applied: Path) -> None:
    for r in _confs(applied):
        sv = r.get("sensitive_values", {})
        assert sv.get("content") is True, message(
            en=f"conf[{r.get('index')!r}]: content is not marked sensitive in "
            "sensitive_values. An attribute fed by a sensitive value must "
            "be: that is the trace of the contamination.",
            fr=f"conf[{r.get('index')!r}] : content n'est pas marqué sensible dans "
            "sensitive_values. Un attribut alimenté par une valeur sensible doit "
            "l'être : c'est la trace de la contamination.",
        )


# --------------------------------------------------------------------------
# 3. empreinte : declassifiee, non sensible, aucun secret
# --------------------------------------------------------------------------

def test_empreinte_declassifiee(applied: Path) -> None:
    out = output_json(applied).get("empreinte", {})
    assert out.get("sensitive") is False, message(
        en="`empreinte` must not be sensitive: the sha256 of a secret stays "
        "sensitive, use nonsensitive() to expose it.",
        fr="`empreinte` ne doit pas être sensible : le sha256 d'un secret reste "
        "sensible, utilisez nonsensitive() pour l'exposer.",
    )
    v = out.get("value")
    assert isinstance(v, str) and len(v) == 64, message(
        en=f"`empreinte` = {v!r}, a sha256 (64 hex) was expected.",
        fr=f"`empreinte` = {v!r}, attendu un sha256 (64 hex).",
    )


# --------------------------------------------------------------------------
# 4. Idempotence
# --------------------------------------------------------------------------

def test_configuration_stable_apres_apply(applied: Path) -> None:
    p = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=applied)
    assert p.returncode == 0, message(
        en=f"`plan -detailed-exitcode` returns {p.returncode} (2 = changes "
        "remain planned). An apply must converge.",
        fr=f"`plan -detailed-exitcode` rend {p.returncode} (2 = des changements "
        "restent planifiés). Un apply doit converger.",
    )
