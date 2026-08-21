"""Tests fonctionnels du lab « source explicite et alias de provider ».

Principe : on ne lit jamais le CONTENU des `.tf` de l'apprenant, seulement
`terraform version -json` (selection de providers), la representation de
configuration du plan JSON (`configuration.provider_config` et le
`provider_config_key` des ressources), `show -json` (state) et des codes retour.

Faits verifies sur Terraform v1.15.4 :
- une source explicite `hashicorp/random` se resout en l'adresse complete
  `registry.terraform.io/hashicorp/random` (version -json) ;
- une seconde config du meme provider SANS alias leve « Duplicate provider
  configuration » ;
- le plan JSON expose chaque config dans `provider_config` (avec `full_name` et
  `alias`) et chaque ressource porte un `provider_config_key`.
"""

import json
from pathlib import Path

import pytest

from conftest import exiger_workdir, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "write-code-providers"


@pytest.fixture(scope="module")
def applied() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(f"`terraform init` a echoue.\n{init.stderr[-1200:]}")
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(
            "`terraform apply` a echoue. Un `???` restant, une source invalide, ou "
            f"une seconde config provider sans alias (doublon) ?\n{app.stderr[-1500:]}"
        )
    return WORKDIR


def _config(cwd: Path) -> dict:
    p = terraform("plan", "-input=false", "-no-color", "-out=tfplan", cwd=cwd)
    if p.returncode != 0:
        pytest.fail(f"`terraform plan` a echoue.\n{p.stderr[-1000:]}")
    return json.loads(terraform("show", "-json", "tfplan", cwd=cwd).stdout)["configuration"]


# --------------------------------------------------------------------------
# 1. La source explicite se resout en adresse complete
# --------------------------------------------------------------------------

def test_source_explicite_resolue(applied: Path) -> None:
    data = json.loads(terraform("version", "-json", cwd=applied).stdout)
    selections = data.get("provider_selections", {})
    assert "registry.terraform.io/hashicorp/random" in selections, (
        f"provider_selections = {selections}. La source doit etre explicite "
        "(hashicorp/random), qui se resout en registry.terraform.io/hashicorp/random."
    )


# --------------------------------------------------------------------------
# 2. Une configuration aliasee "secondaire" est declaree
# --------------------------------------------------------------------------

def test_alias_secondaire_declare(applied: Path) -> None:
    provider_config = _config(applied).get("provider_config", {})
    aliasee = provider_config.get("random.secondaire")
    assert aliasee is not None, (
        f"Pas de configuration aliasee 'random.secondaire'. Configs vues : "
        f"{list(provider_config)}. Declarez un second bloc provider random avec "
        "alias = \"secondaire\"."
    )
    assert aliasee.get("alias") == "secondaire"
    assert aliasee.get("full_name") == "registry.terraform.io/hashicorp/random"


# --------------------------------------------------------------------------
# 3. La bonne ressource est cablee sur l'alias, l'autre sur le defaut
# --------------------------------------------------------------------------

def test_cablage_des_ressources(applied: Path) -> None:
    resources = _config(applied)["root_module"]["resources"]
    keys = {r["address"]: r.get("provider_config_key") for r in resources}
    assert keys.get("random_pet.autre") == "random.secondaire", (
        f"random_pet.autre est cablee sur {keys.get('random_pet.autre')!r}, attendu "
        "'random.secondaire'. Ajoutez `provider = random.secondaire` sur cette ressource."
    )
    assert keys.get("random_pet.defaut") == "random", (
        f"random_pet.defaut est cablee sur {keys.get('random_pet.defaut')!r}, attendu "
        "la config par defaut 'random' (ne pas y mettre de provider=)."
    )


# --------------------------------------------------------------------------
# 4. Les deux ressources existent
# --------------------------------------------------------------------------

def test_deux_pets_dans_le_state(applied: Path) -> None:
    pets = [r for r in show_json(applied)["values"]["root_module"]["resources"]
            if r.get("type") == "random_pet"]
    assert len(pets) == 2, f"{len(pets)} random_pet dans le state, attendu 2."


# --------------------------------------------------------------------------
# 5. Idempotence
# --------------------------------------------------------------------------

def test_configuration_stable_apres_apply(applied: Path) -> None:
    p = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=applied)
    assert p.returncode == 0, (
        f"`plan -detailed-exitcode` rend {p.returncode} (2 = des changements "
        "restent planifies). Un apply doit converger."
    )
