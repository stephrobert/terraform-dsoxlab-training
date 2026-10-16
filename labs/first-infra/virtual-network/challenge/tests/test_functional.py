"""Tests fonctionnels du lab « la dependance que Terraform ne peut pas deviner ».

Terraform construit son graphe a partir des REFERENCES qu'il trouve dans les
expressions. Neuf fois sur dix, un `depends_on` ecrit a la main signale une
reference manquante : il suffit de referencer l'attribut pour que l'arete
apparaisse toute seule, et le meta-argument devient un pansement.

Ce lab porte sur la dixieme fois. Le rapport consomme `var.nom_du_reseau`, une
valeur connue avant tout apply : AUCUNE expression ne le relie au reseau.
Terraform est donc libre d'executer les deux blocs dans n'importe quel ordre, et
il le fait. Sans `depends_on`, le rapport sort vide une fois sur deux, sans la
moindre erreur.

Aucun test ne relit les `.tf` de l'apprenant. La representation de la
configuration est lue dans le plan converti en JSON, ou Terraform expose
lui-meme ce qu'il a compris : les `references` de chaque output, et le
`depends_on` de chaque ressource.

Formes MESUREES avant d'ecrire une assertion :

  configuration.root_module.resources[].depends_on  ->  ['libvirt_network.lab']
  outputs.nom_du_reseau.expression.references       ->  ['libvirt_network.lab.name', ...]
"""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, message, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "first-infra-virtual-network"

URI = "qemu:///system"
RESEAU = "libvirt_network.lab"
RAPPORT = "null_resource.rapport"
NOM_DU_RESEAU = "tf-lab-reseau"
PASSERELLE = "10.77.0.1"
FICHIER_RAPPORT = "rapport.xml"


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
    """`systemctl is-active libvirtd` ment : le service est active PAR SOCKET."""
    sonde = _virsh("net-list", "--all")
    if sonde.returncode == 0:
        return
    explication = message(
        en=f"libvirt cannot be reached at `{URI}`. This lab creates a real virtual "
        "network: check that your user belongs to the `libvirt` group."
        f"\n{sonde.stderr[-400:]}",
        fr=f"libvirt n'est pas joignable en `{URI}`. Ce lab crée un réseau virtuel "
            "réel : vérifiez que votre utilisateur appartient au groupe `libvirt`."
            f"\n{sonde.stderr[-400:]}",
    )
    if os.environ.get("LAB_WORKDIR"):
        pytest.fail(explication)
    pytest.skip(explication)


@pytest.fixture(scope="module")
def applique() -> Iterator[dict]:
    """Applique, et rend la REPRESENTATION de la configuration.

    Le plan est pris avant l'apply : c'est lui qui porte
    `configuration.root_module`, ou Terraform expose ce qu'il a compris du code.
    """
    exiger_workdir(WORKDIR, LAB_ID)
    _exiger_libvirt()

    init = _tf("init", "-input=false", "-no-color")
    if init.returncode != 0:
        pytest.fail(message(
            en=f"`terraform init` failed.\n{init.stderr[-1500:]}",
            fr=f"`terraform init` a échoué.\n{init.stderr[-1500:]}",
        ))

    plan = _tf("plan", "-input=false", "-no-color", "-out=lecture.tfplan")
    if plan.returncode != 0:
        pytest.fail(
            message(
            en="`terraform plan` failed. Are there leftover `???`?\n"
            f"{(plan.stderr or plan.stdout)[-1500:]}",
            fr="`terraform plan` a échoué. Des `???` subsistent-ils ?\n"
            f"{(plan.stderr or plan.stdout)[-1500:]}",
        )
        )
    montre = _tf("show", "-json", "lecture.tfplan")
    montre.check_returncode()
    representation = json.loads(montre.stdout)

    app = _tf("apply", "-auto-approve", "-input=false", "-no-color")
    if app.returncode != 0:
        pytest.fail(message(
            en=f"`terraform apply` failed.\n{(app.stderr or app.stdout)[-1800:]}",
            fr=f"`terraform apply` a échoué.\n{(app.stderr or app.stdout)[-1800:]}",
        ))

    try:
        yield representation
    finally:
        # Un reseau libvirt laisse derriere soi occupe un pont et une plage
        # d'adresses sur la machine de l'apprenant. On detruit quoi qu'il arrive.
        _tf("destroy", "-auto-approve", "-input=false", "-no-color")


