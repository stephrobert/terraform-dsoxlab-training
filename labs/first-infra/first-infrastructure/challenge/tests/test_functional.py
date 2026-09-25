"""Tests fonctionnels du lab « premiere infrastructure, le cycle complet ».

Le cycle Terraform prouve sur une ressource REELLE, pas recite. Une seule
ressource, un volume libvirt cree vierge : aucune image cloud a telecharger,
et cela suffit a derouler `init`, `plan`, `apply`, `destroy`.

Aucun test ne relit le `.tf` de l'apprenant, aucun ne parse une sortie humaine.
Une seule contre-verification sort de Terraform, et c'est delibere : `virsh`
regarde l'hote directement, la ou le state ne fait que rapporter.

Formes MESUREES sur dmacvicar/libvirt 0.9.9 avant d'ecrire une assertion. La
branche 0.9 a REECRIT le schema, et rien de ce qui suit n'est vrai en 0.8 :

  0.8 :  size = 1073741824            format = "qcow2"
  0.9 :  capacity = 1 + capacity_unit target = { format = { type } }

C'est le piege du lab : `~> 0.8` n'interdit pas `0.9.x`, il autorise
l'increment du composant le plus a droite.

## Le nettoyage n'est pas negociable

Ce lab cree un objet sur la machine de l'apprenant, dans un pool `default` qui
porte peut-etre d'autres volumes que les siens. La fixture detruit donc en
sortie, QUOI QU'IL ARRIVE, y compris si tous les tests ont echoue avant. Un lab
qui laisse des traces sur l'hote est un lab qu'on n'ose plus rejouer.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "first-infra-first-infrastructure"

URI = "qemu:///system"
POOL = "default"
NOM_DU_VOLUME = "tf-lab-premiere.qcow2"
CAPACITE_ATTENDUE = 1024 * 1024 * 1024  # 1 GiB, en octets

# Le provider rend la valeur ET son unite, sans convertir. On ramene donc tout
# en octets pour comparer ce qui est comparable.
FACTEURS = {
    "B": 1,
    "KiB": 1024,
    "MiB": 1024 ** 2,
    "GiB": 1024 ** 3,
    "TiB": 1024 ** 4,
}


def _tf(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["terraform", *args], cwd=cwd or WORKDIR, capture_output=True, text=True,
        check=False,
    )


def _virsh(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["virsh", "-c", URI, *args], capture_output=True, text=True, check=False
    )


def _exiger_libvirt() -> None:
    """Skippe proprement si l'hote n'a pas de quoi jouer ce lab.

    Attention au controle : `systemctl is-active libvirtd` rend `inactive` sur
    une machine parfaitement fonctionnelle, parce que le service est active PAR
    SOCKET et ne demarre qu'a la demande. Mesure le 2026-09-24. On interroge
    donc le service par `virsh`, qui est la seule reponse qui ait un sens.
    """
    sonde = _virsh("pool-info", POOL)
    if sonde.returncode == 0:
        return
    message = (
        f"libvirt n'est pas joignable en `{URI}`, ou le pool `{POOL}` n'existe "
        "pas.\n\nCe lab en a besoin : il cree un volume reel. Verifiez que "
        "votre utilisateur appartient au groupe `libvirt` et que le pool "
        f"`{POOL}` est defini et demarre.\n{sonde.stderr[-400:]}"
    )
    import os

    if os.environ.get("LAB_WORKDIR"):
        pytest.fail(message)
    pytest.skip(message)


@pytest.fixture(scope="module")
def applique() -> Iterator[dict]:
    """Deroule le cycle, et detruit en sortie quoi qu'il arrive."""
    exiger_workdir(WORKDIR, LAB_ID)
    _exiger_libvirt()

    init = _tf("init", "-input=false", "-no-color")
    if init.returncode != 0:
        pytest.fail(f"`terraform init` a echoue.\n{init.stderr[-1500:]}")

    # Le plan est ENREGISTRE : c'est lui qu'on relira, et c'est lui qu'on
    # appliquera. Un `apply` qui replanifie n'applique pas ce qu'on a lu.
    plan = _tf("plan", "-input=false", "-no-color", "-out=cycle.tfplan")
    if plan.returncode != 0:
        pytest.fail(
            "`terraform plan` a echoue. La configuration est-elle ecrite, et la "
            f"contrainte de provider resserree ?\n{(plan.stderr or plan.stdout)[-1500:]}"
        )
    montre = _tf("show", "-json", "cycle.tfplan")
    montre.check_returncode()
    plan_json = json.loads(montre.stdout)

    app = _tf("apply", "-input=false", "-no-color", "cycle.tfplan")
    if app.returncode != 0:
        pytest.fail(f"`terraform apply` a echoue.\n{(app.stderr or app.stdout)[-1500:]}")

    try:
        yield plan_json
    finally:
        _tf("destroy", "-auto-approve", "-input=false", "-no-color")


