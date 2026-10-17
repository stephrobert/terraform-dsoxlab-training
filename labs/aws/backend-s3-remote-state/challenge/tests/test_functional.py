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

from conftest import exiger_workdir, message, workdir_lab

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
        pytest.fail(message(
            en=f"The {nom}/ directory is missing from challenge/work.",
            fr=f"Le répertoire {nom}/ est absent de challenge/work.",
        ))
    return chemin


def _backend_retenu(travail: Path, nom: str) -> dict:
    """Configuration de backend telle que Terraform l'a ENREGISTREE."""
    chemin = _stack(travail, nom) / ".terraform" / "terraform.tfstate"
    if not chemin.is_file():
        pytest.fail(
            message(
            en=f"{nom}/.terraform/terraform.tfstate is missing: `terraform init` "
            "never succeeded in this stack.",
            fr=f"{nom}/.terraform/terraform.tfstate est absent : `terraform init` "
            "n'a jamais abouti dans cette stack.",
        )
        )
    return json.loads(chemin.read_text(encoding="utf-8")).get("backend", {})


def _sorties(travail: Path, nom: str) -> dict:
    rendu = _tf("output", "-json", cwd=_stack(travail, nom))
    if rendu.returncode != 0:
        pytest.fail(message(
            en=f"`terraform output -json` fails in {nom}/.\n{rendu.stderr[-700:]}",
            fr=f"`terraform output -json` échoue dans {nom}/.\n{rendu.stderr[-700:]}",
        ))
    return json.loads(rendu.stdout or "{}")


def _etat(travail: Path, nom: str) -> dict:
    montre = _tf("show", "-json", cwd=_stack(travail, nom))
    if montre.returncode != 0:
        pytest.fail(message(
            en=f"`terraform show -json` fails in {nom}/.\n{montre.stderr[-700:]}",
            fr=f"`terraform show -json` échoue dans {nom}/.\n{montre.stderr[-700:]}",
        ))
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
    explication = message(
        en=f"Floci cannot be reached on {FLOCI_HOST}:{FLOCI_PORT}. This lab needs "
        "it: Floci emulates the AWS API locally, with no account and no credit "
        "card.\n\n"
        "Start the lab with `dsoxlab run aws-backend-s3-remote-state`, which starts "
        "it on its own, and run your `dsoxlab check` FROM that session: the "
        "service stops when you leave it.",
        fr=f"Floci n'est pas joignable sur {FLOCI_HOST}:{FLOCI_PORT}. Ce lab en a "
        "besoin : Floci émule l'API AWS en local, sans compte ni carte "
        "bancaire.\n\n"
        "Lancez le lab avec `dsoxlab run aws-backend-s3-remote-state`, qui le démarre tout "
        "seul, et faites votre `dsoxlab check` DEPUIS cette session : le "
        "service s'arrête quand vous la quittez.",
    )
    if os.environ.get("LAB_WORKDIR"):
        pytest.fail(explication)
    pytest.skip(explication)

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
            message(
            en=f"The S3 emulator does not answer on {ENDPOINT} after 6 attempts. "
            "The lab declares it under `runtime.services`: `dsoxlab run` and "
            "`dsoxlab check` start it on their own.\n"
            f"{sonde.stderr[-400:] if sonde else ''}",
            fr=f"L'émulateur S3 ne répond pas sur {ENDPOINT} après 6 tentatives. "
            "Le lab le déclare en `runtime.services` : `dsoxlab run` et "
            "`dsoxlab check` le démarrent tout seuls.\n"
            f"{sonde.stderr[-400:] if sonde else ''}",
        )
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
                message(
                en=f"`terraform apply` fails in {nom}/ although that stack carried "
                f"no resource.\n{applique.stderr[-800:]}",
                fr=f"`terraform apply` échoue dans {nom}/ alors que cette stack ne "
                f"portait aucune ressource.\n{applique.stderr[-800:]}",
            )
            )

    yield WORKDIR

    # Teardown : detruire PENDANT que l'emulateur repond encore.
    #
    # Floci lance un conteneur Docker par instance EC2, et ces conteneurs
    # survivent a son propre arret. Sans ce destroy, chaque execution de la
    # suite en abandonne quelques-uns, indefiniment.
    #
    # Volontairement tolerant : une configuration d'apprenant incomplete fera
    # echouer le destroy, et ce n'est pas au teardown de faire echouer la suite.
    #
    # L'ORDRE compte, et il n'est pas negociable : le `consumer` lit l'etat
    # distant du `producer` par une data source. Detruire le producer d'abord
    # lui retirerait ce qu'il lit, et le destroy du consumer echouerait sur une
    # lecture impossible.
    for nom in ("consumer", "producer"):
        stack = WORKDIR / nom
        if stack.is_dir():
            _tf("destroy", "-auto-approve", "-input=false", "-no-color", cwd=stack)


