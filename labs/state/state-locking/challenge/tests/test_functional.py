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

from conftest import (
    exiger_workdir,
    message,
    output_json,
    show_json,
    terraform,
    workdir_lab,
)

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
        pytest.fail(message(
            en=f"{ou} is {valeur!r}: an integer return code was expected.",
            fr=f"{ou} vaut {valeur!r} : attendu un code de retour entier.",
        ))


def _booleen(valeur: object, ou: str) -> bool:
    if isinstance(valeur, bool):
        return valeur
    if isinstance(valeur, str) and valeur.lower() in ("true", "false"):
        return valeur.lower() == "true"
    pytest.fail(message(
        en=f"{ou} is {valeur!r}: true or false was expected.",
        fr=f"{ou} vaut {valeur!r} : attendu true ou false.",
    ))


def _declare(cwd: Path, nom: str) -> object:
    sorties = output_json(cwd)
    if nom not in sorties:
        pytest.fail(
            message(
            en=f"The output `{nom}` is missing. observations.tf must declare the "
            "four outputs of the provided file, without removing any.",
            fr=f"L'output `{nom}` est absent. observations.tf doit déclarer les "
            "quatre outputs du fichier fourni, sans en retirer aucun.",
        )
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
            message(
            en="`terraform init` failed. A leftover `???` in the backend block?"
            f"\n{init.stderr[-1200:]}",
            fr="`terraform init` a échoué. Un `???` restant dans le bloc backend ?"
            f"\n{init.stderr[-1200:]}",
        )
        )
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(message(
            en=f"`terraform apply` failed.\n{app.stderr[-1500:]}",
            fr=f"`terraform apply` a échoué.\n{app.stderr[-1500:]}",
        ))
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
            message(
            en="No lock file appeared: the apply finishes too fast "
            "for a lock to be observable. The provisioner's command must "
            f"hold the apply for at least {DUREE_MINIMALE:.0f} seconds.",
            fr="Aucun fichier de verrou n'est apparu : l'apply se termine trop vite "
            "pour qu'un verrou soit observable. La commande du provisioner doit "
            f"tenir l'apply au moins {DUREE_MINIMALE:.0f} secondes.",
        )
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
            message(
            en="The lock was released before the measurements ended: the apply is too "
            f"short. It must hold for at least {DUREE_MINIMALE:.0f} seconds.",
            fr="Le verrou s'est libéré avant la fin des mesures : l'apply est trop "
            f"court. Il doit tenir au moins {DUREE_MINIMALE:.0f} secondes.",
        )
        )

    proc.wait(timeout=DUREE_MAXIMALE)
    duree = time.monotonic() - debut
    if proc.returncode != 0:
        pytest.fail(message(
            en=f"The replacement apply failed (code {proc.returncode}).",
            fr=f"L'apply de remplacement a échoué (code {proc.returncode}).",
        ))

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
        pytest.fail(message(
            en="No observable lock: the apply is too short.",
            fr="Aucun verrou observable : l'apply est trop court.",
        ))

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
    assert backend["type"] == "local", message(
        en=f"backend type = {backend['type']}, expected local.",
        fr=f"backend type = {backend['type']}, attendu local.",
    )
    assert backend["config"].get("path") == STATE_ATTENDU, message(
        en=f"resolved path = {backend['config'].get('path')!r}, expected "
        f"{STATE_ATTENDU!r}: the state must live outside the project root.",
        fr=f"path résolu = {backend['config'].get('path')!r}, attendu "
        f"{STATE_ATTENDU!r} : le state doit sortir de la racine du projet.",
    )
    assert (applied / STATE_ATTENDU).is_file(), message(
        en=f"The state must exist at {STATE_ATTENDU}.",
        fr=f"Le state doit exister en {STATE_ATTENDU}.",
    )


# --------------------------------------------------------------------------
# 2. L'apply est assez lent pour qu'un verrou soit observable
# --------------------------------------------------------------------------

def test_apply_assez_lent(mesures: dict) -> None:
    duree = mesures["duree"]
    assert duree >= DUREE_MINIMALE, message(
        en=f"The replacement apply lasted {duree:.1f}s; at least "
        f"{DUREE_MINIMALE:.0f} are needed to take the measurements while the lock is held.",
        fr=f"L'apply de remplacement a duré {duree:.1f}s, il en faut au moins "
        f"{DUREE_MINIMALE:.0f} pour mener les mesures pendant le verrou.",
    )
    ressources = show_json(mesures["cwd"])["values"]["root_module"]["resources"]
    lentes = [r for r in ressources
              if r["address"] == "terraform_data.lent" and r.get("mode") == "managed"]
    assert lentes, message(
        en="terraform_data.lent must appear in the state in managed mode.",
        fr="terraform_data.lent doit figurer au state en mode managed.",
    )


