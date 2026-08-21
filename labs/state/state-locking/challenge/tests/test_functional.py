"""Tests fonctionnels du lab « ce que le verrou du state bloque vraiment ».

Le test REFAIT l'experience au lieu de croire l'apprenant : il lance un apply en
arriere plan, attend l'apparition du verrou, releve lui meme les codes de retour
des gestes tentes pendant qu'il est tenu, tue un apply au milieu pour fabriquer
un fichier residuel, puis confronte ses propres mesures aux outputs declares.
Rien n'est ecrit en dur cote resultat attendu, sauf les deux faits purement
documentaires du backend S3.

Principe : on n'ouvre jamais un `.tf` de l'apprenant. On lit ce que Terraform
ecrit (`.terraform/terraform.tfstate`, le fichier de verrou, `show -json`,
`output -json`) et des codes de retour.

Faits verifies sur Terraform 1.15.4 (terraform_data seul, hors ligne) :
- le fichier de verrou SUIT le state : avec `path = "etat/projet.tfstate"` il
  s'ecrit en `etat/.projet.tfstate.lock.info`, et son champ `Path` vaut le
  chemin du state, pas celui du verrou ;
- il porte SEPT champs, `Info` compris ;
- `plan` est rejete comme `apply` (code 1) : il rafraichit, donc il peut ecrire ;
- `plan -lock=false`, `state list` et `show -json` passent (code 0) ;
- `force-unlock` sur backend local rend 1 dans les quatre cas (verrou tenu ou
  libre, ID juste ou faux), avec deux messages selon le mode : `-force` rend
  `Failed to unlock state: LocalState not locked`, la forme interactive rend
  `Local state cannot be unlocked by another process` ;
- apres un `kill -9`, le fichier de verrou reste sur le disque mais ne bloque
  RIEN : le plan suivant rend 0 et Terraform supprime le fichier lui meme.
"""

import json
import os
import re
import signal
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, output_json, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "state-state-locking"

STATE_ATTENDU = "etat/projet.tfstate"
DUREE_MINIMALE = 15.0
DUREE_MAXIMALE = 90.0
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

# Les deux seuls faits non mesurables hors ligne : ils viennent de la
# documentation du backend S3 (argument `use_lockfile`, « Defaults to false »,
# « DynamoDB-based locking is deprecated »).
S3_ATTENDU = {
    "argument": "use_lockfile",
    "actif_par_defaut": False,
    "dynamodb_deprecie": True,
}


# --------------------------------------------------------------------------
# Outils de mesure
# --------------------------------------------------------------------------

def _apply_arriere_plan(cwd: Path, *extra: str) -> subprocess.Popen[str]:
    """Lance un apply detache, pour pouvoir le tuer par son groupe."""
    return subprocess.Popen(
        ["terraform", "apply", "-auto-approve", "-input=false", "-no-color", *extra],
        cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        start_new_session=True,
    )


def _attendre_verrou(cwd: Path, delai: float = 60.0) -> Path | None:
    """Premier fichier de verrou apparu sous `cwd`, ou None au bout du delai."""
    fin = time.monotonic() + delai
    while time.monotonic() < fin:
        for fichier in cwd.rglob("*.lock.info"):
            return fichier
        time.sleep(0.1)
    return None


def _version_cli() -> str:
    proc = terraform("version", "-json", cwd=WORKDIR)
    proc.check_returncode()
    return json.loads(proc.stdout)["terraform_version"]


def _entier(valeur: object, ou: str) -> int:
    """Code de retour declare, tolerant sur 1 vs \"1\"."""
    try:
        return int(valeur)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        pytest.fail(f"{ou} vaut {valeur!r} : attendu un code de retour entier.")


def _booleen(valeur: object, ou: str) -> bool:
    if isinstance(valeur, bool):
        return valeur
    if isinstance(valeur, str) and valeur.lower() in ("true", "false"):
        return valeur.lower() == "true"
    pytest.fail(f"{ou} vaut {valeur!r} : attendu true ou false.")


def _declare(cwd: Path, nom: str) -> object:
    sorties = output_json(cwd)
    if nom not in sorties:
        pytest.fail(
            f"L'output `{nom}` est absent. observations.tf doit declarer les "
            "quatre outputs du fichier fourni, sans en retirer aucun."
        )
    return sorties[nom]["value"]


