"""Tests fonctionnels du lab « le secret que l'output ne cache pas ».

Principe : on ne lit jamais le CONTENU des `.tf` de l'apprenant, seulement
`terraform show -json`, `output -json`, `output -raw` et des codes retour.

Faits verifies sur Terraform v1.15.4 :
- un output referencant une valeur sensible (random_password.result) est refuse
  au plan tant qu'il ne porte pas `sensitive = true` (« Output refers to
  sensitive values ») ;
- `sensitive` ne masque que l'affichage humain : `output -json` et `output -raw`
  rendent la valeur EN CLAIR, et le state la conserve ;
- la sensibilite se propage a travers les fonctions : `sha256(secret)` reste
  sensible, il faut `nonsensitive()` pour l'exposer dans un output non sensible ;
- une contrainte `type = object({...})` sur un output est respectee ;
- un `precondition` porte par un output fait echouer le plan.
"""

from pathlib import Path

import pytest

from conftest import exiger_workdir, output_json, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "write-code-outputs"


@pytest.fixture(scope="module")
def applied() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(f"`terraform init` a echoue.\n{init.stderr[-1200:]}")
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(
            "`terraform apply` a echoue. Un `???` restant, ou un output sensible "
            f"non marque `sensitive = true` ?\n{app.stderr[-1500:]}"
        )
    return WORKDIR


def _mdp(cwd: Path) -> str:
    return output_json(cwd)["mot_de_passe_admin"]["value"]


# --------------------------------------------------------------------------
# 1. mot_de_passe_admin : sensible en affichage, mais en clair partout ailleurs
# --------------------------------------------------------------------------

def test_mot_de_passe_marque_sensible(applied: Path) -> None:
    out = output_json(applied).get("mot_de_passe_admin", {})
    assert out.get("sensitive") is True, (
        "`mot_de_passe_admin` doit porter `sensitive = true`. Sans cela, "
        "l'apply n'aurait meme pas abouti : un output qui reference une valeur "
        "sensible est refuse au plan."
    )


def test_valeur_en_clair_dans_output_json(applied: Path) -> None:
    v = _mdp(applied)
    assert isinstance(v, str) and len(v) == 24, (
        f"`mot_de_passe_admin` = {v!r} (len {len(v) if isinstance(v, str) else '?'}), "
        "attendu la chaine EN CLAIR de longueur 24. `output -json` ne masque pas "
        "les valeurs sensibles : c'est la demonstration centrale du lab."
    )


def test_valeur_en_clair_dans_le_state(applied: Path) -> None:
    result = next(
        r["values"]["result"]
        for r in show_json(applied)["values"]["root_module"]["resources"]
        if r.get("type") == "random_password"
    )
    assert result == _mdp(applied), (
        "Le state conserve le mot de passe EN CLAIR (random_password.result), "
        "identique a l'output. `sensitive` ne protege pas le state."
    )


def test_raw_leve_la_redaction(applied: Path) -> None:
    p = terraform("output", "-raw", "mot_de_passe_admin", cwd=applied)
    assert p.returncode == 0 and p.stdout.strip() == _mdp(applied), (
        "`terraform output -raw` doit rendre la meme chaine en clair : `-raw` "
        "leve la redaction au meme titre que `-json`."
    )


# --------------------------------------------------------------------------
# 2. resume : contrainte de type object + aucun secret + nonsensitive
# --------------------------------------------------------------------------

def test_resume_objet_type_sans_secret(applied: Path) -> None:
    out = output_json(applied).get("resume", {})
    assert out.get("sensitive") is False, "`resume` ne doit pas etre sensible."
    val = out.get("value")
    assert isinstance(val, dict) and set(val) == {"longueur", "empreinte"}, (
        f"`resume` = {val!r}, attendu un objet {{ longueur, empreinte }} "
        "(contrainte type = object({ longueur = number, empreinte = string }))."
    )
    assert val["longueur"] == 24, f"resume.longueur = {val['longueur']}, attendu 24."
    assert isinstance(val["empreinte"], str) and len(val["empreinte"]) == 64, (
        f"resume.empreinte = {val['empreinte']!r}, attendu un sha256 (64 hex). "
        "Le sha256 d'une valeur sensible reste sensible : utilisez nonsensitive()."
    )
    assert val["empreinte"] != _mdp(applied), "resume ne doit exposer AUCUN secret en clair."


# --------------------------------------------------------------------------
# 3. empreinte_rapport + precondition
# --------------------------------------------------------------------------

def test_empreinte_rapport(applied: Path) -> None:
    v = output_json(applied)["empreinte_rapport"]["value"]
    assert isinstance(v, str) and len(v) == 64, (
        f"`empreinte_rapport` = {v!r}, attendu un sha256 (64 hex) du contenu du rapport."
    )


def test_precondition_bloque_le_plan(applied: Path) -> None:
    p = terraform("plan", "-input=false", "-no-color", "-var",
                  "longueur_mot_de_passe=8", cwd=applied)
    assert p.returncode != 0, (
        "Avec longueur_mot_de_passe=8, le `precondition` de l'output "
        "`empreinte_rapport` doit faire ECHOUER le plan (exige >= 20)."
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
