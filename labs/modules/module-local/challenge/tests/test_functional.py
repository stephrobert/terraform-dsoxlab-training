"""Tests fonctionnels du lab « brancher plusieurs projets sur un module local ».

Terraform ne considere un chemin comme LOCAL que s'il commence par `./` ou
`../`. Tout le reste, chemin absolu compris, devient un paquet recopie dans le
cache de modules. Les tests lisent cette difference dans un artefact que
Terraform ecrit lui-meme, `.terraform/modules/modules.json`.

Faits verifies sur Terraform 1.15.4 (local + random, hors ligne) :
- source `../modules-partages/artefact` : `modules.json` porte `Source` et `Dir`
  hors de `.terraform/`, et `.terraform/modules/` ne contient QUE `modules.json`,
  aucun dossier ;
- le chainage interne du module apparait sous la cle `artefact.nom`, avec
  `Source = "../nom"` (relatif AU MODULE) et un `Dir` normalise ;
- source en chemin ABSOLU : l'init annonce `Downloading file://... for nom`, et
  `modules.json` porte `Source` en `file://` avec `Dir` sous `.terraform/`. Sur
  Linux, ce `Dir` est un LIEN SYMBOLIQUE, pas une copie profonde ;
- un `version` sur une source locale fait echouer l'init sur `Invalid registry
  module source address` ;
- un chemin SANS prefixe (`modules-partages/nom`) est refuse sur `Invalid module
  source address` : la regle `./` ou `../` est normative ;
- modifier le module partage puis relancer `plan` SANS `init` rend le code 2 :
  un module local relatif n'est jamais mis en cache.
"""

import json
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "modules-module-local"

PROJETS_APPLIQUES = ("projet-dev", "projet-staging")
MODULE_PARTAGE = "modules-partages/artefact/main.tf"


def _modules_json(projet: Path) -> dict[str, dict]:
    chemin = projet / ".terraform" / "modules" / "modules.json"
    if not chemin.is_file():
        pytest.fail(
            f"{projet.name}/.terraform/modules/modules.json est absent : "
            "`terraform init` n'a jamais abouti dans ce projet."
        )
    document = json.loads(chemin.read_text(encoding="utf-8"))
    return {m["Key"]: m for m in document["Modules"] if m["Key"]}


def _outputs(projet: Path) -> dict:
    sortie = terraform("output", "-json", cwd=projet)
    sortie.check_returncode()
    return json.loads(sortie.stdout)


@pytest.fixture(scope="module")
def racine() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    for projet in (*PROJETS_APPLIQUES, "projet-fige"):
        chemin = WORKDIR / projet
        init = terraform("init", "-input=false", "-no-color", cwd=chemin)
        if init.returncode != 0:
            pytest.fail(
                f"`terraform init` a echoue dans {projet}. Un `???` restant, ou "
                "un argument qui n'a pas sa place sur une source locale ?"
                f"\n{init.stderr[-1100:]}"
            )
    yield WORKDIR


# --------------------------------------------------------------------------
# 1. Un chemin relatif n'est pas installe
# --------------------------------------------------------------------------

def test_le_module_partage_est_lu_sur_place(racine: Path) -> None:
    modules = _modules_json(racine / "projet-dev")
    assert "artefact" in modules, (
        f"Aucune entree `artefact` dans modules.json. Cles : {sorted(modules)}"
    )
    entree = modules["artefact"]
    assert entree["Source"].startswith("../"), (
        f"`Source` vaut {entree['Source']!r}. Terraform ne considere un chemin "
        "comme LOCAL que s'il commence par `./` ou `../` : tout le reste devient "
        "un paquet recopie dans le cache."
    )
    assert not entree["Dir"].startswith(".terraform"), (
        f"`Dir` vaut {entree['Dir']!r}, sous `.terraform/` : le module a ete "
        "installe dans le cache au lieu d'etre lu sur place."
    )
    cache = racine / "projet-dev" / ".terraform" / "modules"
    contenu = {p.name for p in cache.iterdir()}
    assert contenu == {"modules.json"}, (
        f"`.terraform/modules/` contient {sorted(contenu)}. Pour une source "
        "locale, il ne doit y avoir que `modules.json` : aucun dossier n'est "
        "copie."
    )


def test_le_chainage_interne_est_enregistre(racine: Path) -> None:
    modules = _modules_json(racine / "projet-dev")
    assert "artefact.nom" in modules, (
        f"Aucune entree `artefact.nom`. Cles : {sorted(modules)}. Le module "
        "partage appelle lui-meme un second module."
    )
    entree = modules["artefact.nom"]
    assert entree["Source"] == "../nom", (
        f"`Source` de `artefact.nom` vaut {entree['Source']!r}, attendu "
        "`../nom` : le chemin d'un module est relatif AU MODULE qui l'appelle, "
        "pas au projet racine."
    )
    assert entree["Dir"].endswith("modules-partages/nom"), (
        f"`Dir` vaut {entree['Dir']!r}, attendu un chemin normalise vers "
        "`modules-partages/nom`."
    )


# --------------------------------------------------------------------------
# 2. L'appel de dev est propre, et laisse jouer le defaut du module
# --------------------------------------------------------------------------