def _config(representation: dict) -> dict:
    return representation.get("configuration", {}).get("root_module", {})


def _ressource_configuree(representation: dict, adresse: str) -> dict:
    for r in _config(representation).get("resources", []):
        if r.get("address") == adresse:
            return r
    pytest.fail(
        message(
        en=f"{adresse} does not appear in the configuration. Addresses: "
        f"{[r.get('address') for r in _config(representation).get('resources', [])]}",
        fr=f"{adresse} n'apparaît pas dans la configuration. Adresses : "
        f"{[r.get('address') for r in _config(representation).get('resources', [])]}",
    )
    )


def _etat() -> dict:
    proc = _tf("show", "-json")
    proc.check_returncode()
    return json.loads(proc.stdout)


def _gerees() -> dict[str, dict]:
    racine = _etat().get("values", {}).get("root_module", {})
    return {
        r["address"]: r for r in racine.get("resources", []) if r["mode"] == "managed"
    }


def _sorties() -> dict:
    proc = _tf("output", "-json")
    proc.check_returncode()
    return json.loads(proc.stdout or "{}")


# --------------------------------------------------------------------------
# 1. Le reseau existe cote libvirt, avec ce qu'on lui a demande.
# --------------------------------------------------------------------------
def test_le_reseau_nat_existe_avec_sa_plage_dhcp(applique: dict) -> None:
    gerees = _gerees()
    assert RESEAU in gerees, message(
        en=f"The state does not carry `{RESEAU}`. Managed addresses: {sorted(gerees)}.",
        fr=f"Le state ne porte pas `{RESEAU}`. Adresses gérées : {sorted(gerees)}.",
    )

    xml = _virsh("net-dumpxml", NOM_DU_RESEAU)
    assert xml.returncode == 0, message(
        en=f"`virsh net-dumpxml {NOM_DU_RESEAU}` failed: the host does not know "
        f"that network.\n{xml.stderr[-400:]}",
        fr=f"`virsh net-dumpxml {NOM_DU_RESEAU}` a échoué : l'hôte ne connaît pas "
        f"ce réseau.\n{xml.stderr[-400:]}",
    )

    assert "<forward mode='nat'" in xml.stdout or 'mode="nat"' in xml.stdout, message(
        en="The network is not in NAT mode.\n\nA NAT network gives the machines "
        f"outbound access without exposing them.\n{xml.stdout[:600]}",
        fr="Le réseau n'est pas en mode NAT.\n\nUn réseau NAT donne aux machines "
        f"un accès sortant sans les exposer.\n{xml.stdout[:600]}",
    )
    assert PASSERELLE in xml.stdout, message(
        en=f"The gateway {PASSERELLE} does not appear in the network's definition.",
        fr=f"La passerelle {PASSERELLE} n'apparaît pas dans la définition du réseau.",
    )
    for borne in ("10.77.0.100", "10.77.0.200"):
        assert borne in xml.stdout, message(
            en=f"The DHCP bound {borne} does not appear.\n\nThe range must go from "
            ".100 to .200.",
            fr=f"La borne DHCP {borne} n'apparaît pas.\n\nLa plage doit aller de "
            ".100 à .200.",
        )

    valeurs = gerees[RESEAU]["values"]
    assert valeurs.get("autostart") is False, message(
        en=f"`autostart` is {valeurs.get('autostart')!r}, expected `false`. A "
        "lab network has no business restarting with the learner's machine.",
        fr=f"`autostart` vaut {valeurs.get('autostart')!r}, attendu `false`. Un "
        "réseau de lab n'a pas à redémarrer avec la machine de l'apprenant.",
    )


