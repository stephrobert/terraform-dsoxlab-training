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

from conftest import exiger_workdir, message, terraform, workdir_lab

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
            message(
            en=f"{projet.name}/.terraform/modules/modules.json is missing: "
            "`terraform init` never succeeded in this project.",
            fr=f"{projet.name}/.terraform/modules/modules.json est absent : "
            "`terraform init` n'a jamais abouti dans ce projet.",
        )
        )
    document = json.loads(chemin.read_text(encoding="utf-8"))
    return {m["Key"]: m for m in document["Modules"] if m["Key"]}


def _appel_de_module(projet: Path, nom: str) -> dict:
    plan = terraform("plan", "-input=false", "-no-color", "-out=analyse.tfplan",
                     cwd=projet)
    if plan.returncode != 0:
        pytest.fail(
            message(
            en=f"`terraform plan` failed in {projet.name}.\n{plan.stderr[-900:]}",
            fr=f"`terraform plan` a échoué dans {projet.name}.\n{plan.stderr[-900:]}",
        )
        )
    montre = terraform("show", "-json", "analyse.tfplan", cwd=projet)
    montre.check_returncode()
    appels = json.loads(montre.stdout)["configuration"]["root_module"]["module_calls"]
    assert nom in appels, message(
        en=f"No module call named `{nom}` in {projet.name}. "
        f"Calls found: {sorted(appels)}",
        fr=f"Aucun appel de module nommé `{nom}` dans {projet.name}. "
        f"Appels trouvés : {sorted(appels)}",
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
                message(
                en=f"`terraform init` failed in {projet}. A leftover `???`, an "
                "incomplete registry address, or a sub-directory placed on the "
                f"wrong side of the `?ref=`?\n{init.stderr[-1100:]}",
                fr=f"`terraform init` a échoué dans {projet}. Un `???` restant, une "
                "adresse de registre incomplète, ou un sous-répertoire placé du "
                f"mauvais côté du `?ref=` ?\n{init.stderr[-1100:]}",
            )
            )
    yield WORKDIR


# --------------------------------------------------------------------------
# 1. Un module de registre est telecharge, et sa version est enregistree
# --------------------------------------------------------------------------

def test_le_module_epingle_est_telecharge_dans_le_cache(racine: Path) -> None:
    modules = _modules_json(racine / "projet-epingle")
    assert "etiquette" in modules, message(
        en=f"No `etiquette` entry in modules.json. Keys: {sorted(modules)}",
        fr=f"Aucune entrée `etiquette` dans modules.json. Clés : {sorted(modules)}",
    )
    entree = modules["etiquette"]
    assert entree["Source"] == MODULE_REGISTRE, message(
        en=f"`Source` is {entree['Source']!r}, expected {MODULE_REGISTRE!r}. "
        "Terraform prefixes the address with the registry host: the address has three "
        "parts, `namespace/name/provider`.",
        fr=f"`Source` vaut {entree['Source']!r}, attendu {MODULE_REGISTRE!r}. "
        "Terraform préfixe l'adresse par l'hôte du registre : l'adresse a trois "
        "parties, `namespace/name/provider`.",
    )
    assert entree["Dir"].startswith(".terraform"), message(
        en=f"`Dir` is {entree['Dir']!r}, expected a path under `.terraform/`: "
        "unlike a local module, a registry module really is copied.",
        fr=f"`Dir` vaut {entree['Dir']!r}, attendu un chemin sous `.terraform/` : "
        "contrairement à un module local, un module de registre est bien copié.",
    )


def test_la_version_epinglee_est_exactement_celle_demandee(racine: Path) -> None:
    entree = _modules_json(racine / "projet-epingle")["etiquette"]
    assert "Version" in entree, message(
        en="The entry carries no `Version` key. That key only exists for a "
        "REGISTRY module: a local module never has one.",
        fr="L'entrée ne porte pas de clé `Version`. Cette clé n'existe que pour un "
        "module de REGISTRE : un module local n'en a jamais.",
    )
    assert entree["Version"] == VERSION_EPINGLEE, message(
        en=f"Version installed: {entree['Version']!r}, expected {VERSION_EPINGLEE!r}. "
        "This project must pin an exact version, not the most recent one.",
        fr=f"Version installée : {entree['Version']!r}, attendu {VERSION_EPINGLEE!r}. "
        "Ce projet doit épingler une version exacte, pas la plus récente.",
    )


