"""Tests fonctionnels du lab « rendre un module composable ».

Un guide de bonnes pratiques se coche a la main ; ici, chaque pratique se lit
dans un artefact que Terraform ecrit lui-meme. Le JSON du plan expose la
configuration telle que Terraform l'a comprise, et le JSON de l'etat expose ce
qui a ete cree.

Faits verifies sur Terraform 1.15.4, hors ligne, provider `local` :
- une configuration de provider declaree DANS un module apparait dans
  `configuration.provider_config` avec un champ `module_address` ; c'est le
  detecteur exact de la violation ;
- un module qui configure reellement un provider fait echouer l'appel :
  `Error: Module is incompatible with count, for_each, and depends_on` ;
- `configuration_aliases` cote module et `providers = { ... }` cote appel font
  passer la configuration aliasee, et le JSON du plan la montre avec son `alias` ;
- sans l'argument `providers`, l'init s'arrete sur `Error: Missing required
  provider configuration`, en nommant l'alias attendu.
"""

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, message, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "modules-module-best-practices"

PROJET = "projet"
MODULE = "bibliotheque/plaque"
ETIQUETTES = ("nord", "sud")
REPERTOIRE = "sorties"


def _projet(racine: Path) -> Path:
    chemin = racine / PROJET
    if not chemin.is_dir():
        pytest.fail(message(
            en=f"The {PROJET}/ directory is missing from challenge/work.",
            fr=f"Le répertoire {PROJET}/ est absent de challenge/work.",
        ))
    return chemin


def _plan_json(racine: Path) -> dict:
    projet = _projet(racine)
    plan = terraform("plan", "-input=false", "-no-color", "-out=analyse.tfplan",
                     cwd=projet)
    if plan.returncode != 0:
        pytest.fail(
            message(
            en=f"`terraform plan` failed in {PROJET}. A leftover `???`, a "
            "missing `providers`, or a module still configuring its own "
            f"provider?\n{plan.stderr[-1100:]}",
            fr=f"`terraform plan` a échoué dans {PROJET}. Un `???` restant, un "
            "`providers` manquant, ou un module qui configure encore son "
            f"provider ?\n{plan.stderr[-1100:]}",
        )
        )
    montre = terraform("show", "-json", "analyse.tfplan", cwd=projet)
    montre.check_returncode()
    return json.loads(montre.stdout)


def _etat_json(racine: Path) -> dict:
    montre = terraform("show", "-json", cwd=_projet(racine))
    montre.check_returncode()
    return json.loads(montre.stdout)


@pytest.fixture(scope="module")
def racine() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    projet = _projet(WORKDIR)
    init = terraform("init", "-input=false", "-no-color", cwd=projet)
    if init.returncode != 0:
        pytest.fail(
            message(
            en=f"`terraform init` failed in {PROJET}.\n{init.stderr[-1100:]}",
            fr=f"`terraform init` a échoué dans {PROJET}.\n{init.stderr[-1100:]}",
        )
        )
    yield WORKDIR


@pytest.fixture(scope="module")
def plan(racine: Path) -> dict:
    return _plan_json(racine)


# --------------------------------------------------------------------------
# 1. Le module ne configure plus son provider
# --------------------------------------------------------------------------

def test_aucune_configuration_de_provider_dans_le_module(plan: dict) -> None:
    configs = plan["configuration"].get("provider_config", {})
    fautives = {
        cle: valeur for cle, valeur in configs.items() if "module_address" in valeur
    }
    assert not fautives, message(
        en=f"The plan's JSON exposes {sorted(fautives)}: those provider "
        "configurations are declared INSIDE a module, which their "
        "`module_address` field betrays. A module embedding its provider configuration "
        "can no longer be destroyed cleanly, and its call refuses `count`, "
        "`for_each` and `depends_on`.",
        fr=f"Le JSON du plan expose {sorted(fautives)} : ces configurations de "
        "provider sont déclarées DANS un module, ce que trahit leur champ "
        "`module_address`. Un module qui embarque sa configuration de provider "
        "ne peut plus être détruit proprement, et son appel refuse `count`, "
        "`for_each` et `depends_on`.",
    )


def test_l_appelant_passe_une_configuration_aliasee(plan: dict) -> None:
    configs = plan["configuration"].get("provider_config", {})
    aliasees = {cle: v for cle, v in configs.items() if v.get("alias")}
    assert aliasees, message(
        en=f"No aliased configuration in the plan's JSON. Keys found: "
        f"{sorted(configs)}. The project must declare a named configuration "
        "and pass it to the module, which expects it through `configuration_aliases`.",
        fr=f"Aucune configuration aliasée dans le JSON du plan. Clés trouvées : "
        f"{sorted(configs)}. Le projet doit déclarer une configuration nommée "
        "et la passer au module, qui l'attend via `configuration_aliases`.",
    )
    appel = plan["configuration"]["root_module"]["module_calls"]["plaque"]
    ressources = appel["module"].get("resources", [])
    cles = {r.get("provider_config_key") for r in ressources}
    assert any(cle and "." in str(cle) for cle in cles), message(
        en=f"The module's resources use {sorted(str(c) for c in cles)}: "
        "none points at the aliased configuration passed by the caller.",
        fr=f"Les ressources du module utilisent {sorted(str(c) for c in cles)} : "
        "aucune ne pointe vers la configuration aliasée passée par l'appelant.",
    )


# --------------------------------------------------------------------------
# 2. Le module recoit sa dependance au lieu de la fabriquer
# --------------------------------------------------------------------------

