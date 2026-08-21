"""Tests fonctionnels du lab « consommer un module du registre ».

Un module de registre est TELECHARGE, versionne, et sa version retenue n'est
pas verrouillee par `.terraform.lock.hcl`. Les tests lisent cette mecanique
dans deux artefacts que Terraform ecrit lui-meme, `.terraform/modules/modules.json`
et le JSON du plan, plus l'absence ou le contenu du fichier de verrouillage.

Faits verifies sur Terraform 1.15.4, module `cloudposse/label/null` :
- `modules.json` d'un module de registre porte une cle `Version` que n'a AUCUN
  module local, un `Source` prefixe `registry.terraform.io/` et un `Dir` sous
  `.terraform/` ;
- le JSON du plan expose `module_calls.<nom>.version_constraint`, la CONTRAINTE
  ecrite par l'appelant, distincte de la version resolue ;
- `.terraform.lock.hcl` ne suit QUE les providers : un projet dont la seule
  dependance est un module de registre n'en produit meme pas ;
- une contrainte souple resout la version la plus recente qui la satisfait, une
  contrainte exacte fige la version, y compris vers le bas ;
- la resolution se fait par APPEL : deux appels du meme module, dans un seul
  projet, peuvent installer deux versions differentes ;
- sur une source Git, le sous-repertoire `//` doit preceder `?ref=`, sinon
  l'init echoue sur `invalid ref: "0.25.0//exports"`.

Ce lab exige un acces reseau a `registry.terraform.io` et a `github.com`.
"""

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "modules-module-registry"

MODULE_REGISTRE = "registry.terraform.io/cloudposse/label/null"
VERSION_EPINGLEE = "0.24.1"
VERSION_PLANCHER = (0, 25, 0)
PROJETS = ("projet-epingle", "projet-souple", "projet-sous-module")


def _modules_json(projet: Path) -> dict[str, dict]:
    chemin = projet / ".terraform" / "modules" / "modules.json"
    if not chemin.is_file():
        pytest.fail(
            f"{projet.name}/.terraform/modules/modules.json est absent : "
            "`terraform init` n'a jamais abouti dans ce projet."
        )
    document = json.loads(chemin.read_text(encoding="utf-8"))
    return {m["Key"]: m for m in document["Modules"] if m["Key"]}


def _appel_de_module(projet: Path, nom: str) -> dict:
    plan = terraform("plan", "-input=false", "-no-color", "-out=analyse.tfplan",
                     cwd=projet)
    if plan.returncode != 0:
        pytest.fail(
            f"`terraform plan` a echoue dans {projet.name}.\n{plan.stderr[-900:]}"
        )
    montre = terraform("show", "-json", "analyse.tfplan", cwd=projet)
    montre.check_returncode()
    appels = json.loads(montre.stdout)["configuration"]["root_module"]["module_calls"]
    assert nom in appels, (
        f"Aucun appel de module nomme `{nom}` dans {projet.name}. "
        f"Appels trouves : {sorted(appels)}"
    )
    return appels[nom]


def _outputs(projet: Path) -> dict:
    sortie = terraform("output", "-json", cwd=projet)
    sortie.check_returncode()
    return json.loads(sortie.stdout)


def _version(texte: str) -> tuple[int, ...]:
    return tuple(int(p) for p in texte.split("."))


@pytest.fixture(scope="module")
def racine() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    for projet in PROJETS:
        chemin = WORKDIR / projet
        init = terraform("init", "-input=false", "-no-color", cwd=chemin)
        if init.returncode != 0:
            pytest.fail(
                f"`terraform init` a echoue dans {projet}. Un `???` restant, une "
                "adresse de registre incomplete, ou un sous-repertoire place du "
                f"mauvais cote du `?ref=` ?\n{init.stderr[-1100:]}"
            )
    yield WORKDIR


# --------------------------------------------------------------------------
# 1. Un module de registre est telecharge, et sa version est enregistree
# --------------------------------------------------------------------------

def test_le_module_epingle_est_telecharge_dans_le_cache(racine: Path) -> None:
    modules = _modules_json(racine / "projet-epingle")
    assert "etiquette" in modules, (
        f"Aucune entree `etiquette` dans modules.json. Cles : {sorted(modules)}"
    )
    entree = modules["etiquette"]
    assert entree["Source"] == MODULE_REGISTRE, (
        f"`Source` vaut {entree['Source']!r}, attendu {MODULE_REGISTRE!r}. "
        "Terraform prefixe l'adresse par l'hote du registre : l'adresse a trois "
        "parties, `namespace/name/provider`."
    )
    assert entree["Dir"].startswith(".terraform"), (
        f"`Dir` vaut {entree['Dir']!r}, attendu un chemin sous `.terraform/` : "
        "contrairement a un module local, un module de registre est bien copie."
    )


