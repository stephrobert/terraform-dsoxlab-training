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

from conftest import exiger_workdir, message, show_json, terraform, workdir_lab

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
            message(
            en="`terraform init` failed. A leftover `???` in the configuration, "
            "or a block declared twice after splitting `tout.tf`?"
            f"\n{init.stderr[-1200:]}",
            fr="`terraform init` a échoué. Un `???` restant dans la configuration, "
            "ou un bloc déclaré deux fois après l'éclatement de `tout.tf` ?"
            f"\n{init.stderr[-1200:]}",
        )
        )
    if "values" not in show_json(WORKDIR):
        pytest.fail(
            message(
            en="The state is empty: the configuration was never applied. "
            "Run `terraform apply` once the refactoring is finished.",
            fr="Le state est vide : la configuration n'a jamais été appliquée. "
            "Lancez `terraform apply` une fois le refactoring terminé.",
        )
        )
    yield WORKDIR


# --------------------------------------------------------------------------
# 1. La structure standard est en place
# --------------------------------------------------------------------------

def test_les_fichiers_de_la_structure_standard_existent(applique: Path) -> None:
    manquants = [nom for nom in FICHIERS_ATTENDUS if not (applique / nom).is_file()]
    assert not manquants, message(
        en=f"These files are missing: {manquants}. The official minimal base is "
        "`README.md`, `main.tf`, `variables.tf`, `outputs.tf`; the style guide "
        "adds `terraform.tf` for the `terraform` block; a `LICENSE` is "
        "expected (\"many organizations will not adopt a module unless a clear "
        "license is present\"); and a submodule is only usable from "
        "outside if it carries its own README.",
        fr=f"Ces fichiers manquent : {manquants}. Le socle minimal officiel est "
        "`README.md`, `main.tf`, `variables.tf`, `outputs.tf` ; le style guide "
        "ajoute `terraform.tf` pour le bloc `terraform` ; un `LICENSE` est "
        "attendu (« many organizations will not adopt a module unless a clear "
        "license is present ») ; et un sous-module n'est utilisable de "
        "l'extérieur que s'il porte son propre README.",
    )


# --------------------------------------------------------------------------
# 2. Le module imbrique, appele par chemin relatif
# --------------------------------------------------------------------------

def test_le_module_est_appele_par_un_chemin_relatif(applique: Path) -> None:
    plan = terraform("plan", "-input=false", "-no-color", "-out=analyse.tfplan",
                     cwd=applique)
    if plan.returncode != 0:
        pytest.fail(message(
            en=f"`terraform plan` failed.\n{plan.stderr[-900:]}",
            fr=f"`terraform plan` a échoué.\n{plan.stderr[-900:]}",
        ))
    montre = terraform("show", "-json", "analyse.tfplan", cwd=applique)
    montre.check_returncode()
    document = json.loads(montre.stdout)

    appels = document["configuration"]["root_module"].get("module_calls", {})
    assert "fiche" in appels, message(
        en=f"No `fiche` module call. Calls present: {sorted(appels)}",
        fr=f"Aucun appel de module `fiche`. Appels présents : {sorted(appels)}",
    )
    source = appels["fiche"]["source"]
    assert source == "./modules/fiche", message(
        en=f"The `source` is {source!r}, expected `./modules/fiche`. A RELATIVE "
        "path makes the submodule be considered part of the same "
        "package, instead of being downloaded separately.",
        fr=f"Le `source` vaut {source!r}, attendu `./modules/fiche`. Un chemin "
        "RELATIF fait considérer le sous-module comme faisant partie du même "
        "paquet, au lieu d'être téléchargé séparément.",
    )
    sorties = appels["fiche"]["module"].get("outputs", {})
    assert sorties, message(
        en="The nested module exposes no output: it therefore returns nothing to "
        "the root.",
        fr="Le module imbriqué n'expose aucun output : il ne remonte donc rien à "
        "la racine.",
    )


