"""Épreuve de niveau B : exploiter le state.

Une mesure, pas un cours. Chaque test note un RÉSULTAT sur l'état réel :
identité et temps CPU des domaines libvirt, objets du bucket S3, codes de
retour du script `chaine.sh`. Rien n'est lu dans la forme du code, sinon deux
raccourcis interdits (`-lock=false`, `force-unlock`) cherchés dans le script.

Le nom de chaque test commence par la compétence qu'il note : `state`,
`refactor`, `environment`, `automate`. Le rapport de `dsoxlab check` donne
ainsi un verdict par compétence.

Ce que la préparation (`setup.yaml`) a retenu pour le harnais vit dans
`$LAB_STATE_DIR/epreuve.json`, hors du répertoire de travail : préfixe tiré,
incident, UUID de référence des machines de production, point d'accès S3.

Faits mesurés avant d'écrire ces tests (cahier des charges, §9 et §10) :
SeaweedFS refuse en 412 l'écriture d'un verrou déjà posé, et Terraform attend
avec `-lock-timeout` ; une VM qui boote dépasse 2 s de CPU, une VM sans disque
amorçable reste sous la seconde.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest

from conftest import exiger_workdir, workdir_lab

# Le dossier des tests n'est pas sur le chemin d'import dans le mode de ce dépôt.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _s3 import S3

pytestmark = pytest.mark.no_replay

WORKDIR = workdir_lab(__file__)
LAB_ID = "level-exams-operate-state"
VIRSH = ["virsh", "-c", "qemu:///system"]
CHAINE = WORKDIR / "chaine.sh"
SECONDES_CPU_MINIMUM = 2.0
VERROU_TENU = 20


# ── Ce que la préparation a retenu ───────────────────────────────────────────

def _epreuve() -> dict:
    etat = os.environ.get("LAB_STATE_DIR")
    assert etat, "LAB_STATE_DIR absent : lancez l'épreuve par `dsoxlab run`, puis notez par `dsoxlab check`."
    fichier = Path(etat) / "epreuve.json"
    assert fichier.is_file(), f"{fichier} absent : la préparation n'a pas tourné (`dsoxlab run`)."
    return json.loads(fichier.read_text())


def _env() -> dict[str, str]:
    """L'environnement du script : celui du poste, plus l'identité de l'équipe."""
    env = os.environ.copy()
    texte = (WORKDIR / "exam.env").read_text()
    for cle, valeur in re.findall(r"export (AWS_[A-Z_]+)=(\S+)", texte):
        env[cle] = valeur
    return env


def _s3() -> S3:
    e, env = _epreuve(), _env()
    return S3(e["endpoint"], e["bucket"], env["AWS_ACCESS_KEY_ID"], env["AWS_SECRET_ACCESS_KEY"])


# ── Lecture de l'état réel ───────────────────────────────────────────────────