def test_l_appel_de_dev_ne_porte_pas_de_version(racine: Path) -> None:
    projet = racine / "projet-dev"
    plan = terraform("plan", "-input=false", "-no-color", "-out=analyse.tfplan",
                     cwd=projet)
    if plan.returncode != 0:
        pytest.fail(f"`terraform plan` a echoue dans projet-dev.\n{plan.stderr[-900:]}")
    montre = terraform("show", "-json", "analyse.tfplan", cwd=projet)
    montre.check_returncode()
    appels = json.loads(montre.stdout)["configuration"]["root_module"]["module_calls"]
    appel = appels["artefact"]

    assert "version" not in appel, (
        "L'appel porte encore un argument `version`. Il n'a de sens que pour un "
        "module de REGISTRE : sur une source locale, l'init echoue sur `Invalid "
        "registry module source address`."
    )
    expressions = appel.get("expressions", {})
    assert "suffixe_aleatoire" not in expressions, (
        "projet-dev ne doit pas passer `suffixe_aleatoire` : c'est la valeur par "
        "defaut du module qui doit s'appliquer."
    )


def test_le_defaut_du_module_s_applique_a_dev(racine: Path) -> None:
    configuration = _outputs(racine / "projet-dev")["configuration"]["value"]
    assert configuration == {"nom": "dev", "suffixe_aleatoire": True}, (
        f"projet-dev expose {configuration!r}, attendu `nom = dev` et "
        "`suffixe_aleatoire = true`, ce dernier venant du defaut du module."
    )


# --------------------------------------------------------------------------
# 3. Deux projets, deux states, un seul module
# --------------------------------------------------------------------------

def test_staging_utilise_le_meme_module_autrement(racine: Path) -> None:
    dir_dev = _modules_json(racine / "projet-dev")["artefact"]["Dir"]
    dir_stg = _modules_json(racine / "projet-staging")["artefact"]["Dir"]
    assert dir_dev == dir_stg, (
        f"Les deux projets lisent {dir_dev!r} et {dir_stg!r} : ils doivent "
        "partager le MEME module."
    )
    configuration = _outputs(racine / "projet-staging")["configuration"]["value"]
    assert configuration == {"nom": "staging", "suffixe_aleatoire": False}, (
        f"projet-staging expose {configuration!r}, attendu `nom = staging` et "
        "`suffixe_aleatoire = false`."
    )


# --------------------------------------------------------------------------
# 4. Le contre-exemple : un chemin absolu n'est pas local
# --------------------------------------------------------------------------

def test_le_chemin_absolu_est_traite_comme_un_paquet(racine: Path) -> None:
    modules = _modules_json(racine / "projet-fige")
    assert "nom" in modules, (
        f"Aucune entree `nom` dans le modules.json de projet-fige. Cles : "
        f"{sorted(modules)}"
    )
    entree = modules["nom"]
    assert entree["Source"].startswith("file://"), (
        f"`Source` vaut {entree['Source']!r}, attendu une adresse `file://`. Un "
        "chemin absolu est pourtant bien sur le disque, mais Terraform ne le "
        "considere pas comme local : il le traite comme un paquet distant."
    )
    assert entree["Dir"].startswith(".terraform"), (
        f"`Dir` vaut {entree['Dir']!r}, attendu un chemin sous `.terraform/` : "
        "c'est la difference visible avec un chemin relatif."
    )


# --------------------------------------------------------------------------
# 5. Un module local relatif n'est jamais mis en cache
# --------------------------------------------------------------------------

def test_une_modification_du_module_est_vue_sans_init(
    racine: Path, tmp_path: Path
) -> None:
    """Le reflexe « relancer init » apres modification est inutile ici."""
    copie = tmp_path / "propagation"
    shutil.copytree(racine, copie)
    projet = copie / "projet-dev"

    avant = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color",
                      cwd=projet)
    assert avant.returncode == 0, (
        f"Le plan de depart rend {avant.returncode}, attendu 0 : la copie doit "
        "partir d'un etat converge."
    )

    partage = copie / MODULE_PARTAGE
    contenu = partage.read_text(encoding="utf-8")
    marqueur = 'content  = "artefact ${module.nom.complet}\\n"'
    assert marqueur in contenu, (
        f"{MODULE_PARTAGE} a ete modifie : ce module devait rester intact."
    )
    partage.write_text(
        contenu.replace(marqueur, 'content  = "artefact ${module.nom.complet} v2\\n"'),
        encoding="utf-8",
    )

    apres = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color",
                      cwd=projet)
    assert apres.returncode == 2, (
        f"Apres modification du module partage, `plan -detailed-exitcode` rend "
        f"{apres.returncode}, attendu 2. Aucun `init` n'a ete relance, et c'est "
        "bien le point : « Local paths are special in that they are not "
        "installed in the same sense that other sources are »."
    )


# --------------------------------------------------------------------------
# 6. Les deux projets appliques ont converge
# --------------------------------------------------------------------------

def test_les_projets_appliques_ont_converge(racine: Path) -> None:
    for nom in PROJETS_APPLIQUES:
        plan = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color",
                         cwd=racine / nom)
        assert plan.returncode == 0, (
            f"{nom} : plan -detailed-exitcode rend {plan.returncode}, attendu 0."
            f"\n{plan.stdout[-700:]}"
        )