def _etat() -> dict:
    proc = _tf("show", "-json")
    proc.check_returncode()
    return json.loads(proc.stdout)


def _gerees() -> list[dict]:
    racine = _etat().get("values", {}).get("root_module", {})
    return [r for r in racine.get("resources", []) if r["mode"] == "managed"]


def _sorties() -> dict:
    proc = _tf("output", "-json")
    proc.check_returncode()
    return json.loads(proc.stdout or "{}")


# --------------------------------------------------------------------------
# 1. Le plan annonce UNE creation, et rien d'autre.
# --------------------------------------------------------------------------
def test_le_plan_annonce_une_seule_creation(applique: dict) -> None:
    changements = applique.get("resource_changes", [])
    assert len(changements) == 1, (
        f"Le plan annonce {len(changements)} changements : "
        f"{[c['address'] for c in changements]}.\n\nUne seule ressource est "
        "demandee."
    )
    actions = changements[0]["change"]["actions"]
    assert actions == ["create"], (
        f"Le plan annonce {actions}, attendu `['create']`. Le repertoire "
        "devait partir sans state."
    )


# --------------------------------------------------------------------------
# 2. Le volume existe dans le state, avec les bonnes valeurs.
# --------------------------------------------------------------------------
def test_le_state_porte_un_volume_conforme(applique: dict) -> None:
    gerees = _gerees()
    assert len(gerees) == 1, (
        f"Le state gere {len(gerees)} ressources : "
        f"{[r['address'] for r in gerees]}. Une seule est attendue."
    )
    volume = gerees[0]
    assert volume["type"] == "libvirt_volume", (
        f"La ressource est de type {volume['type']!r}, attendu `libvirt_volume`."
    )

    valeurs = volume["values"]
    assert valeurs.get("name") == NOM_DU_VOLUME, (
        f"Le volume s'appelle {valeurs.get('name')!r}, attendu {NOM_DU_VOLUME!r}."
    )
    assert valeurs.get("pool") == POOL, (
        f"Le volume vit dans le pool {valeurs.get('pool')!r}, attendu {POOL!r}."
    )

    # Le provider NE convertit PAS en octets : il rend la valeur et l'unite
    # telles qu'elles ont ete declarees. Mesure le 2026-09-24, apres avoir
    # suppose l'inverse : `capacity = 1` avec `capacity_unit = "GiB"`.
    #
    # On compare donc la capacite EFFECTIVE, ce qui accepte toute ecriture
    # equivalente. `1 GiB` et `1024 MiB` designent le meme volume, et recaler
    # la seconde serait un faux negatif.
    capacite = valeurs.get("capacity")
    unite = valeurs.get("capacity_unit") or "B"
    assert capacite is not None, "Le volume ne declare aucune capacite."
    assert unite in FACTEURS, (
        f"L'unite {unite!r} n'est pas reconnue. Attendues : {sorted(FACTEURS)}."
    )
    effective = capacite * FACTEURS[unite]
    assert effective == CAPACITE_ATTENDUE, (
        f"La capacite vaut {capacite} {unite}, soit {effective} octets. "
        f"Attendu {CAPACITE_ATTENDUE} octets, c'est-a-dire 1 Gio.\n\nToute "
        "ecriture equivalente convient : `1 GiB` comme `1024 MiB`."
    )

    cible = valeurs.get("target") or {}
    format_ = (cible.get("format") or {}).get("type")
    assert format_ == "qcow2", (
        f"Le format vaut {format_!r}, attendu `qcow2`.\n\nEn 0.9, le format se "
        "declare dans `target = { format = { type } }`. L'argument `format` de "
        "la 0.8 n'existe plus : si votre contrainte de provider laisse flotter "
        "le mineur, vous ne savez pas quel schema vous ecrivez."
    )


