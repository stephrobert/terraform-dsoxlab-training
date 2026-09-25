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

from conftest import exiger_workdir, workdir_lab

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
    message = (
        f"libvirt n'est pas joignable en `{URI}`. Ce lab cree un reseau virtuel "
        "reel : verifiez que votre utilisateur appartient au groupe `libvirt`."
        f"\n{sonde.stderr[-400:]}"
    )
    if os.environ.get("LAB_WORKDIR"):
        pytest.fail(message)
    pytest.skip(message)


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
        pytest.fail(f"`terraform init` a echoue.\n{init.stderr[-1500:]}")

    plan = _tf("plan", "-input=false", "-no-color", "-out=lecture.tfplan")
    if plan.returncode != 0:
        pytest.fail(
            "`terraform plan` a echoue. Des `???` subsistent-ils ?\n"
            f"{(plan.stderr or plan.stdout)[-1500:]}"
        )
    montre = _tf("show", "-json", "lecture.tfplan")
    montre.check_returncode()
    representation = json.loads(montre.stdout)

    app = _tf("apply", "-auto-approve", "-input=false", "-no-color")
    if app.returncode != 0:
        pytest.fail(f"`terraform apply` a echoue.\n{(app.stderr or app.stdout)[-1800:]}")

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
        f"{adresse} n'apparait pas dans la configuration. Adresses : "
        f"{[r.get('address') for r in _config(representation).get('resources', [])]}"
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
    assert RESEAU in gerees, (
        f"Le state ne porte pas `{RESEAU}`. Adresses gerees : {sorted(gerees)}."
    )

    xml = _virsh("net-dumpxml", NOM_DU_RESEAU)
    assert xml.returncode == 0, (
        f"`virsh net-dumpxml {NOM_DU_RESEAU}` a echoue : l'hote ne connait pas "
        f"ce reseau.\n{xml.stderr[-400:]}"
    )

    assert "<forward mode='nat'" in xml.stdout or 'mode="nat"' in xml.stdout, (
        "Le reseau n'est pas en mode NAT.\n\nUn reseau NAT donne aux machines "
        f"un acces sortant sans les exposer.\n{xml.stdout[:600]}"
    )
    assert PASSERELLE in xml.stdout, (
        f"La passerelle {PASSERELLE} n'apparait pas dans la definition du reseau."
    )
    for borne in ("10.77.0.100", "10.77.0.200"):
        assert borne in xml.stdout, (
            f"La borne DHCP {borne} n'apparait pas.\n\nLa plage doit aller de "
            ".100 a .200."
        )

    valeurs = gerees[RESEAU]["values"]
    assert valeurs.get("autostart") is False, (
        f"`autostart` vaut {valeurs.get('autostart')!r}, attendu `false`. Un "
        "reseau de lab n'a pas a redemarrer avec la machine de l'apprenant."
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
        assert nom in outputs, (
            f"L'output `{nom}` n'est pas declare. Presents : {sorted(outputs)}."
        )
        references = (outputs[nom].get("expression") or {}).get("references") or []
        assert any(r.startswith(RESEAU) for r in references), (
            f"L'output `{nom}` ne reference pas `{RESEAU}`.\nIl reference "
            f"{references}.\n\nIl lit sans doute une variable : le texte serait "
            "le meme, mais il rapporterait ce qu'on a DEMANDE et non ce que "
            "libvirt a RETENU."
        )


# --------------------------------------------------------------------------
# 3. Le coeur du lab : un `depends_on` la ou rien ne se reference.
# --------------------------------------------------------------------------
def test_le_rapport_declare_un_depends_on_vers_le_reseau(applique: dict) -> None:
    rapport = _ressource_configuree(applique, RAPPORT)
    declares = rapport.get("depends_on") or []
    assert RESEAU in declares, (
        f"`{RAPPORT}` ne declare aucun `depends_on` vers `{RESEAU}`. Il porte "
        f"{declares}.\n\nCe bloc consomme `var.nom_du_reseau`, une valeur connue "
        "avant tout apply : aucune expression ne le relie au reseau. Terraform "
        "construit son graphe a partir des references qu'il TROUVE, et il n'en "
        "trouve aucune. Les deux blocs sont donc independants a ses yeux, et il "
        "peut lancer le rapport en premier."
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
    assert RESEAU not in expressions, (
        f"Les expressions de `{RAPPORT}` mentionnent `{RESEAU}` :\n"
        f"{expressions[:400]}\n\nAvec une reference, l'arete existerait toute "
        "seule et le `depends_on` serait redondant. Le lab porte sur le cas "
        "inverse : le rapport doit consommer `var.nom_du_reseau`."
    )
    assert "provisioner" in json.dumps(rapport) or rapport.get("provisioners"), (
        f"`{RAPPORT}` ne declare aucun provisioner : il ne produit donc aucun "
        "rapport."
    )


# --------------------------------------------------------------------------
# 5. Le rapport contient ce que seul un reseau DEJA CREE peut fournir.
# --------------------------------------------------------------------------
def test_le_rapport_porte_ce_que_seul_un_reseau_existant_donne(
    applique: dict,
) -> None:
    chemin = WORKDIR / FICHIER_RAPPORT
    assert chemin.is_file(), (
        f"`{FICHIER_RAPPORT}` est absent. Le provisioner ne s'est pas execute, "
        "ou sa commande a echoue."
    )

    contenu = chemin.read_text(encoding="utf-8")
    assert contenu.strip(), (
        f"`{FICHIER_RAPPORT}` est VIDE.\n\nC'est exactement le symptome de la "
        "dependance manquante : `virsh net-dumpxml` s'est execute avant que le "
        "reseau existe, a echoue en silence, et la redirection a cree un "
        "fichier vide. Rien, dans la sortie de Terraform, ne l'a signale."
    )

    for atteste in (NOM_DU_RESEAU, PASSERELLE, "<uuid>"):
        assert atteste in contenu, (
            f"Le rapport ne contient pas {atteste!r}.\n\nUn UUID et une "
            "passerelle ne s'inventent pas : seul un reseau deja cree peut les "
            f"fournir.\nContenu :\n{contenu[:400]}"
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
    assert stable.returncode == 0, (
        f"`plan -detailed-exitcode` rend {stable.returncode}, attendu 0.\n"
        f"{stable.stdout[-1000:]}"
    )

    detruit = _tf("destroy", "-auto-approve", "-input=false", "-no-color")
    assert detruit.returncode == 0, (
        f"`terraform destroy` a echoue.\n{(detruit.stderr or detruit.stdout)[-1500:]}"
    )

    assert not _gerees(), (
        f"Le state porte encore {sorted(_gerees())} apres le `destroy`."
    )

    reste = _virsh("net-info", NOM_DU_RESEAU)
    assert reste.returncode != 0, (
        f"`virsh net-info {NOM_DU_RESEAU}` repond encore apres le `destroy` : "
        "le reseau survit a l'hote.\n\nTerraform l'a retire de son state sans "
        "que l'objet disparaisse, et le pont restera jusqu'au prochain "
        "redemarrage."
    )
