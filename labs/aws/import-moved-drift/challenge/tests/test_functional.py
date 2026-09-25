"""Tests fonctionnels du lab « import, moved et derive ».

Trois pieges que la lecture d'un tutoriel ne revele jamais, parce que tous les
trois sont SILENCIEUX :

- un `moved` qu'on croit passe alors qu'un `plan` seul n'ecrit rien dans le
  state ;
- un `moved` dont l'adresse `from` est fausse, que Terraform ignore sans le
  moindre avertissement, et qui duplique l'objet reel ;
- une derive qu'on ecrase par reflexe au lieu de decider quoi en faire.

Aucun test ne relit les `.tf` de l'apprenant. L'etat structure, l'API de
l'emulateur et des codes retour suffisent.
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "aws-import-moved-drift"

ENDPOINT = "http://localhost:14566"
ENV = {
    **os.environ,
    "AWS_ACCESS_KEY_ID": "test",
    "AWS_SECRET_ACCESS_KEY": "test",
    "AWS_DEFAULT_REGION": "eu-west-3",
}

NOM_HERITE = "legacy-billing-api"
ADRESSE_CIBLE = "aws_instance.billing_api"
OWNER_INITIAL = "finops"


# ── Disponibilite de l'emulateur ────────────────────────────────────────────
FLOCI_HOST = "127.0.0.1"
FLOCI_PORT = 14566


def _floci_joignable() -> bool:
    try:
        with socket.create_connection((FLOCI_HOST, FLOCI_PORT), timeout=2):
            return True
    except OSError:
        return False


def _exiger_floci() -> None:
    if _floci_joignable():
        return
    message = (
        f"Floci n'est pas joignable sur {FLOCI_HOST}:{FLOCI_PORT}. Ce lab en a "
        "besoin : l'instance heritee y est creee par `dsoxlab run`, qui demarre "
        f"le service tout seul.\n\nLancez `dsoxlab run {LAB_ID}` et faites votre "
        "`dsoxlab check` DEPUIS cette session."
    )
    if os.environ.get("LAB_WORKDIR"):
        pytest.fail(message)
    pytest.skip(message)


def _tf(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["terraform", *args], cwd=cwd or WORKDIR, capture_output=True, text=True,
        env=ENV, check=False,
    )


def _aws(*args: str) -> dict:
    proc = subprocess.run(
        ["aws", "--endpoint-url", ENDPOINT, *args],
        capture_output=True, text=True, env=ENV, check=False,
    )
    if proc.returncode != 0:
        pytest.fail(f"`aws {' '.join(args)}` a echoue :\n{proc.stderr[-600:]}")
    return json.loads(proc.stdout or "{}")


@pytest.fixture(scope="module", autouse=True)
def joue() -> Iterator[None]:
    exiger_workdir(WORKDIR, LAB_ID)
    _exiger_floci()
    yield
    # L'instance heritee n'appartient PAS a ce lab : elle preexistait. On ne la
    # detruit donc pas ici, `dsoxlab clean` s'en charge avec le service.


def _instances_vivantes() -> list[dict]:
    reservations = _aws(
        "ec2", "describe-instances",
        "--filters", "Name=instance-state-name,Values=running,pending",
    ).get("Reservations", [])
    return [i for r in reservations for i in r.get("Instances", [])]


def _tags(instance: dict) -> dict[str, str]:
    return {t["Key"]: t["Value"] for t in instance.get("Tags", [])}


def _etat() -> dict:
    proc = _tf("show", "-json")
    proc.check_returncode()
    return json.loads(proc.stdout)


def _gerees() -> dict[str, dict]:
    racine = _etat().get("values", {}).get("root_module", {})
    return {
        r["address"]: r for r in racine.get("resources", []) if r["mode"] == "managed"
    }


def _instance_heritee() -> dict:
    """L'instance creee hors Terraform, retrouvee par son tag."""
    candidates = [i for i in _instances_vivantes() if _tags(i).get("Name") == NOM_HERITE]
    assert candidates, (
        f"Aucune instance vivante ne porte le tag `Name = {NOM_HERITE}`. La mise "
        "en place du lab ne s'est pas faite : relancez `dsoxlab run`."
    )
    assert len(candidates) == 1, (
        f"{len(candidates)} instances portent le tag `Name = {NOM_HERITE}` : "
        f"{[i['InstanceId'] for i in candidates]}.\n\nL'objet reel a ete DUPLIQUE. "
        "C'est la signature d'un `moved` dont le `from` est faux : Terraform ne "
        "trouve rien a cette adresse, ne dit rien, et cree la nouvelle ressource."
    )
    return candidates[0]