# --------------------------------------------------------------------------
# 3. Le chemin est CALCULE, pas ecrit en dur.
# --------------------------------------------------------------------------
def test_la_sortie_reprend_le_chemin_du_state(applique: dict) -> None:
    sorties = _sorties()
    assert sorties, "Aucun output n'est declare."

    noms = sorted(sorties)
    assert len(noms) == 1, f"Un seul output est attendu, trouve : {noms}."
    sortie = sorties[noms[0]]

    assert sortie.get("sensitive") is not True, (
        "Le chemin d'un volume n'est pas un secret : le marquer sensible le "
        "masque sans rien proteger."
    )
    valeur = sortie.get("value")
    assert valeur, f"L'output `{noms[0]}` est vide."

    chemin_du_state = _gerees()[0]["values"].get("path")
    assert valeur == chemin_du_state, (
        f"L'output vaut {valeur!r}, le state porte {chemin_du_state!r}.\n\nLe "
        "chemin doit etre REPRIS de l'attribut de la ressource. Ecrit en dur, "
        "il ment le jour ou le pool change d'emplacement."
    )


# --------------------------------------------------------------------------
# 4. La contrainte de provider ne laisse plus flotter le schema.
# --------------------------------------------------------------------------
def test_la_contrainte_de_provider_ne_laisse_plus_flotter_le_schema(
    applique: dict, tmp_path: Path
) -> None:
    """Ce test a d'abord ete ecrit FAUX, et le sens « 0 » l'a dit aussitot.

    Premiere version : verifier que le verrou a retenu une version 0.9.x. Elle
    passait SANS AUCUN TRAVAIL, et pour une raison qui est justement la lecon du
    lab : `~> 0.8` autorise la 0.9, donc `init` installe 0.9.9 de toute facon.
    Le verrou porte alors la bonne version avec la mauvaise contrainte, et le
    piege reste entier.

    Ce qu'il faut lire est donc la CONTRAINTE, pas la version resolue. Elle
    figure dans `.terraform.lock.hcl` sous `constraints`, mais seulement si
    l'entree y a ete CREEE avec : un `init` lance avant la correction laisse un
    verrou sans elle, et rien ne l'y ajoute ensuite, pas meme `init -upgrade`.
    Mesure sur le lab terraform-vs-opentofu. On reconstruit donc le verrou dans
    une copie, ce qui rend la mesure independante de l'ordre de travail.
    """
    import re
    import shutil

    copie = tmp_path / "verrou"
    shutil.copytree(WORKDIR, copie)
    (copie / ".terraform.lock.hcl").unlink(missing_ok=True)
    init = _tf("init", "-input=false", "-no-color", cwd=copie)
    assert init.returncode == 0, (
        f"La reconstruction du verrou a echoue :\n{init.stderr[-1000:]}"
    )

    texte = (copie / ".terraform.lock.hcl").read_text(encoding="utf-8")
    bloc = re.search(
        r'provider\s+"[^"]*dmacvicar/libvirt"\s*\{(.*?)\n\}', texte, re.DOTALL
    )
    assert bloc, f"Le bloc du provider libvirt est illisible :\n{texte[:400]}"

    contrainte = re.search(r'constraints\s*=\s*"([^"]+)"', bloc.group(1))
    assert contrainte, (
        "Le verrou ne porte AUCUNE contrainte pour `dmacvicar/libvirt` : le "
        "provider a ete devine, pas declare."
    )
    declaree = contrainte.group(1)

    # `~> 0.8` a deux composants : c'est le MINEUR qui flotte, donc 0.9 passe.
    # `~> 0.9.0` en a trois : seul le correctif flotte, le schema est fige.
    assert not re.fullmatch(r"~>\s*\d+\.\d+", declaree), (
        f"La contrainte vaut {declaree!r}, et elle laisse flotter le MINEUR.\n\n"
        "L'operateur pessimiste incremente le composant le plus a droite de ce "
        "qui est ecrit : avec deux composants, `~> 0.8` accepte 0.8.x ET 0.9.x. "
        "Or la 0.9 a reecrit le schema des ressources. Laisser flotter le "
        "mineur, c'est laisser flotter le LANGAGE : votre code s'applique "
        "aujourd'hui et cassera chez le collegue dont le verrou a retenu "
        "l'autre serie.\n\nTrois composants figent le mineur."
    )

    version = re.search(r'version\s*=\s*"([^"]+)"', bloc.group(1))
    assert version, "Le verrou ne porte pas de version resolue."
    majeur, mineur = version.group(1).split(".")[:2]
    assert (majeur, mineur) == ("0", "9"), (
        f"Le verrou a retenu {version.group(1)}, et ce lab est ecrit pour la "
        f"serie 0.9.x. La contrainte {declaree!r} ne la designe pas."
    )