# ── 1. Le bucket de state ───────────────────────────────────────────────────


def test_le_bucket_de_state_est_conforme(travail: Path) -> None:
    assert _aws("s3api", "head-bucket", "--bucket", BUCKET).returncode == 0, message(
        en=f"The bucket {BUCKET} does not exist on the emulator: has the bootstrap "
        "been applied?",
        fr=f"Le bucket {BUCKET} n'existe pas sur l'émulateur : le bootstrap "
        "a-t-il été appliqué ?",
    )

    versioning = _aws("s3api", "get-bucket-versioning", "--bucket", BUCKET,
                      "--output", "json")
    assert json.loads(versioning.stdout or "{}").get("Status") == "Enabled", message(
        en="The bucket's versioning is not enabled. That is what allows going "
        "back to an earlier version of the state.",
        fr="Le versioning du bucket n'est pas actif. C'est lui qui permet de "
        "revenir à une version antérieure du state.",
    )


# ── 2. Le backend du producer ───────────────────────────────────────────────


def test_le_backend_du_producer_est_bien_configure(travail: Path) -> None:
    backend = _backend_retenu(travail, "producer")
    assert backend.get("type") == "s3", message(
        en=f"The producer uses a {backend.get('type')!r} backend, expected `s3`.",
        fr=f"Le producer utilise un backend {backend.get('type')!r}, attendu `s3`.",
    )

    config = backend.get("config") or {}
    assert config.get("bucket") == BUCKET, message(
        en=f"The backend points at bucket {config.get('bucket')!r}, expected {BUCKET!r}.",
        fr=f"Le backend pointe le bucket {config.get('bucket')!r}, attendu {BUCKET!r}.",
    )
    assert config.get("key"), message(
        en="No `key` in the backend configuration.",
        fr="Aucune `key` dans la configuration de backend.",
    )
    assert config.get("use_path_style") is True, message(
        en="`use_path_style` is not enabled: without it, the backend cannot talk to a "
        "local emulator.",
        fr="`use_path_style` n'est pas actif : le backend ne peut pas parler à un "
        "émulateur local sans lui.",
    )

    endpoints = config.get("endpoints") or {}
    assert endpoints.get("s3"), message(
        en="No `endpoints.s3`: without it, Terraform talks to AWS and not to "
        "the emulator.",
        fr="Aucun `endpoints.s3` : sans lui, Terraform s'adresse à AWS et non à "
        "l'émulateur.",
    )

    assert config.get("use_lockfile") is True, message(
        en="`use_lockfile` is not enabled. The S3 backend's locking is "
        "OPT-IN: without that argument, a lock file is purely ignored "
        "and two concurrent applies overwrite each other.",
        fr="`use_lockfile` n'est pas actif. Le verrouillage du backend S3 est un "
        "OPT-IN : sans cet argument, un fichier de verrou est purement ignoré "
        "et deux applies concurrents s'écrasent.",
    )