def test_la_contrainte_ecrite_est_bien_une_version_exacte(racine: Path) -> None:
    appel = _appel_de_module(racine / "projet-epingle", "etiquette")
    contrainte = appel.get("version_constraint")
    assert contrainte is not None, message(
        en="The plan's JSON exposes no `version_constraint` for this call: "
        "the `version` argument is absent from the configuration.",
        fr="Le JSON du plan n'expose aucune `version_constraint` pour cet appel : "
        "l'argument `version` est absent de la configuration.",
    )
    assert contrainte.replace(" ", "") in (VERSION_EPINGLEE, f"={VERSION_EPINGLEE}"), message(
        en=f"Constraint written: {contrainte!r}. An EXACT version is expected "
        f"({VERSION_EPINGLEE}), the only form that guarantees the same version "
        "on another machine, since the lock file does not cover "
        "modules.",
        fr=f"Contrainte écrite : {contrainte!r}. Attendu une version EXACTE "
        f"({VERSION_EPINGLEE}), la seule forme qui garantisse la même version "
        "sur un autre poste, le fichier de verrouillage ne couvrant pas les "
        "modules.",
    )


# --------------------------------------------------------------------------
# 2. Le fichier de verrouillage ne couvre pas les modules
# --------------------------------------------------------------------------

def test_le_verrou_ne_mentionne_aucun_module(racine: Path) -> None:
    verrou = racine / "projet-epingle" / ".terraform.lock.hcl"
    assert verrou.is_file(), message(
        en="`.terraform.lock.hcl` is missing from projet-epingle, although it declares "
        "a provider: the `init` did not succeed.",
        fr="`.terraform.lock.hcl` est absent de projet-epingle, alors qu'il déclare "
        "un provider : l'`init` n'a pas abouti.",
    )
    contenu = verrou.read_text(encoding="utf-8")
    assert "hashicorp/local" in contenu, message(
        en="The lock file does not mention the `local` provider, "
        "which is nevertheless declared.",
        fr="Le fichier de verrouillage ne mentionne pas le provider `local`, "
        "pourtant déclaré.",
    )
    assert "cloudposse" not in contenu, message(
        en="The lock file mentions the module. It tracks ONLY "
        "providers: \"the dependency lock file tracks only provider "
        "dependencies\".",
        fr="Le fichier de verrouillage mentionne le module. Il ne suit QUE les "
        "providers : « the dependency lock file tracks only provider "
        "dependencies ».",
    )

    sans_provider = racine / "projet-souple" / ".terraform.lock.hcl"
    assert not sans_provider.exists(), message(
        en="projet-souple carries a `.terraform.lock.hcl` although it declares "
        "no provider. A project whose only dependency is a registry module "
        "produces none: proof that the lock ignores modules.",
        fr="projet-souple porte un `.terraform.lock.hcl` alors qu'il ne déclare "
        "aucun provider. Un projet dont la seule dépendance est un module de "
        "registre n'en produit aucun : preuve que le verrou ignore les modules.",
    )


# --------------------------------------------------------------------------
# 3. Une contrainte souple resout la version la plus recente qui la satisfait
# --------------------------------------------------------------------------

def test_la_contrainte_souple_accepte_la_serie(racine: Path) -> None:
    appel = _appel_de_module(racine / "projet-souple", "etiquette")
    contrainte = appel.get("version_constraint")
    assert contrainte is not None, message(
        en="No `version_constraint` on the call in projet-souple: the "
        "`version` argument is absent.",
        fr="Aucune `version_constraint` sur l'appel de projet-souple : l'argument "
        "`version` est absent.",
    )
    assert any(marqueur in contrainte for marqueur in ("~>", ">=")), message(
        en=f"Constraint written: {contrainte!r}. This project asks for a LOOSE "
        "constraint, accepting the whole 0.x series without allowing a 1.x.",
        fr=f"Contrainte écrite : {contrainte!r}. Ce projet demande une contrainte "
        "SOUPLE, qui accepte toute la série 0.x sans autoriser un 1.x.",
    )
    assert "1." not in contrainte, message(
        en=f"Constraint written: {contrainte!r}. It must not open the door "
        "to a following major version.",
        fr=f"Contrainte écrite : {contrainte!r}. Elle ne doit pas ouvrir la porte "
        "à une version majeure suivante.",
    )


