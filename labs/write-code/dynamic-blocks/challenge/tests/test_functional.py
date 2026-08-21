"""Tests fonctionnels du lab « générer des blocs, et savoir ne pas le faire ».

Principe : on ne lit jamais les `.tf` de l'apprenant. On applique la
configuration et on lit `terraform show -json`, `output -json` et le plan JSON.

La preuve tient dans la liste ordonnée `part` de `data.cloudinit_config` : sa
longueur suit la variable `modules`, ce qu'aucun bloc écrit en dur ne saurait
faire. Deux variantes (`modules={}` et quatre modules) le confirment.

Faits vérifiés sur Terraform v1.15.4 avant écriture : le bloc `part` répétable
de `cloudinit_config` se génère par `dynamic`, un `dynamic "lifecycle"` échoue
avec « Blocks of type "lifecycle" are not expected here », et un changement de
contenu sur `local_file` en `create_before_destroy` se planifie
`["create", "delete"]`.
"""

import json
import shutil
from pathlib import Path

import pytest

from conftest import exiger_workdir, output_json, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "write-code-dynamic-blocks"


def parties(cwd: Path) -> list[dict]:
    """La liste ordonnée `part` de la data source cloudinit."""
    for r in show_json(cwd).get("values", {}).get("root_module", {}).get("resources", []):
        if r.get("address") == "data.cloudinit_config.principal":
            return r["values"]["part"]
    return []


def apply_variante(base: Path, tmp: Path, var: str) -> Path:
    """Recopie le workdir appliqué et réapplique avec une autre valeur de modules."""
    shutil.copytree(base, tmp)
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color",
                    "-var", var, cwd=tmp)
    assert app.returncode == 0, f"apply variante a échoué.\n{app.stderr[-800:]}"
    return tmp


@pytest.fixture(scope="module")
def applied() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(f"`terraform init` a échoué.\n{init.stderr[-1200:]}")
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(
            "`terraform apply` a échoué. Un `???` subsiste, ou le `dynamic "
            "\"lifecycle\"` n'a pas été remplacé par un bloc `lifecycle` "
            "littéral (Terraform répond « Blocks of type \"lifecycle\" are not "
            "expected here »).\n"
            f"{app.stderr[-1500:]}"
        )
    return WORKDIR


# --------------------------------------------------------------------------
# 1-3. Génération par défaut : en-tête + 2 modules actifs, clé dans le filename
# --------------------------------------------------------------------------

def test_trois_parties_entete_puis_modules_actifs(applied: Path) -> None:
    noms = [p["filename"] for p in parties(applied)]
    assert noms == ["00-entete", "10-paquets", "10-users"], (
        f"parties = {noms}. Attendu l'en-tête littéral en premier, puis les deux "
        "modules actifs triés par clé. `debug` porte actif = false et doit être "
        "absent."
    )


def test_le_filename_derive_de_la_cle(applied: Path) -> None:
    """Une itération qui n'exploiterait que `.value` ne produirait pas ces noms."""
    noms = [p["filename"] for p in parties(applied)]
    assert "10-paquets" in noms and "10-users" in noms, (
        f"parties = {noms}. Le filename doit contenir la clé du module "
        "(`part.key`), pas un rang."
    )


def test_le_module_inactif_est_absent(applied: Path) -> None:
    parts = parties(applied)
    noms = [p["filename"] for p in parts]
    contenus = " ".join(p.get("content", "") for p in parts)
    assert not any("debug" in n for n in noms), (
        f"parties = {noms}. Le module `debug` (actif = false) ne doit produire "
        "aucune partie : le filtre va dans le `for_each`, pas dans le `content`."
    )
    assert "echo debug" not in contenus, (
        "Le contenu du module inactif apparaît dans une partie : filtrez dans le "
        "`for_each`."
    )


# --------------------------------------------------------------------------
# 4-5. La configuration suit la variable (preuve que ce n'est pas du littéral)
# --------------------------------------------------------------------------

def test_sans_module_il_reste_le_seul_entete(applied: Path, tmp_path: Path) -> None:
    """La partie fixe ne doit pas avoir été absorbée dans le bloc dynamique."""
    rep = apply_variante(applied, tmp_path / "vide", "modules={}")
    noms = [p["filename"] for p in parties(rep)]
    assert noms == ["00-entete"], (
        f"Avec modules={{}}, parties = {noms}. Il doit rester exactement l'en-tête. "
        "S'il ne reste rien, l'en-tête a été absorbé dans le `dynamic`."
    )


def test_quatre_modules_donnent_cinq_parties(applied: Path, tmp_path: Path) -> None:
    var = ('modules={a={contenu="a\\n",actif=true},b={contenu="b\\n",actif=true},'
           'c={contenu="c\\n",actif=true},d={contenu="d\\n",actif=true}}')
    rep = apply_variante(applied, tmp_path / "quatre", var)
    noms = [p["filename"] for p in parties(rep)]
    assert noms == ["00-entete", "10-a", "10-b", "10-c", "10-d"], (
        f"Avec quatre modules actifs, parties = {noms}. Attendu l'en-tête plus "
        "quatre parties triées par clé. Des blocs écrits en dur ne pourraient pas "
        "suivre à la fois ce cas et le cas vide."
    )


# --------------------------------------------------------------------------
# 6. Les outputs sont câblés
# --------------------------------------------------------------------------

def test_outputs_parties_et_nombre(applied: Path) -> None:
    sorties = output_json(applied)
    parties_out = sorties["parties"]["value"]
    nb = sorties["nb_parties"]["value"]
    assert isinstance(parties_out, list) and parties_out == [p["filename"] for p in parties(applied)], (
        f"`parties` = {parties_out} ne correspond pas aux filenames générés."
    )
    assert nb == len(parties_out), f"`nb_parties` = {nb}, attendu {len(parties_out)}."


# --------------------------------------------------------------------------
# 7. lifecycle littéral : create_before_destroy
# --------------------------------------------------------------------------

def test_local_file_porte_create_before_destroy(applied: Path) -> None:
    """Un changement de contenu se planifie create puis delete. Aucun `dynamic`
    n'aurait pu poser ce bloc lifecycle."""
    var = 'modules={paquets={contenu="packages:\\n  - vim\\n",actif=true}}'
    p = terraform("plan", "-input=false", "-no-color", "-out=tf.plan", "-var", var,
                  cwd=applied)
    assert p.returncode == 0, f"plan a échoué.\n{p.stderr[-800:]}"
    plan = json.loads(terraform("show", "-json", "tf.plan", cwd=applied).stdout)
    actions = next(
        (rc["change"]["actions"] for rc in plan.get("resource_changes", [])
         if rc["address"] == "local_file.rendu"),
        None,
    )
    assert actions == ["create", "delete"], (
        f"actions sur local_file.rendu = {actions}, attendu ['create', 'delete']. "
        "Le bloc `lifecycle` littéral doit porter `create_before_destroy = true`."
    )


# --------------------------------------------------------------------------
# 8. Idempotence
# --------------------------------------------------------------------------

def test_la_configuration_est_stable_apres_apply(applied: Path) -> None:
    p = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=applied)
    assert p.returncode == 0, (
        f"`plan -detailed-exitcode` rend {p.returncode} (2 = des changements "
        "restent planifiés). Un apply doit converger."
    )
