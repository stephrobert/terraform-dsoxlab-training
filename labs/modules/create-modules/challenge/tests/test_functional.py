"""Tests fonctionnels du lab « un module ne configure pas ses providers ».

La regle officielle tient en une phrase : « a module intended to be called by
one or more other modules must not contain any `provider` blocks ». Les tests
la prouvent par l'etat structure, jamais en lisant un `.tf`.

Faits verifies sur Terraform 1.15.4 (local + random + tls, hors ligne) :
- un module enfant qui CONFIGURE un provider et qu'on appelle avec `for_each`
  fait echouer l'`init` : `Module is incompatible with count, for_each, and
  depends_on`. Le provider doit etre reellement configurable pour cela : avec
  `local` ou `random`, qui n'acceptent aucun argument, Terraform se contente
  d'un avertissement `Redundant empty provider block` ;
- referencer `local.archive` dans un module qui ne l'a pas declaree rend
  `Provider configuration not present` ;
- la declarer par `configuration_aliases` sans que l'appelant la passe rend
  `Missing required provider configuration` ;
- le JSON de configuration expose `for_each_expression` au premier niveau de
  `module_calls`, et n'expose AUCUNE cle `providers` : l'argument se prouve donc
  par le `provider_config_key` des ressources de l'enfant ;
- un `providers` partiel n'annule pas l'heritage des configurations qu'il ne
  nomme pas : `local_file.manifeste` reste rattachee a `local`.
"""

import json
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "modules-create-modules"

ENVIRONNEMENTS = {"dev", "preprod", "prod"}
VARIABLES = {"nom", "cible", "retention"}


def _plan_configuration(cwd: Path, tmp: Path) -> dict:
    """Document de plan complet, produit dans une copie du workdir."""
    copie = tmp / "plan"
    if not copie.exists():
        shutil.copytree(cwd, copie)
    plan = terraform("plan", "-input=false", "-no-color", "-out=analyse.tfplan",
                     cwd=copie)
    if plan.returncode != 0:
        pytest.fail(
            "`terraform plan` a echoue. Tant que la configuration n'est pas "
            f"valide, rien ne peut etre prouve.\n{plan.stderr[-1200:]}"
        )
    montre = terraform("show", "-json", "analyse.tfplan", cwd=copie)
    montre.check_returncode()
    return json.loads(montre.stdout)


@pytest.fixture(scope="module")
def plan(tmp_path_factory: pytest.TempPathFactory) -> Iterator[dict]:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(
            "`terraform init` a echoue. Si le message parle de `count, for_each, "
            "and depends_on`, c'est le point de depart du lab : le module enfant "
            f"configure encore un provider.\n{init.stderr[-1200:]}"
        )
    yield _plan_configuration(WORKDIR, tmp_path_factory.mktemp("analyse"))


@pytest.fixture(scope="module")
def applique() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    if "values" not in show_json(WORKDIR):
        pytest.fail(
            "Le state est vide : la configuration n'a jamais ete appliquee. "
            "Lancez `terraform apply` une fois la configuration valide."
        )
    yield WORKDIR


# --------------------------------------------------------------------------
# 1. Aucune configuration de provider ne vit dans l'enfant
# --------------------------------------------------------------------------

def test_aucune_configuration_de_provider_dans_le_module(plan: dict) -> None:
    configs = plan["configuration"].get("provider_config", {})
    dans_enfant = {
        cle: val.get("module_address")
        for cle, val in configs.items()
        if val.get("module_address")
    }
    assert not dans_enfant, (
        f"Ces configurations de provider vivent dans un module enfant : "
        f"{dans_enfant}. Un module reutilisable n'en contient aucune : elles "
        "sont heritees de l'appelant, ou passees par l'argument `providers`."
    )
    alias = {
        val.get("alias") for val in configs.values() if val.get("alias")
    }
    assert "archive" in alias, (
        f"La configuration aliasee `archive` a disparu de la racine. Alias "
        f"presents : {sorted(alias) or 'aucun'}"
    )


def test_le_module_conserve_ses_exigences_de_provider(plan: dict) -> None:
    """Les configurations s'heritent, les exigences de source jamais."""
    enfant = plan["configuration"]["root_module"]["module_calls"]["livrable"]
    ressources = {r["address"] for r in enfant["module"].get("resources", [])}
    attendues = {
        "random_pet.etiquette",
        "local_file.manifeste",
        "local_file.archive",
        "tls_private_key.scellement",
    }
    assert ressources == attendues, (
        f"Le module declare {sorted(ressources)}, attendu {sorted(attendues)}. "
        "Retirer la configuration de provider ne veut pas dire retirer les "
        "ressources."
    )


