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

from conftest import exiger_workdir, message, workdir_lab

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
    explication = message(
        en=f"libvirt cannot be reached at `{URI}`, or the pool `{POOL}` does not "
        "exist.\n\nThis lab needs it: it creates a real volume. Check that "
        "your user belongs to the `libvirt` group and that the pool "
        f"`{POOL}` is defined and started.\n{sonde.stderr[-400:]}",
        fr=f"libvirt n'est pas joignable en `{URI}`, ou le pool `{POOL}` n'existe "
        "pas.\n\nCe lab en a besoin : il crée un volume réel. Vérifiez que "
        "votre utilisateur appartient au groupe `libvirt` et que le pool "
        f"`{POOL}` est défini et démarré.\n{sonde.stderr[-400:]}",
    )
    import os

    if os.environ.get("LAB_WORKDIR"):
        pytest.fail(explication)
    pytest.skip(explication)


@pytest.fixture(scope="module")
def applique() -> Iterator[dict]:
    """Deroule le cycle, et detruit en sortie quoi qu'il arrive."""
    exiger_workdir(WORKDIR, LAB_ID)
    _exiger_libvirt()

    init = _tf("init", "-input=false", "-no-color")
    if init.returncode != 0:
        pytest.fail(message(
            en=f"`terraform init` failed.\n{init.stderr[-1500:]}",
            fr=f"`terraform init` a échoué.\n{init.stderr[-1500:]}",
        ))

    # Le plan est ENREGISTRE : c'est lui qu'on relira, et c'est lui qu'on
    # appliquera. Un `apply` qui replanifie n'applique pas ce qu'on a lu.
    plan = _tf("plan", "-input=false", "-no-color", "-out=cycle.tfplan")
    if plan.returncode != 0:
        pytest.fail(
            message(
            en="`terraform plan` failed. Is the configuration written, and the "
            f"provider constraint tightened?\n{(plan.stderr or plan.stdout)[-1500:]}",
            fr="`terraform plan` a échoué. La configuration est-elle écrite, et la "
            f"contrainte de provider resserrée ?\n{(plan.stderr or plan.stdout)[-1500:]}",
        )
        )
    montre = _tf("show", "-json", "cycle.tfplan")
    montre.check_returncode()
    plan_json = json.loads(montre.stdout)

    app = _tf("apply", "-input=false", "-no-color", "cycle.tfplan")
    if app.returncode != 0:
        pytest.fail(message(
            en=f"`terraform apply` failed.\n{(app.stderr or app.stdout)[-1500:]}",
            fr=f"`terraform apply` a échoué.\n{(app.stderr or app.stdout)[-1500:]}",
        ))

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
    assert len(changements) == 1, message(
        en=f"The plan announces {len(changements)} changes: "
        f"{[c['address'] for c in changements]}.\n\nA single resource is "
        "asked for.",
        fr=f"Le plan annonce {len(changements)} changements : "
        f"{[c['address'] for c in changements]}.\n\nUne seule ressource est "
        "demandée.",
    )
    actions = changements[0]["change"]["actions"]
    assert actions == ["create"], message(
        en=f"The plan announces {actions}, expected `['create']`. The directory "
        "was supposed to start with no state.",
        fr=f"Le plan annonce {actions}, attendu `['create']`. Le répertoire "
        "devait partir sans state.",
    )


