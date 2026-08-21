"""Tests fonctionnels du lab « les fonctions definies par un provider ».

Principe : on ne lit jamais le CONTENU des `.tf` de l'apprenant, seulement des
sorties JSON de Terraform et des codes retour.

Faits verifies sur Terraform 1.15.4 (provider integre `terraform` sous le nom
local `tfcore`, plus hashicorp/local >= 2.5.0) :
- `providers schema -json` decrit les fonctions de chaque provider :
  tfcore -> encode_tfvars/decode_tfvars/encode_expr, local -> direxists ;
- `metadata functions -json` ne liste QUE les ~238 fonctions du langage :
  aucune fonction de provider n'y figure (la preuve par l'absence) ;
- decode_tfvars restitue les TYPES (node_count est un nombre, pas une chaine) ;
- encode_tfvars/encode_expr produisent les representations attendues ;
- direxists rend vrai/faux selon l'existence du repertoire.
"""

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, output_json, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "write-code-provider-defined-functions"

BUILTIN = "terraform.io/builtin/terraform"
LOCAL = "registry.terraform.io/hashicorp/local"
FONCTIONS_PROVIDER = {"encode_tfvars", "decode_tfvars", "encode_expr", "direxists"}


def _tf_json(cwd: Path, *args: str) -> dict:
    proc = terraform(*args, cwd=cwd)
    proc.check_returncode()
    return json.loads(proc.stdout)


@pytest.fixture(scope="module")
def applied() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(
            "`terraform init` a echoue. Un `???` restant, le provider tfcore non "
            "declare, ou une contrainte de version trop basse pour direxists ?\n"
            f"{init.stderr[-1400:]}"
        )
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(
            "`terraform apply` a echoue. Un appel provider::<nom>::<fonction> mal "
            f"ecrit, ou le nom local tfcore absent de versions.tf ?\n{app.stderr[-1500:]}"
        )
    yield WORKDIR
    terraform("destroy", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)


# --------------------------------------------------------------------------
# 1. Les fonctions sont DECRITES par le schema de chaque provider
# --------------------------------------------------------------------------

def test_schema_expose_les_fonctions_des_providers(applied: Path) -> None:
    schemas = _tf_json(applied, "providers", "schema", "-json")["provider_schemas"]
    builtin = set((schemas.get(BUILTIN, {}).get("functions") or {}).keys())
    local = set((schemas.get(LOCAL, {}).get("functions") or {}).keys())
    assert {"encode_tfvars", "decode_tfvars", "encode_expr"} <= builtin, (
        f"Le provider integre devrait exposer encode/decode_tfvars et encode_expr, "
        f"schema vu : {sorted(builtin)}. Le provider tfcore est-il bien declare ?"
    )
    assert "direxists" in local, (
        f"hashicorp/local devrait exposer direxists, schema vu : {sorted(local)}."
    )


# --------------------------------------------------------------------------
# 2. Aucune de ces fonctions n'est une fonction du LANGAGE
# --------------------------------------------------------------------------

def test_fonctions_provider_absentes_du_langage(applied: Path) -> None:
    doc = _tf_json(applied, "metadata", "functions", "-json")
    langage = set(doc.get("function_signatures", {}).keys())
    intrus = FONCTIONS_PROVIDER & langage
    assert not intrus, (
        f"{intrus} apparaissent parmi les fonctions du langage. Une fonction de "
        "provider ne doit JAMAIS y figurer : c'est ce qui la distingue."
    )
    assert len(langage) > 200, (
        f"metadata functions -json ne liste que {len(langage)} fonctions, attendu "
        "~238 fonctions de langage."
    )


# --------------------------------------------------------------------------
# 3. La version de hashicorp/local admet direxists (>= 2.5.0)
# --------------------------------------------------------------------------

def test_version_local_expose_direxists(applied: Path) -> None:
    sel = _tf_json(applied, "version", "-json")["provider_selections"]
    version = sel.get(LOCAL)
    assert version is not None, f"hashicorp/local absent des provider_selections : {sel}"
    tuple_v = tuple(int(x) for x in version.split("."))
    assert tuple_v >= (2, 5, 0), (
        f"hashicorp/local {version} < 2.5.0 : direxists n'existe pas avant 2.5.0. "
        "La contrainte de version est trop permissive vers le bas."
    )


# --------------------------------------------------------------------------
# 4. decode_tfvars restitue les types, encode_* produisent le bon texte
# --------------------------------------------------------------------------

def test_outputs_encode_decode(applied: Path) -> None:
    out = output_json(applied)
    node_count = out.get("node_count", {})
    assert node_count.get("value") == 3 and not node_count.get("sensitive"), (
        f"node_count = {node_count.get('value')!r}. decode_tfvars restitue un "
        "NOMBRE, pas une chaine : une lecture de texte aurait rendu \"3\"."
    )
    assert isinstance(node_count.get("value"), int), (
        "node_count doit etre un entier JSON, pas une chaine."
    )
    aval = out.get("aval", {}).get("value", "")
    assert 'environment  = "prod"' in aval or 'environment = "prod"' in aval, (
        f"le tfvars re-encode devrait contenir environment = \"prod\" :\n{aval}"
    )
    assert "node_count" in aval and "region" in aval, (
        f"le tfvars re-encode a perdu des cles :\n{aval}"
    )
    assert out.get("zones_expr", {}).get("value") == '["a", "b", "c"]', (
        f"zones_expr = {out.get('zones_expr', {}).get('value')!r}, attendu la "
        "syntaxe d'expression Terraform [\"a\", \"b\", \"c\"] (pas du JSON compact)."
    )
    assert out.get("dir_present", {}).get("value") is True, "dir_present devrait etre vrai."
    assert out.get("dir_absent", {}).get("value") is False, "dir_absent devrait etre faux."


# --------------------------------------------------------------------------
# 5. La valeur re-encodee circule jusqu'au fichier ecrit sur disque
# --------------------------------------------------------------------------

def test_local_file_contient_le_tfvars(applied: Path) -> None:
    resources = show_json(applied)["values"]["root_module"]["resources"]
    fichiers = [r for r in resources if r.get("type") == "local_file"]
    assert len(fichiers) == 1, f"{len(fichiers)} local_file dans le state, attendu 1."
    contenu = fichiers[0]["values"]["content"]
    assert contenu == output_json(applied)["aval"]["value"], (
        "Le content du local_file doit etre exactement le tfvars re-encode (local.aval)."
    )


# --------------------------------------------------------------------------
# 6. Idempotence (fonctions pures : aucun diff apres apply)
# --------------------------------------------------------------------------

def test_configuration_stable_apres_apply(applied: Path) -> None:
    p = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=applied)
    assert p.returncode == 0, (
        f"`plan -detailed-exitcode` rend {p.returncode} (2 = changements planifies). "
        "Des fonctions pures ne produisent aucun diff."
    )