def test_la_version_epinglee_est_exactement_celle_demandee(racine: Path) -> None:
    entree = _modules_json(racine / "projet-epingle")["etiquette"]
    assert "Version" in entree, (
        "L'entree ne porte pas de cle `Version`. Cette cle n'existe que pour un "
        "module de REGISTRE : un module local n'en a jamais."
    )
    assert entree["Version"] == VERSION_EPINGLEE, (
        f"Version installee : {entree['Version']!r}, attendu {VERSION_EPINGLEE!r}. "
        "Ce projet doit epingler une version exacte, pas la plus recente."
    )


def test_la_contrainte_ecrite_est_bien_une_version_exacte(racine: Path) -> None:
    appel = _appel_de_module(racine / "projet-epingle", "etiquette")
    contrainte = appel.get("version_constraint")
    assert contrainte is not None, (
        "Le JSON du plan n'expose aucune `version_constraint` pour cet appel : "
        "l'argument `version` est absent de la configuration."
    )
    assert contrainte.replace(" ", "") in (VERSION_EPINGLEE, f"={VERSION_EPINGLEE}"), (
        f"Contrainte ecrite : {contrainte!r}. Attendu une version EXACTE "
        f"({VERSION_EPINGLEE}), la seule forme qui garantisse la meme version "
        "sur un autre poste, le fichier de verrouillage ne couvrant pas les "
        "modules."
    )


# --------------------------------------------------------------------------
# 2. Le fichier de verrouillage ne couvre pas les modules
# --------------------------------------------------------------------------

def test_le_verrou_ne_mentionne_aucun_module(racine: Path) -> None:
    verrou = racine / "projet-epingle" / ".terraform.lock.hcl"
    assert verrou.is_file(), (
        "`.terraform.lock.hcl` est absent de projet-epingle, alors qu'il declare "
        "un provider : l'`init` n'a pas abouti."
    )
    contenu = verrou.read_text(encoding="utf-8")
    assert "hashicorp/local" in contenu, (
        "Le fichier de verrouillage ne mentionne pas le provider `local`, "
        "pourtant declare."
    )
    assert "cloudposse" not in contenu, (
        "Le fichier de verrouillage mentionne le module. Il ne suit QUE les "
        "providers : « the dependency lock file tracks only provider "
        "dependencies »."
    )

    sans_provider = racine / "projet-souple" / ".terraform.lock.hcl"
    assert not sans_provider.exists(), (
        "projet-souple porte un `.terraform.lock.hcl` alors qu'il ne declare "
        "aucun provider. Un projet dont la seule dependance est un module de "
        "registre n'en produit aucun : preuve que le verrou ignore les modules."
    )


# --------------------------------------------------------------------------
# 3. Une contrainte souple resout la version la plus recente qui la satisfait
# --------------------------------------------------------------------------

def test_la_contrainte_souple_accepte_la_serie(racine: Path) -> None:
    appel = _appel_de_module(racine / "projet-souple", "etiquette")
    contrainte = appel.get("version_constraint")
    assert contrainte is not None, (
        "Aucune `version_constraint` sur l'appel de projet-souple : l'argument "
        "`version` est absent."
    )
    assert any(marqueur in contrainte for marqueur in ("~>", ">=")), (
        f"Contrainte ecrite : {contrainte!r}. Ce projet demande une contrainte "
        "SOUPLE, qui accepte toute la serie 0.x sans autoriser un 1.x."
    )
    assert "1." not in contrainte, (
        f"Contrainte ecrite : {contrainte!r}. Elle ne doit pas ouvrir la porte "
        "a une version majeure suivante."
    )


def test_la_version_resolue_est_la_plus_recente_disponible(racine: Path) -> None:
    entree = _modules_json(racine / "projet-souple")["etiquette"]
    installee = _version(entree["Version"])
    assert installee >= VERSION_PLANCHER, (
        f"Version installee : {entree['Version']!r}. Sous une contrainte souple, "
        "Terraform retient la plus recente qui la satisfait : "
        "« Terraform will always select the newest available module version that "
        "meets the specified version constraints »."
    )
    assert installee < (1, 0, 0), (
        f"Version installee : {entree['Version']!r}, en 1.x : la contrainte "
        "laisse passer une version majeure."
    )
    epinglee = _modules_json(racine / "projet-epingle")["etiquette"]["Version"]
    assert entree["Version"] != epinglee, (
        f"Les deux projets ont installe la meme version ({epinglee}). Tout "
        "l'objet du lab est de montrer qu'une contrainte souple et une version "
        "exacte ne resolvent pas la meme chose."
    )