# --------------------------------------------------------------------------
# 3. Le verrou reel : sept champs, et un Path qui designe le STATE
# --------------------------------------------------------------------------

def test_forme_du_verrou(mesures: dict) -> None:
    verrou = mesures["verrou_contenu"]
    assert set(verrou) == {"ID", "Operation", "Info", "Who", "Version", "Created", "Path"}, message(
        en=f"The lock carries the keys {sorted(verrou)}, expected the seven fields "
        "ID, Operation, Info, Who, Version, Created, Path.",
        fr=f"Le verrou porte les clés {sorted(verrou)}, attendu les sept champs "
        "ID, Operation, Info, Who, Version, Created, Path.",
    )
    assert verrou["Operation"] == "OperationTypeApply", message(
        en=f"Operation = {verrou['Operation']!r}, expected OperationTypeApply.",
        fr=f"Operation = {verrou['Operation']!r}, attendu OperationTypeApply.",
    )
    assert UUID_RE.match(verrou["ID"]), message(
        en=f"ID = {verrou['ID']!r}, a UUID was expected.",
        fr=f"ID = {verrou['ID']!r}, attendu un UUID.",
    )
    assert verrou["Version"] == _version_cli(), message(
        en=f"Version = {verrou['Version']!r} while the CLI is "
        f"{_version_cli()!r}: the field reflects the CLI that placed the lock.",
        fr=f"Version = {verrou['Version']!r} alors que la CLI est en "
        f"{_version_cli()!r} : le champ reflète la CLI qui a posé le verrou.",
    )
    assert verrou["Path"] == STATE_ATTENDU, message(
        en=f"Path = {verrou['Path']!r}, expected {STATE_ATTENDU!r}: the field "
        "names the locked state, not the lock file.",
        fr=f"Path = {verrou['Path']!r}, attendu {STATE_ATTENDU!r} : le champ "
        "désigne le state verrouillé, pas le fichier de verrou.",
    )


# --------------------------------------------------------------------------
# 4. L'emplacement declare est celui qui a ete observe
# --------------------------------------------------------------------------

def test_emplacement_du_verrou(mesures: dict) -> None:
    declare = _declare(mesures["cwd"], "fichier_verrou")
    reel = mesures["verrou_chemin"]
    assert declare == reel, message(
        en=f"fichier_verrou declares {declare!r}, the lock actually observed at "
        f"{reel!r}. The file's name is derived from the state's path, it is "
        "not fixed.",
        fr=f"fichier_verrou déclare {declare!r}, verrou réellement observé en "
        f"{reel!r}. Le nom du fichier se dérive du chemin du state, il n'est "
        "pas fixe.",
    )


# --------------------------------------------------------------------------
# 5. Ce que le verrou rejette, et ce qu'il laisse passer
# --------------------------------------------------------------------------

def test_codes_pendant_verrou(mesures: dict) -> None:
    declares = _declare(mesures["cwd"], "codes_pendant_verrou")
    assert isinstance(declares, dict), message(
        en=f"codes_pendant_verrou is {declares!r}, an object was expected.",
        fr=f"codes_pendant_verrou vaut {declares!r}, attendu un objet.",
    )
    manquants = set(mesures["codes"]) - set(declares)
    assert not manquants, message(
        en=f"Actions not filled in under codes_pendant_verrou: {sorted(manquants)}.",
        fr=f"Gestes non renseignés dans codes_pendant_verrou : {sorted(manquants)}.",
    )

    ecarts = []
    for geste, mesure in mesures["codes"].items():
        declare = _entier(declares[geste], f"codes_pendant_verrou.{geste}")
        if declare != mesure:
            ecarts.append(f"{geste} : declare {declare}, mesure {mesure}")
    assert not ecarts, message(
        en="These actions do not behave as you wrote, while a lock is "
        "really held:\n  " + "\n  ".join(ecarts),
        fr="Ces gestes ne se comportent pas comme vous l'avez écrit, pendant un "
        "verrou réellement tenu :\n  " + "\n  ".join(ecarts),
    )


# --------------------------------------------------------------------------
# 6. Le fichier de verrou laisse par un arret brutal ne bloque rien
# --------------------------------------------------------------------------

