"""Tests fonctionnels du lab « la configuration qui marche mais qu'aucune CI n'accepte ».

Principe : on ne lit jamais le CONTENU des `.tf` de l'apprenant pour l'asserer.
On s'appuie sur `terraform fmt -check`, `validate -json`, `show -json`,
`output -json` et des codes retour. Seul le `.gitignore` (un livrable, pas du
HCL) est lu comme du texte.

Faits verifies sur Terraform v1.15.4 :
- `terraform fmt -check` sort en code 3 quand un fichier n'est pas formate ;
- `validate` echoue sur une reference orpheline ;
- un output declare `type = number` sort en nombre JSON meme quand tfvars
  fournit la valeur entre guillemets ;
- le plan JSON expose la `description` des variables et des outputs.
"""

import json
import re
from pathlib import Path

import pytest

from conftest import exiger_workdir, output_json, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "write-code-style-guide"


@pytest.fixture(scope="module")
def applied() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(f"`terraform init` a echoue.\n{init.stderr[-1200:]}")
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(
            "`terraform apply` a echoue. Reference orpheline non resolue "
            f"(var.env_name) ou config invalide ?\n{app.stderr[-1500:]}"
        )
    return WORKDIR


def _plan(cwd: Path) -> dict:
    terraform("plan", "-input=false", "-no-color", "-out=tfplan", cwd=cwd)
    return json.loads(terraform("show", "-json", "tfplan", cwd=cwd).stdout)


# --------------------------------------------------------------------------
# 1. Formatage et validation
# --------------------------------------------------------------------------

def test_fmt_conforme(applied: Path) -> None:
    p = terraform("fmt", "-check", "-recursive", "-no-color", cwd=applied)
    assert p.returncode == 0, (
        "`terraform fmt -check -recursive` signale un fichier non formate "
        f"(code {p.returncode}). Lancez `terraform fmt` sur le repertoire.\n{p.stdout}"
    )


def test_validate_valide(applied: Path) -> None:
    data = json.loads(terraform("validate", "-json", cwd=applied).stdout)
    assert data.get("valid") is True, (
        f"`terraform validate` echoue ({data.get('error_count')} erreur[s]). "
        "La reference orpheline (var.env_name) doit etre resolue."
    )


# --------------------------------------------------------------------------
# 2. Les memes ressources, nommees selon la convention
# --------------------------------------------------------------------------

def test_deux_ressources_intactes(applied: Path) -> None:
    res = show_json(applied)["values"]["root_module"]["resources"]
    types = sorted(r["type"] for r in res)
    assert types == ["local_file", "random_pet"], (
        f"Ressources = {types}, attendu exactement un local_file et un random_pet. "
        "Le refactoring ne doit rien creer ni supprimer."
    )


def test_noms_en_snake_case(applied: Path) -> None:
    res = show_json(applied)["values"]["root_module"]["resources"]
    motif = re.compile(r"^[a-z][a-z0-9_]*$")
    for r in res:
        nom = r["name"]
        assert motif.match(nom), (
            f"Le nom de ressource {nom!r} n'est pas en snake_case. La convention "
            "officielle impose des minuscules et des underscores, jamais de "
            "camelCase ni de tiret."
        )


# --------------------------------------------------------------------------
# 3. Typage et documentation des variables
# --------------------------------------------------------------------------

def test_variables_decrites(applied: Path) -> None:
    variables = _plan(applied)["configuration"]["root_module"].get("variables", {})
    assert variables, "Aucune variable dans la configuration ?"
    for nom, spec in variables.items():
        desc = spec.get("description") or ""
        assert desc.strip(), (
            f"La variable {nom!r} n'a pas de `description`. Le style guide impose "
            "une description sur chaque variable."
        )


def test_replica_count_type_number(applied: Path) -> None:
    p = terraform("plan", "-input=false", "-no-color", "-var", "replica_count=abc", cwd=applied)
    assert p.returncode != 0, (
        "Passer replica_count=abc devrait ECHOUER : la variable doit etre typee "
        "`number`. Non typee, elle accepterait n'importe quoi."
    )


# --------------------------------------------------------------------------
# 4. Outputs : type, description, sensibilite
# --------------------------------------------------------------------------

def test_outputs_types_et_sensibles(applied: Path) -> None:
    outs = output_json(applied)
    assert outs["api_token"]["sensitive"] is True, (
        "L'output `api_token` expose un jeton et doit etre marque `sensitive`."
    )
    replicas = outs["replicas"]
    assert replicas["type"] == "number" and replicas["value"] == 3, (
        f"`replicas` = {replicas!r}, attendu type number et valeur 3. La contrainte "
        "`type = number` fait sortir la valeur en nombre alors que tfvars la donne "
        'entre guillemets ("3").'
    )


def test_outputs_decrits(applied: Path) -> None:
    outputs = _plan(applied)["configuration"]["root_module"].get("outputs", {})
    for nom, spec in outputs.items():
        desc = spec.get("description") or ""
        assert desc.strip(), f"L'output {nom!r} n'a pas de `description`."


# --------------------------------------------------------------------------
# 5. .gitignore : ce qu'on ignore, et ce qu'on committe
# --------------------------------------------------------------------------

def test_gitignore_correct(applied: Path) -> None:
    gi = applied / ".gitignore"
    assert gi.is_file(), "Il manque un fichier `.gitignore`."
    lignes = [l.strip() for l in gi.read_text(encoding="utf-8").splitlines()]
    actifs = [l for l in lignes if l and not l.startswith("#")]

    assert any(l.rstrip("/") == ".terraform" for l in actifs), (
        "`.gitignore` doit ignorer le repertoire `.terraform/`."
    )
    assert any("tfstate" in l for l in actifs), (
        "`.gitignore` doit ignorer les fichiers d'etat `terraform.tfstate*`."
    )
    dangereux = [l for l in actifs if not l.startswith("!") and
                 l in (".terraform.lock.hcl", ".terraform*")]
    assert not dangereux, (
        f"Le motif {dangereux} ignorerait `.terraform.lock.hcl`, qui doit etre "
        "COMMITTE. Ignorez le repertoire par `.terraform/` (avec le slash), pas "
        "par `.terraform*`."
    )


# --------------------------------------------------------------------------
# 6. Idempotence
# --------------------------------------------------------------------------

def test_configuration_stable_apres_apply(applied: Path) -> None:
    p = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=applied)
    assert p.returncode == 0, (
        f"`plan -detailed-exitcode` rend {p.returncode} (2 = des changements "
        "restent planifies). Un apply doit converger."
    )