# --------------------------------------------------------------------------
# Fixtures : le test conduit lui meme l'experience
# --------------------------------------------------------------------------

@pytest.fixture(scope="module")
def applied() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(
            "`terraform init` a echoue. Un `???` restant dans le bloc backend ?"
            f"\n{init.stderr[-1200:]}"
        )
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(f"`terraform apply` a echoue.\n{app.stderr[-1500:]}")
    yield WORKDIR
    terraform("destroy", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)


@pytest.fixture(scope="module")
def mesures(applied: Path) -> dict:
    """Releve les codes de retour pendant qu'un verrou est REELLEMENT tenu.

    L'apply est relance avec `-replace` : le state existe deja, ce qui est la
    condition d'un releve honnete (sur un state inexistant, `state list` sort en
    erreur pour une raison qui n'a rien a voir avec le verrou).
    """
    cwd = applied
    debut = time.monotonic()
    proc = _apply_arriere_plan(cwd, "-replace=terraform_data.lent")
    verrou = _attendre_verrou(cwd)
    if verrou is None:
        proc.kill()
        pytest.fail(
            "Aucun fichier de verrou n'est apparu : l'apply se termine trop vite "
            "pour qu'un verrou soit observable. La commande du provisioner doit "
            f"tenir l'apply au moins {DUREE_MINIMALE:.0f} secondes."
        )

    chemin_relatif = verrou.relative_to(cwd).as_posix()
    contenu = json.loads(verrou.read_text(encoding="utf-8"))
    lock_id = contenu.get("ID", "")

    # Les gestes rejetes d'abord (immediats), les lectures ensuite, le plan
    # complet en dernier : c'est le plus lent, il ne doit pas manger le verrou.
    codes = {}
    codes["plan"] = terraform(
        "plan", "-input=false", "-no-color", "-lock-timeout=0s", cwd=cwd).returncode
    codes["apply"] = terraform(
        "apply", "-auto-approve", "-input=false", "-no-color", cwd=cwd).returncode
    codes["force_unlock"] = terraform(
        "force-unlock", "-force", lock_id, cwd=cwd).returncode
    codes["state_list"] = terraform("state", "list", cwd=cwd).returncode
    codes["show_json"] = terraform("show", "-json", cwd=cwd).returncode
    codes["plan_lock_false"] = terraform(
        "plan", "-input=false", "-no-color", "-lock=false", cwd=cwd).returncode

    if not verrou.exists():
        proc.wait(timeout=DUREE_MAXIMALE)
        pytest.fail(
            "Le verrou s'est libere avant la fin des mesures : l'apply est trop "
            f"court. Il doit tenir au moins {DUREE_MINIMALE:.0f} secondes."
        )

    proc.wait(timeout=DUREE_MAXIMALE)
    duree = time.monotonic() - debut
    if proc.returncode != 0:
        pytest.fail(f"L'apply de remplacement a echoue (code {proc.returncode}).")

    return {
        "cwd": cwd,
        "verrou_chemin": chemin_relatif,
        "verrou_contenu": contenu,
        "codes": codes,
        "duree": duree,
        "verrou_apres": [p.relative_to(cwd).as_posix() for p in cwd.rglob("*.lock.info")],
    }


@pytest.fixture(scope="module")
def residuel(mesures: dict) -> dict:
    """Fabrique un verrou residuel par `kill -9` et mesure ce qu'il bloque."""
    cwd = mesures["cwd"]
    proc = _apply_arriere_plan(cwd, "-replace=terraform_data.lent")
    verrou = _attendre_verrou(cwd)
    if verrou is None:
        proc.kill()
        pytest.fail("Aucun verrou observable : l'apply est trop court.")

    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    proc.wait(timeout=30)
    time.sleep(1.0)

    present_avant = verrou.exists()
    plan = terraform("plan", "-input=false", "-no-color", cwd=cwd)
    return {
        "present_avant": present_avant,
        "plan_rc": plan.returncode,
        "plan_stderr": plan.stderr[-800:],
        "subsiste_apres": verrou.exists(),
    }


