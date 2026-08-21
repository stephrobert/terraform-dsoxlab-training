"""Tests fonctionnels du lab « structure standard d'un module ».

La Standard Module Structure n'est pas qu'une affaire de gout : l'outillage
s'appuie dessus pour generer la documentation et indexer les modules. Un point
la distingue pourtant des conventions purement cosmetiques, et c'est le coeur du
lab : `override.tf` a un effet FONCTIONNEL.

Faits verifies sur Terraform 1.15.4 (local + random, hors ligne) :
- un `override.tf` qui redeclare `local_file.index` avec `file_permission =
  "0600"` gagne sur le `main.tf` qui dit `"0644"` : le state porte `0600`, et le
  fichier sur le disque aussi ;
- le MEME contenu dans un fichier au nom ordinaire produit `Error: Duplicate
  resource "local_file" configuration`. Aucun autre nom de fichier n'a ce
  pouvoir de fusion ;
- un output declare `type = map(string)` ressort en `"type": ["map","string"]`
  dans `terraform output -json` ;
- le JSON du plan expose `module_calls.<nom>.source`, ce qui permet d'exiger un
  chemin RELATIF, et `module_calls.<nom>.module.outputs`, le contrat de sortie
  du module imbrique ;
- un exemple autonome sous `examples/` se valide independamment de la racine :
  `validate -json` rend `valid: true` et `error_count: 0`.
"""

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "modules-module-structure"

FICHIERS_ATTENDUS = [
    "main.tf",
    "variables.tf",
    "outputs.tf",
    "terraform.tf",
    "README.md",
    "LICENSE",
    "modules/fiche/README.md",
    "examples/minimal/main.tf",
]
ENVIRONNEMENTS = {"dev", "prod"}


@pytest.fixture(scope="module")
def applique() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(
            "`terraform init` a echoue. Un `???` restant dans la configuration, "
            "ou un bloc declare deux fois apres l'eclatement de `tout.tf` ?"
            f"\n{init.stderr[-1200:]}"
        )
    if "values" not in show_json(WORKDIR):
        pytest.fail(
            "Le state est vide : la configuration n'a jamais ete appliquee. "
            "Lancez `terraform apply` une fois le refactoring termine."
        )
    yield WORKDIR


# --------------------------------------------------------------------------
# 1. La structure standard est en place
# --------------------------------------------------------------------------

def test_les_fichiers_de_la_structure_standard_existent(applique: Path) -> None:
    manquants = [nom for nom in FICHIERS_ATTENDUS if not (applique / nom).is_file()]
    assert not manquants, (
        f"Ces fichiers manquent : {manquants}. Le socle minimal officiel est "
        "`README.md`, `main.tf`, `variables.tf`, `outputs.tf` ; le style guide "
        "ajoute `terraform.tf` pour le bloc `terraform` ; un `LICENSE` est "
        "attendu (« many organizations will not adopt a module unless a clear "
        "license is present ») ; et un sous-module n'est utilisable de "
        "l'exterieur que s'il porte son propre README."
    )


# --------------------------------------------------------------------------
# 2. Le module imbrique, appele par chemin relatif
# --------------------------------------------------------------------------

def test_le_module_est_appele_par_un_chemin_relatif(applique: Path) -> None:
    plan = terraform("plan", "-input=false", "-no-color", "-out=analyse.tfplan",
                     cwd=applique)
    if plan.returncode != 0:
        pytest.fail(f"`terraform plan` a echoue.\n{plan.stderr[-900:]}")
    montre = terraform("show", "-json", "analyse.tfplan", cwd=applique)
    montre.check_returncode()
    document = json.loads(montre.stdout)

    appels = document["configuration"]["root_module"].get("module_calls", {})
    assert "fiche" in appels, (
        f"Aucun appel de module `fiche`. Appels presents : {sorted(appels)}"
    )
    source = appels["fiche"]["source"]
    assert source == "./modules/fiche", (
        f"Le `source` vaut {source!r}, attendu `./modules/fiche`. Un chemin "
        "RELATIF fait considerer le sous-module comme faisant partie du meme "
        "paquet, au lieu d'etre telecharge separement."
    )
    sorties = appels["fiche"]["module"].get("outputs", {})
    assert sorties, (
        "Le module imbrique n'expose aucun output : il ne remonte donc rien a "
        "la racine."
    )


