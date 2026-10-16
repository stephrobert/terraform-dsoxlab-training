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

from conftest import (
    exiger_workdir,
    message,
    output_json,
    show_json,
    terraform,
    workdir_lab,
)

WORKDIR = workdir_lab(__file__)
LAB_ID = "write-code-style-guide"


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
            en="`terraform apply` failed. An unresolved orphan reference "
            f"(var.env_name) or an invalid configuration?\n{app.stderr[-1500:]}",
            fr="`terraform apply` a échoué. Référence orpheline non résolue "
            f"(var.env_name) ou config invalide ?\n{app.stderr[-1500:]}",
        )
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
    assert p.returncode == 0, message(
        en="`terraform fmt -check -recursive` reports an unformatted file "
        f"(code {p.returncode}). Run `terraform fmt` on the directory.\n{p.stdout}",
        fr="`terraform fmt -check -recursive` signale un fichier non formaté "
        f"(code {p.returncode}). Lancez `terraform fmt` sur le répertoire.\n{p.stdout}",
    )


def test_validate_valide(applied: Path) -> None:
    data = json.loads(terraform("validate", "-json", cwd=applied).stdout)
    assert data.get("valid") is True, message(
        en=f"`terraform validate` fails ({data.get('error_count')} error(s)). "
        "The orphan reference (var.env_name) must be resolved.",
        fr=f"`terraform validate` échoue ({data.get('error_count')} erreur[s]). "
        "La référence orpheline (var.env_name) doit être résolue.",
    )


# --------------------------------------------------------------------------
# 2. Les memes ressources, nommees selon la convention
# --------------------------------------------------------------------------

def test_deux_ressources_intactes(applied: Path) -> None:
    res = show_json(applied)["values"]["root_module"]["resources"]
    types = sorted(r["type"] for r in res)
    assert types == ["local_file", "random_pet"], message(
        en=f"Resources = {types}, exactly one local_file and one random_pet expected. "
        "The refactoring must create and delete nothing.",
        fr=f"Ressources = {types}, attendu exactement un local_file et un random_pet. "
        "Le refactoring ne doit rien créer ni supprimer.",
    )


def test_noms_en_snake_case(applied: Path) -> None:
    res = show_json(applied)["values"]["root_module"]["resources"]
    motif = re.compile(r"^[a-z][a-z0-9_]*$")
    for r in res:
        nom = r["name"]
        assert motif.match(nom), message(
            en=f"The resource name {nom!r} is not in snake_case. The official "
            "convention requires lower case and underscores, never "
            "camelCase or a hyphen.",
            fr=f"Le nom de ressource {nom!r} n'est pas en snake_case. La convention "
            "officielle impose des minuscules et des underscores, jamais de "
            "camelCase ni de tiret.",
        )


# --------------------------------------------------------------------------
# 3. Typage et documentation des variables
# --------------------------------------------------------------------------

def test_variables_decrites(applied: Path) -> None:
    variables = _plan(applied)["configuration"]["root_module"].get("variables", {})
    assert variables, message(
        en="No variable in the configuration?",
        fr="Aucune variable dans la configuration ?",
    )
    for nom, spec in variables.items():
        desc = spec.get("description") or ""
        assert desc.strip(), message(
            en=f"The variable {nom!r} has no `description`. The style guide requires "
            "a description on every variable.",
            fr=f"La variable {nom!r} n'a pas de `description`. Le style guide impose "
            "une description sur chaque variable.",
        )


def test_replica_count_type_number(applied: Path) -> None:
    p = terraform("plan", "-input=false", "-no-color", "-var", "replica_count=abc", cwd=applied)
    assert p.returncode != 0, message(
        en="Passing replica_count=abc should FAIL: the variable must be typed "
        "`number`. Untyped, it would accept anything.",
        fr="Passer replica_count=abc devrait ÉCHOUER : la variable doit être typée "
        "`number`. Non typée, elle accepterait n'importe quoi.",
    )


# --------------------------------------------------------------------------
# 4. Outputs : type, description, sensibilite
# --------------------------------------------------------------------------

def test_outputs_types_et_sensibles(applied: Path) -> None:
    outs = output_json(applied)
    assert outs["api_token"]["sensitive"] is True, message(
        en="The `api_token` output exposes a token and must be marked `sensitive`.",
        fr="L'output `api_token` expose un jeton et doit être marqué `sensitive`.",
    )
    replicas = outs["replicas"]
    assert replicas["type"] == "number" and replicas["value"] == 3, message(
        en=f"`replicas` = {replicas!r}, type number and value 3 expected. The "
        "`type = number` constraint makes the value come out as a number although tfvars gives it "
        "in quotes (\"3\").",
        fr=f"`replicas` = {replicas!r}, attendu type number et valeur 3. La contrainte "
        "`type = number` fait sortir la valeur en nombre alors que tfvars la donne "
        'entre guillemets ("3").',
    )


def test_outputs_decrits(applied: Path) -> None:
    outputs = _plan(applied)["configuration"]["root_module"].get("outputs", {})
    for nom, spec in outputs.items():
        desc = spec.get("description") or ""
        assert desc.strip(), message(
            en=f"The output {nom!r} has no `description`.",
            fr=f"L'output {nom!r} n'a pas de `description`.",
        )


# --------------------------------------------------------------------------
# 5. .gitignore : ce qu'on ignore, et ce qu'on committe
# --------------------------------------------------------------------------

def test_gitignore_correct(applied: Path) -> None:
    gi = applied / ".gitignore"
    assert gi.is_file(), message(
        en="A `.gitignore` file is missing.",
        fr="Il manque un fichier `.gitignore`.",
    )
    lignes = [ligne.strip() for ligne in gi.read_text(encoding="utf-8").splitlines()]
    actifs = [ligne for ligne in lignes if ligne and not ligne.startswith("#")]

    assert any(ligne.rstrip("/") == ".terraform" for ligne in actifs), message(
        en="`.gitignore` must ignore the `.terraform/` directory.",
        fr="`.gitignore` doit ignorer le répertoire `.terraform/`.",
    )
    assert any("tfstate" in ligne for ligne in actifs), message(
        en="`.gitignore` must ignore the state files `terraform.tfstate*`.",
        fr="`.gitignore` doit ignorer les fichiers d'état `terraform.tfstate*`.",
    )
    dangereux = [
        ligne
        for ligne in actifs
        if not ligne.startswith("!")
        and ligne in (".terraform.lock.hcl", ".terraform*")
    ]
    assert not dangereux, message(
        en=f"The pattern {dangereux} would ignore `.terraform.lock.hcl`, which must be "
        "COMMITTED. Ignore the directory with `.terraform/` (with the slash), not "
        "with `.terraform*`.",
        fr=f"Le motif {dangereux} ignorerait `.terraform.lock.hcl`, qui doit être "
        "COMMITTÉ. Ignorez le répertoire par `.terraform/` (avec le slash), pas "
        "par `.terraform*`.",
    )


# --------------------------------------------------------------------------
# 6. Idempotence
# --------------------------------------------------------------------------

def test_configuration_stable_apres_apply(applied: Path) -> None:
    p = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=applied)
    assert p.returncode == 0, message(
        en=f"`plan -detailed-exitcode` returns {p.returncode} (2 = changes "
        "remain planned). An apply must converge.",
        fr=f"`plan -detailed-exitcode` rend {p.returncode} (2 = des changements "
        "restent planifiés). Un apply doit converger.",
    )
