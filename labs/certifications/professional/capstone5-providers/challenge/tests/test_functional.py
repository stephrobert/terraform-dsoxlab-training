"""Tests fonctionnels du capstone 5 : deux configurations d'un meme provider.

Faire cohabiter plusieurs instances d'un meme provider, maitriser la contrainte
de version et le verrou, et diagnostiquer une erreur de provider au lieu de la
subir.

## La preuve du rattachement, et pourquoi elle ne peut pas se deviner

Deux instances EC2 creees dans deux regions se ressemblent : rien, dans l'etat,
ne dit quelle configuration de provider les a produites. Rien, sauf le champ
`provider_config_key` de la section `configuration` du plan JSON :

    aws_instance.principal  ->  aws
    aws_instance.archives   ->  aws.archives

C'est ce champ, et lui seul, qui distingue une ressource rattachee de la ressource
qui a simplement pris la configuration par defaut sans que personne ne le
remarque.

## Une preuve qui sort de Terraform

Mesure du 2026-09-25 : Floci isole par REGION. Une instance creee en `us-east-1`
est invisible depuis une requete `eu-west-3`. Chaque instance doit donc etre vue
dans SA region et absente de l'autre, ce qui prouve, hors de tout ce que
Terraform raconte, que deux configurations differentes les ont produites.

## L'environnement expurge, et pourquoi il est indispensable

Les commandes tournent sans aucune variable `AWS_*` et avec un `HOME` sans
`.aws`. Mesure du 2026-09-25 : avec des identifiants dans l'environnement, la
configuration de depart PASSE, et le lab ne prouverait rien. C'est l'absence
d'identifiants qui fait apparaitre l'erreur a diagnostiquer :

    Error: No valid credential sources found
    failed to refresh cached credentials, no EC2 IMDS role found
"""

from __future__ import annotations

import json
import os
import subprocess
import urllib.request
from pathlib import Path

import pytest

from conftest import exiger_workdir, message, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "certifications-professional-capstone5-providers"

ENDPOINT = "http://localhost:14566"

PRINCIPAL = "aws_instance.principal"
ARCHIVES = "aws_instance.archives"

REGION_PAR_DEFAUT = "eu-west-3"
REGION_ARCHIVES = "us-east-1"

# Les noms que Terraform donne aux deux configurations dans le plan JSON.
CLE_DEFAUT = "aws"
CLE_ALIASEE = "aws.archives"


def _environnement_expurge() -> dict[str, str]:
    """Sans identifiants AWS, ni dans l'environnement ni dans un fichier.

    Sans cela, le lab passerait chez qui a des credentials configures, et
    echouerait chez les autres : il mesurerait le poste, pas le travail.
    """
    propre = {c: v for c, v in os.environ.items() if not c.startswith("AWS_")}
    propre["HOME"] = str(Path(WORKDIR) / ".maison-vide")
    Path(propre["HOME"]).mkdir(parents=True, exist_ok=True)
    return propre


def _tf(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["terraform", *args],
        cwd=cwd or WORKDIR,
        capture_output=True,
        text=True,
        check=False,
        env=_environnement_expurge(),
    )


def _instances_vivantes(nom: str, region: str) -> list[str]:
    """Ce que l'emulateur connait, DANS UNE REGION donnee.

    Mesure du 2026-09-25 : Floci isole par region autant que par identifiants.
    Une instance creee en `us-east-1` est invisible depuis une requete
    `eu-west-3`, et inversement.

    C'est ce qui permet de prouver, hors de Terraform, que les deux instances
    vivent bien dans deux regions differentes : il ne suffit pas de les voir,
    il faut les voir CHACUNE DANS LA SIENNE, et pas dans l'autre.
    """
    entetes = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": (
            f"AWS4-HMAC-SHA256 Credential=test/00000000/{region}/ec2/aws4_request, "
            "SignedHeaders=host, Signature=0000"
        ),
    }
    requete = (
        "Action=DescribeInstances&Version=2016-11-15"
        f"&Filter.1.Name=tag:Name&Filter.1.Value.1={nom}"
        "&Filter.2.Name=instance-state-name"
        "&Filter.2.Value.1=running&Filter.2.Value.2=pending"
    ).encode()
    demande = urllib.request.Request(f"{ENDPOINT}/", data=requete, headers=entetes, method="POST")
    with urllib.request.urlopen(demande, timeout=30) as reponse:
        xml = reponse.read().decode()
    return [m.split("<")[0] for m in xml.split("<instanceId>")[1:]]


