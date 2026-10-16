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

from conftest import exiger_workdir, message, workdir_lab

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
    assert proc.returncode == 0, message(
        en=f"`terraform show -json` failed.\n\nThe directory was not "
        f"initialised, or nothing was applied.\n{proc.stderr[-800:]}",
        fr=f"`terraform show -json` a échoué.\n\nLe répertoire n'a pas été "
        f"initialisé, ou rien n'a été appliqué.\n{proc.stderr[-800:]}",
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
    assert ADRESSE_INSTANCE in gerees, message(
        en=f"`{ADRESSE_INSTANCE}` is not in the state. Addresses present: "
        f"{sorted(gerees)}.",
        fr=f"`{ADRESSE_INSTANCE}` n'est pas dans le state. Adresses présentes : "
        f"{sorted(gerees)}.",
    )

    dans_le_state = gerees[ADRESSE_INSTANCE]["values"].get("id")
    vivantes = _instances_vivantes()

    assert dans_le_state in vivantes, message(
        en=f"The state's instance carries the identifier {dans_le_state!r}, and Floci "
        f"only knows {vivantes}.\n\nThat instance was CREATED by Terraform, "
        "not imported: an import takes over the existing object with its identifier.",
        fr=f"L'instance du state porte l'identifiant {dans_le_state!r}, et Floci ne "
        f"connaît que {vivantes}.\n\nCette instance a été CRÉÉE par Terraform, "
        "pas importée : un import reprend l'objet existant avec son identifiant.",
    )
    assert len(vivantes) == 1, message(
        en=f"Floci counts {len(vivantes)} `{NOM_INSTANCE}` instances: {vivantes}.\n\n"
        "A single one was supposed to exist. A failed import leaves the original object "
        "next to the one Terraform created.",
        fr=f"Floci compte {len(vivantes)} instances `{NOM_INSTANCE}` : {vivantes}.\n\n"
        "Une seule devait exister. Un import raté laisse l'objet d'origine à "
        "côté de celui que Terraform a créé.",
    )


def test_le_bucket_est_importe(etat: dict) -> None:
    gerees = _gerees(etat)
    assert ADRESSE_BUCKET in gerees, message(
        en=f"`{ADRESSE_BUCKET}` is not in the state. Addresses present: "
        f"{sorted(gerees)}.",
        fr=f"`{ADRESSE_BUCKET}` n'est pas dans le state. Adresses présentes : "
        f"{sorted(gerees)}.",
    )
    identifiant = gerees[ADRESSE_BUCKET]["values"].get("id")
    assert identifiant == BUCKET, message(
        en=f"The state's bucket carries the identifier {identifiant!r}, expected "
        f"{BUCKET!r}.\n\nAn S3 bucket's identifier is its name: a bucket "
        "created under another name is not the one that had to be taken over.",
        fr=f"Le bucket du state porte l'identifiant {identifiant!r}, attendu "
        f"{BUCKET!r}.\n\nL'identifiant d'un bucket S3 est son nom : un bucket "
        "créé sous un autre nom n'est pas celui qu'il fallait reprendre.",
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
    assert chez_le_fournisseur == OWNER_APRES_DERIVE, message(
        en=f"On the Floci side, the `Owner` tag is {chez_le_fournisseur!r}, expected "
        f"{OWNER_APRES_DERIVE!r}.\n\n"
        + (
            "The drift was not provoked: the instruction asks you to create it by "
            "hand, outside Terraform, before deciding what to do with it."
            if chez_le_fournisseur == OWNER_ORIGINE
            else "The tag does not have the expected value."
        ),
        fr=f"Côté Floci, le tag `Owner` vaut {chez_le_fournisseur!r}, attendu "
        f"{OWNER_APRES_DERIVE!r}.\n\n"
        + (
            "La dérive n'a pas été provoquée : l'énoncé demande de la créer à la "
            "main, hors Terraform, avant de décider quoi en faire."
            if chez_le_fournisseur == OWNER_ORIGINE
            else "Le tag n'a pas la valeur attendue."
        ),
    )

    dans_le_state = gerees[ADRESSE_INSTANCE]["values"].get("tags", {}).get("Owner")
    assert dans_le_state == OWNER_APRES_DERIVE, message(
        en=f"In the state, the `Owner` tag is {dans_le_state!r} while the "
        f"provider carries {chez_le_fournisseur!r}.\n\nThe drift was observed "
        "but not reconciled: the state must follow reality.",
        fr=f"Dans le state, le tag `Owner` vaut {dans_le_state!r} alors que le "
        f"fournisseur porte {chez_le_fournisseur!r}.\n\nLa dérive a été constatée "
        "mais pas réconciliée : le state doit suivre le réel.",
    )


# --------------------------------------------------------------------------
# 3. Les deux criteres d'arret, qui tombent ensemble.
# --------------------------------------------------------------------------
def test_le_reel_colle_au_code_et_le_state_colle_au_reel(joue: Path) -> None:
    ordinaire = _tf("plan", "-detailed-exitcode", "-input=false", "-no-color")
    assert ordinaire.returncode == 0, message(
        en=f"`plan -detailed-exitcode` returns {ordinaire.returncode}, expected 0.\n\n"
        + (
            "A code 2 signals that your configuration describes something other than "
            "the real object. That is an import's success criterion, and the most "
            "often forgotten: as long as the plan proposes something, the import "
            "is not finished.\n"
            if ordinaire.returncode == 2
            else "A code 1 signals an error.\n"
        )
        + ordinaire.stdout[-1000:],
        fr=f"`plan -detailed-exitcode` rend {ordinaire.returncode}, attendu 0.\n\n"
        + (
            "Un code 2 signale que votre configuration décrit autre chose que "
            "l'objet réel. C'est le critère de réussite d'un import, et le plus "
            "souvent oublié : tant que le plan propose quelque chose, l'import "
            "n'est pas fini.\n"
            if ordinaire.returncode == 2
            else "Un code 1 signale une erreur.\n"
        )
        + ordinaire.stdout[-1000:],
    )

    refresh = _tf("plan", "-refresh-only", "-detailed-exitcode", "-input=false", "-no-color")
    assert refresh.returncode == 0, message(
        en=f"`plan -refresh-only -detailed-exitcode` returns {refresh.returncode}, "
        "expected 0.\n\nThe ordinary plan passes, but the state does not match "
        "reality: a drift remains to be reconciled. The two criteria come out "
        "together, and the first alone can return 0 on a stale state.\n"
        + refresh.stdout[-1000:],
        fr=f"`plan -refresh-only -detailed-exitcode` rend {refresh.returncode}, "
        "attendu 0.\n\nLe plan ordinaire passe, mais le state ne colle pas au "
        "réel : une dérive reste à réconcilier. Les deux critères tombent "
        "ensemble, et le premier seul peut sortir en 0 sur un state périmé.\n"
        + refresh.stdout[-1000:],
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
    assert detruit.returncode == 0, message(
        en=f"`terraform destroy` failed.\n{detruit.stderr[-1000:]}",
        fr=f"`terraform destroy` a échoué.\n{detruit.stderr[-1000:]}",
    )

    apres = _tf("show", "-json")
    apres.check_returncode()
    restantes = _gerees(json.loads(apres.stdout))
    assert not restantes, message(
        en=f"The state still carries {sorted(restantes)} after the destroy.",
        fr=f"Le state porte encore {sorted(restantes)} après le destroy.",
    )

    vivantes = _instances_vivantes()
    assert not vivantes, message(
        en=f"Floci still knows the instances {vivantes} after the destroy.\n\n"
        "An imported instance is managed like any other: the destroy takes it away.",
        fr=f"Floci connaît encore les instances {vivantes} après le destroy.\n\n"
        "Une instance importée est gérée comme une autre : le destroy l'emporte.",
    )