def test_le_repertoire_est_une_entree_du_module(plan: dict) -> None:
    appel = plan["configuration"]["root_module"]["module_calls"]["plaque"]
    variables = appel["module"].get("variables", {})
    assert len(variables) >= 2, message(
        en=f"The module declares only {sorted(variables)}: the output directory "
        "must become an INPUT, so that the caller can wire the module "
        "elsewhere. That is dependency inversion.",
        fr=f"Le module ne déclare que {sorted(variables)} : le répertoire de sortie "
        "doit devenir une ENTRÉE, pour que l'appelant puisse brancher le module "
        "ailleurs. C'est l'inversion de dépendance.",
    )
    passees = set(appel.get("expressions", {}))
    assert len(passees) >= 2, message(
        en=f"The call only passes {sorted(passees)}: the project must provide the "
        "directory, not suffer it.",
        fr=f"L'appel ne passe que {sorted(passees)} : le projet doit fournir le "
        "répertoire, et non le subir.",
    )


def test_le_projet_choisit_le_repertoire_de_sortie(racine: Path) -> None:
    chemins = _etat_json(racine)["values"]["outputs"]["chemins"]["value"]
    for etiquette, chemin in chemins.items():
        assert REPERTOIRE in chemin, message(
            en=f"The plate `{etiquette}` is written to {chemin!r}, without "
            f"`{REPERTOIRE}`: it is the project that must decide where.",
            fr=f"La plaque `{etiquette}` est écrite dans {chemin!r}, sans "
            f"`{REPERTOIRE}` : c'est le projet qui doit décider de l'endroit.",
        )


# --------------------------------------------------------------------------
# 3. Un seul appel, plusieurs instances
# --------------------------------------------------------------------------

def test_l_appel_est_multiple(plan: dict) -> None:
    """Un seul bloc `module`, plusieurs instances.

    Le JSON du plan n'expose pas de `for_each_expression` sur un appel de
    module, contrairement a une ressource : la multiplicite se lit dans les
    REFERENCES des arguments passes, `each.key` ou `count.index`.
    """
    appel = plan["configuration"]["root_module"]["module_calls"]["plaque"]
    references = {
        ref
        for expression in appel.get("expressions", {}).values()
        for ref in expression.get("references", [])
    }
    multiples = {r for r in references if r.startswith(("each.", "count."))}
    assert multiples, message(
        en=f"No argument of the call references `each` or `count`: references "
        f"found {sorted(references)}. Two plates must come out of a SINGLE "
        "module call, which a module rid of its provider configuration finally "
        "makes possible.",
        fr=f"Aucun argument de l'appel ne référence `each` ni `count` : références "
        f"trouvées {sorted(references)}. Deux plaques doivent sortir d'un SEUL "
        "appel de module, ce qu'un module débarrassé de sa configuration de "
        "provider rend enfin possible.",
    )


def test_les_deux_plaques_sont_dans_l_etat(racine: Path) -> None:
    enfants = _etat_json(racine)["values"]["root_module"].get("child_modules", [])
    adresses = sorted(m["address"] for m in enfants)
    attendues = sorted(f'module.plaque["{e}"]' for e in ETIQUETTES)
    assert adresses == attendues, message(
        en=f"The state contains {adresses}, expected {attendues}.",
        fr=f"L'état contient {adresses}, attendu {attendues}.",
    )
    for enfant in enfants:
        for ressource in enfant.get("resources", []):
            assert ressource["mode"] == "managed", message(
                en=f"{ressource['address']} is in mode {ressource['mode']!r}: the "
                "module must manage its resources, not merely read them.",
                fr=f"{ressource['address']} est en mode {ressource['mode']!r} : le "
                "module doit gérer ses ressources, pas seulement les lire.",
            )


def test_les_deux_plaques_portent_leur_etiquette(racine: Path) -> None:
    chemins = _etat_json(racine)["values"]["outputs"]["chemins"]["value"]
    assert sorted(chemins) == sorted(ETIQUETTES), message(
        en=f"The `chemins` output carries {sorted(chemins)}, expected "
        f"{sorted(ETIQUETTES)}.",
        fr=f"La sortie `chemins` porte {sorted(chemins)}, attendu "
        f"{sorted(ETIQUETTES)}.",
    )
    for etiquette, chemin in chemins.items():
        assert chemin.endswith(f"{etiquette}.txt"), message(
            en=f"The plate `{etiquette}` points at {chemin!r}, which does not carry its name.",
            fr=f"La plaque `{etiquette}` pointe {chemin!r}, qui ne porte pas son nom.",
        )


# --------------------------------------------------------------------------
# 4. Le module se documente, et le projet converge
# --------------------------------------------------------------------------

def test_le_module_porte_un_readme(racine: Path) -> None:
    readme = racine / MODULE / "README.md"
    assert readme.is_file(), message(
        en=f"{MODULE}/README.md is missing. The Standard Module Structure puts it "
        "in the MINIMUM: \"The root module and any nested modules should have "
        "README files.\" That is the file the registry and documentation "
        "generators use.",
        fr=f"{MODULE}/README.md est absent. La Standard Module Structure le place "
        "dans le MINIMUM : « The root module and any nested modules should have "
        "README files. » C'est ce fichier que le registre et les générateurs de "
        "documentation exploitent.",
    )
    assert readme.read_text(encoding="utf-8").strip(), message(
        en=f"{MODULE}/README.md is empty.",
        fr=f"{MODULE}/README.md est vide.",
    )


def test_le_projet_a_converge(racine: Path) -> None:
    plan = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color",
                     cwd=_projet(racine))
    assert plan.returncode == 0, message(
        en=f"plan -detailed-exitcode returns {plan.returncode}, expected 0."
        f"\n{plan.stdout[-700:]}",
        fr=f"plan -detailed-exitcode rend {plan.returncode}, attendu 0."
        f"\n{plan.stdout[-700:]}",
    )