@pytest.fixture(scope="module")
def joue() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    init = _tf("init", "-input=false", "-no-color")
    assert init.returncode == 0, message(
        en=f"`terraform init` failed.\n{init.stderr[-1000:]}",
        fr=f"`terraform init` a échoué.\n{init.stderr[-1000:]}",
    )
    return WORKDIR


@pytest.fixture(scope="module")
def configuration(joue: Path) -> dict:
    """La configuration telle que Terraform la comprend, pas telle qu'elle est ecrite."""
    plan = _tf("plan", "-out=providers.tfplan", "-input=false", "-no-color")
    assert plan.returncode == 0, message(
        en="`terraform plan` failed.\n\nIf the message mentions \"No valid "
        "credential sources found\", the provider is looking for credentials where "
        "there are none: it needs non-empty dummy credentials and "
        "the options that spare it from going to check an identity.\n\n"
        f"{plan.stderr[-1200:]}",
        fr="`terraform plan` a échoué.\n\nSi le message parle de « No valid "
        "credential sources found », le provider cherche des identifiants là où "
        "il n'y en a pas : il lui faut des identifiants factices non vides et "
        "les options qui le dispensent d'aller vérifier une identité.\n\n"
        f"{plan.stderr[-1200:]}",
    )
    montre = _tf("show", "-json", "providers.tfplan")
    montre.check_returncode()
    return json.loads(montre.stdout)["configuration"]


@pytest.fixture(scope="module")
def etat(joue: Path) -> dict:
    applique = _tf("apply", "-auto-approve", "-input=false", "-no-color")
    assert applique.returncode == 0, message(
        en=f"`terraform apply` failed.\n{applique.stderr[-1200:]}",
        fr=f"`terraform apply` a échoué.\n{applique.stderr[-1200:]}",
    )
    proc = _tf("show", "-json")
    proc.check_returncode()
    return json.loads(proc.stdout)


# --------------------------------------------------------------------------
# 1. Deux configurations du meme provider, avec deux regions.
# --------------------------------------------------------------------------
def test_deux_configurations_du_provider_coexistent(configuration: dict) -> None:
    configs = configuration.get("provider_config") or {}

    assert CLE_DEFAUT in configs, message(
        en=f"No default provider configuration. Present: "
        f"{sorted(configs)}.",
        fr=f"Aucune configuration par défaut du provider. Présentes : "
        f"{sorted(configs)}.",
    )
    assert CLE_ALIASEE in configs, message(
        en=f"No aliased configuration `{CLE_ALIASEE}`.\nPresent: "
        f"{sorted(configs)}.\n\nA second configuration of the SAME provider requires "
        "an `alias`: without it, Terraform refuses the duplicate.",
        fr=f"Aucune configuration aliasée `{CLE_ALIASEE}`.\nPrésentes : "
        f"{sorted(configs)}.\n\nUne seconde configuration du MÊME provider exige "
        "un `alias` : sans lui, Terraform refuse le doublon.",
    )

    alias = configs[CLE_ALIASEE].get("alias")
    assert alias == "archives", message(
        en=f"The second configuration carries the alias {alias!r}, `archives` expected.",
        fr=f"La seconde configuration porte l'alias {alias!r}, `archives` attendu.",
    )

    regions = {
        cle: (configs[cle].get("expressions", {}).get("region", {}) or {}).get("constant_value")
        for cle in (CLE_DEFAUT, CLE_ALIASEE)
    }
    assert regions[CLE_DEFAUT] == REGION_PAR_DEFAUT, message(
        en=f"The default configuration targets region {regions[CLE_DEFAUT]!r}, "
        f"{REGION_PAR_DEFAUT!r} expected.",
        fr=f"La configuration par défaut vise la région {regions[CLE_DEFAUT]!r}, "
        f"{REGION_PAR_DEFAUT!r} attendue.",
    )
    assert regions[CLE_ALIASEE] == REGION_ARCHIVES, message(
        en=f"The aliased configuration targets region {regions[CLE_ALIASEE]!r}, "
        f"{REGION_ARCHIVES!r} expected.\n\nTwo configurations targeting the "
        "same region are of no use: that is what distinguishes them.",
        fr=f"La configuration aliasée vise la région {regions[CLE_ALIASEE]!r}, "
        f"{REGION_ARCHIVES!r} attendue.\n\nDeux configurations qui visent la "
        "même région ne servent à rien : c'est ce qui les distingue.",
    )