# --------------------------------------------------------------------------
# 1. Le state est hors racine : c'est ce qui rend le verrou observable ailleurs
# --------------------------------------------------------------------------

def test_state_hors_racine(applied: Path) -> None:
    backend = json.loads(
        (applied / ".terraform" / "terraform.tfstate").read_text(encoding="utf-8")
    )["backend"]
    assert backend["type"] == "local", (
        f"backend type = {backend['type']}, attendu local."
    )
    assert backend["config"].get("path") == STATE_ATTENDU, (
        f"path resolu = {backend['config'].get('path')!r}, attendu "
        f"{STATE_ATTENDU!r} : le state doit sortir de la racine du projet."
    )
    assert (applied / STATE_ATTENDU).is_file(), (
        f"Le state doit exister en {STATE_ATTENDU}."
    )


# --------------------------------------------------------------------------
# 2. L'apply est assez lent pour qu'un verrou soit observable
# --------------------------------------------------------------------------

def test_apply_assez_lent(mesures: dict) -> None:
    duree = mesures["duree"]
    assert duree >= DUREE_MINIMALE, (
        f"L'apply de remplacement a dure {duree:.1f}s, il en faut au moins "
        f"{DUREE_MINIMALE:.0f} pour mener les mesures pendant le verrou."
    )
    ressources = show_json(mesures["cwd"])["values"]["root_module"]["resources"]
    lentes = [r for r in ressources
              if r["address"] == "terraform_data.lent" and r.get("mode") == "managed"]
    assert lentes, "terraform_data.lent doit figurer au state en mode managed."


# --------------------------------------------------------------------------
# 3. Le verrou reel : sept champs, et un Path qui designe le STATE
# --------------------------------------------------------------------------

def test_forme_du_verrou(mesures: dict) -> None:
    verrou = mesures["verrou_contenu"]
    assert set(verrou) == {"ID", "Operation", "Info", "Who", "Version", "Created", "Path"}, (
        f"Le verrou porte les cles {sorted(verrou)}, attendu les sept champs "
        "ID, Operation, Info, Who, Version, Created, Path."
    )
    assert verrou["Operation"] == "OperationTypeApply", (
        f"Operation = {verrou['Operation']!r}, attendu OperationTypeApply."
    )
    assert UUID_RE.match(verrou["ID"]), f"ID = {verrou['ID']!r}, attendu un UUID."
    assert verrou["Version"] == _version_cli(), (
        f"Version = {verrou['Version']!r} alors que la CLI est en "
        f"{_version_cli()!r} : le champ reflete la CLI qui a pose le verrou."
    )
    assert verrou["Path"] == STATE_ATTENDU, (
        f"Path = {verrou['Path']!r}, attendu {STATE_ATTENDU!r} : le champ "
        "designe le state verrouille, pas le fichier de verrou."
    )


# --------------------------------------------------------------------------
# 4. L'emplacement declare est celui qui a ete observe
# --------------------------------------------------------------------------

def test_emplacement_du_verrou(mesures: dict) -> None:
    declare = _declare(mesures["cwd"], "fichier_verrou")
    reel = mesures["verrou_chemin"]
    assert declare == reel, (
        f"fichier_verrou declare {declare!r}, verrou reellement observe en "
        f"{reel!r}. Le nom du fichier se derive du chemin du state, il n'est "
        "pas fixe."
    )


# --------------------------------------------------------------------------
# 5. Ce que le verrou rejette, et ce qu'il laisse passer
# --------------------------------------------------------------------------

def test_codes_pendant_verrou(mesures: dict) -> None:
    declares = _declare(mesures["cwd"], "codes_pendant_verrou")
    assert isinstance(declares, dict), (
        f"codes_pendant_verrou vaut {declares!r}, attendu un objet."
    )
    manquants = set(mesures["codes"]) - set(declares)
    assert not manquants, f"Gestes non renseignes dans codes_pendant_verrou : {sorted(manquants)}."

    ecarts = []
    for geste, mesure in mesures["codes"].items():
        declare = _entier(declares[geste], f"codes_pendant_verrou.{geste}")
        if declare != mesure:
            ecarts.append(f"{geste} : declare {declare}, mesure {mesure}")
    assert not ecarts, (
        "Ces gestes ne se comportent pas comme vous l'avez ecrit, pendant un "
        "verrou reellement tenu :\n  " + "\n  ".join(ecarts)
    )