def _virsh(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([*VIRSH, *args], capture_output=True, text=True, timeout=60,
                          check=False)


def _uuid(nom: str) -> str | None:
    r = _virsh("domuuid", nom)
    return r.stdout.strip() if r.returncode == 0 else None


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


def _domaines(prefixe: str) -> list[str]:
    noms = _virsh("list", "--all", "--name").stdout.split()
    return [n for n in noms if n.startswith(prefixe)]


def _states(s3: S3) -> dict[str, dict]:
    """Chaque state du bucket, par clé, avec les noms de domaines qu'il gère."""
    resultat: dict[str, dict] = {}
    for cle in s3.cles():
        if cle.endswith(".tflock"):
            continue
        try:
            state = json.loads(s3.lire(cle))
        except (ValueError, AssertionError):
            continue
        if "resources" not in state:
            continue
        noms = {
            inst.get("attributes", {}).get("name")
            for res in state["resources"] if res.get("type") == "libvirt_domain"
            for inst in res.get("instances", [])
        }
        resultat[cle] = {"state": state, "domaines": {n for n in noms if n}}
    return resultat


def _chaine(env_cible: str, action: str, timeout: int = 600) -> subprocess.CompletedProcess[str]:
    assert CHAINE.is_file() and os.access(CHAINE, os.X_OK), (
        "chaine.sh absent ou non exécutable à la racine du répertoire de travail : "
        "c'est l'interface que le harnais appelle."
    )
    # stdin fermé : un script qui pose une question échoue au lieu de se bloquer.
    return subprocess.run(
        [str(CHAINE), env_cible, action], cwd=WORKDIR, env=_env(),
        stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout,
        check=False,
    )


def _fichiers_de_plan() -> list[Path]:
    """Un plan Terraform sauvegardé est une archive zip : on les cherche au contenu."""
    trouves = []
    for f in WORKDIR.rglob("*"):
        if f.is_file() and ".terraform" not in f.parts and f.stat().st_size > 4:
            with f.open("rb") as h:
                if h.read(4) == b"PK\x03\x04":
                    trouves.append(f)
    return trouves


@pytest.fixture(scope="module", autouse=True)
def _preparee() -> None:
    exiger_workdir(WORKDIR, LAB_ID)


# ── refactor : la production réparée sans recréer ────────────────────────────

def test_refactor_les_machines_de_prod_gardent_leur_identite() -> None:
    """Garder l'UUID ne prouve rien tant que rien n'est réparé : une tentative
    vide le garde aussi. Le test exige donc d'abord la production convergée."""
    e = _epreuve()
    r = _chaine("prod", "plan")
    assert r.returncode == 0, "la production n'est pas encore remise d'aplomb : l'identité des machines ne prouve rien seule."
    for role, uuid in e["uuid_prod"].items():
        nom = f"{e['prefixe']}-prod-{role}"
        actuel = _uuid(nom)
        assert actuel is not None, f"{nom} n'existe plus : la machine a été supprimée."
        assert actuel == uuid, f"{nom} a été RECRÉÉE (UUID {uuid} devenu {actuel}) : l'incident se répare sans recréer."
        assert _boote(nom), f"{nom} ne tourne pas, ou ne boote pas (moins de {SECONDES_CPU_MINIMUM} s de CPU)."


def test_refactor_le_plan_de_prod_ne_propose_plus_rien() -> None:
    r = _chaine("prod", "plan")
    assert r.returncode == 0, (
        f"`chaine.sh prod plan` rend {r.returncode}, attendu 0 : la production n'est pas remise d'aplomb.\n"
        f"{r.stdout[-1500:]}{r.stderr[-1500:]}"
    )


# ── state : verrou attendu, jamais forcé ; sauvegarde avant d'écrire ─────────

def test_state_aucun_forcage_du_verrou() -> None:
    assert CHAINE.is_file(), "chaine.sh absent : rien à vérifier, donc rien de prouvé."
    texte = CHAINE.read_text()
    for interdit in ("-lock=false", "force-unlock"):
        assert interdit not in texte, f"`{interdit}` dans chaine.sh : un verrou ne se force pas, il s'attend."


def test_state_le_verrou_tenu_par_une_autre_execution_est_attendu() -> None:
    e, s3 = _epreuve(), _s3()
    prod = [k for k, v in _states(s3).items() if f"{e['prefixe']}-prod-web" in v["domaines"]]
    assert len(prod) == 1, f"un seul state doit gérer la production, trouvé : {prod or 'aucun'}"
    cle_verrou = prod[0] + ".tflock"
    verrou = json.dumps({
        "ID": "00000000-0000-0000-0000-00000000harn", "Operation": "OperationTypeApply",
        "Info": "", "Who": "harnais@epreuve-b", "Version": "1.16.1",
        "Created": datetime.now(UTC).isoformat(), "Path": prod[0],
    }).encode()
    assert s3.ecrire(cle_verrou, verrou) == 200, "le harnais n'a pas pu poser son verrou"
    liberer = threading.Timer(VERROU_TENU, lambda: s3.supprimer(cle_verrou))
    liberer.start()
    try:
        debut = time.monotonic()
        r = _chaine("prod", "plan")
        duree = time.monotonic() - debut
    finally:
        liberer.cancel()
        s3.supprimer(cle_verrou)
    if r.returncode != 0:
        pytest.fail(f"pendant qu'une autre exécution tient le verrou, `chaine.sh prod plan` échoue (rc {r.returncode}) au lieu d'attendre.\n{r.stderr[-1200:]}")
    assert duree >= VERROU_TENU - 2, (
        f"`chaine.sh prod plan` a fini en {duree:.0f} s alors que le verrou était tenu {VERROU_TENU} s : "
        "le verrou est ignoré."
    )


# ── environment : dev et prod séparés ────────────────────────────────────────

def test_environment_dev_a_ses_propres_machines() -> None:
    e = _epreuve()
    dev = _domaines(f"{e['prefixe']}-dev-")
    assert dev, f"aucune machine `{e['prefixe']}-dev-*` : l'environnement dev n'existe pas."
    for nom in dev:
        assert _boote(nom), f"{nom} ne boote pas."


def test_environment_dev_et_prod_ne_partagent_aucun_state() -> None:
    e, s3 = _epreuve(), _s3()
    prefixe_prod, prefixe_dev = f"{e['prefixe']}-prod-", f"{e['prefixe']}-dev-"
    states = _states(s3)
    avec_prod = [k for k, v in states.items() if any(n.startswith(prefixe_prod) for n in v["domaines"])]
    avec_dev = [k for k, v in states.items() if any(n.startswith(prefixe_dev) for n in v["domaines"])]
    assert len(avec_prod) == 1 and len(avec_dev) == 1, f"states de prod : {avec_prod}, de dev : {avec_dev}"
    assert avec_prod != avec_dev, f"dev et prod partagent le state {avec_prod[0]}."


def test_environment_un_changement_sur_dev_laisse_prod_intacte_et_sauvegarde_avant() -> None:
    """Le harnais arrête une machine de dev, puis rejoue la chaîne sur dev et sur prod.

    Ce test note aussi la règle de sauvegarde (`state`) : avant l'écriture que
    provoque l'apply de dev, une copie du state de dev doit exister, en fichier
    dans le répertoire de travail ou en version du bucket.
    """
    e, s3 = _epreuve(), _s3()
    dev = sorted(_domaines(f"{e['prefixe']}-dev-"))
    assert dev, "aucune machine de dev"
    cle_dev = next(k for k, v in _states(s3).items() if dev[0] in v["domaines"])
    avant = json.loads(s3.lire(cle_dev))

    _virsh("destroy", dev[0])
    plan = _chaine("dev", "plan")
    assert plan.returncode == 2, f"dev a dérivé (machine arrêtée) : `chaine.sh dev plan` doit rendre 2, il rend {plan.returncode}."
    apply = _chaine("dev", "apply")
    assert apply.returncode == 0, f"`chaine.sh dev apply` rend {apply.returncode}.\n{apply.stderr[-1200:]}"
    assert _boote(dev[0]), f"{dev[0]} n'a pas été relancée par l'apply."

    copies = [f for f in WORKDIR.rglob("*.tfstate*") if ".terraform" not in f.parts and f.is_file()]
    sauvee = any(
        (d := json.loads(f.read_text())).get("lineage") == avant["lineage"] and d.get("serial") == avant["serial"]
        for f in copies if f.read_text().lstrip().startswith("{")
    )
    if not sauvee and s3.versionnage_actif():
        for v in s3.versions(cle_dev):
            contenu = s3.lire_version(cle_dev, v)
            if contenu and json.loads(contenu).get("serial") == avant["serial"]:
                sauvee = True
                break
    assert sauvee, (
        f"aucune sauvegarde du state de dev au serial {avant['serial']} avant l'apply : "
        "ni copie dans le répertoire de travail, ni version dans le bucket."
    )

    prod = _chaine("prod", "plan")
    assert prod.returncode == 0, f"après un changement sur dev, le plan de prod rend {prod.returncode} au lieu de 0."
    for role, uuid in e["uuid_prod"].items():
        assert _uuid(f"{e['prefixe']}-prod-{role}") == uuid, "un changement sur dev a touché la production"


# ── automate : codes de retour, aucune invite, plan relu ─────────────────────

def test_automate_une_erreur_rend_1_sans_attendre_de_reponse() -> None:
    r = _chaine("inexistant", "plan", timeout=180)
    assert r.returncode == 1, f"`chaine.sh inexistant plan` rend {r.returncode}, attendu 1."


def test_automate_apply_n_applique_que_le_plan_relu() -> None:
    """Le harnais change le monde APRÈS le plan : seul le plan relu doit s'appliquer.

    `dev-web` est arrêtée, puis `plan` ; `dev-db` est arrêtée ensuite, puis
    `apply`. Un apply qui rejoue un plan neuf relance les deux ; celui qui
    applique le plan relu ne relance que `web`.
    """
    e = _epreuve()
    web, db = f"{e['prefixe']}-dev-web", f"{e['prefixe']}-dev-db"
    assert _uuid(web) and _uuid(db), f"dev doit avoir ses machines web et db ({web}, {db})."
    _virsh("destroy", web)
    assert _chaine("dev", "plan").returncode == 2
    _virsh("destroy", db)
    r = _chaine("dev", "apply")
    assert r.returncode == 0, f"`chaine.sh dev apply` rend {r.returncode}.\n{r.stderr[-1200:]}"
    assert _boote(web), f"{web} n'a pas été relancée : le plan relu n'a pas été appliqué."
    assert _virsh("domstate", db).stdout.strip() != "running", (
        f"{db}, arrêtée APRÈS le plan, a été relancée : l'apply n'a pas appliqué le plan relu "
        "mais en a calculé un nouveau."
    )
    # Remettre dev d'aplomb pour la suite.
    assert _chaine("dev", "plan").returncode == 2
    assert _chaine("dev", "apply").returncode == 0
    assert _boote(db)


def test_automate_aucun_fichier_de_plan_ne_reste() -> None:
    assert _chaine("prod", "plan").returncode == 0
    assert _chaine("prod", "apply").returncode == 0
    restes = _fichiers_de_plan()
    assert not restes, f"fichier(s) de plan laissé(s) après l'apply : {[str(f.relative_to(WORKDIR)) for f in restes]}"