# --------------------------------------------------------------------------
# 2. LA preuve : chaque ressource est rattachee a la bonne.
# --------------------------------------------------------------------------
def test_chaque_ressource_est_rattachee_a_la_bonne_configuration(
    configuration: dict,
) -> None:
    """Le seul champ qui distingue une ressource rattachee d'une ressource oubliee.

    Sans `provider = aws.archives`, la seconde instance prendrait la
    configuration par defaut : elle serait creee dans la mauvaise region, et
    RIEN dans l'etat ne le signalerait. Les deux instances se ressemblent.
    """
    rattachements = {
        r["address"]: r.get("provider_config_key")
        for r in configuration["root_module"]["resources"]
    }

    assert rattachements.get(PRINCIPAL) == CLE_DEFAUT, message(
        en=f"`{PRINCIPAL}` is attached to {rattachements.get(PRINCIPAL)!r}, "
        f"{CLE_DEFAUT!r} expected.",
        fr=f"`{PRINCIPAL}` est rattachée à {rattachements.get(PRINCIPAL)!r}, "
        f"{CLE_DEFAUT!r} attendu.",
    )
    assert rattachements.get(ARCHIVES) == CLE_ALIASEE, message(
        en=f"`{ARCHIVES}` is attached to {rattachements.get(ARCHIVES)!r}, "
        f"{CLE_ALIASEE!r} expected.\n\nWithout the `provider` argument, a resource "
        "uses the DEFAULT configuration. It would be created in the wrong "
        "place, silently: the two instances look alike.",
        fr=f"`{ARCHIVES}` est rattachée à {rattachements.get(ARCHIVES)!r}, "
        f"{CLE_ALIASEE!r} attendu.\n\nSans l'argument `provider`, une ressource "
        "utilise la configuration PAR DÉFAUT. Elle serait créée au mauvais "
        "endroit, en silence : les deux instances se ressemblent.",
    )


# --------------------------------------------------------------------------
# 3. La contrainte de version, lue dans le verrou.
# --------------------------------------------------------------------------
def test_la_version_du_provider_est_contrainte(joue: Path) -> None:
    """Le verrou dit ce qui est REELLEMENT epingle, le `.tf` ce qui est souhaite."""
    verrou = joue / ".terraform.lock.hcl"
    assert verrou.is_file(), message(
        en="`.terraform.lock.hcl` is missing: `init` did not succeed.",
        fr="`.terraform.lock.hcl` est absent : `init` n'a pas abouti.",
    )

    contenu = verrou.read_text(encoding="utf-8")
    assert "hashicorp/aws" in contenu, message(
        en="The lock does not mention `hashicorp/aws`.",
        fr="Le verrou ne mentionne pas `hashicorp/aws`.",
    )
    assert "constraints" in contenu, message(
        en="The lock carries NO version constraint.\n\nThe provider was "
        "installed without a constraint: nothing guarantees that the colleague will get "
        "the same version.\n\nCareful, `constraints` is only written at the "
        "CREATION of the entry: if you added the constraint afterwards, "
        "delete `.terraform.lock.hcl` and run `init` again.",
        fr="Le verrou ne porte AUCUNE contrainte de version.\n\nLe provider a été "
        "installé sans contrainte : rien ne garantit que le collègue obtiendra "
        "la même version.\n\nAttention, `constraints` n'est écrit qu'à la "
        "CRÉATION de l'entrée : si vous avez ajouté la contrainte après coup, "
        "supprimez `.terraform.lock.hcl` et relancez `init`.",
    )

    proc = _tf("version", "-json")
    proc.check_returncode()
    choisis = json.loads(proc.stdout).get("provider_selections", {})
    assert any("hashicorp/aws" in cle for cle in choisis), message(
        en=f"The aws provider is not installed. Present: {sorted(choisis)}.",
        fr=f"Le provider aws n'est pas installé. Présents : {sorted(choisis)}.",
    )


