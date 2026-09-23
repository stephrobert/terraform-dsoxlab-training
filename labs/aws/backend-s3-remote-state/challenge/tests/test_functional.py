"""Tests fonctionnels du lab « un state distant, verrouille, et lu ».

Aucun test n'ouvre un `.tf` de l'apprenant, aucun ne lit une sortie humaine de
Terraform. Tout passe par l'etat structure, par la configuration de backend que
Terraform ecrit lui-meme, et par l'API S3 de l'emulateur.

Faits verifies sur Terraform 1.15.4, contre Floci 1.6.0 en local, sans aucun
compte AWS :

- un bloc `backend` refuse toute valeur nommee (`Error: Variables not allowed`) ;
- le verrouillage S3 est un OPT-IN strict : avec `use_lockfile = true`, un objet
  `.tflock` depose a la main fait echouer `plan -lock-timeout=0s` en code 1 ;
  sans l'argument, le MEME objet est ignore et le plan sort en 0 ;
- apres migration, il ne reste AUCUN `terraform.tfstate` local ;
- `defaults` comble un output MANQUANT dans un etat qui EXISTE, jamais un etat
  absent : sur une cle inexistante, Terraform rend « Unable to find remote
  state » en code 1.
"""

import json
import os
import socket
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "aws-backend-s3-remote-state"

ENDPOINT = "http://localhost:14566"
BUCKET = "tf-state-lab"
REPLI = "maintenance_window"

ENV = {
    **os.environ,
    "AWS_ACCESS_KEY_ID": "test",
    "AWS_SECRET_ACCESS_KEY": "test",
    "AWS_DEFAULT_REGION": "eu-west-3",
    "AWS_PAGER": "",
}


# ── Helpers ─────────────────────────────────────────────────────────────────


def _tf(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["terraform", *args], cwd=cwd, capture_output=True, text=True, env=ENV,
        check=False,
    )


def _aws(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["aws", "--endpoint-url", ENDPOINT, *args],
        capture_output=True, text=True, env=ENV,
        check=False,
    )


def _stack(travail: Path, nom: str) -> Path:
    chemin = travail / nom
    if not chemin.is_dir():
        pytest.fail(f"Le repertoire {nom}/ est absent de challenge/work.")
    return chemin


def _backend_retenu(travail: Path, nom: str) -> dict:
    """Configuration de backend telle que Terraform l'a ENREGISTREE."""
    chemin = _stack(travail, nom) / ".terraform" / "terraform.tfstate"
    if not chemin.is_file():
        pytest.fail(
            f"{nom}/.terraform/terraform.tfstate est absent : `terraform init` "
            "n'a jamais abouti dans cette stack."
        )
    return json.loads(chemin.read_text(encoding="utf-8")).get("backend", {})


def _sorties(travail: Path, nom: str) -> dict:
    rendu = _tf("output", "-json", cwd=_stack(travail, nom))
    if rendu.returncode != 0:
        pytest.fail(f"`terraform output -json` echoue dans {nom}/.\n{rendu.stderr[-700:]}")
    return json.loads(rendu.stdout or "{}")


def _etat(travail: Path, nom: str) -> dict:
    montre = _tf("show", "-json", cwd=_stack(travail, nom))
    if montre.returncode != 0:
        pytest.fail(f"`terraform show -json` echoue dans {nom}/.\n{montre.stderr[-700:]}")
    return json.loads(montre.stdout or "{}")


def _porte_des_ressources(stack: Path) -> bool:
    """True si la stack a deja un etat non vide, qu'il soit local ou distant.

    On interroge Terraform plutot que de chercher un `terraform.tfstate` sur le
    disque : le producer garde le sien dans le bucket, donc l'absence de fichier
    local n'y prouve rien.
    """
    res = _tf("show", "-json", cwd=stack)
    if res.returncode != 0:
        return False
    try:
        etat = json.loads(res.stdout or "{}")
    except json.JSONDecodeError:
        return False
    module = etat.get("values", {}).get("root_module", {})
    return bool(module.get("resources"))



# ── Disponibilite de l'emulateur ────────────────────────────────────────────
#
# Floci est publie sur le port 14566 de l'hote (cf. `runtime.services` du lab).
# Il n'est demarre QUE pendant une session `dsoxlab` : hors session, le port est
# ferme et chaque commande Terraform echoue sur un point de terminaison
# injoignable. Sans la garde ci-dessous, l'apprenant lit une pile d'erreurs
# Terraform la ou une seule phrase suffit.
FLOCI_HOST = "127.0.0.1"
FLOCI_PORT = 14566


def _floci_joignable() -> bool:
    try:
        with socket.create_connection((FLOCI_HOST, FLOCI_PORT), timeout=2):
            return True
    except OSError:
        return False