# --------------------------------------------------------------------------
# 5. Le reel confirme le state, vu d'ailleurs que par Terraform.
# --------------------------------------------------------------------------
def test_virsh_voit_le_volume_au_chemin_annonce(applique: dict) -> None:
    """La seule verification qui sort de Terraform, et c'est voulu.

    Le state RAPPORTE ce que le provider a bien voulu y ecrire. `virsh`
    interroge l'hote. Tant que les deux ne sont pas confrontes, on ne prouve
    que la coherence de Terraform avec lui-meme.
    """
    chemin = _sorties()[sorted(_sorties())[0]]["value"]

    liste = _virsh("vol-list", POOL)
    assert liste.returncode == 0, f"`virsh vol-list` a echoue :\n{liste.stderr[-400:]}"
    assert chemin in liste.stdout, (
        f"`virsh vol-list {POOL}` ne liste pas {chemin!r}.\n\nLe state annonce "
        "un volume que l'hote ne connait pas.\n{liste.stdout[-600:]}"
    )


# --------------------------------------------------------------------------
# 6. Les deux cotes : le cycle converge, ET le destroy ne laisse rien.
# --------------------------------------------------------------------------
def test_le_cycle_converge_puis_le_destroy_ne_laisse_rien(applique: dict) -> None:
    """Le dernier test derole la fin du cycle, et c'est lui qui le prouve.

    La convergence seule serait vraie de toute configuration appliquee. Ce qui
    compte ici, c'est qu'elle soit suivie d'un `destroy` qui ne laisse RIEN :
    ni dans le state, ni sur l'hote. Un lab qui laisse un volume derriere lui
    est un lab qu'on n'ose plus rejouer, et le pool `default` de l'apprenant
    porte peut-etre d'autres volumes que les siens.
    """
    stable = _tf("plan", "-detailed-exitcode", "-input=false", "-no-color")
    assert stable.returncode == 0, (
        f"`plan -detailed-exitcode` rend {stable.returncode} juste apres "
        f"l'apply, attendu 0.\n{stable.stdout[-1000:]}"
    )

    chemin = _sorties()[sorted(_sorties())[0]]["value"]

    detruit = _tf("destroy", "-auto-approve", "-input=false", "-no-color")
    assert detruit.returncode == 0, (
        f"`terraform destroy` a echoue.\n{(detruit.stderr or detruit.stdout)[-1500:]}"
    )

    assert not _gerees(), (
        f"Le state porte encore {[r['address'] for r in _gerees()]} apres le "
        "`destroy`."
    )

    liste = _virsh("vol-list", POOL)
    assert chemin not in liste.stdout, (
        f"`virsh vol-list {POOL}` liste encore {chemin!r} apres le `destroy`.\n\n"
        "Terraform a retire la ressource de son state sans que l'objet "
        "disparaisse de l'hote : c'est exactement le genre de residu qui "
        "s'accumule et qu'on ne remarque qu'une fois le disque plein."
    )
