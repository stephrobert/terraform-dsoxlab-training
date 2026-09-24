"""Tests fonctionnels du capstone 1 : cycle de vie, import et derive.

Reprendre en main une infrastructure qu'on n'a pas creee est le quotidien d'un
profil Professional, et c'est le seul objectif pour lequel HashiCorp publie des
practice labs officiels.

## Les deux criteres qui separent un import reussi d'un import rate

Un import qui « marche » mais dont le plan veut ensuite modifier la ressource
est un import RATE : la configuration decrit autre chose que l'objet reel, et
le prochain apply modifiera cet objet. Les tests exigent donc les deux :

    terraform plan -detailed-exitcode                 0  le reel colle au code
    terraform plan -refresh-only -detailed-exitcode   0  le state colle au reel

Le premier seul ne suffit pas : il peut sortir en 0 sur un state perime.

## Ce qui empeche le lab d'etre vert sans travail

L'identifiant de l'instance est celui de l'objet cree HORS Terraform, et il
change a chaque mise en place. Une ressource recreee en porterait un autre.

Et la derive doit avoir ete ACCEPTEE : le tag `Owner` vaut sa valeur manuelle,
cote Floci comme dans le state. Ne rien faire laisserait la valeur d'origine, et
l'ecraser la remettrait : les deux echouent.

## Le nettoyage est un test, pas une politesse

Le dernier test detruit, et il s'execute meme si les precedents ont echoue.
Sans lui, un lab rate laisserait une instance et un bucket derriere lui, et
c'est le lab suivant qui en paierait le prix.
"""

from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from conftest import exiger_workdir, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "certifications-professional-capstone1-resource-lifecycle"

ENDPOINT = "http://localhost:14566"
NOM_INSTANCE = "capstone-facturation"
BUCKET = "capstone-archives-legacy"

ADRESSE_INSTANCE = "aws_instance.facturation"
ADRESSE_BUCKET = "aws_s3_bucket.archives"

# La valeur que la derive pose, et que le lab demande d'ACCEPTER.
OWNER_APRES_DERIVE = "plateforme"
OWNER_ORIGINE = "finops"


def _tf(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["terraform", *args], cwd=WORKDIR, capture_output=True, text=True, check=False
    )


def _appel_ec2(requete: str) -> str:
    """Un appel EC2 non signe, mais AVEC l'en-tete d'identifiants.

    Mesure du 2026-09-24 : Floci accepte les requetes non signees, mais il
    ISOLE par identifiants. Sans `Credential=test/...`, les objets crees par
    Terraform sont invisibles, et le test conclurait a tort qu'ils n'existent
    pas.
    """
    entetes = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": (
            "AWS4-HMAC-SHA256 Credential=test/00000000/eu-west-3/ec2/aws4_request, "
            "SignedHeaders=host, Signature=0000"
        ),
    }
    demande = urllib.request.Request(
        f"{ENDPOINT}/", data=requete.encode(), headers=entetes, method="POST"
    )
    with urllib.request.urlopen(demande, timeout=30) as reponse:
        return reponse.read().decode()


def _instances_vivantes() -> list[str]:
    xml = _appel_ec2(
        "Action=DescribeInstances&Version=2016-11-15"
        f"&Filter.1.Name=tag:Name&Filter.1.Value.1={NOM_INSTANCE}"
        "&Filter.2.Name=instance-state-name"
        "&Filter.2.Value.1=running&Filter.2.Value.2=pending"
    )
    # Decouper sur `<`, et non sur `>` : ce qui suit la balise ouvrante est
    # `i-xxx</instanceId>...`, donc `split(">")[-1]` rendait le dernier segment
    # du document, soit une chaine vide. Mesure du 2026-09-24, le test echouait
    # sur `assert 'i-b8dca...' in ['']`.
    return [m.split("<")[0] for m in xml.split("<instanceId>")[1:]]


def _tag_owner(identifiant: str) -> str | None:
    xml = _appel_ec2(
        "Action=DescribeTags&Version=2016-11-15"
        f"&Filter.1.Name=resource-id&Filter.1.Value.1={identifiant}"
        "&Filter.2.Name=key&Filter.2.Value.1=Owner"
    )
    if "<value>" not in xml:
        return None
    return xml.split("<value>")[1].split("<")[0]


@pytest.fixture(scope="module")
def joue() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    return WORKDIR


@pytest.fixture(scope="module")
def etat(joue: Path) -> dict:
    proc = _tf("show", "-json")
    assert proc.returncode == 0, (
        f"`terraform show -json` a echoue.\n\nLe repertoire n'a pas ete "
        f"initialise, ou rien n'a ete applique.\n{proc.stderr[-800:]}"
    )
    return json.loads(proc.stdout)


def _gerees(etat: dict) -> dict[str, dict]:
    racine = etat.get("values", {}).get("root_module", {})
    return {
        r["address"]: r for r in racine.get("resources", []) if r["mode"] == "managed"
    }


# --------------------------------------------------------------------------
# 1. Les deux objets sont sous gestion, et ils n'ont PAS ete recrees.
# --------------------------------------------------------------------------
def test_l_instance_est_importee_et_non_recreee(etat: dict) -> None:
    gerees = _gerees(etat)
    assert ADRESSE_INSTANCE in gerees, (
        f"`{ADRESSE_INSTANCE}` n'est pas dans le state. Adresses presentes : "
        f"{sorted(gerees)}."
    )

    dans_le_state = gerees[ADRESSE_INSTANCE]["values"].get("id")
    vivantes = _instances_vivantes()

    assert dans_le_state in vivantes, (
        f"L'instance du state porte l'identifiant {dans_le_state!r}, et Floci ne "
        f"connait que {vivantes}.\n\nCette instance a ete CREEE par Terraform, "
        "pas importee : un import reprend l'objet existant avec son identifiant."
    )
    assert len(vivantes) == 1, (
        f"Floci compte {len(vivantes)} instances `{NOM_INSTANCE}` : {vivantes}.\n\n"
        "Une seule devait exister. Un import rate laisse l'objet d'origine a "
        "cote de celui que Terraform a cree."
    )