def _exiger_floci() -> None:
    """Skippe proprement si l'emulateur n'est pas la, sauf pour le formateur.

    `LAB_WORKDIR` est pose par `scripts/verify-solutions.py`, qui materialise
    lui-meme le repertoire : dans ce cas un service absent est un vrai defaut et
    doit ECHOUER, pas disparaitre dans un skip.
    """
    if _floci_joignable():
        return
    message = (
        f"Floci n'est pas joignable sur {FLOCI_HOST}:{FLOCI_PORT}. Ce lab en a "
        "besoin : Floci emule l'API AWS en local, sans compte ni carte "
        "bancaire.\n\n"
        "Lancez le lab avec `dsoxlab run aws-backend-s3-remote-state`, qui le demarre tout "
        "seul, et faites votre `dsoxlab check` DEPUIS cette session : le "
        "service s'arrete quand vous la quittez."
    )
    if os.environ.get("LAB_WORKDIR"):
        pytest.fail(message)
    pytest.skip(message)

@pytest.fixture(scope="module")
def travail() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    _exiger_floci()

    # La sonde est REESSAYEE : un emulateur conteneurise refuse parfois une
    # requete isolee alors qu'il est sain, notamment quand plusieurs rejeux
    # s'enchainent. Mesure a l'appui : une meme suite echouait en 1,5 s sur
    # cette seule ligne, puis passait en 19 s quelques secondes plus tard,
    # bucket intact et conteneur `healthy`. Un test qui tombe pour cela mesure
    # sa propre impatience, pas le travail de l'apprenant.
    sonde = None
    for _tentative in range(6):
        sonde = _aws("s3", "ls")
        if sonde.returncode == 0:
            break
        time.sleep(2)
    if sonde is None or sonde.returncode != 0:
        pytest.fail(
            f"L'emulateur S3 ne repond pas sur {ENDPOINT} apres 6 tentatives. "
            "Le lab le declare en `runtime.services` : `dsoxlab run` et "
            "`dsoxlab check` le demarrent tout seuls.\n"
            f"{sonde.stderr[-400:] if sonde else ''}"
        )

    # L'ordre compte, et il n'est pas negociable : le backend du producer VIT
    # dans le bucket que le bootstrap cree. Initialiser le producer avant
    # d'avoir applique le bootstrap echoue donc sur un emulateur neuf, avec
    # « Failed to get existing workspaces: S3 bucket does not exist ». C'est
    # pourquoi init et apply sont traites stack par stack, dans l'ordre des
    # dependances, et non en deux boucles separees.
    #
    # Aucun etat n'est fige dans la solution de reference, et c'est delibere.
    #
    # Deux raisons, toutes deux constatees. D'abord le consumer LIT un state
    # distant, donc partage : sa valeur n'est juste qu'au moment de son propre
    # apply, et une re-application du producer regenere `random_pet` en amont,
    # ce qui perime son etat. Ensuite un rejeu peut partir d'un emulateur NEUF,
    # car recreer son conteneur vide son contenu et le bucket disparait avec
    # lui ; un etat fige affirmerait alors l'existence d'un bucket absent.
    #
    # On applique donc chaque stack UNIQUEMENT quand elle ne porte aucune
    # ressource, dans l'ordre de leurs dependances. Pour l'apprenant, qui a
    # applique lui-meme, les etats existent : rien n'est joue a sa place, et
    # une stack jamais appliquee continue de faire echouer les tests qui la
    # verifient.
    # Le bootstrap cree une ressource PARTAGEE par tous les rejeux : le bucket.
    # Son idempotence se juge donc sur l'API de l'emulateur, jamais sur un etat
    # local. Le reappliquer alors que le bucket existe deja rendrait
    # `BucketAlreadyOwnedByYou` (HTTP 409), constate en rejouant deux fois de
    # suite dans deux repertoires differents.
    a_faire = ["producer", "consumer"]
    if _aws("s3api", "head-bucket", "--bucket", BUCKET).returncode != 0:
        a_faire.insert(0, "bootstrap")

    for nom in a_faire:
        stack = WORKDIR / nom
        if not stack.is_dir() or _porte_des_ressources(stack):
            continue
        # Une stack appliquee a neuf a besoin d'un `init` a jour : le fichier de
        # verrouillage livre avec les fixtures peut ne pas selectionner tous les
        # providers de la solution, et l'apply rendrait alors « Inconsistent
        # dependency lock file ». L'init est idempotent, il ne coute rien ici.
        _tf("init", "-input=false", "-no-color", cwd=stack)
        applique = _tf("apply", "-auto-approve", "-input=false", "-no-color",
                       cwd=stack)
        if applique.returncode != 0:
            pytest.fail(
                f"`terraform apply` echoue dans {nom}/ alors que cette stack ne "
                f"portait aucune ressource.\n{applique.stderr[-800:]}"
            )

    yield WORKDIR


