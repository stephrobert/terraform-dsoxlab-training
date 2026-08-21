"""Tests fonctionnels du lab « le local qui ne se calcule pas au plan ».

Principe : on ne lit jamais les `.tf` de l'apprenant, et jamais une sortie
humaine. On lit `terraform show -json` (plan et state) et `output -json`.

Deux preuves structurent le lab. Le champ `output_changes[].after_unknown` du
plan sépare ce qui est connu au plan (`base_name`) de ce qui ne l'est qu'à
l'apply (`manifest_name`, dérivé d'une ressource). Et le **type JSON** de
`effective_ram` prouve que le ternaire n'a pas glissé vers une chaîne.

Faits vérifiés sur Terraform v1.15.4 : `type(true ? 4096 : "2048")` vaut string
(conversion silencieuse), un local dérivé de `random_id.hex` est
`(known after apply)`, et une sortie dérivant d'une variable sensible doit être
marquée `sensitive` sous peine d'erreur.
"""

import json
import re
from pathlib import Path

import pytest

from conftest import exiger_workdir, output_json, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "write-code-locals"


def plan_json(cwd: Path, *var: str) -> dict:
    p = terraform("plan", "-input=false", "-no-color", "-out=tfplan", *var, cwd=cwd)
    if p.returncode != 0:
        pytest.fail(f"`terraform plan` a échoué. Un `???` subsiste.\n{p.stderr[-1200:]}")
    return json.loads(terraform("show", "-json", "tfplan", cwd=cwd).stdout)


@pytest.fixture(scope="module")
def plan_a_vide() -> dict:
    """Plan sur un état vierge : c'est là que after_unknown se lit."""
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(f"`terraform init` a échoué.\n{init.stderr[-1200:]}")
    return plan_json(WORKDIR)


@pytest.fixture(scope="module")
def applied(plan_a_vide: dict) -> Path:
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(
            "`terraform apply` a échoué. Une sortie sensible non marquée, ou un "
            "`???` restant.\n"
            f"{app.stderr[-1500:]}"
        )
    return WORKDIR


# --------------------------------------------------------------------------
# 1. Plan contre apply : la frontière after_unknown
# --------------------------------------------------------------------------

def test_manifest_inconnu_au_plan_base_name_connu(plan_a_vide: dict) -> None:
    oc = plan_a_vide.get("output_changes", {})
    assert oc.get("base_name", {}).get("after_unknown") is False, (
        "`base_name` devrait être connu au plan : il ne dépend que de variables."
    )
    assert oc.get("manifest_name", {}).get("after_unknown") is True, (
        "`manifest_name` devrait être inconnu au plan (after_unknown). Il dérive "
        "de `random_id.build.hex`, un attribut de ressource résolu à l'apply."
    )


# --------------------------------------------------------------------------
# 2. base_name : normalisation
# --------------------------------------------------------------------------

def test_base_name_normalise(applied: Path) -> None:
    v = output_json(applied)["base_name"]["value"]
    assert v == "atelier-locaux-prod", (
        f"`base_name` = {v!r}, attendu 'atelier-locaux-prod'. Il faut mettre "
        "`project` en minuscules et changer l'underscore en tiret, puis joindre "
        "à `environment`."
    )


# --------------------------------------------------------------------------
# 3. node_names : expression for + format
# --------------------------------------------------------------------------

def test_node_names_liste_formatee(applied: Path) -> None:
    v = output_json(applied)["node_names"]["value"]
    assert isinstance(v, list) and len(v) == 3, (
        f"`node_names` = {v!r}, attendu une liste de 3 (node_count)."
    )
    motif = re.compile(r"^atelier-locaux-prod-\d{3}$")
    for nom in v:
        assert motif.match(nom), (
            f"`{nom}` ne suit pas le gabarit atelier-locaux-prod-NNN. Utilisez "
            "une expression `for` et `format(\"%s-%03d\", ...)`."
        )


