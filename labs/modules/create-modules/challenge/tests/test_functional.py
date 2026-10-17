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

from conftest import exiger_workdir, message, show_json, terraform, workdir_lab

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
            message(
            en="`terraform plan` failed. As long as the configuration is not "
            f"valid, nothing can be proven.\n{plan.stderr[-1200:]}",
            fr="`terraform plan` a échoué. Tant que la configuration n'est pas "
            f"valide, rien ne peut être prouvé.\n{plan.stderr[-1200:]}",
        )
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
            message(
            en="`terraform init` failed. If the message mentions `count, for_each, "
            "and depends_on`, that is the lab's starting point: the child module "
            f"still configures a provider.\n{init.stderr[-1200:]}",
            fr="`terraform init` a échoué. Si le message parle de `count, for_each, "
            "and depends_on`, c'est le point de départ du lab : le module enfant "
            f"configure encore un provider.\n{init.stderr[-1200:]}",
        )
        )
    yield _plan_configuration(WORKDIR, tmp_path_factory.mktemp("analyse"))


@pytest.fixture(scope="module")
def applique() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    if "values" not in show_json(WORKDIR):
        pytest.fail(
            message(
            en="The state is empty: the configuration was never applied. "
            "Run `terraform apply` once the configuration is valid.",
            fr="Le state est vide : la configuration n'a jamais été appliquée. "
            "Lancez `terraform apply` une fois la configuration valide.",
        )
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
    assert not dans_enfant, message(
        en=f"These provider configurations live inside a child module: "
        f"{dans_enfant}. A reusable module contains none: they are "
        "inherited from the caller, or passed through the `providers` argument.",
        fr=f"Ces configurations de provider vivent dans un module enfant : "
        f"{dans_enfant}. Un module réutilisable n'en contient aucune : elles "
        "sont héritées de l'appelant, ou passées par l'argument `providers`.",
    )
    alias = {
        val.get("alias") for val in configs.values() if val.get("alias")
    }
    assert "archive" in alias, message(
        en=f"The aliased configuration `archive` has disappeared from the root. Aliases "
        f"present: {sorted(alias) or 'none'}",
        fr=f"La configuration aliasée `archive` a disparu de la racine. Alias "
        f"présents : {sorted(alias) or 'aucun'}",
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
    assert ressources == attendues, message(
        en=f"The module declares {sorted(ressources)}, expected {sorted(attendues)}. "
        "Removing the provider configuration does not mean removing the "
        "resources.",
        fr=f"Le module déclare {sorted(ressources)}, attendu {sorted(attendues)}. "
        "Retirer la configuration de provider ne veut pas dire retirer les "
        "ressources.",
    )


# --------------------------------------------------------------------------
# 2. Un seul bloc `module`, trois instances
# --------------------------------------------------------------------------

def test_le_module_est_instancie_par_for_each(plan: dict) -> None:
    appel = plan["configuration"]["root_module"]["module_calls"]["livrable"]
    assert "for_each_expression" in appel, message(
        en="The `module` block carries no `for_each`. A single block must produce "
        "the three environments, which the documentation recommends rather than "
        f"repeating the block. Keys present: {sorted(appel)}",
        fr="Le bloc `module` ne porte pas de `for_each`. Un seul bloc doit produire "
        "les trois environnements, ce que la documentation recommande plutôt que "
        f"de répéter le bloc. Clés présentes : {sorted(appel)}",
    )


def test_les_trois_instances_existent(applique: Path) -> None:
    enfants = show_json(applique)["values"]["root_module"].get("child_modules", [])
    adresses = {e["address"] for e in enfants}
    attendues = {f'module.livrable["{nom}"]' for nom in ENVIRONNEMENTS}
    assert adresses == attendues, message(
        en=f"The state carries {sorted(adresses)}, expected {sorted(attendues)}.",
        fr=f"Le state porte {sorted(adresses)}, attendu {sorted(attendues)}.",
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
    assert cles.get("local_file.archive") == "local.archive", message(
        en="`local_file.archive` should be attached to the aliased configuration, "
        f"and therefore carry `provider_config_key = local.archive`. Recorded: "
        f"{cles.get('local_file.archive')!r}. That is the proof that the "
        "`providers` argument was wired, since the JSON does not expose that argument.",
        fr="`local_file.archive` devrait être rattachée à la configuration aliasée, "
        f"donc porter `provider_config_key = local.archive`. Relevé : "
        f"{cles.get('local_file.archive')!r}. C'est la preuve que l'argument "
        "`providers` a bien été câblé, le JSON n'exposant pas cet argument.",
    )
    assert cles.get("local_file.manifeste") == "local", message(
        en="`local_file.manifeste` should stay on the default, inherited "
        f"configuration. Recorded: {cles.get('local_file.manifeste')!r}",
        fr="`local_file.manifeste` devrait rester sur la configuration par défaut, "
        f"héritée. Relevé : {cles.get('local_file.manifeste')!r}",
    )


# --------------------------------------------------------------------------
# 4. Un module reutilisable se documente
# --------------------------------------------------------------------------

def test_chaque_variable_du_module_porte_une_description(plan: dict) -> None:
    enfant = plan["configuration"]["root_module"]["module_calls"]["livrable"]
    variables = enfant["module"].get("variables", {})
    assert set(variables) == VARIABLES, message(
        en=f"The module declares {sorted(variables)}, expected {sorted(VARIABLES)}.",
        fr=f"Le module déclare {sorted(variables)}, attendu {sorted(VARIABLES)}.",
    )
    sans = sorted(
        nom for nom, val in variables.items() if not val.get("description")
    )
    assert not sans, message(
        en=f"These variables have no `description`: {sans}. It is the only "
        "documentation the caller sees, and the configuration JSON exposes it.",
        fr=f"Ces variables n'ont pas de `description` : {sans}. C'est la seule "
        "documentation que voit l'appelant, et le JSON de configuration l'expose.",
    )
    avec_defaut = sorted(nom for nom, val in variables.items() if "default" in val)
    assert not avec_defaut, message(
        en=f"These variables were given a `default`: {avec_defaut}. With no default "
        "value, a variable is required, and the caller cannot forget "
        "to provide it.",
        fr=f"Ces variables ont pris un `default` : {avec_defaut}. Sans valeur par "
        "défaut, une variable est obligatoire, et l'appelant ne peut pas oublier "
        "de la fournir.",
    )


# --------------------------------------------------------------------------
# 5. Les sorties agregees, et les fichiers reellement ecrits
# --------------------------------------------------------------------------

def test_les_sorties_agregent_les_trois_instances(applique: Path) -> None:
    sortie = terraform("output", "-json", cwd=applique)
    sortie.check_returncode()
    outputs = json.loads(sortie.stdout)
    for nom in ("empreintes", "chemins_archives"):
        assert nom in outputs, message(
            en=f"The `{nom}` output is missing at the root. Outputs present: "
            f"{sorted(outputs)}",
            fr=f"L'output `{nom}` manque à la racine. Outputs présents : "
            f"{sorted(outputs)}",
        )
        valeur = outputs[nom]["value"]
        assert isinstance(valeur, dict) and set(valeur) == ENVIRONNEMENTS, message(
            en=f"`{nom}` should be an object with three keys, one per environment. "
            f"Recorded: {valeur!r}",
            fr=f"`{nom}` devrait être un objet à trois clés, une par environnement. "
            f"Relevé : {valeur!r}",
        )
    for nom, chemin in outputs["chemins_archives"]["value"].items():
        assert (applique / chemin).is_file(), message(
            en=f"`chemins_archives[{nom}]` announces {chemin!r}, which does not exist on "
            "disk.",
            fr=f"`chemins_archives[{nom}]` annonce {chemin!r}, qui n'existe pas sur "
            "le disque.",
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