def test_la_version_resolue_est_la_plus_recente_disponible(racine: Path) -> None:
    entree = _modules_json(racine / "projet-souple")["etiquette"]
    installee = _version(entree["Version"])
    assert installee >= VERSION_PLANCHER, message(
        en=f"Version installed: {entree['Version']!r}. Under a loose constraint, "
        "Terraform keeps the most recent one that satisfies it: "
        "\"Terraform will always select the newest available module version that "
        "meets the specified version constraints\".",
        fr=f"Version installée : {entree['Version']!r}. Sous une contrainte souple, "
        "Terraform retient la plus récente qui la satisfait : "
        "« Terraform will always select the newest available module version that "
        "meets the specified version constraints ».",
    )
    assert installee < (1, 0, 0), message(
        en=f"Version installed: {entree['Version']!r}, in 1.x: the constraint "
        "lets a major version through.",
        fr=f"Version installée : {entree['Version']!r}, en 1.x : la contrainte "
        "laisse passer une version majeure.",
    )
    epinglee = _modules_json(racine / "projet-epingle")["etiquette"]["Version"]
    assert entree["Version"] != epinglee, message(
        en=f"Both projects installed the same version ({epinglee}). The whole "
        "point of the lab is to show that a loose constraint and an exact version "
        "do not resolve to the same thing.",
        fr=f"Les deux projets ont installé la même version ({epinglee}). Tout "
        "l'objet du lab est de montrer qu'une contrainte souple et une version "
        "exacte ne résolvent pas la même chose.",
    )


def test_deux_versions_du_meme_module_cohabitent(racine: Path) -> None:
    modules = _modules_json(racine / "projet-souple")
    assert "etiquette_patch" in modules, message(
        en=f"No `etiquette_patch` entry. Keys: {sorted(modules)}. The project "
        "must call the SAME module TWICE, with two constraints.",
        fr=f"Aucune entrée `etiquette_patch`. Clés : {sorted(modules)}. Le projet "
        "doit appeler DEUX fois le même module, avec deux contraintes.",
    )
    patch = modules["etiquette_patch"]
    assert patch["Source"] == MODULE_REGISTRE, message(
        en=f"`Source` of `etiquette_patch` is {patch['Source']!r}, expected "
        f"{MODULE_REGISTRE!r}: it is the SAME module.",
        fr=f"`Source` de `etiquette_patch` vaut {patch['Source']!r}, attendu "
        f"{MODULE_REGISTRE!r} : c'est le MÊME module.",
    )
    assert patch["Version"] == VERSION_EPINGLEE, message(
        en=f"Version of `etiquette_patch`: {patch['Version']!r}, expected "
        f"{VERSION_EPINGLEE!r}. A patch window on 0.24.1 excludes "
        "0.25.0, which is nevertheless available.",
        fr=f"Version de `etiquette_patch` : {patch['Version']!r}, attendu "
        f"{VERSION_EPINGLEE!r}. Une fenêtre de correctifs sur la 0.24.1 exclut "
        "la 0.25.0, pourtant disponible.",
    )
    souple = modules["etiquette"]["Version"]
    assert souple != patch["Version"], message(
        en=f"Both calls resolved to the same version ({souple}). Resolution "
        "happens per CALL, not per project: two versions of the same module "
        "can coexist in a single `modules.json`.",
        fr=f"Les deux appels ont résolu la même version ({souple}). La résolution "
        "se fait par APPEL, pas par projet : deux versions du même module "
        "peuvent coexister dans un seul `modules.json`.",
    )

    appel = _appel_de_module(racine / "projet-souple", "etiquette_patch")
    contrainte = appel.get("version_constraint", "")
    assert "0.25" not in contrainte, message(
        en=f"Constraint written: {contrainte!r}. It must not name 0.25: "
        "it is the patch window of 0.24.1 that must exclude it.",
        fr=f"Contrainte écrite : {contrainte!r}. Elle ne doit pas nommer la 0.25 : "
        "c'est la fenêtre de correctifs de la 0.24.1 qui doit l'exclure.",
    )


# --------------------------------------------------------------------------
# 4. Le sous-repertoire precede la revision, sur une source Git
# --------------------------------------------------------------------------

