"""Tests fonctionnels du lab « mise a jour en place ou remplacement ».

Sur une machine virtuelle, certains attributs se modifient en place et d'autres
detruisent puis recreent la machine. Le plan le dit AVANT l'apply, a condition
de savoir ou regarder.

Ce lab provisionne une VRAIE VM : un domaine qui demarre sur une image cloud en
copie sur ecriture. Le disque ne porte que les blocs modifies, ce qui permet de
recreer une machine en une seconde plutot que de recopier 600 Mio.

Formes MESUREES sur dmacvicar/libvirt 0.9.9 avant d'ecrire une assertion :

  memory  -> ['update']            replace_paths = None
  vcpu    -> ['update']            replace_paths = None
  name    -> ['delete', 'create']  replace_paths = [['name']]

## Comment on prouve qu'une VM BOOTE

Une machine qui ne trouve aucun disque bootable est `running` elle aussi :
l'etat libvirt ne prouve donc rien. Ce qui distingue les deux est le TEMPS CPU.
Mesure : 0,3 s pour un domaine sans OS, 7,1 s pour le meme avec l'image cloud.
Le seuil retenu est volontairement bas, pour ne pas recaler une machine lente.

Le bail DHCP aurait ete une preuve plus directe, et il a ete ecarte : une image
cloud sans cloud-init attend ses metadonnees, et le bail peut ne jamais venir.
Un test qui en depend recale un travail juste selon l'humeur du reseau.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "first-infra-vm-libvirt"

URI = "qemu:///system"
POOL = "default"
NOM_DE_LA_VM = "tf-lab-vm"
# `/var/tmp` et non `/var/lib/libvirt/images`, qui exige les droits root, ni
# `/tmp`, vide au redemarrage : une image de 600 Mio ne se retelecharge pas a
# chaque session. Le repertoire doit rester lisible par qemu, qui tourne sous un
# autre utilisateur que l'apprenant.
IMAGE_DE_BASE = "/var/tmp/dsoxlab-images/noble-server-cloudimg-amd64.img"  # noqa: S108

# Une VM qui boote consomme des SECONDES de CPU ; une VM sans disque bootable
# reste sous la seconde. Le seuil est bas exprès : on veut distinguer les deux
# cas, pas mesurer la vitesse du poste.
SECONDES_CPU_MINIMUM = 2.0
ATTENTE_MAXIMUM = 90


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

    `systemctl is-active libvirtd` rend `inactive` sur une machine parfaitement
    fonctionnelle, le service etant active PAR SOCKET : on interroge donc
    `virsh`, seule reponse qui ait un sens.
    """
    manques = []
    if _virsh("pool-info", POOL).returncode != 0:
        manques.append(f"le pool `{POOL}` n'est pas utilisable en `{URI}`")
    if _virsh("net-info", "default").returncode != 0:
        manques.append("le reseau libvirt `default` n'est pas defini")
    if not Path(IMAGE_DE_BASE).is_file():
        manques.append(
            f"l'image cloud `{IMAGE_DE_BASE}` est absente. Telechargez-la :\n"
            "    mkdir -p /var/tmp/dsoxlab-images && curl -fsSL -o "
            f"{IMAGE_DE_BASE} \\\n"
            "      https://cloud-images.ubuntu.com/noble/current/"
            "noble-server-cloudimg-amd64.img"
        )
    if not manques:
        return

    message = (
        "Ce lab provisionne une VRAIE machine virtuelle, et il manque de quoi le "
        "faire :\n  - " + "\n  - ".join(manques)
    )
    if os.environ.get("LAB_WORKDIR"):
        pytest.fail(message)
    pytest.skip(message)


def _temps_cpu(domaine: str) -> float:
    """Secondes de CPU consommees par le domaine, lues chez libvirt."""
    info = _virsh("dominfo", domaine)
    if info.returncode != 0:
        return 0.0
    for ligne in info.stdout.splitlines():
        if "CPU time" in ligne:
            brut = ligne.split(":", 1)[1].strip().rstrip("s")
            return float(brut.replace(",", "."))
    return 0.0


@pytest.fixture(scope="module")
def applique() -> Iterator[None]:
    exiger_workdir(WORKDIR, LAB_ID)
    _exiger_libvirt()

    init = _tf("init", "-input=false", "-no-color")
    if init.returncode != 0:
        pytest.fail(f"`terraform init` a echoue.\n{init.stderr[-1500:]}")

    app = _tf("apply", "-auto-approve", "-input=false", "-no-color")
    if app.returncode != 0:
        pytest.fail(
            "`terraform apply` a echoue. Des `???` subsistent-ils ?\n"
            f"{(app.stderr or app.stdout)[-1800:]}"
        )
    try:
        yield
    finally:
        # Une VM et un volume laisses derriere soi occupent de la memoire et du
        # disque sur la machine de l'apprenant. On detruit quoi qu'il arrive.
        _tf("destroy", "-auto-approve", "-input=false", "-no-color")


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


