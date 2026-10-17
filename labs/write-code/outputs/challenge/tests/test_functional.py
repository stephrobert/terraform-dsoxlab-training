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

from conftest import (
    exiger_workdir,
    message,
    output_json,
    show_json,
    terraform,
    workdir_lab,
)

WORKDIR = workdir_lab(__file__)
LAB_ID = "write-code-outputs"


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
            en="`terraform apply` failed. A leftover `???`, or a sensitive output "
            f"not marked `sensitive = true`?\n{app.stderr[-1500:]}",
            fr="`terraform apply` a échoué. Un `???` restant, ou un output sensible "
            f"non marqué `sensitive = true` ?\n{app.stderr[-1500:]}",
        )
        )
    return WORKDIR


def _mdp(cwd: Path) -> str:
    return output_json(cwd)["mot_de_passe_admin"]["value"]


# --------------------------------------------------------------------------
# 1. mot_de_passe_admin : sensible en affichage, mais en clair partout ailleurs
# --------------------------------------------------------------------------

def test_mot_de_passe_marque_sensible(applied: Path) -> None:
    out = output_json(applied).get("mot_de_passe_admin", {})
    assert out.get("sensitive") is True, message(
        en="`mot_de_passe_admin` must carry `sensitive = true`. Without that, "
        "the apply would not even have succeeded: an output referencing a "
        "sensitive value is refused at plan time.",
        fr="`mot_de_passe_admin` doit porter `sensitive = true`. Sans cela, "
        "l'apply n'aurait même pas abouti : un output qui référence une valeur "
        "sensible est refusé au plan.",
    )


def test_valeur_en_clair_dans_output_json(applied: Path) -> None:
    v = _mdp(applied)
    assert isinstance(v, str) and len(v) == 24, message(
        en=f"`mot_de_passe_admin` = {v!r} (len {len(v) if isinstance(v, str) else '?'}), "
        "the CLEAR string of length 24 was expected. `output -json` does not hide "
        "sensitive values: that is the lab's central demonstration.",
        fr=f"`mot_de_passe_admin` = {v!r} (len {len(v) if isinstance(v, str) else '?'}), "
        "attendu la chaîne EN CLAIR de longueur 24. `output -json` ne masque pas "
        "les valeurs sensibles : c'est la démonstration centrale du lab.",
    )


def test_valeur_en_clair_dans_le_state(applied: Path) -> None:
    result = next(
        r["values"]["result"]
        for r in show_json(applied)["values"]["root_module"]["resources"]
        if r.get("type") == "random_password"
    )
    assert result == _mdp(applied), message(
        en="The state keeps the password IN CLEAR (random_password.result), "
        "identical to the output. `sensitive` does not protect the state.",
        fr="Le state conserve le mot de passe EN CLAIR (random_password.result), "
        "identique à l'output. `sensitive` ne protège pas le state.",
    )


def test_raw_leve_la_redaction(applied: Path) -> None:
    p = terraform("output", "-raw", "mot_de_passe_admin", cwd=applied)
    assert p.returncode == 0 and p.stdout.strip() == _mdp(applied), message(
        en="`terraform output -raw` must return the same clear string: `-raw` "
        "lifts the redaction just as `-json` does.",
        fr="`terraform output -raw` doit rendre la même chaîne en clair : `-raw` "
        "lève la rédaction au même titre que `-json`.",
    )


# --------------------------------------------------------------------------
# 2. resume : contrainte de type object + aucun secret + nonsensitive
# --------------------------------------------------------------------------

def test_resume_objet_type_sans_secret(applied: Path) -> None:
    out = output_json(applied).get("resume", {})
    assert out.get("sensitive") is False, message(
        en="`resume` must not be sensitive.",
        fr="`resume` ne doit pas être sensible.",
    )
    val = out.get("value")
    assert isinstance(val, dict) and set(val) == {"longueur", "empreinte"}, message(
        en=f"`resume` = {val!r}, an object {{ longueur, empreinte }} was expected "
        "(constraint type = object({ longueur = number, empreinte = string })).",
        fr=f"`resume` = {val!r}, attendu un objet {{ longueur, empreinte }} "
        "(contrainte type = object({ longueur = number, empreinte = string })).",
    )
    assert val["longueur"] == 24, message(
        en=f"resume.longueur = {val['longueur']}, expected 24.",
        fr=f"resume.longueur = {val['longueur']}, attendu 24.",
    )
    assert isinstance(val["empreinte"], str) and len(val["empreinte"]) == 64, message(
        en=f"resume.empreinte = {val['empreinte']!r}, a sha256 (64 hex) was expected. "
        "The sha256 of a sensitive value stays sensitive: use nonsensitive().",
        fr=f"resume.empreinte = {val['empreinte']!r}, attendu un sha256 (64 hex). "
        "Le sha256 d'une valeur sensible reste sensible : utilisez nonsensitive().",
    )
    assert val["empreinte"] != _mdp(applied), message(
        en="resume must expose NO secret in clear.",
        fr="resume ne doit exposer AUCUN secret en clair.",
    )


# --------------------------------------------------------------------------
# 3. empreinte_rapport + precondition
# --------------------------------------------------------------------------

def test_empreinte_rapport(applied: Path) -> None:
    v = output_json(applied)["empreinte_rapport"]["value"]
    assert isinstance(v, str) and len(v) == 64, message(
        en=f"`empreinte_rapport` = {v!r}, a sha256 (64 hex) of the report's content was expected.",
        fr=f"`empreinte_rapport` = {v!r}, attendu un sha256 (64 hex) du contenu du rapport.",
    )


def test_precondition_bloque_le_plan(applied: Path) -> None:
    p = terraform("plan", "-input=false", "-no-color", "-var",
                  "longueur_mot_de_passe=8", cwd=applied)
    assert p.returncode != 0, message(
        en="With longueur_mot_de_passe=8, the `precondition` of the "
        "`empreinte_rapport` output must make the plan FAIL (it requires >= 20).",
        fr="Avec longueur_mot_de_passe=8, le `precondition` de l'output "
        "`empreinte_rapport` doit faire ÉCHOUER le plan (exige >= 20).",
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