def test_le_sous_repertoire_precede_la_revision(racine: Path) -> None:
    modules = _modules_json(racine / "projet-sous-module")
    assert "exports" in modules, message(
        en=f"No `exports` entry in modules.json. Keys: {sorted(modules)}",
        fr=f"Aucune entrée `exports` dans modules.json. Clés : {sorted(modules)}",
    )
    source = modules["exports"]["Source"]
    assert "//exports" in source and "?ref=" in source, message(
        en=f"`Source` is {source!r}. The address must carry the `//exports` "
        "sub-directory AND the `?ref=0.25.0` revision.",
        fr=f"`Source` vaut {source!r}. L'adresse doit porter le sous-répertoire "
        "`//exports` ET la révision `?ref=0.25.0`.",
    )
    assert source.index("//exports") < source.index("?ref="), message(
        en=f"`Source` is {source!r}: the sub-directory must come BEFORE the "
        "query arguments. \"the sub-directory portion must be before those "
        "arguments\".",
        fr=f"`Source` vaut {source!r} : le sous-répertoire doit venir AVANT les "
        "arguments de requête. « the sub-directory portion must be before those "
        "arguments ».",
    )
    assert "0.25.0" in source, message(
        en=f"`Source` is {source!r}, expected the `0.25.0` revision.",
        fr=f"`Source` vaut {source!r}, attendu la révision `0.25.0`.",
    )
    assert modules["exports"]["Dir"].endswith("/exports"), message(
        en=f"`Dir` is {modules['exports']['Dir']!r}: the `//` makes `Dir` point "
        "at the SUB-DIRECTORY of the downloaded package, not at its root.",
        fr=f"`Dir` vaut {modules['exports']['Dir']!r} : le `//` fait pointer `Dir` "
        "vers le SOUS-RÉPERTOIRE du paquet téléchargé, pas vers sa racine.",
    )


def test_le_sous_module_entraine_son_propre_module(racine: Path) -> None:
    modules = _modules_json(racine / "projet-sous-module")
    assert "exports.this" in modules, message(
        en=f"No chained `exports.this` entry. Keys: {sorted(modules)}. The "
        "targeted sub-directory calls the registry module itself.",
        fr=f"Aucune entrée chaînée `exports.this`. Clés : {sorted(modules)}. Le "
        "sous-répertoire visé appelle lui-même le module du registre.",
    )
    entree = modules["exports.this"]
    assert entree["Source"] == MODULE_REGISTRE, message(
        en=f"`Source` of `exports.this` is {entree['Source']!r}, expected "
        f"{MODULE_REGISTRE!r}.",
        fr=f"`Source` de `exports.this` vaut {entree['Source']!r}, attendu "
        f"{MODULE_REGISTRE!r}.",
    )


# --------------------------------------------------------------------------
# 5. Les deux projets appliques produisent deux etiquettes distinctes
# --------------------------------------------------------------------------

def test_les_deux_projets_produisent_des_etiquettes_distinctes(racine: Path) -> None:
    epingle = _outputs(racine / "projet-epingle")
    souple = _outputs(racine / "projet-souple")
    assert epingle["id"]["value"] == "atelier-nord", message(
        en=f"projet-epingle exposes id = {epingle['id']['value']!r}, expected "
        "`atelier-nord`: the module composes the identifier from the "
        "`namespace` and the `name`.",
        fr=f"projet-epingle expose id = {epingle['id']['value']!r}, attendu "
        "`atelier-nord` : le module compose l'identifiant à partir du "
        "`namespace` et du `name`.",
    )
    assert souple["id"]["value"] == "atelier-sud", message(
        en=f"projet-souple exposes id = {souple['id']['value']!r}, expected "
        "`atelier-sud`.",
        fr=f"projet-souple expose id = {souple['id']['value']!r}, attendu "
        "`atelier-sud`.",
    )
    assert souple["id_patch"]["value"] == "atelier-sud-patch", message(
        en=f"projet-souple exposes id_patch = {souple['id_patch']['value']!r}, "
        "expected `atelier-sud-patch`: the second call produces its own "
        "label, from another version of the module.",
        fr=f"projet-souple expose id_patch = {souple['id_patch']['value']!r}, "
        "attendu `atelier-sud-patch` : le second appel produit sa propre "
        "étiquette, depuis une autre version du module.",
    )
    assert epingle["plaque"]["value"].endswith("plaques/atelier-nord.txt"), message(
        en=f"projet-epingle exposes plaque = {epingle['plaque']['value']!r}, "
        "expected a path to `plaques/atelier-nord.txt`.",
        fr=f"projet-epingle expose plaque = {epingle['plaque']['value']!r}, "
        "attendu un chemin vers `plaques/atelier-nord.txt`.",
    )


def test_les_projets_appliques_ont_converge(racine: Path) -> None:
    for nom in ("projet-epingle", "projet-souple"):
        plan = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color",
                         cwd=racine / nom)
        assert plan.returncode == 0, message(
            en=f"{nom}: plan -detailed-exitcode returns {plan.returncode}, expected 0."
            f"\n{plan.stdout[-700:]}",
            fr=f"{nom} : plan -detailed-exitcode rend {plan.returncode}, attendu 0."
            f"\n{plan.stdout[-700:]}",
        )
