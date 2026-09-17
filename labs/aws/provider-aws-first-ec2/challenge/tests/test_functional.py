"""Tests fonctionnels du lab « faire parler le provider AWS a une API locale ».

Aucun test n'ouvre un `.tf` de l'apprenant : tout passe par les sorties
structurees de Terraform (`version -json`, `show -json`, `output -json`) et par
l'etat que l'emulateur rapporte reellement.

Faits mesures sur Terraform 1.15.4 et le provider AWS 6.59.0, contre l'emulateur
local, sans aucun compte AWS :

- sous la contrainte `>= 6.0, < 7.0`, la version resolue etait 6.56.0 a la
  redaction de l'audit et 6.59.0 quelques jours plus tard : c'est pourquoi les
  tests verifient une PLAGE, jamais un numero exact ;
- `terraform validate` sort en 0 sur un provider incompletement configure ;
  c'est le `plan` qui echoue, avec `Error: No valid credential sources found`
  suivi de `no EC2 IMDS role found` ;
- `default_tags` n'ecrit JAMAIS dans `tags` : les tags par defaut n'apparaissent
  que dans `tags_all`. Un tag homonyme declare sur la ressource l'emporte, sans
  la moindre erreur ni le moindre avertissement ;
- l'instance passe par `pending` avant `running`, l'emulateur creant un vrai
  conteneur de support ; un `pending` definitif signe un emulateur mal lance.
"""

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

from conftest import exiger_workdir, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "aws-provider-aws-first-ec2"

ENDPOINT = "http://localhost:14566"
PROVIDER = "registry.terraform.io/hashicorp/aws"
TAGS_ATTENDUS = {"projet", "environnement", "gestion"}

# Environnement EXPURGE : aucune variable AWS_*, et un HOME sans `.aws`. Si les
# identifiants ne sont pas dans la configuration de l'apprenant, le plan echoue.
# C'est ce qui donne sa valeur a l'exercice : on ne peut pas le reussir en
# s'appuyant sur les identifiants de la machine.
_HOME_NU = WORKDIR / ".home-sans-aws"
ENV = {
    **{k: v for k, v in os.environ.items()
       if not k.startswith("AWS_") and k != "HOME"},
    "HOME": str(_HOME_NU),
}


# ── Helpers ─────────────────────────────────────────────────────────────────