def _plan_avec(variable: str, valeur: str, cwd: Path | None = None) -> dict:
    """Le plan qu'un changement produirait, SANS l'appliquer."""
    rep = cwd or WORKDIR
    produit = _tf(
        "plan", "-input=false", "-no-color", "-var", f"{variable}={valeur}",
        "-out=essai.tfplan", cwd=rep,
    )
    assert produit.returncode == 0, (
        f"Le plan avec {variable}={valeur} a echoue :\n"
        f"{(produit.stderr or produit.stdout)[-1200:]}"
    )
    montre = _tf("show", "-json", "essai.tfplan", cwd=rep)
    montre.check_returncode()
    return json.loads(montre.stdout)


def _actions(plan: dict, adresse: str) -> list[str] | None:
    for c in plan.get("resource_changes", []):
        if c["address"] == adresse:
            return c["change"]["actions"]
    return None


# --------------------------------------------------------------------------
# 1. Le provider est fige sur la serie dont le code utilise le schema.
# --------------------------------------------------------------------------
def test_le_verrou_fige_la_serie_du_schema(applique: None, tmp_path: Path) -> None:
    import re

    copie = tmp_path / "verrou"
    shutil.copytree(WORKDIR, copie)
    (copie / ".terraform.lock.hcl").unlink(missing_ok=True)
    init = _tf("init", "-input=false", "-no-color", cwd=copie)
    assert init.returncode == 0, f"Reconstruction du verrou impossible :\n{init.stderr[-800:]}"

    texte = (copie / ".terraform.lock.hcl").read_text(encoding="utf-8")
    bloc = re.search(r'provider\s+"[^"]*dmacvicar/libvirt"\s*\{(.*?)\n\}', texte, re.DOTALL)
    assert bloc, "Le bloc du provider libvirt est illisible dans le verrou."

    contrainte = re.search(r'constraints\s*=\s*"([^"]+)"', bloc.group(1))
    assert contrainte, "Le verrou ne porte aucune contrainte : le provider a ete devine."
    assert not re.fullmatch(r"~>\s*\d+\.\d+", contrainte.group(1)), (
        f"La contrainte {contrainte.group(1)!r} laisse flotter le MINEUR, et la "
        "0.9 a reecrit le schema. Trois composants le figent."
    )


# --------------------------------------------------------------------------
# 2. La VM existe, et elle TOURNE.
# --------------------------------------------------------------------------
def test_le_volume_et_le_domaine_existent_et_la_vm_tourne(applique: None) -> None:
    gerees = _gerees()
    types = sorted(r["type"] for r in gerees.values())
    assert types == ["libvirt_domain", "libvirt_volume"], (
        f"Le state gere {types}, attendu exactement un volume et un domaine."
    )

    nom = _sorties()["nom_du_domaine"]["value"]
    etat = _virsh("domstate", nom)
    assert etat.returncode == 0, (
        f"`virsh domstate {nom}` a echoue : l'hote ne connait pas ce domaine.\n"
        f"{etat.stderr[-400:]}"
    )
    assert etat.stdout.strip() == "running", (
        f"Le domaine est en etat {etat.stdout.strip()!r}, attendu `running`. "
        "La machine doit demarrer, pas seulement etre definie."
    )


# --------------------------------------------------------------------------
# 3. La VM BOOTE vraiment, et c'est autre chose qu'etre `running`.
# --------------------------------------------------------------------------
def test_la_vm_consomme_du_cpu_donc_elle_boote(applique: None) -> None:
    """`running` ne prouve rien : une VM sans OS l'est aussi.

    Mesure : 0,3 s de CPU pour un domaine sans disque bootable, 7,1 s pour le
    meme avec l'image cloud. C'est cette difference qu'on lit, et non un bail
    DHCP, qu'une image cloud sans cloud-init peut ne jamais demander.
    """
    nom = _sorties()["nom_du_domaine"]["value"]

    debut = time.monotonic()
    consomme = 0.0
    while time.monotonic() - debut < ATTENTE_MAXIMUM:
        consomme = _temps_cpu(nom)
        if consomme >= SECONDES_CPU_MINIMUM:
            return
        time.sleep(3)

    pytest.fail(
        f"Apres {ATTENTE_MAXIMUM} s, le domaine n'a consomme que {consomme} s de "
        f"CPU, seuil attendu {SECONDES_CPU_MINIMUM} s.\n\nUne machine qui ne "
        "trouve aucun disque bootable reste `running` sans rien faire. "
        "Verifiez que le disque derive bien de l'image cloud par un "
        "`backing_store`, et que le peripherique est declare bootable."
    )


