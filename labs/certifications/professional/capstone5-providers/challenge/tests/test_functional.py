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

from conftest import exiger_workdir, workdir_lab

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
    assert init.returncode == 0, f"`terraform init` a echoue.\n{init.stderr[-1000:]}"
    return WORKDIR


@pytest.fixture(scope="module")
def configuration(joue: Path) -> dict:
    """La configuration telle que Terraform la comprend, pas telle qu'elle est ecrite."""
    plan = _tf("plan", "-out=providers.tfplan", "-input=false", "-no-color")
    assert plan.returncode == 0, (
        "`terraform plan` a echoue.\n\nSi le message parle de « No valid "
        "credential sources found », le provider cherche des identifiants la ou "
        "il n'y en a pas : il lui faut des identifiants factices non vides et "
        "les options qui le dispensent d'aller verifier une identite.\n\n"
        f"{plan.stderr[-1200:]}"
    )
    montre = _tf("show", "-json", "providers.tfplan")
    montre.check_returncode()
    return json.loads(montre.stdout)["configuration"]


@pytest.fixture(scope="module")
def etat(joue: Path) -> dict:
    applique = _tf("apply", "-auto-approve", "-input=false", "-no-color")
    assert applique.returncode == 0, (
        f"`terraform apply` a echoue.\n{applique.stderr[-1200:]}"
    )
    proc = _tf("show", "-json")
    proc.check_returncode()
    return json.loads(proc.stdout)


# --------------------------------------------------------------------------
# 1. Deux configurations du meme provider, avec deux regions.
# --------------------------------------------------------------------------
def test_deux_configurations_du_provider_coexistent(configuration: dict) -> None:
    configs = configuration.get("provider_config") or {}

    assert CLE_DEFAUT in configs, (
        f"Aucune configuration par defaut du provider. Presentes : "
        f"{sorted(configs)}."
    )
    assert CLE_ALIASEE in configs, (
        f"Aucune configuration aliasee `{CLE_ALIASEE}`.\nPresentes : "
        f"{sorted(configs)}.\n\nUne seconde configuration du MEME provider exige "
        "un `alias` : sans lui, Terraform refuse le doublon."
    )

    alias = configs[CLE_ALIASEE].get("alias")
    assert alias == "archives", (
        f"La seconde configuration porte l'alias {alias!r}, `archives` attendu."
    )

    regions = {
        cle: (configs[cle].get("expressions", {}).get("region", {}) or {}).get("constant_value")
        for cle in (CLE_DEFAUT, CLE_ALIASEE)
    }
    assert regions[CLE_DEFAUT] == REGION_PAR_DEFAUT, (
        f"La configuration par defaut vise la region {regions[CLE_DEFAUT]!r}, "
        f"{REGION_PAR_DEFAUT!r} attendue."
    )
    assert regions[CLE_ALIASEE] == REGION_ARCHIVES, (
        f"La configuration aliasee vise la region {regions[CLE_ALIASEE]!r}, "
        f"{REGION_ARCHIVES!r} attendue.\n\nDeux configurations qui visent la "
        "meme region ne servent a rien : c'est ce qui les distingue."
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

    assert rattachements.get(PRINCIPAL) == CLE_DEFAUT, (
        f"`{PRINCIPAL}` est rattachee a {rattachements.get(PRINCIPAL)!r}, "
        f"{CLE_DEFAUT!r} attendu."
    )
    assert rattachements.get(ARCHIVES) == CLE_ALIASEE, (
        f"`{ARCHIVES}` est rattachee a {rattachements.get(ARCHIVES)!r}, "
        f"{CLE_ALIASEE!r} attendu.\n\nSans l'argument `provider`, une ressource "
        "utilise la configuration PAR DEFAUT. Elle serait creee au mauvais "
        "endroit, en silence : les deux instances se ressemblent."
    )


# --------------------------------------------------------------------------
# 3. La contrainte de version, lue dans le verrou.
# --------------------------------------------------------------------------
def test_la_version_du_provider_est_contrainte(joue: Path) -> None:
    """Le verrou dit ce qui est REELLEMENT epingle, le `.tf` ce qui est souhaite."""
    verrou = joue / ".terraform.lock.hcl"
    assert verrou.is_file(), "`.terraform.lock.hcl` est absent : `init` n'a pas abouti."

    contenu = verrou.read_text(encoding="utf-8")
    assert "hashicorp/aws" in contenu, (
        "Le verrou ne mentionne pas `hashicorp/aws`."
    )
    assert "constraints" in contenu, (
        "Le verrou ne porte AUCUNE contrainte de version.\n\nLe provider a ete "
        "installe sans contrainte : rien ne garantit que le collegue obtiendra "
        "la meme version.\n\nAttention, `constraints` n'est ecrit qu'a la "
        "CREATION de l'entree : si vous avez ajoute la contrainte apres coup, "
        "supprimez `.terraform.lock.hcl` et relancez `init`."
    )

    proc = _tf("version", "-json")
    proc.check_returncode()
    choisis = json.loads(proc.stdout).get("provider_selections", {})
    assert any("hashicorp/aws" in cle for cle in choisis), (
        f"Le provider aws n'est pas installe. Presents : {sorted(choisis)}."
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
    assert set(adresses) == {PRINCIPAL, ARCHIVES}, (
        f"Le state porte {sorted(adresses)}, attendu {sorted({PRINCIPAL, ARCHIVES})}."
    )

    attendu = (
        (PRINCIPAL, "capstone5-principal", REGION_PAR_DEFAUT, REGION_ARCHIVES),
        (ARCHIVES, "capstone5-archives", REGION_ARCHIVES, REGION_PAR_DEFAUT),
    )
    for adresse, nom, sa_region, l_autre in attendu:
        chez_elle = _instances_vivantes(nom, sa_region)
        assert adresses[adresse] in chez_elle, (
            f"L'instance `{nom}` du state porte l'identifiant "
            f"{adresses[adresse]!r}, et l'emulateur ne connait que {chez_elle} "
            f"dans la region {sa_region}."
        )

        ailleurs = _instances_vivantes(nom, l_autre)
        assert adresses[adresse] not in ailleurs, (
            f"L'instance `{nom}` est visible dans la region {l_autre}, alors "
            f"qu'elle devrait vivre en {sa_region}.\n\nLes deux ressources ont "
            "ete creees par la MEME configuration de provider : l'argument "
            "`provider` manque sur celle qui devait aller ailleurs."
        )


def test_la_configuration_converge(joue: Path, etat: dict) -> None:
    plan = _tf("plan", "-detailed-exitcode", "-input=false", "-no-color")
    assert plan.returncode == 0, (
        f"`plan -detailed-exitcode` rend {plan.returncode}, attendu 0.\n"
        + plan.stdout[-800:]
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
    assert detruit.returncode == 0, f"`destroy` a echoue.\n{detruit.stderr[-1000:]}"

    for nom, region in (
        ("capstone5-principal", REGION_PAR_DEFAUT),
        ("capstone5-archives", REGION_ARCHIVES),
    ):
        vivantes = _instances_vivantes(nom, region)
        assert not vivantes, (
            f"L'emulateur connait encore {vivantes} pour `{nom}` apres le destroy."
        )