def test_le_module_est_instancie_par_environnement(applique: Path) -> None:
    enfants = show_json(applique)["values"]["root_module"].get("child_modules", [])
    adresses = {e["address"] for e in enfants}
    attendues = {f'module.fiche["{nom}"]' for nom in ENVIRONNEMENTS}
    assert adresses == attendues, message(
        en=f"The state carries {sorted(adresses)}, expected {sorted(attendues)}.",
        fr=f"Le state porte {sorted(adresses)}, attendu {sorted(attendues)}.",
    )
    for enfant in enfants:
        types = {r["type"] for r in enfant.get("resources", [])}
        assert types == {"random_pet", "local_file"}, message(
            en=f"{enfant['address']} carries {sorted(types)}, a `random_pet` "
            "and a `local_file` were expected.",
            fr=f"{enfant['address']} porte {sorted(types)}, attendu un `random_pet` "
            "et un `local_file`.",
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
    assert index is not None, message(
        en="`local_file.index` has disappeared from the root: that is the resource the "
        "override file must modify.",
        fr="`local_file.index` a disparu de la racine : c'est la ressource que le "
        "fichier de surcharge doit modifier.",
    )
    permissions = index["values"]["file_permission"]
    assert permissions == "0600", message(
        en=f"`file_permission` is {permissions!r}, expected `0600`. The value "
        "declared in `main.tf` stays `0644`: only a file named "
        "`override.tf` or `*_override.tf`, loaded LAST by Terraform, can "
        "replace it. The same content in a file with an ordinary name produces "
        "`Duplicate resource configuration`.",
        fr=f"`file_permission` vaut {permissions!r}, attendu `0600`. La valeur "
        "déclarée dans `main.tf` reste `0644` : seul un fichier nommé "
        "`override.tf` ou `*_override.tf`, chargé en DERNIER par Terraform, peut "
        "la remplacer. Le même contenu dans un fichier au nom ordinaire produit "
        "`Duplicate resource configuration`.",
    )
    assert (applique / "index.txt").is_file(), message(
        en="index.txt does not exist: the configuration was not applied.",
        fr="index.txt n'existe pas : la configuration n'a pas été appliquée.",
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
    assert "chemins" in outputs, message(
        en=f"The `chemins` output is missing. Outputs present: {sorted(outputs)}",
        fr=f"L'output `chemins` manque. Outputs présents : {sorted(outputs)}",
    )
    type_declare = outputs["chemins"]["type"]
    assert type_declare == ["map", "string"], message(
        en=f"The type of `chemins` comes out as {type_declare!r}, expected "
        '["map", "string"]. Style guide 1.15 asks for a `type` on every '
        "output, just as on every variable.",
        fr=f"Le type de `chemins` ressort en {type_declare!r}, attendu "
        '["map", "string"]. Le style guide 1.15 demande un `type` sur chaque '
        "output, au même titre que sur chaque variable.",
    )
    valeur = outputs["chemins"]["value"]
    assert set(valeur) == ENVIRONNEMENTS, message(
        en=f"`chemins` carries the keys {sorted(valeur)}, expected "
        f"{sorted(ENVIRONNEMENTS)}.",
        fr=f"`chemins` porte les clés {sorted(valeur)}, attendu "
        f"{sorted(ENVIRONNEMENTS)}.",
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
            message(
            en=f"`init` failed in examples/minimal.\n{init.stderr[-900:]}",
            fr=f"`init` a échoué dans examples/minimal.\n{init.stderr[-900:]}",
        )
        )
    valide = terraform(f"-chdir={exemple}", "validate", "-json", cwd=applique)
    document = json.loads(valide.stdout)
    assert document.get("valid") is True and document.get("error_count") == 0, message(
        en=f"`validate` of the example returns valid={document.get('valid')} and "
        f"error_count={document.get('error_count')}. An example must stand "
        "on its own: it will end up copied elsewhere.",
        fr=f"`validate` de l'exemple rend valid={document.get('valid')} et "
        f"error_count={document.get('error_count')}. Un exemple doit tenir "
        "debout seul : il finira copié ailleurs.",
    )


# --------------------------------------------------------------------------
# 6. La configuration a converge
# --------------------------------------------------------------------------

def test_plus_aucun_changement_en_attente(applique: Path) -> None:
    plan = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color",
                     cwd=applique)
    assert plan.returncode == 0, message(
        en=f"plan -detailed-exitcode returns {plan.returncode}, expected 0.\n"
        f"{plan.stdout[-900:]}",
        fr=f"plan -detailed-exitcode rend {plan.returncode}, attendu 0.\n"
        f"{plan.stdout[-900:]}",
    )