# --------------------------------------------------------------------------
# 4. Juste apres l'apply, rien n'est en attente.
# --------------------------------------------------------------------------
def test_aucun_changement_juste_apres_l_apply(applique: None) -> None:
    plan = _tf("plan", "-detailed-exitcode", "-input=false", "-no-color")
    assert plan.returncode == 0, (
        f"`plan -detailed-exitcode` rend {plan.returncode}, attendu 0.\n"
        f"{plan.stdout[-1200:]}"
    )


# --------------------------------------------------------------------------
# 5. Les ressources allouees se modifient EN PLACE.
# --------------------------------------------------------------------------
def test_changer_la_memoire_ou_les_vcpu_met_a_jour_en_place(applique: None) -> None:
    for variable, valeur in (("memoire_mio", "1024"), ("vcpu", "2")):
        actions = _actions(_plan_avec(variable, valeur), "libvirt_domain.vm")
        assert actions == ["update"], (
            f"Changer `{variable}` annonce {actions}, attendu `['update']`.\n\n"
            "libvirt sait redefinir un domaine sans le detruire : la memoire et "
            "les vCPU se modifient en place."
        )


# --------------------------------------------------------------------------
# 6. L'identite du domaine, elle, force un remplacement.
# --------------------------------------------------------------------------
def test_changer_le_nom_detruit_puis_recree(applique: None) -> None:
    plan = _plan_avec("nom_de_la_vm", "tf-lab-vm-bis")
    actions = _actions(plan, "libvirt_domain.vm")
    assert actions is not None and set(actions) == {"delete", "create"}, (
        f"Changer le nom annonce {actions}, attendu une destruction suivie "
        "d'une creation.\n\nLe nom EST l'identite du domaine pour libvirt : le "
        "changer ne modifie pas la machine, il en fabrique une autre."
    )

    chemins = next(
        c["change"].get("replace_paths")
        for c in plan["resource_changes"]
        if c["address"] == "libvirt_domain.vm"
    )
    assert ["name"] in (chemins or []), (
        f"Le plan declare les chemins de remplacement {chemins}, attendu "
        "`[['name']]` : c'est bien le nom qui declenche le remplacement."
    )


# --------------------------------------------------------------------------
# 7. Les deux cotes : ce qu'un remplacement emporte, et ce qu'une mise a jour
#    epargne.
# --------------------------------------------------------------------------
def test_l_identifiant_survit_a_une_mise_a_jour_et_pas_a_un_remplacement(
    applique: None,
) -> None:
    """La preuve que le plan ne mentait pas, verifiee en APPLIQUANT.

    Les tests 5 et 6 lisent des PLANS. Un plan est une prediction : tant qu'on
    ne l'a pas appliquee, on ne sait pas si l'outil tient parole. Ce test
    applique les deux changements et compare l'identifiant du domaine, attribue
    par libvirt a la creation.

    Une machine modifiee en place garde le sien. Une machine remplacee en
    recoit un autre. C'est la difference entre « on a change un reglage » et
    « on a jete la machine », et sur un vrai systeme elle se paie en donnees.
    """
    avant = _sorties()["identifiant_du_domaine"]["value"]

    majeure = _tf("apply", "-auto-approve", "-input=false", "-no-color",
                  "-var", "memoire_mio=1024")
    assert majeure.returncode == 0, (
        f"L'application du changement de memoire a echoue.\n{majeure.stderr[-1200:]}"
    )
    apres_mise_a_jour = _sorties()["identifiant_du_domaine"]["value"]
    assert apres_mise_a_jour == avant, (
        f"L'identifiant est passe de {avant!r} a {apres_mise_a_jour!r} apres un "
        "simple changement de memoire.\n\nLa machine a donc ete REMPLACEE la ou "
        "le plan annoncait une mise a jour. Tout ce qu'elle contenait est perdu."
    )

    renomme = _tf("apply", "-auto-approve", "-input=false", "-no-color",
                  "-var", "memoire_mio=1024", "-var", "nom_de_la_vm=tf-lab-vm-bis")
    assert renomme.returncode == 0, (
        f"L'application du changement de nom a echoue.\n{renomme.stderr[-1200:]}"
    )
    apres_remplacement = _sorties()["identifiant_du_domaine"]["value"]
    assert apres_remplacement != avant, (
        f"L'identifiant vaut encore {apres_remplacement!r} apres un changement "
        "de nom.\n\nLe domaine aurait donc ete modifie en place, ce que libvirt "
        "ne sait pas faire sur une identite."
    )

    # On revient a l'etat nominal, pour que le teardown detruise ce qu'il a cree.
    _tf("apply", "-auto-approve", "-input=false", "-no-color")