# --------------------------------------------------------------------------
# 2. Le volume existe dans le state, avec les bonnes valeurs.
# --------------------------------------------------------------------------
def test_le_state_porte_un_volume_conforme(applique: dict) -> None:
    gerees = _gerees()
    assert len(gerees) == 1, message(
        en=f"The state manages {len(gerees)} resources: "
        f"{[r['address'] for r in gerees]}. A single one is expected.",
        fr=f"Le state gère {len(gerees)} ressources : "
        f"{[r['address'] for r in gerees]}. Une seule est attendue.",
    )
    volume = gerees[0]
    assert volume["type"] == "libvirt_volume", message(
        en=f"The resource is of type {volume['type']!r}, expected `libvirt_volume`.",
        fr=f"La ressource est de type {volume['type']!r}, attendu `libvirt_volume`.",
    )

    valeurs = volume["values"]
    assert valeurs.get("name") == NOM_DU_VOLUME, message(
        en=f"The volume is named {valeurs.get('name')!r}, expected {NOM_DU_VOLUME!r}.",
        fr=f"Le volume s'appelle {valeurs.get('name')!r}, attendu {NOM_DU_VOLUME!r}.",
    )
    assert valeurs.get("pool") == POOL, message(
        en=f"The volume lives in pool {valeurs.get('pool')!r}, expected {POOL!r}.",
        fr=f"Le volume vit dans le pool {valeurs.get('pool')!r}, attendu {POOL!r}.",
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
    assert capacite is not None, message(
        en="The volume declares no capacity.",
        fr="Le volume ne déclare aucune capacité.",
    )
    assert unite in FACTEURS, message(
        en=f"The unit {unite!r} is not recognised. Expected: {sorted(FACTEURS)}.",
        fr=f"L'unité {unite!r} n'est pas reconnue. Attendues : {sorted(FACTEURS)}.",
    )
    effective = capacite * FACTEURS[unite]
    assert effective == CAPACITE_ATTENDUE, message(
        en=f"The capacity is {capacite} {unite}, that is {effective} bytes. "
        f"Expected {CAPACITE_ATTENDUE} bytes, that is 1 GiB.\n\nAny "
        "equivalent writing is fine: `1 GiB` as well as `1024 MiB`.",
        fr=f"La capacité vaut {capacite} {unite}, soit {effective} octets. "
        f"Attendu {CAPACITE_ATTENDUE} octets, c'est-à-dire 1 Gio.\n\nToute "
        "écriture équivalente convient : `1 GiB` comme `1024 MiB`.",
    )

    cible = valeurs.get("target") or {}
    format_ = (cible.get("format") or {}).get("type")
    assert format_ == "qcow2", message(
        en=f"The format is {format_!r}, expected `qcow2`.\n\nIn 0.9, the format is "
        "declared in `target = { format = { type } }`. The `format` argument of "
        "0.8 no longer exists: if your provider constraint lets the minor "
        "float, you do not know which schema you are writing.",
        fr=f"Le format vaut {format_!r}, attendu `qcow2`.\n\nEn 0.9, le format se "
        "déclare dans `target = { format = { type } }`. L'argument `format` de "
        "la 0.8 n'existe plus : si votre contrainte de provider laisse flotter "
        "le mineur, vous ne savez pas quel schéma vous écrivez.",
    )


# --------------------------------------------------------------------------
# 3. Le chemin est CALCULE, pas ecrit en dur.
# --------------------------------------------------------------------------
def test_la_sortie_reprend_le_chemin_du_state(applique: dict) -> None:
    sorties = _sorties()
    assert sorties, message(
        en="No output is declared.",
        fr="Aucun output n'est déclaré.",
    )

    noms = sorted(sorties)
    assert len(noms) == 1, message(
        en=f"A single output is expected, found: {noms}.",
        fr=f"Un seul output est attendu, trouvé : {noms}.",
    )
    sortie = sorties[noms[0]]

    assert sortie.get("sensitive") is not True, message(
        en="A volume's path is not a secret: marking it sensitive hides it "
        "without protecting anything.",
        fr="Le chemin d'un volume n'est pas un secret : le marquer sensible le "
        "masque sans rien protéger.",
    )
    valeur = sortie.get("value")
    assert valeur, message(
        en=f"The output `{noms[0]}` is empty.",
        fr=f"L'output `{noms[0]}` est vide.",
    )

    chemin_du_state = _gerees()[0]["values"].get("path")
    assert valeur == chemin_du_state, message(
        en=f"The output is {valeur!r}, the state carries {chemin_du_state!r}.\n\nThe "
        "path must be TAKEN from the resource's attribute. Written by hand, "
        "it lies the day the pool moves.",
        fr=f"L'output vaut {valeur!r}, le state porte {chemin_du_state!r}.\n\nLe "
        "chemin doit être REPRIS de l'attribut de la ressource. Écrit en dur, "
        "il ment le jour où le pool change d'emplacement.",
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
    assert init.returncode == 0, message(
        en=f"Rebuilding the lock failed:\n{init.stderr[-1000:]}",
        fr=f"La reconstruction du verrou a échoué :\n{init.stderr[-1000:]}",
    )

    texte = (copie / ".terraform.lock.hcl").read_text(encoding="utf-8")
    bloc = re.search(
        r'provider\s+"[^"]*dmacvicar/libvirt"\s*\{(.*?)\n\}', texte, re.DOTALL
    )
    assert bloc, message(
        en=f"The libvirt provider block cannot be read:\n{texte[:400]}",
        fr=f"Le bloc du provider libvirt est illisible :\n{texte[:400]}",
    )

    contrainte = re.search(r'constraints\s*=\s*"([^"]+)"', bloc.group(1))
    assert contrainte, message(
        en="The lock carries NO constraint for `dmacvicar/libvirt`: the "
        "provider was guessed, not declared.",
        fr="Le verrou ne porte AUCUNE contrainte pour `dmacvicar/libvirt` : le "
        "provider a été deviné, pas déclaré.",
    )
    declaree = contrainte.group(1)

    # `~> 0.8` a deux composants : c'est le MINEUR qui flotte, donc 0.9 passe.
    # `~> 0.9.0` en a trois : seul le correctif flotte, le schema est fige.
    assert not re.fullmatch(r"~>\s*\d+\.\d+", declaree), message(
        en=f"The constraint is {declaree!r}, and it lets the MINOR float.\n\n"
        "The pessimistic operator increments the rightmost component of what "
        "is written: with two components, `~> 0.8` accepts 0.8.x AND 0.9.x. "
        "But 0.9 rewrote the resources' schema. Letting the minor float "
        "means letting the LANGUAGE float: your code applies "
        "today and will break on the machine of the colleague whose lock kept "
        "the other series.\n\nThree components freeze the minor.",
        fr=f"La contrainte vaut {declaree!r}, et elle laisse flotter le MINEUR.\n\n"
        "L'opérateur pessimiste incrémente le composant le plus à droite de ce "
        "qui est écrit : avec deux composants, `~> 0.8` accepte 0.8.x ET 0.9.x. "
        "Or la 0.9 a réécrit le schéma des ressources. Laisser flotter le "
        "mineur, c'est laisser flotter le LANGAGE : votre code s'applique "
        "aujourd'hui et cassera chez le collègue dont le verrou a retenu "
        "l'autre série.\n\nTrois composants figent le mineur.",
    )

    version = re.search(r'version\s*=\s*"([^"]+)"', bloc.group(1))
    assert version, message(
        en="The lock carries no resolved version.",
        fr="Le verrou ne porte pas de version résolue.",
    )
    majeur, mineur = version.group(1).split(".")[:2]
    assert (majeur, mineur) == ("0", "9"), message(
        en=f"The lock kept {version.group(1)}, and this lab is written for the "
        f"0.9.x series. The constraint {declaree!r} does not name it.",
        fr=f"Le verrou a retenu {version.group(1)}, et ce lab est écrit pour la "
        f"série 0.9.x. La contrainte {declaree!r} ne la désigne pas.",
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
    assert liste.returncode == 0, message(
        en=f"`virsh vol-list` failed:\n{liste.stderr[-400:]}",
        fr=f"`virsh vol-list` a échoué :\n{liste.stderr[-400:]}",
    )
    assert chemin in liste.stdout, message(
        en=f"`virsh vol-list {POOL}` does not list {chemin!r}.\n\nThe state announces "
        "a volume the host does not know about.\n{liste.stdout[-600:]}",
        fr=f"`virsh vol-list {POOL}` ne liste pas {chemin!r}.\n\nLe state annonce "
        "un volume que l'hôte ne connaît pas.\n{liste.stdout[-600:]}",
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
    assert stable.returncode == 0, message(
        en=f"`plan -detailed-exitcode` returns {stable.returncode} right after "
        f"the apply, expected 0.\n{stable.stdout[-1000:]}",
        fr=f"`plan -detailed-exitcode` rend {stable.returncode} juste après "
        f"l'apply, attendu 0.\n{stable.stdout[-1000:]}",
    )

    chemin = _sorties()[sorted(_sorties())[0]]["value"]

    detruit = _tf("destroy", "-auto-approve", "-input=false", "-no-color")
    assert detruit.returncode == 0, message(
        en=f"`terraform destroy` failed.\n{(detruit.stderr or detruit.stdout)[-1500:]}",
        fr=f"`terraform destroy` a échoué.\n{(detruit.stderr or detruit.stdout)[-1500:]}",
    )

    assert not _gerees(), message(
        en=f"The state still carries {[r['address'] for r in _gerees()]} after the "
        "`destroy`.",
        fr=f"Le state porte encore {[r['address'] for r in _gerees()]} après le "
        "`destroy`.",
    )

    liste = _virsh("vol-list", POOL)
    assert chemin not in liste.stdout, message(
        en=f"`virsh vol-list {POOL}` still lists {chemin!r} after the `destroy`.\n\n"
        "Terraform removed the resource from its state without the object "
        "disappearing from the host: that is exactly the kind of leftover that "
        "piles up and is only noticed once the disk is full.",
        fr=f"`virsh vol-list {POOL}` liste encore {chemin!r} après le `destroy`.\n\n"
        "Terraform a retiré la ressource de son state sans que l'objet "
        "disparaisse de l'hôte : c'est exactement le genre de résidu qui "
        "s'accumule et qu'on ne remarque qu'une fois le disque plein.",
    )