# --------------------------------------------------------------------------
# 2. Un seul bloc `module`, trois instances
# --------------------------------------------------------------------------

def test_le_module_est_instancie_par_for_each(plan: dict) -> None:
    appel = plan["configuration"]["root_module"]["module_calls"]["livrable"]
    assert "for_each_expression" in appel, (
        "Le bloc `module` ne porte pas de `for_each`. Un seul bloc doit produire "
        "les trois environnements, ce que la documentation recommande plutot que "
        f"de repeter le bloc. Cles presentes : {sorted(appel)}"
    )


def test_les_trois_instances_existent(applique: Path) -> None:
    enfants = show_json(applique)["values"]["root_module"].get("child_modules", [])
    adresses = {e["address"] for e in enfants}
    attendues = {f'module.livrable["{nom}"]' for nom in ENVIRONNEMENTS}
    assert adresses == attendues, (
        f"Le state porte {sorted(adresses)}, attendu {sorted(attendues)}."
    )


# --------------------------------------------------------------------------
# 3. Le cablage des deux configurations d'un meme provider
# --------------------------------------------------------------------------

def test_chaque_ressource_est_sur_la_bonne_configuration(plan: dict) -> None:
    """Le JSON n'expose pas l'argument `providers` : ce champ le prouve."""
    enfant = plan["configuration"]["root_module"]["module_calls"]["livrable"]
    cles = {
        r["address"]: r.get("provider_config_key")
        for r in enfant["module"].get("resources", [])
    }
    assert cles.get("local_file.archive") == "local.archive", (
        "`local_file.archive` devrait etre rattachee a la configuration aliasee, "
        f"donc porter `provider_config_key = local.archive`. Releve : "
        f"{cles.get('local_file.archive')!r}. C'est la preuve que l'argument "
        "`providers` a bien ete cable, le JSON n'exposant pas cet argument."
    )
    assert cles.get("local_file.manifeste") == "local", (
        "`local_file.manifeste` devrait rester sur la configuration par defaut, "
        f"heritee. Releve : {cles.get('local_file.manifeste')!r}"
    )


# --------------------------------------------------------------------------
# 4. Un module reutilisable se documente
# --------------------------------------------------------------------------

def test_chaque_variable_du_module_porte_une_description(plan: dict) -> None:
    enfant = plan["configuration"]["root_module"]["module_calls"]["livrable"]
    variables = enfant["module"].get("variables", {})
    assert set(variables) == VARIABLES, (
        f"Le module declare {sorted(variables)}, attendu {sorted(VARIABLES)}."
    )
    sans = sorted(
        nom for nom, val in variables.items() if not val.get("description")
    )
    assert not sans, (
        f"Ces variables n'ont pas de `description` : {sans}. C'est la seule "
        "documentation que voit l'appelant, et le JSON de configuration l'expose."
    )
    avec_defaut = sorted(nom for nom, val in variables.items() if "default" in val)
    assert not avec_defaut, (
        f"Ces variables ont pris un `default` : {avec_defaut}. Sans valeur par "
        "defaut, une variable est obligatoire, et l'appelant ne peut pas oublier "
        "de la fournir."
    )


# --------------------------------------------------------------------------
# 5. Les sorties agregees, et les fichiers reellement ecrits
# --------------------------------------------------------------------------

def test_les_sorties_agregent_les_trois_instances(applique: Path) -> None:
    sortie = terraform("output", "-json", cwd=applique)
    sortie.check_returncode()
    outputs = json.loads(sortie.stdout)
    for nom in ("empreintes", "chemins_archives"):
        assert nom in outputs, (
            f"L'output `{nom}` manque a la racine. Outputs presents : "
            f"{sorted(outputs)}"
        )
        valeur = outputs[nom]["value"]
        assert isinstance(valeur, dict) and set(valeur) == ENVIRONNEMENTS, (
            f"`{nom}` devrait etre un objet a trois cles, une par environnement. "
            f"Releve : {valeur!r}"
        )
    for nom, chemin in outputs["chemins_archives"]["value"].items():
        assert (applique / chemin).is_file(), (
            f"`chemins_archives[{nom}]` annonce {chemin!r}, qui n'existe pas sur "
            "le disque."
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