# --------------------------------------------------------------------------
# 4. Les deux objets existent vraiment, chez l'emulateur.
# --------------------------------------------------------------------------
def test_les_deux_instances_existent_chez_l_emulateur(etat: dict) -> None:
    """Sortir de Terraform pour verifier Terraform.

    L'etat est le RAPPORT de Terraform sur le monde. Pour savoir si les objets
    existent, il faut demander a quelqu'un d'autre.
    """
    adresses = {
        r["address"]: r["values"].get("id")
        for r in etat["values"]["root_module"]["resources"]
        if r["mode"] == "managed"
    }
    assert set(adresses) == {PRINCIPAL, ARCHIVES}, message(
        en=f"The state carries {sorted(adresses)}, expected {sorted({PRINCIPAL, ARCHIVES})}.",
        fr=f"Le state porte {sorted(adresses)}, attendu {sorted({PRINCIPAL, ARCHIVES})}.",
    )

    attendu = (
        (PRINCIPAL, "capstone5-principal", REGION_PAR_DEFAUT, REGION_ARCHIVES),
        (ARCHIVES, "capstone5-archives", REGION_ARCHIVES, REGION_PAR_DEFAUT),
    )
    for adresse, nom, sa_region, l_autre in attendu:
        chez_elle = _instances_vivantes(nom, sa_region)
        assert adresses[adresse] in chez_elle, message(
            en=f"The `{nom}` instance in the state carries the identifier "
            f"{adresses[adresse]!r}, and the emulator only knows {chez_elle} "
            f"in region {sa_region}.",
            fr=f"L'instance `{nom}` du state porte l'identifiant "
            f"{adresses[adresse]!r}, et l'émulateur ne connaît que {chez_elle} "
            f"dans la région {sa_region}.",
        )

        ailleurs = _instances_vivantes(nom, l_autre)
        assert adresses[adresse] not in ailleurs, message(
            en=f"The `{nom}` instance is visible in region {l_autre}, although "
            f"it should live in {sa_region}.\n\nBoth resources were "
            "created by the SAME provider configuration: the `provider` "
            "argument is missing on the one that was supposed to go elsewhere.",
            fr=f"L'instance `{nom}` est visible dans la région {l_autre}, alors "
            f"qu'elle devrait vivre en {sa_region}.\n\nLes deux ressources ont "
            "été créées par la MÊME configuration de provider : l'argument "
            "`provider` manque sur celle qui devait aller ailleurs.",
        )


def test_la_configuration_converge(joue: Path, etat: dict) -> None:
    plan = _tf("plan", "-detailed-exitcode", "-input=false", "-no-color")
    assert plan.returncode == 0, message(
        en=f"`plan -detailed-exitcode` returns {plan.returncode}, expected 0.\n"
        + plan.stdout[-800:],
        fr=f"`plan -detailed-exitcode` rend {plan.returncode}, attendu 0.\n"
        + plan.stdout[-800:],
    )


# --------------------------------------------------------------------------
# 5. Le nettoyage, inconditionnel.
# --------------------------------------------------------------------------
def test_le_destroy_ne_laisse_aucune_instance(joue: Path) -> None:
    """Deux instances valent deux conteneurs chez Floci, et deux ports retenus.

    Ce test s'execute meme si les precedents ont echoue : un lab rate qui les
    laisse fait echouer le lab suivant sur un message de port, qui ne parle ni
    d'instance ni de lab.
    """
    detruit = _tf("destroy", "-auto-approve", "-input=false", "-no-color")
    assert detruit.returncode == 0, message(
        en=f"`destroy` failed.\n{detruit.stderr[-1000:]}",
        fr=f"`destroy` a échoué.\n{detruit.stderr[-1000:]}",
    )

    for nom, region in (
        ("capstone5-principal", REGION_PAR_DEFAUT),
        ("capstone5-archives", REGION_ARCHIVES),
    ):
        vivantes = _instances_vivantes(nom, region)
        assert not vivantes, message(
            en=f"The emulator still knows {vivantes} for `{nom}` after the destroy.",
            fr=f"L'émulateur connaît encore {vivantes} pour `{nom}` après le destroy.",
        )
