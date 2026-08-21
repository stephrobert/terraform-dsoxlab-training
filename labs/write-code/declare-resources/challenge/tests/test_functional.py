"""Tests fonctionnels du lab « le cycle de vie d'une ressource se lit dans le plan ».

Principe : on ne lit jamais les `.tf` de l'apprenant. On applique la
configuration, puis on lit `terraform show -json` (state et configuration),
`output -json` et surtout le tableau `resource_changes[].actions` du plan JSON.

Ce tableau distingue les quatre opérations : `["update"]` (mise à jour en place),
`["delete","create"]` (remplacement, ordre par défaut), `["create","delete"]`
(remplacement avec `create_before_destroy`), `["delete"]` (destruction).

Faits vérifiés sur Terraform v1.15.4 avant écriture : un changement de
`terraform_data.input` produit `["update"]` ; un `triggers_replace` qui bouge
produit un remplacement ; `create_before_destroy` inverse l'ordre en
`["create","delete"]`.
"""

import json
from pathlib import Path

import pytest

from conftest import exiger_workdir, output_json, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "write-code-declare-resources"

ADRESSES = {"random_pet.hote", "local_file.fiche", "terraform_data.sceau", "local_file.journal"}


def actions(cwd: Path, adresse: str, *var: str) -> list[str] | None:
    p = terraform("plan", "-input=false", "-no-color", "-out=tfplan", *var, cwd=cwd)
    if p.returncode != 0:
        pytest.fail(f"`terraform plan` a échoué.\n{p.stderr[-1000:]}")
    plan = json.loads(terraform("show", "-json", "tfplan", cwd=cwd).stdout)
    for rc in plan.get("resource_changes", []):
        if rc["address"] == adresse:
            return rc["change"]["actions"]
    return None


@pytest.fixture(scope="module")
def applied() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(f"`terraform init` a échoué.\n{init.stderr[-1200:]}")
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(f"`terraform apply` a échoué. Un `???` subsiste.\n{app.stderr[-1500:]}")
    return WORKDIR


# --------------------------------------------------------------------------
# 1. Le state : quatre ressources gérées aux bonnes adresses
# --------------------------------------------------------------------------

def test_les_quatre_ressources_sont_dans_le_state(applied: Path) -> None:
    module = show_json(applied).get("values", {}).get("root_module", {})
    trouvees = {r["address"]: r.get("mode") for r in module.get("resources", [])}
    assert set(trouvees) == ADRESSES, (
        f"Adresses dans le state : {sorted(trouvees)}. Attendu : {sorted(ADRESSES)}."
    )
    assert all(m == "managed" for m in trouvees.values()), (
        f"Toutes les ressources doivent être en mode managed : {trouvees}."
    )


# --------------------------------------------------------------------------
# 2. Dépendances : implicite sur la fiche, explicite sur le journal
# --------------------------------------------------------------------------

def test_la_fiche_n_a_pas_de_depends_on(applied: Path) -> None:
    p = terraform("plan", "-input=false", "-no-color", "-out=tfplan", cwd=applied)
    assert p.returncode == 0
    conf = json.loads(terraform("show", "-json", "tfplan", cwd=applied).stdout)
    res = {r["address"]: r for r in conf["configuration"]["root_module"]["resources"]}
    assert not res["local_file.fiche"].get("depends_on"), (
        "`local_file.fiche` doit dépendre de `random_pet.hote` par une référence "
        "implicite (son filename), sans depends_on."
    )
    assert res["local_file.journal"].get("depends_on") == ["terraform_data.sceau"], (
        "`local_file.journal` doit porter depends_on = [terraform_data.sceau] : "
        "c'est une dépendance de comportement, sans référence."
    )


# --------------------------------------------------------------------------
# 3. Les outputs
# --------------------------------------------------------------------------

def test_outputs_cables(applied: Path) -> None:
    sorties = output_json(applied)
    assert "out/fiche-" in sorties["chemin_fiche"]["value"], (
        f"`chemin_fiche` = {sorties['chemin_fiche']['value']!r}."
    )
    assert sorties["sceau"]["value"] == "v1", (
        f"`sceau` = {sorties['sceau']['value']!r}, attendu l'étiquette appliquée 'v1'. "
        "L'output doit exposer terraform_data.sceau.output."
    )


# --------------------------------------------------------------------------
# 4. Mise à jour EN PLACE : le sceau quand l'étiquette change
# --------------------------------------------------------------------------

def test_changer_l_etiquette_met_le_sceau_a_jour_en_place(applied: Path) -> None:
    a = actions(applied, "terraform_data.sceau", "-var", "etiquette=v2")
    assert a == ["update"], (
        f"actions sur terraform_data.sceau = {a}, attendu ['update']. Un changement "
        "de `input` se met à jour en place, il ne remplace pas. Vérifiez que `input` "
        "porte bien `var.etiquette`."
    )


# --------------------------------------------------------------------------
# 5. REMPLACEMENT : la génération change, l'ordre create_before_destroy
# --------------------------------------------------------------------------

def test_changer_la_generation_remplace_le_sceau(applied: Path) -> None:
    a = actions(applied, "terraform_data.sceau", "-var", "generation=2")
    assert a is not None and set(a) == {"create", "delete"}, (
        f"actions sur terraform_data.sceau = {a}, attendu un remplacement. "
        "`triggers_replace` doit valoir l'id de l'hôte, qui change avec la génération."
    )


def test_la_fiche_est_creee_avant_d_etre_detruite(applied: Path) -> None:
    a = actions(applied, "local_file.fiche", "-var", "generation=2")
    assert a == ["create", "delete"], (
        f"actions sur local_file.fiche = {a}, attendu ['create', 'delete']. Sans "
        "`create_before_destroy = true`, l'ordre serait ['delete', 'create'], avec une "
        "fenêtre où le fichier n'existe plus."
    )


# --------------------------------------------------------------------------
# 6. Idempotence
# --------------------------------------------------------------------------

def test_la_configuration_est_stable_apres_apply(applied: Path) -> None:
    p = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=applied)
    assert p.returncode == 0, (
        f"`plan -detailed-exitcode` rend {p.returncode} (2 = des changements restent "
        "planifiés). Un apply doit converger."
    )