# --------------------------------------------------------------------------
# 2. Les outputs REFERENCENT la ressource, ils ne recopient pas les variables.
# --------------------------------------------------------------------------
def test_les_outputs_referencent_la_ressource_et_pas_les_variables(
    applique: dict,
) -> None:
    """Le texte produit serait identique, et la difference est ailleurs.

    Les variables portent deja le nom et la passerelle : un output qui les lit
    rendrait exactement la meme chaine. Mais il n'apprendrait RIEN a Terraform,
    et ne prouverait rien a personne : il rapporterait ce qu'on a demande, pas
    ce que libvirt a retenu.

    Une reference, elle, cree une arete dans le graphe, et Terraform l'expose
    dans `configuration.root_module.outputs[].expression.references`.
    """
    outputs = _config(applique).get("outputs") or {}
    for nom in ("nom_du_reseau", "passerelle"):
        assert nom in outputs, message(
            en=f"The output `{nom}` is not declared. Present: {sorted(outputs)}.",
            fr=f"L'output `{nom}` n'est pas déclaré. Présents : {sorted(outputs)}.",
        )
        references = (outputs[nom].get("expression") or {}).get("references") or []
        assert any(r.startswith(RESEAU) for r in references), message(
            en=f"The output `{nom}` does not reference `{RESEAU}`.\nIt references "
            f"{references}.\n\nIt probably reads a variable: the text would be "
            "the same, but it would report what was ASKED FOR and not what "
            "libvirt actually KEPT.",
            fr=f"L'output `{nom}` ne référence pas `{RESEAU}`.\nIl référence "
            f"{references}.\n\nIl lit sans doute une variable : le texte serait "
            "le même, mais il rapporterait ce qu'on a DEMANDÉ et non ce que "
            "libvirt a RETENU.",
        )


# --------------------------------------------------------------------------
# 3. Le coeur du lab : un `depends_on` la ou rien ne se reference.
# --------------------------------------------------------------------------
def test_le_rapport_declare_un_depends_on_vers_le_reseau(applique: dict) -> None:
    rapport = _ressource_configuree(applique, RAPPORT)
    declares = rapport.get("depends_on") or []
    assert RESEAU in declares, message(
        en=f"`{RAPPORT}` declares no `depends_on` towards `{RESEAU}`. It carries "
        f"{declares}.\n\nThat block consumes `var.nom_du_reseau`, a value known "
        "before any apply: no expression ties it to the network. Terraform "
        "builds its graph from the references it FINDS, and it finds "
        "none. The two blocks are therefore independent in its eyes, and it "
        "may start the report first.",
        fr=f"`{RAPPORT}` ne déclare aucun `depends_on` vers `{RESEAU}`. Il porte "
        f"{declares}.\n\nCe bloc consomme `var.nom_du_reseau`, une valeur connue "
        "avant tout apply : aucune expression ne le relie au réseau. Terraform "
        "construit son graphe à partir des références qu'il TROUVE, et il n'en "
        "trouve aucune. Les deux blocs sont donc indépendants à ses yeux, et il "
        "peut lancer le rapport en premier.",
    )


# --------------------------------------------------------------------------
# 4. Et ce `depends_on` est bien la SEULE chose qui les relie.
# --------------------------------------------------------------------------
def test_le_rapport_ne_reference_le_reseau_nulle_part_ailleurs(
    applique: dict,
) -> None:
    """Le controle qui donne son sens au precedent.

    Un `depends_on` pose a cote d'une reference ne prouve rien : l'arete
    existerait de toute facon, et le meta-argument serait le pansement habituel.

    Ce qui fait la valeur du lab, c'est qu'il n'y a RIEN d'autre. On verifie
    donc que les expressions du bloc ne mentionnent le reseau nulle part.
    """
    rapport = _ressource_configuree(applique, RAPPORT)
    expressions = json.dumps(rapport.get("expressions") or {})
    assert RESEAU not in expressions, message(
        en=f"The expressions of `{RAPPORT}` do mention `{RESEAU}`:\n"
        f"{expressions[:400]}\n\nWith a reference, the edge would exist on its "
        "own and the `depends_on` would be redundant. The lab is about the "
        "opposite case: the report must consume `var.nom_du_reseau`.",
        fr=f"Les expressions de `{RAPPORT}` mentionnent `{RESEAU}` :\n"
        f"{expressions[:400]}\n\nAvec une référence, l'arête existerait toute "
        "seule et le `depends_on` serait redondant. Le lab porte sur le cas "
        "inverse : le rapport doit consommer `var.nom_du_reseau`.",
    )
    assert "provisioner" in json.dumps(rapport) or rapport.get("provisioners"), message(
        en=f"`{RAPPORT}` declares no provisioner: it therefore produces no "
        "report.",
        fr=f"`{RAPPORT}` ne déclare aucun provisioner : il ne produit donc aucun "
        "rapport.",
    )