# --------------------------------------------------------------------------
# 1. L'instance a ete IMPORTEE, pas recreee.
# --------------------------------------------------------------------------
def test_l_instance_du_state_est_celle_qui_preexistait() -> None:
    reelle = _instance_heritee()
    gerees = _gerees()

    assert ADRESSE_CIBLE in gerees, (
        f"Le state ne porte pas `{ADRESSE_CIBLE}`. Adresses gerees : "
        f"{sorted(gerees)}."
    )
    identifiant = gerees[ADRESSE_CIBLE]["values"]["id"]
    assert identifiant == reelle["InstanceId"], (
        f"Le state porte l'instance {identifiant!r}, alors que celle qui "
        f"preexistait est {reelle['InstanceId']!r}.\n\nUne instance a ete CREEE "
        "au lieu d'etre importee. L'objet d'origine est toujours la, et plus "
        "personne ne le gere."
    )


# --------------------------------------------------------------------------
# 2. L'import est FINI : un plan ordinaire ne propose plus rien.
# --------------------------------------------------------------------------
def test_la_configuration_est_fidele_a_l_objet_importe() -> None:
    plan = _tf("plan", "-detailed-exitcode", "-input=false", "-no-color")
    assert plan.returncode == 0, (
        f"`plan -detailed-exitcode` rend {plan.returncode}, attendu 0.\n\n"
        "C'est le VRAI critere de reussite d'un import : la ressource dans le "
        "state ne suffit pas, encore faut-il que la configuration lui "
        "corresponde. `-generate-config-out` produit des arguments que l'API "
        "rend et que la configuration n'a pas a porter : tant qu'ils sont la, "
        f"le plan n'est jamais vide.\n{plan.stdout[-1200:]}"
    )


# --------------------------------------------------------------------------
# 3. Le state colle au reel, autant que le reel colle au code.
# --------------------------------------------------------------------------
def test_plus_rien_a_rafraichir() -> None:
    plan = _tf("plan", "-refresh-only", "-detailed-exitcode", "-input=false",
               "-no-color")
    assert plan.returncode == 0, (
        f"`plan -refresh-only -detailed-exitcode` rend {plan.returncode}, "
        "attendu 0.\n\nLe premier plan prouve que le REEL colle au CODE ; "
        "celui-ci prouve que le STATE colle au REEL. Les deux doivent tomber "
        f"ensemble, sinon une derive subsiste.\n{plan.stdout[-1000:]}"
    )


