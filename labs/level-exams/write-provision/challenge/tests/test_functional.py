"""Épreuve de niveau A : écrire et provisionner.

Une mesure, pas un cours. Chaque test note un RÉSULTAT sur l'état réel :
domaines et réseaux libvirt, temps CPU, plans Terraform et leurs codes de
retour, secret relu dans la machine. Le code de l'apprenant n'est jamais lu :
le harnais lui donne d'autres catalogues et observe ce qu'il en fait.

Le nom de chaque test commence par la compétence qu'il note : `workflow`,
`resource`, `parameterize`, `expression`, `guard`, `sensitive`. Le rapport de
`dsoxlab check` donne ainsi un verdict par compétence.

Ce que la préparation (`setup.yaml`) a retenu pour le harnais vit dans
`$LAB_STATE_DIR/epreuve.json`, hors du répertoire de travail : préfixe,
réseau, catalogue, machine critique, machine applicative, fronts.

Faits mesurés avant d'écrire ces tests (cahier des charges, §12 et §13) :
un secret éphémère posé par provisioner ne laisse aucune trace dans le state
ni dans le plan, alors que `sensitive` seul l'y laisse en clair ;
`prevent_destroy` refuse aussi un remplacement ; `create_before_destroy`
n'aboutit sur libvirt qu'avec un nom unique par génération. Une VM qui boote
dépasse 2 s de CPU.
"""

from __future__ import annotations

import copy
import json
import os
import re
import subprocess
import tempfile
import time
import zipfile
from pathlib import Path

import pytest

from conftest import exiger_workdir, message, workdir_lab

pytestmark = pytest.mark.no_replay

WORKDIR = workdir_lab(__file__)
LAB_ID = "level-exams-write-provision"
VIRSH = ["virsh", "-c", "qemu:///system"]
SECONDES_CPU_MINIMUM = 2.0
MEMOIRE_KIB = {"petite": 512 * 1024, "moyenne": 768 * 1024}
CLE = WORKDIR / "acces" / "id_ed25519"


# ── Ce que la préparation a retenu ───────────────────────────────────────────

def _epreuve() -> dict:
    etat = os.environ.get("LAB_STATE_DIR")
    assert etat, message(
        en="LAB_STATE_DIR missing: start the exam with `dsoxlab run`, then grade it with `dsoxlab check`.",
        fr="LAB_STATE_DIR absent : lancez l'épreuve par `dsoxlab run`, puis notez par `dsoxlab check`.",
    )
    fichier = Path(etat) / "epreuve.json"
    assert fichier.is_file(), message(
        en=f"{fichier} missing: the preparation did not run (`dsoxlab run`).",
        fr=f"{fichier} absent : la préparation n'a pas tourné (`dsoxlab run`).",
    )
    return json.loads(fichier.read_text())


# ── Lecture de l'état réel ───────────────────────────────────────────────────