# --------------------------------------------------------------------------
# 6. Le fichier de verrou laisse par un arret brutal ne bloque rien
# --------------------------------------------------------------------------

def test_verrou_residuel(mesures: dict, residuel: dict) -> None:
    assert residuel["present_avant"], (
        "Le fichier de verrou n'a pas survecu au kill -9 : mesure impossible."
    )
    declares = _declare(mesures["cwd"], "verrou_residuel")
    assert isinstance(declares, dict), (
        f"verrou_residuel vaut {declares!r}, attendu un objet."
    )
    for cle in ("plan_rc", "fichier_subsiste"):
        assert cle in declares, f"verrou_residuel.{cle} est absent."

    plan_declare = _entier(declares["plan_rc"], "verrou_residuel.plan_rc")
    assert plan_declare == residuel["plan_rc"], (
        f"verrou_residuel.plan_rc declare {plan_declare}, mesure "
        f"{residuel['plan_rc']} : un fichier de verrou laisse par un arret "
        "brutal ne bloque pas le plan suivant, le verrou local est un verrou "
        f"systeme libere par le noyau.\n{residuel['plan_stderr']}"
    )
    subsiste_declare = _booleen(declares["fichier_subsiste"], "verrou_residuel.fichier_subsiste")
    assert subsiste_declare == residuel["subsiste_apres"], (
        f"verrou_residuel.fichier_subsiste declare {subsiste_declare}, mesure "
        f"{residuel['subsiste_apres']} : c'est Terraform qui fait le menage, "
        "le `rm` enseigne ici et la est un rituel sans effet."
    )


# --------------------------------------------------------------------------
# 7. Le verrouillage S3 est opt-in, et DynamoDB est deprecie
# --------------------------------------------------------------------------

def test_backend_s3(mesures: dict) -> None:
    declares = _declare(mesures["cwd"], "backend_s3")
    assert isinstance(declares, dict), (
        f"backend_s3 vaut {declares!r}, attendu un objet."
    )
    for cle in S3_ATTENDU:
        assert cle in declares, f"backend_s3.{cle} est absent."

    assert declares["argument"] == S3_ATTENDU["argument"], (
        f"backend_s3.argument declare {declares['argument']!r}, attendu "
        f"{S3_ATTENDU['argument']!r} : c'est l'argument qui active le "
        "verrouillage natif du backend S3."
    )
    actif = _booleen(declares["actif_par_defaut"], "backend_s3.actif_par_defaut")
    assert actif is S3_ATTENDU["actif_par_defaut"], (
        "backend_s3.actif_par_defaut declare true : le verrouillage S3 est "
        "opt-in, l'argument vaut false par defaut. Un state S3 sans "
        "use_lockfile n'est pas protege."
    )
    deprecie = _booleen(declares["dynamodb_deprecie"], "backend_s3.dynamodb_deprecie")
    assert deprecie is S3_ATTENDU["dynamodb_deprecie"], (
        "backend_s3.dynamodb_deprecie declare false : le verrouillage par "
        "table DynamoDB est deprecie et sera retire dans une version mineure."
    )


# --------------------------------------------------------------------------
# 8. Le verrou est libere a la fin, et le projet reste convergent
# --------------------------------------------------------------------------

def test_aucun_verrou_apres_apply(mesures: dict) -> None:
    restants = mesures["verrou_apres"]
    assert not restants, (
        f"Des fichiers de verrou subsistent apres la fin de l'apply : {restants}."
    )


def test_idempotence(mesures: dict, residuel: dict) -> None:
    cwd = mesures["cwd"]
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=cwd)
    assert app.returncode == 0, f"`terraform apply` a echoue.\n{app.stderr[-1200:]}"
    plan = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=cwd)
    assert plan.returncode == 0, (
        f"plan -detailed-exitcode rend {plan.returncode}, attendu 0 : le state "
        "doit decrire la realite une fois le projet converge."
    )