def test_deux_versions_du_meme_module_cohabitent(racine: Path) -> None:
    modules = _modules_json(racine / "projet-souple")
    assert "etiquette_patch" in modules, (
        f"Aucune entree `etiquette_patch`. Cles : {sorted(modules)}. Le projet "
        "doit appeler DEUX fois le meme module, avec deux contraintes."
    )
    patch = modules["etiquette_patch"]
    assert patch["Source"] == MODULE_REGISTRE, (
        f"`Source` de `etiquette_patch` vaut {patch['Source']!r}, attendu "
        f"{MODULE_REGISTRE!r} : c'est le MEME module."
    )
    assert patch["Version"] == VERSION_EPINGLEE, (
        f"Version de `etiquette_patch` : {patch['Version']!r}, attendu "
        f"{VERSION_EPINGLEE!r}. Une fenetre de correctifs sur la 0.24.1 exclut "
        "la 0.25.0, pourtant disponible."
    )
    souple = modules["etiquette"]["Version"]
    assert souple != patch["Version"], (
        f"Les deux appels ont resolu la meme version ({souple}). La resolution "
        "se fait par APPEL, pas par projet : deux versions du meme module "
        "peuvent coexister dans un seul `modules.json`."
    )

    appel = _appel_de_module(racine / "projet-souple", "etiquette_patch")
    contrainte = appel.get("version_constraint", "")
    assert "0.25" not in contrainte, (
        f"Contrainte ecrite : {contrainte!r}. Elle ne doit pas nommer la 0.25 : "
        "c'est la fenetre de correctifs de la 0.24.1 qui doit l'exclure."
    )


# --------------------------------------------------------------------------
# 4. Le sous-repertoire precede la revision, sur une source Git
# --------------------------------------------------------------------------

def test_le_sous_repertoire_precede_la_revision(racine: Path) -> None:
    modules = _modules_json(racine / "projet-sous-module")
    assert "exports" in modules, (
        f"Aucune entree `exports` dans modules.json. Cles : {sorted(modules)}"
    )
    source = modules["exports"]["Source"]
    assert "//exports" in source and "?ref=" in source, (
        f"`Source` vaut {source!r}. L'adresse doit porter le sous-repertoire "
        "`//exports` ET la revision `?ref=0.25.0`."
    )
    assert source.index("//exports") < source.index("?ref="), (
        f"`Source` vaut {source!r} : le sous-repertoire doit venir AVANT les "
        "arguments de requete. « the sub-directory portion must be before those "
        "arguments »."
    )
    assert "0.25.0" in source, (
        f"`Source` vaut {source!r}, attendu la revision `0.25.0`."
    )
    assert modules["exports"]["Dir"].endswith("/exports"), (
        f"`Dir` vaut {modules['exports']['Dir']!r} : le `//` fait pointer `Dir` "
        "vers le SOUS-REPERTOIRE du paquet telecharge, pas vers sa racine."
    )


def test_le_sous_module_entraine_son_propre_module(racine: Path) -> None:
    modules = _modules_json(racine / "projet-sous-module")
    assert "exports.this" in modules, (
        f"Aucune entree chainee `exports.this`. Cles : {sorted(modules)}. Le "
        "sous-repertoire vise appelle lui-meme le module du registre."
    )
    entree = modules["exports.this"]
    assert entree["Source"] == MODULE_REGISTRE, (
        f"`Source` de `exports.this` vaut {entree['Source']!r}, attendu "
        f"{MODULE_REGISTRE!r}."
    )


# --------------------------------------------------------------------------
# 5. Les deux projets appliques produisent deux etiquettes distinctes
# --------------------------------------------------------------------------

def test_les_deux_projets_produisent_des_etiquettes_distinctes(racine: Path) -> None:
    epingle = _outputs(racine / "projet-epingle")
    souple = _outputs(racine / "projet-souple")
    assert epingle["id"]["value"] == "atelier-nord", (
        f"projet-epingle expose id = {epingle['id']['value']!r}, attendu "
        "`atelier-nord` : le module compose l'identifiant a partir du "
        "`namespace` et du `name`."
    )
    assert souple["id"]["value"] == "atelier-sud", (
        f"projet-souple expose id = {souple['id']['value']!r}, attendu "
        "`atelier-sud`."
    )
    assert souple["id_patch"]["value"] == "atelier-sud-patch", (
        f"projet-souple expose id_patch = {souple['id_patch']['value']!r}, "
        "attendu `atelier-sud-patch` : le second appel produit sa propre "
        "etiquette, depuis une autre version du module."
    )
    assert epingle["plaque"]["value"].endswith("plaques/atelier-nord.txt"), (
        f"projet-epingle expose plaque = {epingle['plaque']['value']!r}, "
        "attendu un chemin vers `plaques/atelier-nord.txt`."
    )


def test_les_projets_appliques_ont_converge(racine: Path) -> None:
    for nom in ("projet-epingle", "projet-souple"):
        plan = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color",
                         cwd=racine / nom)
        assert plan.returncode == 0, (
            f"{nom} : plan -detailed-exitcode rend {plan.returncode}, attendu 0."
            f"\n{plan.stdout[-700:]}"
        )