def _virsh(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([*VIRSH, *args], capture_output=True, text=True, timeout=60,
                          check=False)


def _domaines(e: dict, nom: str) -> list[str]:
    """Les domaines d'une entrée du catalogue : leur nom commence par `<préfixe>-<nom>`."""
    tous = _virsh("list", "--all", "--name").stdout.split()
    return [d for d in tous if d == f"{e['prefixe']}-{nom}" or d.startswith(f"{e['prefixe']}-{nom}-")]


def _domaine(e: dict, nom: str) -> str:
    d = _domaines(e, nom)
    assert len(d) == 1, message(
        en=f"\"{nom}\": a domain whose name starts with {e['prefixe']}-{nom} was expected, found {d or 'none'}.",
        fr=f"« {nom} » : un domaine attendu dont le nom commence par {e['prefixe']}-{nom}, trouvé {d or 'aucun'}.",
    )
    return d[0]


def _boote(nom: str) -> bool:
    """Une machine `running` sans OS l'est aussi : seul le temps CPU prouve le boot."""
    debut = time.monotonic()
    while time.monotonic() - debut < 90:
        if _virsh("domstate", nom).stdout.strip() == "running":
            m = re.search(r"cpu\.time=(\d+)", _virsh("domstats", nom, "--cpu-total").stdout)
            if m and int(m.group(1)) / 1e9 >= SECONDES_CPU_MINIMUM:
                return True
        time.sleep(3)
    return False


def _ipv4(domaine: str) -> str:
    debut = time.monotonic()
    while time.monotonic() - debut < 120:
        m = re.search(r"ipv4\s+(\d+\.\d+\.\d+\.\d+)", _virsh("domifaddr", domaine, "--source", "lease").stdout)
        if m:
            return m.group(1)
        time.sleep(3)
    raise AssertionError(f"{domaine} : aucune adresse IPv4 attribuée par le réseau de l'environnement.")


def _ssh(ip: str, commande: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["ssh", "-i", str(CLE), "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
         "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "-o", "LogLevel=ERROR", f"exploit@{ip}", commande],
        capture_output=True, text=True, timeout=60, check=False,
    )


# ── Terraform, joué dans le répertoire de l'apprenant ────────────────────────

def _terraform(*args: str, timeout: int = 900) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["TF_IN_AUTOMATION"] = "1"
    return subprocess.run(["terraform", *args, "-no-color"], cwd=WORKDIR, capture_output=True,
                          text=True, timeout=timeout, env=env, check=False)


def _catalogue_modifie(e: dict, modifier) -> Path:
    """Un fichier de variables qui remplace le catalogue, hors du répertoire de l'apprenant."""
    machines = copy.deepcopy(e["machines"])
    modifier(machines)
    f = Path(tempfile.mkdtemp(prefix="epreuve-a-")) / "catalogue.tfvars.json"
    f.write_text(json.dumps({"machines": machines}))
    return f


def _plan_json(*args: str) -> tuple[subprocess.CompletedProcess[str], dict | None, Path]:
    """Un plan enregistré hors du répertoire de l'apprenant, et sa lecture JSON."""
    fichier = Path(tempfile.mkdtemp(prefix="epreuve-a-")) / "plan.tfplan"
    r = _terraform("plan", "-input=false", f"-out={fichier}", *args)
    if r.returncode != 0 or not fichier.is_file():
        return r, None, fichier
    montre = _terraform("show", "-json", str(fichier))
    return r, json.loads(montre.stdout), fichier


def _changements(plan: dict) -> list[tuple[str, list[str]]]:
    return [(c["address"], c["change"]["actions"]) for c in plan.get("resource_changes", [])
            if c["change"]["actions"] not in (["no-op"], ["read"])]


def _secret(e: dict) -> str:
    ip = _ipv4(_domaine(e, e["app"]))
    r = _ssh(ip, "sudo cat /etc/app/secret")
    assert r.returncode == 0 and r.stdout.strip(), message(
        en=f"The secret cannot be read at /etc/app/secret on \"{e['app']}\" ({ip}): {r.stderr.strip()[:200]}",
        fr=f"Le secret n'est pas lisible dans /etc/app/secret sur « {e['app']} » ({ip}) : {r.stderr.strip()[:200]}",
    )
    return r.stdout.strip()


@pytest.fixture(autouse=True)
def _workdir() -> None:
    exiger_workdir(WORKDIR, LAB_ID)


# ── workflow ─────────────────────────────────────────────────────────────────

def test_workflow_la_configuration_converge() -> None:
    """Après l'apply, un plan ne propose plus rien : `-detailed-exitcode` rend 0."""
    r = _terraform("plan", "-input=false", "-detailed-exitcode")
    assert r.returncode == 0, message(
        en=f"plan -detailed-exitcode returns {r.returncode} (0 expected: nothing to do after the apply).\n"
        f"{(r.stdout + r.stderr)[-600:]}",
        fr=f"plan -detailed-exitcode rend {r.returncode} (0 attendu : rien à faire après l'apply).\n"
        f"{(r.stdout + r.stderr)[-600:]}",
    )


# ── resource ─────────────────────────────────────────────────────────────────

def test_resource_chaque_machine_du_catalogue_existe_et_boote() -> None:
    e = _epreuve()
    for nom, m in e["machines"].items():
        d = _domaine(e, nom)
        assert _boote(d), message(
            en=f"{d} did not boot a system (less than {SECONDES_CPU_MINIMUM} s of CPU).",
            fr=f"{d} n'a pas démarré de système (moins de {SECONDES_CPU_MINIMUM} s de CPU).",
        )
        memoire = int(re.search(r"Max memory:\s+(\d+)", _virsh("dominfo", d).stdout).group(1))
        assert memoire == MEMOIRE_KIB[m["taille"]], message(
            en=f"{d}: {memoire} KiB of memory, {MEMOIRE_KIB[m['taille']]} expected for size \"{m['taille']}\".",
            fr=f"{d} : {memoire} KiB de mémoire, {MEMOIRE_KIB[m['taille']]} attendus pour la taille « {m['taille']} ».",
        )


def test_resource_les_machines_sont_sur_un_reseau_isole() -> None:
    e = _epreuve()
    reseaux = [n for n in _virsh("net-list", "--all", "--name").stdout.split() if n.startswith(e["prefixe"])]
    assert reseaux, message(
        en=f"No libvirt network whose name starts with {e['prefixe']}.",
        fr=f"Aucun réseau libvirt dont le nom commence par {e['prefixe']}.",
    )
    isoles = [n for n in reseaux if "<forward" not in _virsh("net-dumpxml", n).stdout]
    assert isoles, message(
        en=f"Network {reseaux}: it routes to the outside (a <forward> block); an isolated network has none.",
        fr=f"Réseau {reseaux} : il route vers l'extérieur (bloc <forward>), un réseau isolé n'en a pas.",
    )
    for nom in e["machines"]:
        d = _domaine(e, nom)
        sources = _virsh("domiflist", d).stdout
        assert any(n in sources for n in isoles), message(
            en=f"{d} is not attached to the isolated network {isoles}.",
            fr=f"{d} n'est pas raccordée au réseau isolé {isoles}.",
        )


def test_resource_les_providers_sont_verrouilles() -> None:
    verrou = WORKDIR / ".terraform.lock.hcl"
    assert verrou.is_file(), message(
        en="No .terraform.lock.hcl: the providers' versions are not locked.",
        fr="Pas de .terraform.lock.hcl : les versions des providers ne sont pas verrouillées.",
    )
    texte = verrou.read_text()
    assert 'provider "registry.terraform.io/dmacvicar/libvirt"' in texte, message(
        en="The libvirt provider is not locked.",
        fr="Le provider libvirt n'est pas verrouillé.",
    )


# ── sensitive ────────────────────────────────────────────────────────────────

def test_sensitive_le_secret_est_arrive_dans_la_machine_applicative() -> None:
    e = _epreuve()
    secret = _secret(e)
    assert len(secret) >= 16, message(
        en=f"The secret is only {len(secret)} characters long (16 at least).",
        fr=f"Le secret ne fait que {len(secret)} caractères (16 au moins).",
    )
    droits = _ssh(_ipv4(_domaine(e, e["app"])), "sudo stat -c '%a %U' /etc/app/secret").stdout.strip()
    assert droits == "600 root", message(
        en=f"/etc/app/secret: permissions \"{droits}\", \"600 root\" expected.",
        fr=f"/etc/app/secret : droits « {droits} », « 600 root » attendus.",
    )


def test_sensitive_le_secret_ne_figure_ni_dans_le_state_ni_dans_le_plan() -> None:
    e = _epreuve()
    secret = _secret(e)
    state = _terraform("state", "pull")
    assert state.returncode == 0, message(
        en=f"state pull impossible: {state.stderr[-300:]}",
        fr=f"state pull impossible : {state.stderr[-300:]}",
    )
    assert secret not in state.stdout, message(
        en="The secret appears in clear text in the state.",
        fr="Le secret figure en clair dans le state.",
    )
    r, plan, fichier = _plan_json()
    assert plan is not None, message(
        en=f"Plan impossible: {(r.stdout + r.stderr)[-300:]}",
        fr=f"Plan impossible : {(r.stdout + r.stderr)[-300:]}",
    )
    assert secret not in json.dumps(plan), message(
        en="The secret appears in the JSON plan.",
        fr="Le secret figure dans le plan JSON.",
    )
    with zipfile.ZipFile(fichier) as z:
        for nom in z.namelist():
            assert secret.encode() not in z.read(nom), message(
                en=f"The secret appears in the saved plan ({nom}).",
                fr=f"Le secret figure dans le plan enregistré ({nom}).",
            )


# ── parameterize ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("cas", ["taille-inconnue", "role-inconnu", "champ-manquant"])
def test_parameterize_un_catalogue_invalide_est_refuse_avant_le_plan(cas: str) -> None:
    e = _epreuve()
    nom = e["fronts"][0]

    def abimer(machines: dict) -> None:
        if cas == "taille-inconnue":
            machines[nom]["taille"] = "enorme"
        elif cas == "role-inconnu":
            machines[nom]["role"] = "cache"
        else:
            del machines[nom]["taille"]

    r = _terraform("plan", "-input=false", f"-var-file={_catalogue_modifie(e, abimer)}")
    sortie = r.stdout + r.stderr
    # Une règle de validation écrit « Invalid value for variable », une erreur
    # de type (champ manquant) « Invalid value for input variable ».
    assert r.returncode == 1 and re.search(r"Invalid value for (input )?variable", sortie), message(
        en=f"Invalid catalogue ({cas}): the plan was supposed to refuse it on the catalogue variable.\n{sortie[-500:]}",
        fr=f"Catalogue invalide ({cas}) : le plan devait le refuser sur la variable du catalogue.\n{sortie[-500:]}",
    )
    assert "Plan:" not in sortie, message(
        en=f"Invalid catalogue ({cas}): a plan was computed.",
        fr=f"Catalogue invalide ({cas}) : un plan a été calculé.",
    )


# ── expression ───────────────────────────────────────────────────────────────

def test_expression_retirer_une_machine_ne_touche_qu_elle() -> None:
    e = _epreuve()
    nom = e["fronts"][1]
    r, plan, _ = _plan_json(f"-var-file={_catalogue_modifie(e, lambda m: m.pop(nom))}")
    assert plan is not None, message(
        en=f"Plan impossible without \"{nom}\": {(r.stdout + r.stderr)[-400:]}",
        fr=f"Plan impossible sans « {nom} » : {(r.stdout + r.stderr)[-400:]}",
    )
    changements = _changements(plan)
    assert changements, message(
        en=f"Removing \"{nom}\" from the catalogue changes nothing: the catalogue does not drive the code.",
        fr=f"Retirer « {nom} » du catalogue ne change rien : le catalogue ne pilote pas le code.",
    )
    autres = [(a, act) for a, act in changements if act != ["delete"] or f'["{nom}"]' not in a]
    assert not autres, message(
        en=f"Removing \"{nom}\" also affects something other than it: {autres}",
        fr=f"Retirer « {nom} » touche aussi autre chose qu'elle : {autres}",
    )
    assert any("libvirt_domain" in a for a, _ in changements), message(
        en=f"Removing \"{nom}\" does not destroy its domain.",
        fr=f"Retirer « {nom} » ne détruit pas son domaine.",
    )


# ── guard ────────────────────────────────────────────────────────────────────

def test_guard_la_machine_critique_refuse_un_plan_de_destruction() -> None:
    r = _terraform("plan", "-input=false", "-destroy")
    assert r.returncode == 1 and "cannot be destroyed" in (r.stdout + r.stderr), message(
        en=f"plan -destroy returns {r.returncode}: the critical machine was supposed to refuse it.\n{(r.stdout + r.stderr)[-400:]}",
        fr=f"plan -destroy rend {r.returncode} : la machine critique devait le refuser.\n{(r.stdout + r.stderr)[-400:]}",
    )


def test_guard_la_machine_critique_refuse_son_remplacement() -> None:
    e = _epreuve()
    nom = e["critique"]

    def nouvelle_generation(machines: dict) -> None:
        machines[nom]["generation"] += 1

    r = _terraform("plan", "-input=false", f"-var-file={_catalogue_modifie(e, nouvelle_generation)}")
    sortie = r.stdout + r.stderr
    assert r.returncode == 1 and "cannot be destroyed" in sortie, message(
        en=f"New generation of \"{nom}\": replacing the critical machine was supposed to be refused.\n{sortie[-400:]}",
        fr=f"Nouvelle génération de « {nom} » : le remplacement de la machine critique devait être refusé.\n{sortie[-400:]}",
    )


def test_guard_un_front_remplace_est_recree_avant_d_etre_detruit() -> None:
    e = _epreuve()
    nom = e["fronts"][0]
    ancien = _domaine(e, nom)

    def nouvelle_generation(machines: dict) -> None:
        machines[nom]["generation"] += 1

    r, plan, fichier = _plan_json(f"-var-file={_catalogue_modifie(e, nouvelle_generation)}")
    assert plan is not None, message(
        en=f"Plan impossible: {(r.stdout + r.stderr)[-400:]}",
        fr=f"Plan impossible : {(r.stdout + r.stderr)[-400:]}",
    )
    domaines = [(a, act) for a, act in _changements(plan) if "libvirt_domain" in a and f'["{nom}"]' in a]
    assert domaines, message(
        en=f"New generation of \"{nom}\": its domain is not replaced.",
        fr=f"Nouvelle génération de « {nom} » : son domaine n'est pas remplacé.",
    )
    assert all(act == ["create", "delete"] for _, act in domaines), message(
        en=f"\"{nom}\" must be created before being destroyed: actions {domaines}.",
        fr=f"« {nom} » doit être créée avant d'être détruite : actions {domaines}.",
    )
    autres = [a for a, _ in _changements(plan) if f'["{nom}"]' not in a]
    assert not autres, message(
        en=f"Replacing \"{nom}\" also affects: {autres}",
        fr=f"Remplacer « {nom} » touche aussi : {autres}",
    )

    applique = _terraform("apply", "-input=false", str(fichier), timeout=1200)
    assert applique.returncode == 0, message(
        en=f"The replacement fails: {(applique.stdout + applique.stderr)[-500:]}",
        fr=f"Le remplacement échoue : {(applique.stdout + applique.stderr)[-500:]}",
    )
    nouveau = _domaine(e, nom)
    assert nouveau != ancien and _boote(nouveau), message(
        en=f"\"{nom}\": the new machine ({nouveau}) does not replace {ancien}.",
        fr=f"« {nom} » : la nouvelle machine ({nouveau}) ne remplace pas {ancien}.",
    )

    # On remet l'environnement dans l'état du catalogue de l'apprenant.
    retour = _terraform("apply", "-input=false", "-auto-approve", timeout=1200)
    assert retour.returncode == 0, message(
        en=f"Going back to the original catalogue fails: {(retour.stdout + retour.stderr)[-500:]}",
        fr=f"Le retour au catalogue d'origine échoue : {(retour.stdout + retour.stderr)[-500:]}",
    )
    final = _terraform("plan", "-input=false", "-detailed-exitcode")
    assert final.returncode == 0, message(
        en=f"After going back, the plan returns {final.returncode} (0 expected).",
        fr=f"Après le retour, le plan rend {final.returncode} (0 attendu).",
    )