# --------------------------------------------------------------------------
# 4. Le `moved` a ete REELLEMENT applique, et il est toujours la.
# --------------------------------------------------------------------------
def test_le_bloc_moved_existe_et_a_ete_applique(tmp_path: Path) -> None:
    """La preuve d'un `moved`, sans jamais ouvrir un `.tf`.

    On copie le repertoire, on remet dans le state COPIE l'ancienne adresse, et
    on demande un plan. Si le bloc `moved` est la et juste, Terraform reconnait
    le deplacement : le plan porte un `previous_address` et l'action `no-op`.

    S'il avait ete supprime, ou si son `from` etait faux, le meme plan
    annoncerait un `create` et un `delete`. Sans la moindre erreur : c'est ce
    silence qui rend le piege si couteux.
    """
    copie = tmp_path / "ancien-nom"
    shutil.copytree(WORKDIR, copie)

    renomme = _tf("state", "mv", ADRESSE_CIBLE, "aws_instance.legacy", cwd=copie)
    assert renomme.returncode == 0, (
        f"Impossible de remettre l'ancienne adresse dans le state copie :\n"
        f"{renomme.stderr[-600:]}"
    )

    plan = _tf("plan", "-input=false", "-no-color", "-out=retour.tfplan", cwd=copie)
    assert plan.returncode == 0, f"Le plan a echoue :\n{plan.stderr[-800:]}"

    montre = _tf("show", "-json", "retour.tfplan", cwd=copie)
    changements = json.loads(montre.stdout).get("resource_changes", [])

    deplacements = [c for c in changements if c.get("previous_address")]
    assert deplacements, (
        "Le plan ne porte aucun `previous_address` : Terraform n'a reconnu "
        "aucun deplacement.\n\nLe bloc `moved` a ete supprime, ou son `from` ne "
        "designe pas l'ancienne adresse. Le supprimer est un changement cassant "
        "pour quiconque part encore de l'ancien nom."
    )
    for deplacement in deplacements:
        assert deplacement["change"]["actions"] == ["no-op"], (
            f"Le deplacement de {deplacement.get('previous_address')} vers "
            f"{deplacement['address']} annonce "
            f"{deplacement['change']['actions']}, attendu `['no-op']`.\n\n"
            "Un renommage ne doit RIEN detruire ni creer : c'est le meme objet."
        )


# --------------------------------------------------------------------------
# 5. La derive a ete ACCEPTEE, pas ecrasee.
# --------------------------------------------------------------------------
def test_la_derive_a_ete_acceptee_et_le_code_aligne() -> None:
    reelle = _instance_heritee()
    owner_reel = _tags(reelle).get("Owner")

    assert owner_reel != OWNER_INITIAL, (
        f"Le tag `Owner` vaut encore {owner_reel!r} cote emulateur.\n\nLa derive "
        "a ete ECRASEE : un `apply` a remis la valeur du code par-dessus le "
        "changement manuel. C'est le reflexe que ce lab combat, et sur un vrai "
        "systeme il efface le travail de quelqu'un sans que personne ne le sache."
    )

    gerees = _gerees()
    owner_state = gerees[ADRESSE_CIBLE]["values"].get("tags", {}).get("Owner")
    assert owner_state == owner_reel, (
        f"Le state porte `Owner = {owner_state!r}` et l'emulateur "
        f"{owner_reel!r} : le state ne reflete pas la realite."
    )


# --------------------------------------------------------------------------
# 6. Les deux cotes : rien n'a ete cree, rien n'a ete detruit.
# --------------------------------------------------------------------------
def test_aucune_instance_supplementaire_n_a_ete_creee() -> None:
    """Le test qui donne son sens a tous les autres.

    Un import reussi, un renommage propre et une derive acceptee ont ceci en
    commun : l'objet reel n'a jamais bouge. Si une seule de ces trois etapes
    avait ete faite de travers, il y aurait ici deux instances au lieu d'une,
    ou une instance terminee.
    """
    vivantes = _instances_vivantes()
    assert len(vivantes) == 1, (
        f"{len(vivantes)} instances vivantes cote emulateur : "
        f"{[i['InstanceId'] for i in vivantes]}.\n\nUne seule est attendue, "
        "celle qui preexistait. Un import rate, un `moved` au `from` faux, ou "
        "un `destroy` malencontreux en laissent deux."
    )

    gerees = _gerees()
    assert set(gerees) == {ADRESSE_CIBLE}, (
        f"Le state gere {sorted(gerees)}, attendu la seule adresse "
        f"`{ADRESSE_CIBLE}`.\n\nL'ancienne adresse subsiste : le `moved` n'a pas "
        "ete applique, il a seulement ete planifie."
    )
    assert gerees[ADRESSE_CIBLE]["values"]["id"] == vivantes[0]["InstanceId"], (
        "Le state ne designe pas l'instance vivante."
    )