# ── 1. Le bucket de state ───────────────────────────────────────────────────


def test_le_bucket_de_state_est_conforme(travail: Path) -> None:
    assert _aws("s3api", "head-bucket", "--bucket", BUCKET).returncode == 0, (
        f"Le bucket {BUCKET} n'existe pas sur l'emulateur : le bootstrap "
        "a-t-il ete applique ?"
    )

    versioning = _aws("s3api", "get-bucket-versioning", "--bucket", BUCKET,
                      "--output", "json")
    assert json.loads(versioning.stdout or "{}").get("Status") == "Enabled", (
        "Le versioning du bucket n'est pas actif. C'est lui qui permet de "
        "revenir a une version anterieure du state."
    )


# ── 2. Le backend du producer ───────────────────────────────────────────────


def test_le_backend_du_producer_est_bien_configure(travail: Path) -> None:
    backend = _backend_retenu(travail, "producer")
    assert backend.get("type") == "s3", (
        f"Le producer utilise un backend {backend.get('type')!r}, attendu `s3`."
    )

    config = backend.get("config") or {}
    assert config.get("bucket") == BUCKET, (
        f"Le backend pointe le bucket {config.get('bucket')!r}, attendu {BUCKET!r}."
    )
    assert config.get("key"), "Aucune `key` dans la configuration de backend."
    assert config.get("use_path_style") is True, (
        "`use_path_style` n'est pas actif : le backend ne peut pas parler a un "
        "emulateur local sans lui."
    )

    endpoints = config.get("endpoints") or {}
    assert endpoints.get("s3"), (
        "Aucun `endpoints.s3` : sans lui, Terraform s'adresse a AWS et non a "
        "l'emulateur."
    )

    assert config.get("use_lockfile") is True, (
        "`use_lockfile` n'est pas actif. Le verrouillage du backend S3 est un "
        "OPT-IN : sans cet argument, un fichier de verrou est purement ignore "
        "et deux applies concurrents s'ecrasent."
    )


def test_le_state_du_producer_est_distant_et_pas_local(travail: Path) -> None:
    cle = (_backend_retenu(travail, "producer").get("config") or {})["key"]

    objets = _aws("s3api", "list-objects-v2", "--bucket", BUCKET, "--output", "json")
    cles = [o["Key"] for o in json.loads(objets.stdout or "{}").get("Contents", [])]
    assert cle in cles, (
        f"L'objet de state {cle!r} n'est pas dans le bucket. Objets presents : "
        f"{cles}"
    )

    # Les deux ensemble, jamais l'un seul : un state distant qui laisserait une
    # copie locale ne prouverait pas la migration.
    locaux = sorted(p.name for p in _stack(travail, "producer").glob("terraform.tfstate*"))
    assert not locaux, (
        f"Le producer garde un state local : {locaux}. Apres migration vers S3, "
        "il ne doit en rester aucun."
    )


# ── 3. Le verrou, par difference de codes retour ────────────────────────────


def test_le_verrou_est_effectif(travail: Path, tmp_path: Path) -> None:
    """Le controle central : un `.tflock` depose a la main doit bloquer."""
    cle = (_backend_retenu(travail, "producer").get("config") or {})["key"]
    verrou = f"{cle}.tflock"

    contenu = tmp_path / "lock.json"
    contenu.write_text(json.dumps({
        "ID": "00000000-0000-0000-0000-000000000000",
        "Operation": "OperationTypePlan",
        "Who": "validation",
        "Version": "1.15.4",
        "Created": "2026-07-31T00:00:00Z",
        "Path": "",
    }), encoding="utf-8")

    depot = _aws("s3", "cp", str(contenu), f"s3://{BUCKET}/{verrou}")
    assert depot.returncode == 0, f"Impossible de deposer le verrou.\n{depot.stderr[-400:]}"

    try:
        bloque = _tf("plan", "-input=false", "-no-color", "-lock-timeout=0s",
                     cwd=_stack(travail, "producer"))
        assert bloque.returncode != 0, (
            "Un objet .tflock est present dans le bucket et le plan passe quand "
            "meme : le verrouillage n'est donc PAS actif. C'est exactement ce "
            "que `use_lockfile = true` doit empecher."
        )
        assert "state lock" in (bloque.stdout + bloque.stderr).lower(), (
            "Le plan echoue, mais pas sur le verrou d'etat.\n"
            f"{(bloque.stdout + bloque.stderr)[-500:]}"
        )
    finally:
        _aws("s3", "rm", f"s3://{BUCKET}/{verrou}")

    libre = _tf("plan", "-input=false", "-no-color", "-lock-timeout=0s",
                cwd=_stack(travail, "producer"))
    assert libre.returncode == 0, (
        f"Le verrou retire, le plan rend {libre.returncode} au lieu de 0.\n"
        f"{(libre.stdout + libre.stderr)[-500:]}"
    )