def test_le_module_est_instancie_par_environnement(applique: Path) -> None:
    enfants = show_json(applique)["values"]["root_module"].get("child_modules", [])
    adresses = {e["address"] for e in enfants}
    attendues = {f'module.fiche["{nom}"]' for nom in ENVIRONNEMENTS}
    assert adresses == attendues, (
        f"Le state porte {sorted(adresses)}, attendu {sorted(attendues)}."
    )
    for enfant in enfants:
        types = {r["type"] for r in enfant.get("resources", [])}
        assert types == {"random_pet", "local_file"}, (
            f"{enfant['address']} porte {sorted(types)}, attendu un `random_pet` "
            "et un `local_file`."
        )


# --------------------------------------------------------------------------
# 3. override.tf, le seul nom de fichier qui agisse
# --------------------------------------------------------------------------

def test_override_a_bien_ecrase_les_permissions(applique: Path) -> None:
    racine = show_json(applique)["values"]["root_module"]
    index = next(
        (r for r in racine.get("resources", []) if r["address"] == "local_file.index"),
        None,
    )
    assert index is not None, (
        "`local_file.index` a disparu de la racine : c'est la ressource que le "
        "fichier de surcharge doit modifier."
    )
    permissions = index["values"]["file_permission"]
    assert permissions == "0600", (
        f"`file_permission` vaut {permissions!r}, attendu `0600`. La valeur "
        "declaree dans `main.tf` reste `0644` : seul un fichier nomme "
        "`override.tf` ou `*_override.tf`, charge en DERNIER par Terraform, peut "
        "la remplacer. Le meme contenu dans un fichier au nom ordinaire produit "
        "`Duplicate resource configuration`."
    )
    assert (applique / "index.txt").is_file(), (
        "index.txt n'existe pas : la configuration n'a pas ete appliquee."
    )
    # Les permissions REELLES du fichier ne sont volontairement pas verifiees :
    # en mode formateur, la solution de reference est deposee par une ecriture
    # Python soumise a l'umask, et non par Terraform. Le state, lui, ne ment pas.


# --------------------------------------------------------------------------
# 4. Le contrat de sortie, type compris
# --------------------------------------------------------------------------

def test_la_sortie_chemins_est_typee(applique: Path) -> None:
    sortie = terraform("output", "-json", cwd=applique)
    sortie.check_returncode()
    outputs = json.loads(sortie.stdout)
    assert "chemins" in outputs, (
        f"L'output `chemins` manque. Outputs presents : {sorted(outputs)}"
    )
    type_declare = outputs["chemins"]["type"]
    assert type_declare == ["map", "string"], (
        f"Le type de `chemins` ressort en {type_declare!r}, attendu "
        '["map", "string"]. Le style guide 1.15 demande un `type` sur chaque '
        "output, au meme titre que sur chaque variable."
    )
    valeur = outputs["chemins"]["value"]
    assert set(valeur) == ENVIRONNEMENTS, (
        f"`chemins` porte les cles {sorted(valeur)}, attendu "
        f"{sorted(ENVIRONNEMENTS)}."
    )


# --------------------------------------------------------------------------
# 5. L'exemple autonome se valide tout seul
# --------------------------------------------------------------------------

def test_l_exemple_minimal_est_valide(applique: Path) -> None:
    exemple = applique / "examples" / "minimal"
    init = terraform(f"-chdir={exemple}", "init", "-input=false", "-no-color",
                     cwd=applique)
    if init.returncode != 0:
        pytest.fail(
            f"`init` a echoue dans examples/minimal.\n{init.stderr[-900:]}"
        )
    valide = terraform(f"-chdir={exemple}", "validate", "-json", cwd=applique)
    document = json.loads(valide.stdout)
    assert document.get("valid") is True and document.get("error_count") == 0, (
        f"`validate` de l'exemple rend valid={document.get('valid')} et "
        f"error_count={document.get('error_count')}. Un exemple doit tenir "
        "debout seul : il finira copie ailleurs."
    )


# --------------------------------------------------------------------------
# 6. La configuration a converge
# --------------------------------------------------------------------------

def test_plus_aucun_changement_en_attente(applique: Path) -> None:
    plan = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color",
                     cwd=applique)
    assert plan.returncode == 0, (
        f"plan -detailed-exitcode rend {plan.returncode}, attendu 0.\n"
        f"{plan.stdout[-900:]}"
    )