def test_le_state_du_producer_est_distant_et_pas_local(travail: Path) -> None:
    cle = (_backend_retenu(travail, "producer").get("config") or {})["key"]

    objets = _aws("s3api", "list-objects-v2", "--bucket", BUCKET, "--output", "json")
    cles = [o["Key"] for o in json.loads(objets.stdout or "{}").get("Contents", [])]
    assert cle in cles, message(
        en=f"The state object {cle!r} is not in the bucket. Objects present: "
        f"{cles}",
        fr=f"L'objet de state {cle!r} n'est pas dans le bucket. Objets présents : "
        f"{cles}",
    )

    # Les deux ensemble, jamais l'un seul : un state distant qui laisserait une
    # copie locale ne prouverait pas la migration.
    locaux = sorted(p.name for p in _stack(travail, "producer").glob("terraform.tfstate*"))
    assert not locaux, message(
        en=f"The producer keeps a local state: {locaux}. After migrating to S3, "
        "none must remain.",
        fr=f"Le producer garde un state local : {locaux}. Après migration vers S3, "
        "il ne doit en rester aucun.",
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
    assert depot.returncode == 0, message(
        en=f"Cannot place the lock.\n{depot.stderr[-400:]}",
        fr=f"Impossible de déposer le verrou.\n{depot.stderr[-400:]}",
    )

    try:
        bloque = _tf("plan", "-input=false", "-no-color", "-lock-timeout=0s",
                     cwd=_stack(travail, "producer"))
        assert bloque.returncode != 0, message(
            en="A .tflock object is present in the bucket and the plan passes "
            "anyway: locking is therefore NOT enabled. That is exactly what "
            "`use_lockfile = true` must prevent.",
            fr="Un objet .tflock est présent dans le bucket et le plan passe quand "
            "même : le verrouillage n'est donc PAS actif. C'est exactement ce "
            "que `use_lockfile = true` doit empêcher.",
        )
        assert "state lock" in (bloque.stdout + bloque.stderr).lower(), message(
            en="The plan fails, but not on the state lock.\n"
            f"{(bloque.stdout + bloque.stderr)[-500:]}",
            fr="Le plan échoue, mais pas sur le verrou d'état.\n"
            f"{(bloque.stdout + bloque.stderr)[-500:]}",
        )
    finally:
        _aws("s3", "rm", f"s3://{BUCKET}/{verrou}")

    libre = _tf("plan", "-input=false", "-no-color", "-lock-timeout=0s",
                cwd=_stack(travail, "producer"))
    assert libre.returncode == 0, message(
        en=f"With the lock removed, the plan returns {libre.returncode} instead of 0.\n"
        f"{(libre.stdout + libre.stderr)[-500:]}",
        fr=f"Le verrou retiré, le plan rend {libre.returncode} au lieu de 0.\n"
        f"{(libre.stdout + libre.stderr)[-500:]}",
    )


# ── 4. Le consumer lit l'etat distant ───────────────────────────────────────


def test_le_consumer_ne_gere_rien_et_lit_l_amont(travail: Path) -> None:
    ressources = (
        _etat(travail, "consumer")
        .get("values", {}).get("root_module", {}).get("resources", [])
    )
    gerees = [r for r in ressources if r.get("mode") == "managed"]
    assert not gerees, message(
        en=f"The consumer manages {len(gerees)} resource(s): {[r['address'] for r in gerees]}. "
        "It must create nothing, only read what is upstream.",
        fr=f"Le consumer gère {len(gerees)} ressource(s) : {[r['address'] for r in gerees]}. "
        "Il ne doit rien créer, seulement lire l'amont.",
    )

    donnees = [r for r in ressources if r.get("mode") == "data"]
    assert len(donnees) == 1, message(
        en=f"The consumer carries {len(donnees)} data source(s), 1 expected.",
        fr=f"Le consumer porte {len(donnees)} source(s) de données, attendu 1.",
    )
    seule = donnees[0]
    assert seule.get("type") == "terraform_remote_state", message(
        en=f"The source is of type {seule.get('type')!r}, expected "
        "`terraform_remote_state`.",
        fr=f"La source est de type {seule.get('type')!r}, attendu "
        "`terraform_remote_state`.",
    )
    assert seule.get("provider_name") == "terraform.io/builtin/terraform", message(
        en=f"The source is served by {seule.get('provider_name')!r}, expected the "
        "built-in provider `terraform.io/builtin/terraform`.",
        fr=f"La source est servie par {seule.get('provider_name')!r}, attendu le "
        "fournisseur intégré `terraform.io/builtin/terraform`.",
    )


def test_les_sorties_du_consumer_valent_celles_du_producer(travail: Path) -> None:
    amont = _sorties(travail, "producer")
    aval = _sorties(travail, "consumer")
    for nom in ("network_name", "network_cidr", "region"):
        assert nom in aval, message(
            en=f"The consumer does not expose `{nom}`.",
            fr=f"Le consumer n'expose pas `{nom}`.",
        )
        assert aval[nom]["value"] == amont[nom]["value"], message(
            en=f"`{nom}` is {aval[nom]['value']!r} downstream and "
            f"{amont[nom]['value']!r} upstream.",
            fr=f"`{nom}` vaut {aval[nom]['value']!r} en aval et "
            f"{amont[nom]['value']!r} en amont.",
        )


def test_le_repli_joue_pour_une_sortie_absente(travail: Path) -> None:
    """`defaults` comble un output MANQUANT dans un etat qui existe."""
    amont = _sorties(travail, "producer")
    assert REPLI not in amont, message(
        en=f"The producer publishes `{REPLI}`: the fallback would then prove nothing. "
        "That output must stay absent upstream.",
        fr=f"Le producer publie `{REPLI}` : le repli ne prouverait alors rien. "
        "Cette sortie doit rester absente de l'amont.",
    )
    aval = _sorties(travail, "consumer")
    assert REPLI in aval, message(
        en=f"The consumer does not expose `{REPLI}`.",
        fr=f"Le consumer n'expose pas `{REPLI}`.",
    )
    valeur = aval[REPLI]["value"]
    assert valeur not in (None, ""), message(
        en=f"`{REPLI}` is empty although the producer does not publish it: the "
        "`defaults` block must provide a fallback value.",
        fr=f"`{REPLI}` est vide alors que le producer ne le publie pas : le bloc "
        "`defaults` doit fournir une valeur de repli.",
    )


def test_la_valeur_amont_se_propage(travail: Path, tmp_path: Path) -> None:
    """Une valeur recopiee a la main resterait figee ; celle-ci doit suivre."""
    avant = _sorties(travail, "consumer")["network_name"]["value"]

    rejoue = _tf("apply", "-auto-approve", "-input=false", "-no-color",
                 "-var", "graine=validation", cwd=_stack(travail, "producer"))
    assert rejoue.returncode == 0, message(
        en=f"Cannot replay the producer.\n{rejoue.stderr[-600:]}",
        fr=f"Impossible de rejouer le producer.\n{rejoue.stderr[-600:]}",
    )
    try:
        suivi = _tf("apply", "-auto-approve", "-input=false", "-no-color",
                    cwd=_stack(travail, "consumer"))
        assert suivi.returncode == 0, message(
            en=f"Cannot replay the consumer.\n{suivi.stderr[-600:]}",
            fr=f"Impossible de rejouer le consumer.\n{suivi.stderr[-600:]}",
        )
        apres_amont = _sorties(travail, "producer")["network_name"]["value"]
        apres_aval = _sorties(travail, "consumer")["network_name"]["value"]
        assert apres_amont != avant, message(
            en="The producer replayed with another seed produces the same value: "
            "the witness does not discriminate.",
            fr="Le producer rejoué avec une autre graine produit la même valeur : "
            "le témoin ne discrimine pas.",
        )
        assert apres_aval == apres_amont, message(
            en=f"The producer now publishes {apres_amont!r} and the consumer "
            f"exposes {apres_aval!r}: the value was COPIED instead of being "
            "read from the remote state.",
            fr=f"Le producer publie maintenant {apres_amont!r} et le consumer "
            f"expose {apres_aval!r} : la valeur a été RECOPIÉE au lieu d'être "
            "lue dans l'état distant.",
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
        assert plan.returncode == 0, message(
            en=f"{nom}: `plan -detailed-exitcode` returns {plan.returncode}, "
            f"expected 0.\n{(plan.stdout + plan.stderr)[-600:]}",
            fr=f"{nom} : `plan -detailed-exitcode` rend {plan.returncode}, "
            f"attendu 0.\n{(plan.stdout + plan.stderr)[-600:]}",
        )
