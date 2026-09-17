"""Tests fonctionnels du lab « ce que les expressions calculent vraiment ».

Principe : on ne lit jamais le CONTENU des `.tf` de l'apprenant, seulement
`terraform show -json`, `output -json` et des codes retour.

Faits verifies sur Terraform v1.15.4 :
- une ressource geree se reference SANS prefixe (`random_pet.hote.id`) ;
- l'operateur `==` NE convertit PAS les types : `var.seuil == "3"` vaut false
  quand seuil est le nombre 3 ;
- la precedence est classique : `1 + var.seuil * 2` vaut 7, pas 8 ;
- `null` sur un argument de ressource vaut OMISSION : `file_permission = null`
  retombe sur le defaut du provider (0777), la ou "" serait invalide.
"""

from pathlib import Path

import pytest

from conftest import exiger_workdir, output_json, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "write-code-expressions"


@pytest.fixture(scope="module")
def applied() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(f"`terraform init` a echoue.\n{init.stderr[-1200:]}")
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(
            "`terraform apply` a echoue. Un `???` restant, ou file_permission mis "
            f'a "" au lieu de null (permission invalide) ?\n{app.stderr[-1500:]}'
        )
    return WORKDIR


# --------------------------------------------------------------------------
# 1. Reference SANS prefixe
# --------------------------------------------------------------------------

def test_ref_hote_sans_prefixe(applied: Path) -> None:
    pet_id = next(
        r["values"]["id"]
        for r in show_json(applied)["values"]["root_module"]["resources"]
        if r.get("type") == "random_pet"
    )
    ref = output_json(applied)["ref_hote"]["value"]
    assert ref == pet_id, (
        f"`ref_hote` = {ref!r}, attendu l'id du random_pet ({pet_id!r}). "
        "Une ressource geree se reference SANS prefixe : random_pet.hote.id."
    )


# --------------------------------------------------------------------------
# 2. == ne convertit pas les types
# --------------------------------------------------------------------------

def test_egalite_stricte_ne_convertit_pas(applied: Path) -> None:
    v = output_json(applied)["egalite_stricte"]["value"]
    assert v is False, (
        f"`egalite_stricte` = {v!r}, attendu false. L'operateur == ne convertit "
        'PAS : le nombre 3 n\'est pas egal a la chaine "3".'
    )


# --------------------------------------------------------------------------
# 3. Precedence des operateurs
# --------------------------------------------------------------------------

def test_calcul_precedence(applied: Path) -> None:
    v = output_json(applied)["calcul"]["value"]
    assert v == 7, (
        f"`calcul` = {v!r}, attendu 7 (1 + 3 * 2). La multiplication passe avant "
        "l'addition : 1 + (var.seuil * 2), pas (1 + var.seuil) * 2."
    )
    assert isinstance(v, (int, float)) and not isinstance(v, bool), (
        f"`calcul` doit etre un NOMBRE, obtenu {type(v).__name__}."
    )


# --------------------------------------------------------------------------
# 4. null = argument omis
# --------------------------------------------------------------------------

def test_null_vaut_omission(applied: Path) -> None:
    v = output_json(applied)["perm_effective"]["value"]
    assert v == "0777", (
        f"`perm_effective` = {v!r}, attendu '0777'. Avec var.perm_forcee vide, "
        "file_permission doit valoir null (omission), et le provider applique "
        "alors son defaut 0777. Une chaine vide aurait ete une permission invalide."
    )


def test_perm_forcee_prise_en_compte(applied: Path) -> None:
    """Rejeu avec une permission explicite : elle doit passer, puis on restaure."""
    p = terraform("apply", "-auto-approve", "-input=false", "-no-color",
                  "-var", "perm_forcee=0600", cwd=applied)
    assert p.returncode == 0, f"apply avec perm_forcee=0600 a echoue.\n{p.stderr[-600:]}"
    try:
        v = output_json(applied)["perm_effective"]["value"]
        assert v == "0600", f"`perm_effective` = {v!r}, attendu '0600' quand force."
    finally:
        terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=applied)


# --------------------------------------------------------------------------
# 5. Idempotence
# --------------------------------------------------------------------------

def test_configuration_stable_apres_apply(applied: Path) -> None:
    p = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=applied)
    assert p.returncode == 0, (
        f"`plan -detailed-exitcode` rend {p.returncode} (2 = des changements "
        "restent planifies). Un apply doit converger."
    )