# ── 4. Le consumer lit l'etat distant ───────────────────────────────────────


def test_le_consumer_ne_gere_rien_et_lit_l_amont(travail: Path) -> None:
    ressources = (
        _etat(travail, "consumer")
        .get("values", {}).get("root_module", {}).get("resources", [])
    )
    gerees = [r for r in ressources if r.get("mode") == "managed"]
    assert not gerees, (
        f"Le consumer gere {len(gerees)} ressource(s) : {[r['address'] for r in gerees]}. "
        "Il ne doit rien creer, seulement lire l'amont."
    )

    donnees = [r for r in ressources if r.get("mode") == "data"]
    assert len(donnees) == 1, (
        f"Le consumer porte {len(donnees)} source(s) de donnees, attendu 1."
    )
    seule = donnees[0]
    assert seule.get("type") == "terraform_remote_state", (
        f"La source est de type {seule.get('type')!r}, attendu "
        "`terraform_remote_state`."
    )
    assert seule.get("provider_name") == "terraform.io/builtin/terraform", (
        f"La source est servie par {seule.get('provider_name')!r}, attendu le "
        "fournisseur integre `terraform.io/builtin/terraform`."
    )


def test_les_sorties_du_consumer_valent_celles_du_producer(travail: Path) -> None:
    amont = _sorties(travail, "producer")
    aval = _sorties(travail, "consumer")
    for nom in ("network_name", "network_cidr", "region"):
        assert nom in aval, f"Le consumer n'expose pas `{nom}`."
        assert aval[nom]["value"] == amont[nom]["value"], (
            f"`{nom}` vaut {aval[nom]['value']!r} en aval et "
            f"{amont[nom]['value']!r} en amont."
        )


def test_le_repli_joue_pour_une_sortie_absente(travail: Path) -> None:
    """`defaults` comble un output MANQUANT dans un etat qui existe."""
    amont = _sorties(travail, "producer")
    assert REPLI not in amont, (
        f"Le producer publie `{REPLI}` : le repli ne prouverait alors rien. "
        "Cette sortie doit rester absente de l'amont."
    )
    aval = _sorties(travail, "consumer")
    assert REPLI in aval, f"Le consumer n'expose pas `{REPLI}`."
    valeur = aval[REPLI]["value"]
    assert valeur not in (None, ""), (
        f"`{REPLI}` est vide alors que le producer ne le publie pas : le bloc "
        "`defaults` doit fournir une valeur de repli."
    )


def test_la_valeur_amont_se_propage(travail: Path, tmp_path: Path) -> None:
    """Une valeur recopiee a la main resterait figee ; celle-ci doit suivre."""
    avant = _sorties(travail, "consumer")["network_name"]["value"]

    rejoue = _tf("apply", "-auto-approve", "-input=false", "-no-color",
                 "-var", "graine=validation", cwd=_stack(travail, "producer"))
    assert rejoue.returncode == 0, (
        f"Impossible de rejouer le producer.\n{rejoue.stderr[-600:]}"
    )
    try:
        suivi = _tf("apply", "-auto-approve", "-input=false", "-no-color",
                    cwd=_stack(travail, "consumer"))
        assert suivi.returncode == 0, (
            f"Impossible de rejouer le consumer.\n{suivi.stderr[-600:]}"
        )
        apres_amont = _sorties(travail, "producer")["network_name"]["value"]
        apres_aval = _sorties(travail, "consumer")["network_name"]["value"]
        assert apres_amont != avant, (
            "Le producer rejoue avec une autre graine produit la meme valeur : "
            "le temoin ne discrimine pas."
        )
        assert apres_aval == apres_amont, (
            f"Le producer publie maintenant {apres_amont!r} et le consumer "
            f"expose {apres_aval!r} : la valeur a ete RECOPIEE au lieu d'etre "
            "lue dans l'etat distant."
        )
    finally:
        # On remet l'amont dans son etat initial, puis l'aval a jour.
        _tf("apply", "-auto-approve", "-input=false", "-no-color",
            cwd=_stack(travail, "producer"))
        _tf("apply", "-auto-approve", "-input=false", "-no-color",
            cwd=_stack(travail, "consumer"))


# ── 5. Convergence ──────────────────────────────────────────────────────────


def test_les_deux_stacks_sont_idempotentes(travail: Path) -> None:
    for nom in ("producer", "consumer"):
        plan = _tf("plan", "-input=false", "-detailed-exitcode", "-no-color",
                   cwd=_stack(travail, nom))
        assert plan.returncode == 0, (
            f"{nom} : `plan -detailed-exitcode` rend {plan.returncode}, "
            f"attendu 0.\n{(plan.stdout + plan.stderr)[-600:]}"
        )
