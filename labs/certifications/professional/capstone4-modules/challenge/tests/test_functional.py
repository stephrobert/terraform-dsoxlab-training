"""Tests fonctionnels du capstone 4 : extraire un module sans rien detruire.

Transformer une configuration plate et repetitive en module reutilisable, puis
la reorganiser SANS detruire ni recreer ce qui existe. C'est la que se joue le
niveau Professional : un refactor qui detruit la production est un refactor rate.

## La preuve centrale : les identifiants

L'etat de depart est FOURNI, deja applique, avec neuf objets et leurs
identifiants. Apres le refactor, ces neuf identifiants doivent etre les memes,
aux nouvelles adresses. Une ressource recreee en porterait d'autres.

Un plan a zero changement ne suffirait pas : il serait vrai aussi d'une
configuration qui aurait tout detruit et tout recree, puisqu'elle aurait
converge elle aussi.

## Deux pieges mesures en ecrivant le lab

`version` sur un bloc `module` ne s'applique QU'AUX modules de registry. Sur une
source locale, Terraform refuse des l'init : « applies only to registry
modules ».

Et un bloc a plusieurs arguments ne tient pas sur une ligne :
`moved { from = X  to = Y }` repond « The argument "to" is required ». La forme
compacte n'est valide qu'avec un seul argument.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from conftest import exiger_workdir, message, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "certifications-professional-capstone4-modules"

SERVICES = {"api": 3, "web": 2, "batch": 1}

# Les neuf adresses d'origine, celles de la configuration plate. Aucune ne doit
# subsister apres le refactor.
ADRESSES_PLATES = {
    f"{type_}.{service}_{suffixe}"
    for service in SERVICES
    for type_, suffixe in (
        ("random_pet", "nom"),
        ("local_file", "config"),
        ("local_file", "journal"),
    )
}


def _tf(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["terraform", *args], cwd=cwd or WORKDIR, capture_output=True, text=True, check=False
    )


@pytest.fixture(scope="module")
def joue() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    init = _tf("init", "-input=false", "-no-color")
    assert init.returncode == 0, message(
        en="`terraform init` failed.\n\nIf the message mentions \"applies only to "
        "registry modules\", it is the `version` argument set on a local "
        "module: it only applies to registry modules.\n\n"
        f"{init.stderr[-1000:]}",
        fr="`terraform init` a échoué.\n\nSi le message parle de « applies only to "
        "registry modules », c'est l'argument `version` posé sur un module "
        "local : il ne s'applique qu'aux modules de registry.\n\n"
        f"{init.stderr[-1000:]}",
    )
    return WORKDIR


@pytest.fixture(scope="module")
def etat(joue: Path) -> dict:
    proc = _tf("show", "-json")
    assert proc.returncode == 0, message(
        en=f"`terraform show -json` failed.\n{proc.stderr[-800:]}",
        fr=f"`terraform show -json` a échoué.\n{proc.stderr[-800:]}",
    )
    return json.loads(proc.stdout)


def _adresses_et_identifiants(etat: dict) -> dict[str, str]:
    """Toutes les ressources gerees, racine et modules confondus."""
    trouve: dict[str, str] = {}

    def parcourir(module: dict) -> None:
        for r in module.get("resources", []):
            if r["mode"] == "managed":
                trouve[r["address"]] = r["values"].get("id")
        for enfant in module.get("child_modules", []):
            parcourir(enfant)

    parcourir(etat.get("values", {}).get("root_module", {}))
    return trouve


def _exiger_refactor_fait(etat: dict) -> None:
    """Refuse de mesurer tant que les ressources ne sont pas sous un module.

    Sans cette garde, trois tests etaient VERTS a vide, mesure du 2026-09-25 :
    l'etat de depart fourni porte deja les bons identifiants, converge deja, et
    ne configure aucun provider dans un module puisqu'il n'a pas de module.

    Ils mesuraient l'etat de depart, pas le travail. C'est le defaut le plus
    couteux du domaine, et il ne se voit qu'en jouant le lab sans rien faire.
    """
    adresses = set(_adresses_et_identifiants(etat))
    sous_module = {a for a in adresses if a.startswith("module.")}
    assert sous_module, message(
        en="No resource lives under a module: the refactor did not happen.\n\n"
        f"Addresses present: {sorted(adresses)}\n\n"
        "This test measures nothing as long as the configuration has stayed flat.",
        fr="Aucune ressource ne vit sous un module : le refactor n'a pas eu lieu.\n\n"
        f"Adresses présentes : {sorted(adresses)}\n\n"
        "Ce test ne mesure rien tant que la configuration est restée plate.",
    )


def _etat_courant() -> dict:
    """L'etat, relu a la demande, pour les tests qui n'ont pas la fixture."""
    proc = _tf("show", "-json")
    proc.check_returncode()
    return json.loads(proc.stdout)


def _identifiants_de_depart(joue: Path) -> set[str]:
    """Les identifiants figes dans la fixture, avant tout refactor.

    Ils sont relus depuis le state FOURNI, et non depuis une liste ecrite ici :
    une constante recopiee finirait par mentir le jour ou la fixture change.
    """
    reference = joue.parent.parent / "fixtures" / "terraform.tfstate"
    assert reference.is_file(), message(
        en=f"The reference state cannot be found: {reference}",
        fr=f"Le state de référence est introuvable : {reference}",
    )
    document = json.loads(reference.read_text(encoding="utf-8"))
    return {
        instance["attributes"]["id"]
        for ressource in document["resources"]
        for instance in ressource["instances"]
    }


# --------------------------------------------------------------------------
# 1. La duplication a disparu, les ressources vivent sous un module.
# --------------------------------------------------------------------------
def test_les_ressources_vivent_desormais_sous_un_module(etat: dict) -> None:
    adresses = set(_adresses_et_identifiants(etat))
    assert adresses, message(
        en="The state carries no managed resource.",
        fr="Le state ne porte aucune ressource gérée.",
    )

    restantes = adresses & ADRESSES_PLATES
    assert not restantes, message(
        en=f"These flat addresses still exist: {sorted(restantes)}.\n\nThe "
        "duplication has not gone: the resources must live under "
        "`module.*`.",
        fr=f"Ces adresses plates existent encore : {sorted(restantes)}.\n\nLa "
        "duplication n'a pas disparu : les ressources doivent vivre sous "
        "`module.*`.",
    )

    hors_module = {a for a in adresses if not a.startswith("module.")}
    assert not hors_module, message(
        en=f"These resources are not in a module: {sorted(hors_module)}.",
        fr=f"Ces ressources ne sont pas dans un module : {sorted(hors_module)}.",
    )

    assert len(adresses) == len(ADRESSES_PLATES), message(
        en=f"The state carries {len(adresses)} resources, {len(ADRESSES_PLATES)} "
        f"expected.\nPresent: {sorted(adresses)}",
        fr=f"Le state porte {len(adresses)} ressources, {len(ADRESSES_PLATES)} "
        f"attendues.\nPrésentes : {sorted(adresses)}",
    )


def test_le_module_est_appele_une_fois_par_service(etat: dict) -> None:
    """Trois instances, indexees par le NOM du service.

    Un `count` donnerait des index entiers, et retirer un service du milieu
    decalerait les autres : ce sont alors deux services qui bougent au lieu
    d'un.
    """
    adresses = _adresses_et_identifiants(etat)
    cles = set()
    for adresse in adresses:
        if adresse.startswith("module.") and '["' in adresse:
            cles.add(adresse.split('["', 1)[1].split('"]', 1)[0])

    assert cles == set(SERVICES), message(
        en=f"The module is instantiated for {sorted(cles) or 'no key'}.\n"
        f"One instance per service was expected: {sorted(SERVICES)}.\n\nThe "
        "instances must be indexed by the service's NAME, not by a rank.",
        fr=f"Le module est instancié pour {sorted(cles) or 'aucune clé'}.\n"
        f"Attendu une instance par service : {sorted(SERVICES)}.\n\nLes "
        "instances doivent être indexées par le NOM du service, pas par un rang.",
    )


# --------------------------------------------------------------------------
# 2. LA preuve : rien n'a ete recree.
# --------------------------------------------------------------------------
def test_aucune_ressource_n_a_ete_recreee(joue: Path, etat: dict) -> None:
    """Les neuf identifiants d'avant doivent se retrouver, aux nouvelles adresses.

    C'est ce qu'un plan a zero changement ne dit PAS : une configuration qui
    aurait tout detruit et tout recree aurait converge elle aussi.
    """
    _exiger_refactor_fait(etat)

    avant = _identifiants_de_depart(joue)
    apres = set(_adresses_et_identifiants(etat).values())

    perdus = avant - apres
    assert not perdus, message(
        en=f"{len(perdus)} original identifier(s) have disappeared from the state.\n\n"
        "Those resources were DESTROYED and then RECREATED by the refactor: the "
        "`moved` blocks declaring their change of address are missing.\n\n"
        f"Gone: {sorted(perdus)[:4]}\n\n"
        "Reminder: a `moved` block carries two arguments, so it is written over "
        "several lines. The compact single-line form answers \"The "
        "argument \\\"to\\\" is required\".",
        fr=f"{len(perdus)} identifiant(s) d'origine ont disparu du state.\n\n"
        "Ces ressources ont été DÉTRUITES puis RECRÉÉES par le refactor : il "
        "manque les blocs `moved` qui déclarent leur changement d'adresse.\n\n"
        f"Disparus : {sorted(perdus)[:4]}\n\n"
        "Rappel : un bloc `moved` porte deux arguments, il s'écrit donc en "
        "plusieurs lignes. La forme compacte sur une ligne répond « The "
        "argument \"to\" is required ».",
    )

    nouveaux = apres - avant
    assert not nouveaux, message(
        en=f"These identifiers did not exist before: {sorted(nouveaux)[:4]}.\n\n"
        "Resources were created on top of those that existed.",
        fr=f"Ces identifiants n'existaient pas avant : {sorted(nouveaux)[:4]}.\n\n"
        "Des ressources ont été créées en plus de celles qui existaient.",
    )


# --------------------------------------------------------------------------
# 3. Le module a une interface, et il n'impose aucun provider.
# --------------------------------------------------------------------------
def test_le_module_expose_une_interface_typee_et_documentee(joue: Path) -> None:
    """Lue dans le plan JSON, qui expose la configuration telle que comprise.

    Un module sans `description` ni `type` marche, et laisse le prochain
    lecteur deviner. Le lab l'exige parce que c'est ce qui distingue un module
    reutilisable d'un copier-coller deplace.
    """
    plan = _tf("plan", "-out=interface.tfplan", "-input=false", "-no-color")
    assert plan.returncode == 0, message(
        en=f"The plan failed.\n{plan.stderr[-800:]}",
        fr=f"Le plan a échoué.\n{plan.stderr[-800:]}",
    )

    montre = _tf("show", "-json", "interface.tfplan")
    montre.check_returncode()
    racine = json.loads(montre.stdout)["configuration"]["root_module"]

    appels = racine.get("module_calls") or {}
    assert appels, message(
        en="The root configuration calls no module.\n\nThe refactor must "
        "extract a local module and call it.",
        fr="La configuration racine n'appelle aucun module.\n\nLe refactor doit "
        "extraire un module local et l'appeler.",
    )

    nom_appel, appel = next(iter(appels.items()))
    module = appel.get("module", {})

    variables = module.get("variables") or {}
    assert variables, message(
        en=f"The module `{nom_appel}` declares no variable.",
        fr=f"Le module `{nom_appel}` ne déclare aucune variable.",
    )
    sans_description = [n for n, v in variables.items() if not (v.get("description") or "").strip()]
    assert not sans_description, message(
        en=f"These module variables have no `description`: {sans_description}.",
        fr=f"Ces variables du module n'ont pas de `description` : {sans_description}.",
    )

    sorties = module.get("outputs") or {}
    assert sorties, message(
        en=f"The module `{nom_appel}` exposes no output.\n\nA module that returns "
        "nothing cannot be composed: its values stay prisoners.",
        fr=f"Le module `{nom_appel}` n'expose aucun output.\n\nUn module qui ne "
        "rend rien ne peut pas être composé : ses valeurs restent prisonnières.",
    )


def test_le_module_ne_configure_aucun_provider(joue: Path) -> None:
    """Un module appele plusieurs fois ne peut pas configurer ses providers.

    La regle officielle est nette : « a module intended to be called by one or
    more other modules must not contain any provider blocks ». Avec un
    `for_each`, Terraform refuse purement et simplement.

    La preuve : la configuration s'applique avec un `for_each`. Si le module
    configurait un provider, l'init aurait deja echoue.
    """
    _exiger_refactor_fait(_etat_courant())

    plan = _tf("plan", "-out=providers.tfplan", "-input=false", "-no-color")
    assert plan.returncode == 0, message(
        en=f"The plan failed.\n{plan.stderr[-800:]}",
        fr=f"Le plan a échoué.\n{plan.stderr[-800:]}",
    )

    montre = _tf("show", "-json", "providers.tfplan")
    montre.check_returncode()
    configuration = json.loads(montre.stdout)["configuration"]

    dans_le_module = [
        cle for cle, valeur in (configuration.get("provider_config") or {}).items()
        if (valeur.get("module_address") or "")
    ]
    assert not dans_le_module, message(
        en=f"These provider configurations live inside a module: "
        f"{dans_le_module}.\n\nA module called several times must carry "
        "none: they are inherited from the caller.",
        fr=f"Ces configurations de provider vivent dans un module : "
        f"{dans_le_module}.\n\nUn module appelé plusieurs fois ne doit en porter "
        "aucune : elles s'héritent de l'appelant.",
    )


# --------------------------------------------------------------------------
# 4. Les deux cotes : le refactor converge, et les fichiers sont intacts.
# --------------------------------------------------------------------------
def test_le_refactor_converge_et_les_fichiers_sont_inchanges(joue: Path) -> None:
    """La convergence seule serait vraie d'une configuration qui a tout recree.

    Accolee au contenu des fichiers produits, elle dit autre chose : les objets
    sont les memes, au meme endroit, avec le meme contenu.
    """
    _exiger_refactor_fait(_etat_courant())

    plan = _tf("plan", "-detailed-exitcode", "-input=false", "-no-color")
    assert plan.returncode == 0, message(
        en=f"`plan -detailed-exitcode` returns {plan.returncode}, expected 0.\n"
        + plan.stdout[-1000:],
        fr=f"`plan -detailed-exitcode` rend {plan.returncode}, attendu 0.\n"
        + plan.stdout[-1000:],
    )

    for service, replicas in SERVICES.items():
        config = joue / "out" / f"{service}.json"
        assert config.is_file(), message(
            en=f"`out/{service}.json` has disappeared.\n\nThe refactor moved the "
            "files on disk: the module must write where they were, "
            "which requires `path.root` and not `path.module`.",
            fr=f"`out/{service}.json` a disparu.\n\nLe refactor a déplacé les "
            "fichiers sur le disque : le module doit écrire là où ils étaient, "
            "ce qui demande `path.root` et non `path.module`.",
        )
        document = json.loads(config.read_text(encoding="utf-8"))
        assert document["service"] == service, message(
            en=f"`out/{service}.json` announces the service {document['service']!r}.",
            fr=f"`out/{service}.json` annonce le service {document['service']!r}.",
        )
        assert document["replicas"] == replicas, message(
            en=f"`out/{service}.json` announces {document['replicas']} replicas, "
            f"{replicas} expected.",
            fr=f"`out/{service}.json` annonce {document['replicas']} replicas, "
            f"{replicas} attendus.",
        )