# --------------------------------------------------------------------------
# 5. Le rapport contient ce que seul un reseau DEJA CREE peut fournir.
# --------------------------------------------------------------------------
def test_le_rapport_porte_ce_que_seul_un_reseau_existant_donne(
    applique: dict,
) -> None:
    chemin = WORKDIR / FICHIER_RAPPORT
    assert chemin.is_file(), message(
        en=f"`{FICHIER_RAPPORT}` is missing. The provisioner did not run, "
        "or its command failed.",
        fr=f"`{FICHIER_RAPPORT}` est absent. Le provisioner ne s'est pas exécuté, "
        "ou sa commande a échoué.",
    )

    contenu = chemin.read_text(encoding="utf-8")
    assert contenu.strip(), message(
        en=f"`{FICHIER_RAPPORT}` is EMPTY.\n\nThat is exactly the symptom of the "
        "missing dependency: `virsh net-dumpxml` ran before the "
        "network existed, failed silently, and the redirection created an "
        "empty file. Nothing in Terraform's output reported it.",
        fr=f"`{FICHIER_RAPPORT}` est VIDE.\n\nC'est exactement le symptôme de la "
        "dépendance manquante : `virsh net-dumpxml` s'est exécuté avant que le "
        "réseau existe, a échoué en silence, et la redirection a créé un "
        "fichier vide. Rien, dans la sortie de Terraform, ne l'a signalé.",
    )

    for atteste in (NOM_DU_RESEAU, PASSERELLE, "<uuid>"):
        assert atteste in contenu, message(
            en=f"The report does not contain {atteste!r}.\n\nA UUID and a "
            "gateway are not invented: only a network that already exists can "
            f"provide them.\nContents:\n{contenu[:400]}",
            fr=f"Le rapport ne contient pas {atteste!r}.\n\nUn UUID et une "
            "passerelle ne s'inventent pas : seul un réseau déjà créé peut les "
            f"fournir.\nContenu :\n{contenu[:400]}",
        )


# --------------------------------------------------------------------------
# 6. Les deux cotes : la convergence, et ce que le destroy ne laisse pas.
# --------------------------------------------------------------------------
def test_la_configuration_converge_puis_le_destroy_ne_laisse_rien(
    applique: dict,
) -> None:
    """La convergence seule serait vraie de toute configuration appliquee.

    Ce qui compte est qu'elle soit suivie d'un `destroy` qui ne laisse rien, ni
    dans le state ni chez libvirt. Un reseau oublie occupe un pont et une plage
    d'adresses, et c'est le lab suivant qui en paierait le prix.
    """
    stable = _tf("plan", "-detailed-exitcode", "-input=false", "-no-color")
    assert stable.returncode == 0, message(
        en=f"`plan -detailed-exitcode` returns {stable.returncode}, expected 0.\n"
        f"{stable.stdout[-1000:]}",
        fr=f"`plan -detailed-exitcode` rend {stable.returncode}, attendu 0.\n"
        f"{stable.stdout[-1000:]}",
    )

    detruit = _tf("destroy", "-auto-approve", "-input=false", "-no-color")
    assert detruit.returncode == 0, message(
        en=f"`terraform destroy` failed.\n{(detruit.stderr or detruit.stdout)[-1500:]}",
        fr=f"`terraform destroy` a échoué.\n{(detruit.stderr or detruit.stdout)[-1500:]}",
    )

    assert not _gerees(), message(
        en=f"The state still carries {sorted(_gerees())} after the `destroy`.",
        fr=f"Le state porte encore {sorted(_gerees())} après le `destroy`.",
    )

    reste = _virsh("net-info", NOM_DU_RESEAU)
    assert reste.returncode != 0, message(
        en=f"`virsh net-info {NOM_DU_RESEAU}` still answers after the `destroy`: "
        "the network outlives the host.\n\nTerraform removed it from its state without "
        "the object disappearing, and the bridge will stay until the next "
        "reboot.",
        fr=f"`virsh net-info {NOM_DU_RESEAU}` répond encore après le `destroy` : "
        "le réseau survit à l'hôte.\n\nTerraform l'a retiré de son state sans "
        "que l'objet disparaisse, et le pont restera jusqu'au prochain "
        "redémarrage.",
    )