def test_le_bucket_est_importe(etat: dict) -> None:
    gerees = _gerees(etat)
    assert ADRESSE_BUCKET in gerees, (
        f"`{ADRESSE_BUCKET}` n'est pas dans le state. Adresses presentes : "
        f"{sorted(gerees)}."
    )
    identifiant = gerees[ADRESSE_BUCKET]["values"].get("id")
    assert identifiant == BUCKET, (
        f"Le bucket du state porte l'identifiant {identifiant!r}, attendu "
        f"{BUCKET!r}.\n\nL'identifiant d'un bucket S3 est son nom : un bucket "
        "cree sous un autre nom n'est pas celui qu'il fallait reprendre."
    )


# --------------------------------------------------------------------------
# 2. La derive a ete acceptee, et non ecrasee.
# --------------------------------------------------------------------------
def test_la_derive_a_ete_acceptee_des_deux_cotes(etat: dict) -> None:
    """Ni ne rien faire, ni ecraser, ne passe ce test.

    Ne rien faire laisse `finops` partout. Ecraser remet `finops` chez le
    fournisseur. Accepter, c'est aligner le CODE sur la realite, et les deux
    cotes portent alors la valeur manuelle.
    """
    gerees = _gerees(etat)
    identifiant = gerees[ADRESSE_INSTANCE]["values"]["id"]

    chez_le_fournisseur = _tag_owner(identifiant)
    assert chez_le_fournisseur == OWNER_APRES_DERIVE, (
        f"Cote Floci, le tag `Owner` vaut {chez_le_fournisseur!r}, attendu "
        f"{OWNER_APRES_DERIVE!r}.\n\n"
        + (
            "La derive n'a pas ete provoquee : l'enonce demande de la creer a la "
            "main, hors Terraform, avant de decider quoi en faire."
            if chez_le_fournisseur == OWNER_ORIGINE
            else "Le tag n'a pas la valeur attendue."
        )
    )

    dans_le_state = gerees[ADRESSE_INSTANCE]["values"].get("tags", {}).get("Owner")
    assert dans_le_state == OWNER_APRES_DERIVE, (
        f"Dans le state, le tag `Owner` vaut {dans_le_state!r} alors que le "
        f"fournisseur porte {chez_le_fournisseur!r}.\n\nLa derive a ete constatee "
        "mais pas reconciliee : le state doit suivre le reel."
    )


# --------------------------------------------------------------------------
# 3. Les deux criteres d'arret, qui tombent ensemble.
# --------------------------------------------------------------------------
def test_le_reel_colle_au_code_et_le_state_colle_au_reel(joue: Path) -> None:
    ordinaire = _tf("plan", "-detailed-exitcode", "-input=false", "-no-color")
    assert ordinaire.returncode == 0, (
        f"`plan -detailed-exitcode` rend {ordinaire.returncode}, attendu 0.\n\n"
        + (
            "Un code 2 signale que votre configuration decrit autre chose que "
            "l'objet reel. C'est le critere de reussite d'un import, et le plus "
            "souvent oublie : tant que le plan propose quelque chose, l'import "
            "n'est pas fini.\n"
            if ordinaire.returncode == 2
            else "Un code 1 signale une erreur.\n"
        )
        + ordinaire.stdout[-1000:]
    )

    refresh = _tf("plan", "-refresh-only", "-detailed-exitcode", "-input=false", "-no-color")
    assert refresh.returncode == 0, (
        f"`plan -refresh-only -detailed-exitcode` rend {refresh.returncode}, "
        "attendu 0.\n\nLe plan ordinaire passe, mais le state ne colle pas au "
        "reel : une derive reste a reconcilier. Les deux criteres tombent "
        "ensemble, et le premier seul peut sortir en 0 sur un state perime.\n"
        + refresh.stdout[-1000:]
    )


# --------------------------------------------------------------------------
# 4. Le nettoyage, inconditionnel.
# --------------------------------------------------------------------------
def test_le_destroy_ne_laisse_rien_ni_dans_le_state_ni_chez_le_fournisseur(
    joue: Path,
) -> None:
    """Il s'execute meme si tout ce qui precede a echoue.

    C'est deliberé : un lab rate qui laisse une instance et un bucket derriere
    lui fait payer le lab suivant. Le cout d'un nettoyage inutile est nul, celui
    d'un nettoyage oublie ne l'est pas.
    """
    detruit = _tf("destroy", "-auto-approve", "-input=false", "-no-color")
    assert detruit.returncode == 0, (
        f"`terraform destroy` a echoue.\n{detruit.stderr[-1000:]}"
    )

    apres = _tf("show", "-json")
    apres.check_returncode()
    restantes = _gerees(json.loads(apres.stdout))
    assert not restantes, (
        f"Le state porte encore {sorted(restantes)} apres le destroy."
    )

    vivantes = _instances_vivantes()
    assert not vivantes, (
        f"Floci connait encore les instances {vivantes} apres le destroy.\n\n"
        "Une instance importee est geree comme une autre : le destroy l'emporte."
    )