# --------------------------------------------------------------------------
# 4. effective_ram : le piège du ternaire (type avant valeur)
# --------------------------------------------------------------------------

def test_effective_ram_est_un_nombre_en_prod(applied: Path) -> None:
    v = output_json(applied)["effective_ram"]["value"]
    assert isinstance(v, (int, float)) and not isinstance(v, bool), (
        f"`effective_ram` = {v!r} de type {type(v).__name__}, attendu un NOMBRE. "
        "Un mélange nombre/chaîne dans le ternaire (ex. `4096 : \"2048\"`) "
        "convertit tout en chaîne sans erreur : retirez les guillemets."
    )
    assert v == 4096, f"`effective_ram` = {v}, attendu 4096 (2048 doublé en prod)."


def test_effective_ram_reste_un_nombre_en_dev(applied: Path) -> None:
    """Rejeu avec environment=dev : le type ne doit pas changer, la valeur si."""
    p = terraform("apply", "-auto-approve", "-input=false", "-no-color",
                  "-var", "environment=dev", cwd=applied)
    assert p.returncode == 0, f"apply en dev a échoué.\n{p.stderr[-800:]}"
    try:
        v = output_json(applied)["effective_ram"]["value"]
        assert isinstance(v, (int, float)) and not isinstance(v, bool), (
            f"`effective_ram` en dev = {v!r}, doit rester un nombre."
        )
        assert v == 2048, f"`effective_ram` en dev = {v}, attendu 2048."
    finally:
        terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=applied)


# --------------------------------------------------------------------------
# 5. manifest_name : dérivé réel du hex de la ressource
# --------------------------------------------------------------------------

def test_manifest_name_derive_du_hex(applied: Path) -> None:
    state = show_json(applied)
    hexval = next(
        r["values"]["hex"]
        for r in state["values"]["root_module"]["resources"]
        if r.get("type") == "random_id"
    )
    manifest = output_json(applied)["manifest_name"]["value"]
    attendu = f"atelier-locaux-prod-{hexval[:8]}.json"
    assert manifest == attendu, (
        f"`manifest_name` = {manifest!r}, attendu {attendu!r} (les 8 premiers "
        "caractères de random_id.build.hex)."
    )


# --------------------------------------------------------------------------
# 6. db_dsn : la sensibilité se propage
# --------------------------------------------------------------------------

def test_db_dsn_sortie_sensible(applied: Path) -> None:
    outs = show_json(applied).get("values", {}).get("outputs", {})
    assert outs.get("db_dsn", {}).get("sensitive") is True, (
        "La sortie `db_dsn` n'est pas marquée sensible. Un local qui assemble "
        "`var.db_password` (sensitive) hérite de sa sensibilité, et la sortie "
        "doit porter `sensitive = true`. Sans cela, l'apply n'aurait pas abouti."
    )


# --------------------------------------------------------------------------
# 7. Le manifest : contenu confronté aux sorties
# --------------------------------------------------------------------------

def test_le_manifest_reprend_les_locaux(applied: Path) -> None:
    state = show_json(applied)
    contenu = next(
        r["values"]["content"]
        for r in state["values"]["root_module"]["resources"]
        if r.get("type") == "local_file"
    )
    data = json.loads(contenu)
    sorties = output_json(applied)
    assert data["base_name"] == sorties["base_name"]["value"]
    assert data["node_names"] == sorties["node_names"]["value"]
    assert data["effective_ram"] == sorties["effective_ram"]["value"]


# --------------------------------------------------------------------------
# 8. Idempotence
# --------------------------------------------------------------------------

def test_la_configuration_est_stable_apres_apply(applied: Path) -> None:
    p = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=applied)
    assert p.returncode == 0, (
        f"`plan -detailed-exitcode` rend {p.returncode} (2 = des changements "
        "restent planifiés). Un apply doit converger."
    )