def test_verrou_residuel(mesures: dict, residuel: dict) -> None:
    assert residuel["present_avant"], message(
        en="The lock file did not survive the kill -9: measurement impossible.",
        fr="Le fichier de verrou n'a pas survécu au kill -9 : mesure impossible.",
    )
    declares = _declare(mesures["cwd"], "verrou_residuel")
    assert isinstance(declares, dict), message(
        en=f"verrou_residuel is {declares!r}, an object was expected.",
        fr=f"verrou_residuel vaut {declares!r}, attendu un objet.",
    )
    for cle in ("plan_rc", "fichier_subsiste"):
        assert cle in declares, message(
            en=f"verrou_residuel.{cle} is missing.",
            fr=f"verrou_residuel.{cle} est absent.",
        )

    plan_declare = _entier(declares["plan_rc"], "verrou_residuel.plan_rc")
    assert plan_declare == residuel["plan_rc"], message(
        en=f"verrou_residuel.plan_rc declares {plan_declare}, measured "
        f"{residuel['plan_rc']}: a lock file left behind by an abrupt stop "
        "does not block the next plan, since the local lock is a system "
        f"lock released by the kernel.\n{residuel['plan_stderr']}",
        fr=f"verrou_residuel.plan_rc déclare {plan_declare}, mesuré "
        f"{residuel['plan_rc']} : un fichier de verrou laissé par un arrêt "
        "brutal ne bloque pas le plan suivant, le verrou local est un verrou "
        f"système libéré par le noyau.\n{residuel['plan_stderr']}",
    )
    subsiste_declare = _booleen(declares["fichier_subsiste"], "verrou_residuel.fichier_subsiste")
    assert subsiste_declare == residuel["subsiste_apres"], message(
        en=f"verrou_residuel.fichier_subsiste declares {subsiste_declare}, measured "
        f"{residuel['subsiste_apres']}: it is Terraform that cleans up, and "
        "the `rm` taught here and there is a ritual with no effect.",
        fr=f"verrou_residuel.fichier_subsiste déclare {subsiste_declare}, mesuré "
        f"{residuel['subsiste_apres']} : c'est Terraform qui fait le ménage, "
        "le `rm` enseigné ici et là est un rituel sans effet.",
    )


# --------------------------------------------------------------------------
# 7. Le verrouillage S3 est opt-in, et DynamoDB est deprecie
# --------------------------------------------------------------------------

def test_backend_s3(mesures: dict) -> None:
    declares = _declare(mesures["cwd"], "backend_s3")
    assert isinstance(declares, dict), message(
        en=f"backend_s3 is {declares!r}, an object was expected.",
        fr=f"backend_s3 vaut {declares!r}, attendu un objet.",
    )
    for cle in S3_ATTENDU:
        assert cle in declares, message(
            en=f"backend_s3.{cle} is missing.",
            fr=f"backend_s3.{cle} est absent.",
        )

    assert declares["argument"] == S3_ATTENDU["argument"], message(
        en=f"backend_s3.argument declares {declares['argument']!r}, expected "
        f"{S3_ATTENDU['argument']!r}: that is the argument enabling the S3 "
        "backend's native locking.",
        fr=f"backend_s3.argument déclare {declares['argument']!r}, attendu "
        f"{S3_ATTENDU['argument']!r} : c'est l'argument qui active le "
        "verrouillage natif du backend S3.",
    )
    actif = _booleen(declares["actif_par_defaut"], "backend_s3.actif_par_defaut")
    assert actif is S3_ATTENDU["actif_par_defaut"], message(
        en="backend_s3.actif_par_defaut declares true: S3 locking is "
        "opt-in, the argument defaults to false. An S3 state without "
        "use_lockfile is not protected.",
        fr="backend_s3.actif_par_defaut déclare true : le verrouillage S3 est "
        "opt-in, l'argument vaut false par défaut. Un state S3 sans "
        "use_lockfile n'est pas protégé.",
    )
    deprecie = _booleen(declares["dynamodb_deprecie"], "backend_s3.dynamodb_deprecie")
    assert deprecie is S3_ATTENDU["dynamodb_deprecie"], message(
        en="backend_s3.dynamodb_deprecie declares false: locking through a "
        "DynamoDB table is deprecated and will be removed in a minor version.",
        fr="backend_s3.dynamodb_deprecie déclare false : le verrouillage par "
        "table DynamoDB est déprécié et sera retiré dans une version mineure.",
    )


# --------------------------------------------------------------------------
# 8. Le verrou est libere a la fin, et le projet reste convergent
# --------------------------------------------------------------------------

def test_aucun_verrou_apres_apply(mesures: dict) -> None:
    restants = mesures["verrou_apres"]
    assert not restants, message(
        en=f"Lock files remain after the apply has finished: {restants}.",
        fr=f"Des fichiers de verrou subsistent après la fin de l'apply : {restants}.",
    )


def test_idempotence(mesures: dict, residuel: dict) -> None:
    cwd = mesures["cwd"]
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=cwd)
    assert app.returncode == 0, message(
        en=f"`terraform apply` failed.\n{app.stderr[-1200:]}",
        fr=f"`terraform apply` a échoué.\n{app.stderr[-1200:]}",
    )
    plan = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=cwd)
    assert plan.returncode == 0, message(
        en=f"plan -detailed-exitcode returns {plan.returncode}, expected 0: the state "
        "must describe reality once the project has converged.",
        fr=f"plan -detailed-exitcode rend {plan.returncode}, attendu 0 : le state "
        "doit décrire la réalité une fois le projet convergé.",
    )