def _tf(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    _HOME_NU.mkdir(parents=True, exist_ok=True)
    return subprocess.run(
        ["terraform", *args], cwd=cwd or WORKDIR,
        capture_output=True, text=True, env=ENV,
        check=False,
    )


def _json(*args: str, cwd: Path | None = None) -> dict:
    res = _tf(*args, cwd=cwd)
    if res.returncode != 0:
        pytest.fail(
            f"`terraform {' '.join(args)}` a echoue (code {res.returncode}) :\n"
            f"{(res.stderr or res.stdout).strip()[:1500]}"
        )
    try:
        return json.loads(res.stdout or "{}")
    except json.JSONDecodeError as err:  # pragma: no cover - diagnostic
        pytest.fail(f"sortie JSON illisible pour `{' '.join(args)}` : {err}")


@pytest.fixture(scope="module", autouse=True)
def applique() -> None:
    """Initialise et applique une fois pour tout le module.

    Un echec ici n'est pas un detail d'intendance : c'est le resultat du lab.
    Le message doit donc porter la sortie de Terraform, sinon l'apprenant lit
    « erreur de fixture » la ou il a laisse un `???`.
    """
    exiger_workdir(WORKDIR, LAB_ID)
    _HOME_NU.mkdir(parents=True, exist_ok=True)

    init = _tf("init", "-input=false", "-no-color")
    if init.returncode != 0:
        pytest.fail(
            "`terraform init` a echoue. Le `source` ou la `version` du provider "
            f"est-il encore a `???` ?\n{(init.stderr or init.stdout).strip()[:1500]}"
        )

    app = _tf("apply", "-auto-approve", "-input=false", "-no-color")
    if app.returncode != 0:
        pytest.fail(
            "`terraform apply` a echoue. Configuration du provider incomplete "
            "(identifiants, endpoints, skip_*) ou outputs encore a `???` ?\n"
            f"{(app.stderr or app.stdout).strip()[:1500]}"
        )


def _plan_json() -> dict:
    _tf("plan", "-out=tfplan", "-input=false", "-no-color")
    return _json("show", "-json", "tfplan")


def _provider_config() -> dict:
    conf = _plan_json().get("configuration", {}).get("provider_config", {})
    assert "aws" in conf, (
        "aucune configuration de provider `aws` dans le plan : le bloc "
        "`provider \"aws\"` a-t-il disparu ?"
    )
    return conf["aws"]


def _ressources_etat() -> list[dict]:
    etat = _json("show", "-json")
    return etat.get("values", {}).get("root_module", {}).get("resources", [])


def _borne(contrainte: str) -> tuple[bool, bool]:
    """(borne basse sur la majeure 6, borne haute sous la 7) d'une contrainte."""
    morceaux = [m.strip() for m in contrainte.replace(",", " ").split()]
    joint = " ".join(morceaux)
    basse = any(t in joint for t in (">= 6", "~> 6", "6.0", "> 6"))
    haute = ("~>" in joint) or any(t in joint for t in ("< 7", "<7", "<= 6"))
    return basse, haute


# ── 1. Sourcing et versionnement ────────────────────────────────────────────


def test_le_provider_installe_est_la_majeure_6() -> None:
    """La 5.x que trainent les vieux exemples ne doit pas passer."""
    selections = _json("version", "-json").get("provider_selections", {})
    assert PROVIDER in selections, (
        f"le provider installe n'est pas {PROVIDER} : {selections}. "
        "Le `source` doit valoir `hashicorp/aws`."
    )
    version = selections[PROVIDER]
    majeure = int(version.split(".")[0])
    assert majeure == 6, (
        f"version installee {version} : le lab vise la majeure 6, "
        "ni la 5.x ni une majeure future non testee."
    )


def test_la_contrainte_borne_la_version_des_deux_cotes() -> None:
    """Un plancher sans plafond laisse la majeure 7 arriver sans prevenir.

    La version resolue a bouge de 6.56.0 a 6.59.0 en quelques jours pendant la
    preparation de ce lab : c'est exactement ce qu'une borne haute encadre.
    """
    contrainte = _provider_config().get("version_constraint", "")
    assert contrainte, (
        "aucune contrainte de version : `version` est-il encore a `???` ?"
    )
    basse, haute = _borne(contrainte)
    assert basse, f"contrainte `{contrainte}` : la borne basse ne vise pas la 6.x"
    assert haute, (
        f"contrainte `{contrainte}` : rien n'empeche la majeure 7 de s'installer. "
        "Bornez en haut (`< 7.0`, ou `~> 6.0` qui l'implique)."
    )


def test_le_provider_est_bien_celui_du_registre_officiel() -> None:
    assert _provider_config().get("full_name") == PROVIDER


# ── 2. Authentification et redirection ──────────────────────────────────────


def test_les_identifiants_sont_dans_la_configuration() -> None:
    """Rien ne doit dependre de l'environnement ni de `~/.aws`.

    Tous les tests de ce module tournent deja sans variable `AWS_*` et avec un
    `HOME` depourvu de `.aws` : si l'apply a reussi, c'est deja une preuve. Ce
    test verifie en plus que les valeurs sont bien ecrites dans le bloc.
    """
    exprs = _provider_config().get("expressions", {})
    for cle in ("access_key", "secret_key"):
        valeur = exprs.get(cle, {}).get("constant_value")
        assert valeur, (
            f"`{cle}` absent ou vide du bloc provider. Sans lui, le plan rend "
            "`No valid credential sources found` des que l'environnement ne "
            "porte pas d'identifiants."
        )


def test_les_trois_validations_distantes_sont_desactivees() -> None:
    """Ces trois appels partiraient vers le vrai AWS, pas vers l'emulateur."""
    exprs = _provider_config().get("expressions", {})
    for cle in ("skip_credentials_validation", "skip_metadata_api_check",
                "skip_requesting_account_id"):
        assert exprs.get(cle, {}).get("constant_value") is True, (
            f"`{cle}` doit valoir true : sinon le provider interroge AWS avant "
            "meme de planifier."
        )


def test_le_service_ec2_est_redirige_vers_l_emulateur() -> None:
    exprs = _provider_config().get("expressions", {})
    assert "endpoints" in exprs, (
        "aucun bloc `endpoints` : le provider appelle donc le vrai AWS."
    )
    rendu = json.dumps(exprs["endpoints"])
    assert "ec2" in rendu, "le bloc `endpoints` ne redirige pas le service `ec2`"
    assert "floci_endpoint" in rendu or ENDPOINT in rendu, (
        "l'endpoint `ec2` doit pointer vers l'API locale, via "
        "`var.floci_endpoint` de preference."
    )


# ── 3. Les tags viennent du provider ────────────────────────────────────────


def test_les_tags_sont_poses_par_le_provider_pas_par_la_ressource() -> None:
    """`default_tags` n'ecrit jamais dans `tags`, seulement dans `tags_all`.

    C'est la mesure qui donne son sens au test : si l'apprenant recopie les
    tags sur la ressource, ils apparaissent dans `tags`, et l'exercice est
    manque meme si `tags_all` a l'air correct.
    """
    exprs = _provider_config().get("expressions", {})
    assert "default_tags" in exprs, (
        "aucun bloc `default_tags` dans le provider : les tags doivent venir "
        "de la, pas d'un `tags` recopie sur chaque ressource."
    )

    instances = [r for r in _ressources_etat() if r.get("type") == "aws_instance"]
    assert instances, "aucune `aws_instance` dans l'etat"
    valeurs = instances[0]["values"]

    tags_all = valeurs.get("tags_all") or {}
    manquants = TAGS_ATTENDUS - set(tags_all)
    assert not manquants, (
        f"`tags_all` ne porte pas {sorted(manquants)} : les tags de "
        f"`var.common_tags` ne sont pas appliques. Obtenu : {tags_all}"
    )

    tags = valeurs.get("tags") or {}
    assert not tags, (
        f"la ressource declare ses propres `tags` ({tags}). `main.tf` ne doit "
        "pas etre modifie : les tags arrivent par `default_tags`."
    )


# ── 4. L'instance tourne vraiment ───────────────────────────────────────────


def test_l_instance_est_geree_et_atteint_l_etat_running() -> None:
    """`pending` n'est pas `running` : l'emulateur cree un vrai conteneur.

    La transition n'est pas instantanee, d'ou la boucle bornee. Un `pending`
    definitif ne vient pas de la configuration de l'apprenant mais d'un
    emulateur lance sans acces au moteur de conteneurs.
    """
    ressources = _ressources_etat()
    assert len(ressources) == 1, (
        f"l'etat doit contenir exactement une ressource, il en contient "
        f"{len(ressources)} : {[r.get('address') for r in ressources]}"
    )
    unique = ressources[0]
    assert unique.get("mode") == "managed"
    assert unique.get("type") == "aws_instance"

    etat = unique["values"].get("instance_state")
    limite = time.monotonic() + 120
    while etat != "running" and time.monotonic() < limite:
        time.sleep(3)
        _tf("apply", "-refresh-only", "-auto-approve", "-input=false", "-no-color")
        courant = _ressources_etat()
        etat = courant[0]["values"].get("instance_state") if courant else etat

    assert etat == "running", (
        f"l'instance est restee en `{etat}` au bout de 120 s. Si tout le reste "
        "passe, c'est l'emulateur qui n'a pas pu creer son conteneur de "
        "support, pas votre configuration."
    )


def test_les_trois_outputs_sont_renseignes() -> None:
    sorties = _json("output", "-json")
    for nom in ("instance_id", "instance_state", "instance_private_ip"):
        assert nom in sorties, f"output `{nom}` absent"
        valeur = sorties[nom].get("value")
        assert valeur, f"output `{nom}` vide : sa `value` est-elle encore a `???` ?"

    assert sorties["instance_state"]["value"] == "running"
    assert sorties["instance_id"]["value"].startswith("i-"), (
        f"identifiant inattendu : {sorties['instance_id']['value']}"
    )


# ── 5. Le cycle se referme ──────────────────────────────────────────────────


def test_un_plan_relance_n_annonce_aucun_changement() -> None:
    """Idempotence : `-detailed-exitcode` rend 0 sans changement, 2 avec."""
    res = _tf("plan", "-input=false", "-detailed-exitcode", "-no-color")
    assert res.returncode == 0, (
        f"`plan -detailed-exitcode` a rendu {res.returncode} (2 = des "
        f"changements restent a appliquer) :\n{(res.stdout or res.stderr)[:900]}"
    )


def test_la_configuration_se_detruit_entierement(tmp_path: Path) -> None:
    """Un cycle complet joue sur une COPIE, avec son propre etat.

    Detruire l'etat de l'apprenant ferait echouer un `dsoxlab check` relance
    juste apres. La copie cree donc sa propre instance, la detruit, et laisse
    l'exercice intact.
    """
    copie = tmp_path / "cycle"
    copie.mkdir()
    for fichier in WORKDIR.glob("*.tf"):
        shutil.copy2(fichier, copie / fichier.name)

    assert _tf("init", "-input=false", "-no-color", cwd=copie).returncode == 0
    applique = _tf("apply", "-auto-approve", "-input=false", "-no-color", cwd=copie)
    assert applique.returncode == 0, (
        f"apply en echec sur la copie :\n{(applique.stderr or applique.stdout)[:900]}"
    )

    detruit = _tf("destroy", "-auto-approve", "-input=false", "-no-color", cwd=copie)
    assert detruit.returncode == 0, (
        f"destroy en echec :\n{(detruit.stderr or detruit.stdout)[:900]}"
    )

    restant = _json("show", "-json", cwd=copie).get("values", {})
    ressources = restant.get("root_module", {}).get("resources", [])
    assert not ressources, (
        f"apres destroy, il reste {len(ressources)} ressource(s) dans l'etat"
    )
