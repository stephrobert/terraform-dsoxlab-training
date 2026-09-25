"""Tests fonctionnels du lab « un identifiant ne vit ni dans le code ni dans le state ».

L'objectif 6c porte sur la gestion des identifiants de provider dans HCP
Terraform. Il est evalue en QCM, mais son enseignement se mesure, et ce lab le
mesure sur un vrai provider face a un emulateur.

## Ce que les tests incarnent

HCP Terraform pose les identifiants dans l'ENVIRONNEMENT du run, juste avant le
plan ou l'apply, et les jette avec cet environnement a la fin. Les tests jouent
ce role : ils appliquent la configuration dans un environnement ou les
identifiants AWS sont poses en variables d'environnement, et ou rien d'autre ne
peut en fournir, ni `~/.aws`, ni un profil.

Une configuration ecrite pour recevoir ses identifiants marche dans cet
environnement. Une configuration qui les contient marche aussi, et c'est
pourquoi ce test ne suffit pas : un second lit les fichiers.

## La mesure au coeur du lab

Le 2026-09-25, sur cette configuration meme, avec Terraform 1.16.1 :

    variable marquee `sensitive`   -> `terraform show` affiche (sensitive value)
    le meme state, en clair        -> "Jeton": "svc-7f3a91c4e2b8-prod", deux fois

`sensitive` protege l'affichage. Il ne protege ni le state ni un plan
enregistre, qui portent la valeur telle quelle.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "hcp-terraform-shared-credentials"

CONFIGURATION = "configuration"
QUESTIONNAIRE = "questionnaire"

FLOCI_HOST = "localhost"
FLOCI_PORT = 14566
ENDPOINT = f"http://{FLOCI_HOST}:{FLOCI_PORT}"

# La valeur que la fixture pose, et qui ne doit se retrouver nulle part dans le
# state. Elle est ecrite ici parce que c'est le lab qui la fixe ; l'empreinte,
# elle, est CALCULEE par le test, jamais recopiee.
JETON = "svc-7f3a91c4e2b8-prod"

# Ce que la configuration ne doit plus porter.
ARGUMENTS_INTERDITS = ("access_key", "secret_key")

SOURCE = (
    "https://developer.hashicorp.com/terraform/cloud-docs/workspaces/"
    "dynamic-provider-credentials"
)

REPONSES_ATTENDUES = {
    "ce_que_sensible_protege": (
        "l_affichage_seulement",
        "vous venez de le mesurer : `terraform show` masque la valeur, le state "
        "la porte en clair. L'annotation agit sur ce que Terraform ecrit a "
        "l'ecran, pas sur ce qu'il enregistre",
    ),
    "ce_que_hcp_envoie_au_cloud": (
        "un_workload_identity_token",
        "« HCP Terraform generates a workload identity token. The token is "
        "compliant with OpenID Connect protocol (OIDC) standards and includes "
        "information about the organization, workspace or Stack, and run "
        "stage. »",
    ),
    "ce_qui_verifie_ce_jeton": (
        "la_cle_publique_de_hcp",
        "« The cloud platform uses HCP Terraform's public signing key to verify "
        "the workload identity token. » Rien ne circule qui serait a la fois le "
        "secret et sa preuve",
    ),
    "duree_de_vie_des_identifiants": (
        "le_temps_du_run",
        "« When the plan or apply completes, the run environment is torn down "
        "and the temporary credentials are discarded. » C'est tout l'interet : "
        "un identifiant qui ne survit pas au run n'a pas besoin d'etre tourne",
    ),
    "ou_vivent_les_identifiants_hcp": (
        "des_variables_d_environnement",
        "« You must add specific environment variables to that workspace to tell "
        "HCP Terraform how to authenticate. » Elles vivent dans le workspace, "
        "jamais dans la configuration",
    ),
}


def _floci_joignable() -> bool:
    import socket

    try:
        with socket.create_connection((FLOCI_HOST, FLOCI_PORT), timeout=2):
            return True
    except OSError:
        return False


def _exiger_floci() -> None:
    if _floci_joignable():
        return
    message = (
        f"Floci n'est pas joignable sur {FLOCI_HOST}:{FLOCI_PORT}. Ce lab en a "
        "besoin : Floci emule l'API AWS en local, sans compte ni carte "
        "bancaire.\n\n"
        f"Lancez le lab avec `dsoxlab run {LAB_ID}`, qui le demarre tout seul, "
        "et faites votre `dsoxlab check` DEPUIS cette session : le service "
        "s'arrete quand vous la quittez."
    )
    if os.environ.get("LAB_WORKDIR"):
        pytest.fail(message)
    pytest.skip(message)


def _environnement_de_run(tmp: Path) -> dict[str, str]:
    """L'environnement qu'un run recoit, et rien de plus.

    Les identifiants y sont poses comme HCP Terraform les pose : en variables
    d'environnement, valables le temps du run. Tout ce qui pourrait en fournir
    d'autres est retire, `AWS_PROFILE` comme un `~/.aws` du poste, sinon une
    configuration qui ne sait pas les recevoir passerait quand meme.
    """
    env = {
        c: v
        for c, v in os.environ.items()
        if not c.startswith("AWS_")
    }
    env["HOME"] = str(tmp)
    env["AWS_ACCESS_KEY_ID"] = "identifiant-pose-par-la-plateforme"
    # Ruff y voit un secret en dur, et c'en est un. C'est
    # précisément le sujet du lab : la plateforme pose un identifiant
    # factice dans l'environnement du run, et la configuration doit le
    # recevoir au lieu de le contenir. L'émulateur ne le vérifie pas.
    env["AWS_SECRET_ACCESS_KEY"] = "secret-pose-par-la-plateforme"  # noqa: S105
    env["AWS_REGION"] = "eu-west-3"
    return env


def _tf(*args: str, cwd: Path, env: dict[str, str] | None = None):
    return subprocess.run(
        ["terraform", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture(scope="module")
def applique(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    """Applique la configuration dans un environnement de run, puis range."""
    exiger_workdir(WORKDIR, LAB_ID)
    _exiger_floci()

    repertoire = WORKDIR / CONFIGURATION
    env = _environnement_de_run(tmp_path_factory.mktemp("faux-home"))

    init = _tf("init", "-input=false", "-no-color", cwd=repertoire, env=env)
    if init.returncode != 0:
        pytest.fail(f"`terraform init` a echoue :\n{init.stderr[-800:]}")

    # L'emulateur refuse parfois une requete isolee alors qu'il est sain.
    applique = None
    for _ in range(3):
        applique = _tf(
            "apply", "-auto-approve", "-input=false", "-no-color",
            cwd=repertoire, env=env,
        )
        if applique.returncode == 0:
            break
        time.sleep(3)

    if applique is None or applique.returncode != 0:
        sortie = (applique.stderr or applique.stdout) if applique else ""
        pytest.fail(
            "`terraform apply` a echoue dans un environnement ou les "
            "identifiants ne viennent QUE de l'environnement.\n\nC'est "
            "precisement ce que fait HCP Terraform : il les pose la, juste "
            "avant le run. Une configuration qui ne sait pas les recevoir "
            f"repond « No valid credential sources found ».\n{sortie[-1500:]}"
        )

    yield repertoire

    # Teardown : detruire PENDANT que l'emulateur repond encore.
    #
    # Floci lance un conteneur Docker par instance EC2, et ces conteneurs
    # survivent a son propre arret. Sans ce destroy, chaque execution de la
    # suite en abandonne quelques-uns, indefiniment.
    #
    # Volontairement tolerant : une configuration d'apprenant incomplete fera
    # echouer le destroy, et ce n'est pas au teardown de faire echouer la suite.
    _tf("destroy", "-auto-approve", "-input=false", "-no-color", cwd=repertoire, env=env)


@pytest.fixture(scope="module")
def etat(applique: Path) -> dict:
    proc = _tf("show", "-json", cwd=applique)
    proc.check_returncode()
    return json.loads(proc.stdout)


def _instances(etat: dict) -> list[dict]:
    racine = (etat.get("values") or {}).get("root_module", {})
    return [r for r in racine.get("resources", []) if r["type"] == "aws_instance"]


# --------------------------------------------------------------------------
# 1. Le secret ne doit plus etre dans le state.
# --------------------------------------------------------------------------
def test_le_jeton_n_apparait_nulle_part_dans_le_state(applique: Path) -> None:
    """On balaie le fichier entier, pas seulement les etiquettes attendues.

    Un secret deplace d'une etiquette vers un `user_data` ou une description
    serait tout aussi expose, et une verification ciblee ne le verrait pas.
    """
    fichier = applique / "terraform.tfstate"
    assert fichier.is_file(), (
        "Aucun `terraform.tfstate` : la configuration n'a pas ete appliquee."
    )

    contenu = fichier.read_text(encoding="utf-8")
    assert JETON not in contenu, (
        f"Le state porte le jeton en clair.\n\nIl y apparait "
        f"{contenu.count(JETON)} fois. L'annotation `sensitive` de la variable "
        "n'y change rien : elle empeche Terraform de l'AFFICHER, pas de "
        "l'enregistrer. Un state se lit, se sauvegarde et se partage.\n\n"
        "Ce qu'il faut poser a la place est une empreinte : elle permet de "
        "verifier un jeton presente, sans jamais le conserver."
    )


def test_l_instance_porte_l_empreinte_du_jeton(etat: dict) -> None:
    instances = _instances(etat)
    assert len(instances) == 1, (
        f"{len(instances)} instance(s) dans le state, une attendue."
    )

    etiquettes = instances[0]["values"].get("tags") or {}
    assert "Jeton" not in etiquettes, (
        "L'etiquette `Jeton` existe encore. C'est elle qui portait le secret."
    )

    attendue = hashlib.sha256(JETON.encode()).hexdigest()
    obtenue = etiquettes.get("Empreinte")
    assert obtenue == attendue, (
        f"L'etiquette `Empreinte` vaut {obtenue!r}, attendu {attendue!r}.\n\n"
        "C'est l'empreinte SHA-256 du jeton, celle que rend la fonction "
        "`sha256`. Elle prouve qu'un jeton presente est le bon, sans le "
        "contenir."
    )


# --------------------------------------------------------------------------
# 2. Les identifiants ne doivent plus etre dans le code.
# --------------------------------------------------------------------------
def test_les_cles_ont_disparu_et_le_provider_s_authentifie_quand_meme(
    applique: Path, etat: dict
) -> None:
    """Le test qui exerce les deux cotes, et il est ecrit en un seul morceau.

    La premiere version de ce lab en faisait deux tests, et le second, « une
    instance existe », etait VERT avant tout travail : avec ses cles en dur, la
    configuration de depart s'authentifie parfaitement. Mesure du 2026-09-25,
    au premier cycle : 1/9 sans avoir rien fait.

    Les deux moities sont donc reunies, et leur conjonction n'est atteignable
    qu'apres le travail :

      - ce qui est interdit : porter les identifiants dans la configuration.
        Cela se lit dans les fichiers, parce qu'aucune observation de l'etat ne
        distingue une configuration qui contient ses cles d'une qui les
        recoit : les deux fonctionnent ;
      - ce qui reste exige : que le provider s'authentifie quand meme.
        L'instance n'existe que parce qu'il a trouve ses identifiants dans
        l'environnement pose par la fixture, expurge de tout `AWS_*` du poste
        et sans `~/.aws`.

    Separer les deux laisserait passer une configuration videe de ses cles ET
    de sa capacite a fonctionner, ce qui est le reproche fait a tout
    durcissement mal mesure : la porte est fermee, le service ne rend plus rien.
    """
    fautifs: dict[str, list[str]] = {}
    for fichier in sorted(applique.glob("*.tf")):
        nu = "\n".join(
            ligne.split("#")[0] for ligne in fichier.read_text(encoding="utf-8").splitlines()
        )
        trouves = [a for a in ARGUMENTS_INTERDITS if a in nu]
        if trouves:
            fautifs[fichier.name] = trouves

    assert not fautifs, (
        f"Des identifiants sont encore declares dans la configuration : "
        f"{fautifs}\n\nHCP Terraform pose les identifiants dans "
        "l'environnement du run et les jette a la fin. Une configuration qui "
        "les contient les met dans le depot, dans son historique, et dans "
        "chaque copie de travail."
    )

    instances = _instances(etat)
    assert len(instances) == 1, (
        f"{len(instances)} instance(s) dans le state, une attendue.\n\nSans "
        "instance, rien ne prouve que le provider s'est authentifie : une "
        "configuration qui ne cree rien satisferait la moitie de ce lab sans "
        "rien demontrer."
    )

    identifiant = instances[0]["values"].get("id") or ""
    assert identifiant.startswith("i-"), (
        f"L'instance porte l'identifiant {identifiant!r}, inattendu : l'API n'a "
        "pas repondu comme elle le devrait."
    )


# --------------------------------------------------------------------------
# 3. Les identifiants dynamiques.
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def reponses() -> dict:
    exiger_workdir(WORKDIR, LAB_ID)
    repertoire = WORKDIR / QUESTIONNAIRE

    init = _tf("init", "-input=false", "-no-color", cwd=repertoire)
    assert init.returncode == 0, f"`init` a echoue.\n{init.stderr[-800:]}"

    applique = _tf(
        "apply", "-auto-approve", "-input=false", "-no-color", cwd=repertoire
    )
    assert applique.returncode == 0, (
        f"`apply` a echoue dans `{QUESTIONNAIRE}/`.\n\nUne reponse hors de "
        "l'enumere est refusee AU PLAN, et le message dit quoi ecrire.\n"
        f"{applique.stderr[-1200:]}"
    )

    proc = _tf("output", "-json", cwd=repertoire)
    proc.check_returncode()
    return json.loads(proc.stdout)["reponses"]["value"]


@pytest.mark.parametrize("question", sorted(REPONSES_ATTENDUES))
def test_chaque_reponse_sur_les_identifiants(reponses: dict, question: str) -> None:
    attendue, pourquoi = REPONSES_ATTENDUES[question]
    obtenue = reponses.get(question)
    assert obtenue == attendue, (
        f"`{question}` vaut {obtenue!r}, {attendue!r} attendu.\n\n"
        f"{pourquoi.capitalize()}.\n\nSource : {SOURCE}"
    )
