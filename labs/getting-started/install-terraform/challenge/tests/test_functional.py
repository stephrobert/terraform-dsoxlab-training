"""test_functional.py : getting-started/install-terraform

Cinq preuves, et aucune ne lit les `.tf` ecrits par l'apprenant.

Le lab porte sur une frontiere que la documentation enonce mais qu'on oublie
vite : `required_version` contraint la CLI, `required_providers` contraint les
providers, et `.terraform.lock.hcl` fige ce qui a ete RESOLU. Trois mecanismes,
trois preuves distinctes.

La derniere preuve est celle qui separe un lab fait d'un lab commence : on
efface `.terraform/`, on relance `init`, et on exige que les versions retenues
soient STRICTEMENT les memes. Le verrou fait autorite, ou rien ne le fait.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pytest

from conftest import exiger_workdir, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "getting-started-install-terraform"

PROVIDERS_ATTENDUS = {
    "registry.terraform.io/hashicorp/local",
    "registry.terraform.io/hashicorp/null",
    "registry.terraform.io/hashicorp/random",
}

#: Un bloc `provider "..." { ... }` du fichier de verrouillage.
BLOC_VERROU = re.compile(r'provider\s+"([^"]+)"\s*\{(.*?)\n\}', re.DOTALL)

#: Deux plateformes au minimum : un verrou qui n'en couvre qu'une change au
#: premier `init` d'un collegue sur un autre systeme.
PLATEFORMES_MINIMUM = 2


@pytest.fixture(scope="module")
def prepared() -> Path:
    """`terraform init`, sans `-upgrade` : le verrou doit faire autorite."""
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(
            "`terraform init` a echoue dans challenge/work. Le bloc "
            "`terraform {}` declare-t-il bien ses `required_providers` ?\n"
            f"{init.stderr[-1200:]}"
        )
    return WORKDIR


@pytest.fixture(scope="module")
def applied(prepared: Path) -> Path:
    app = terraform(
        "apply", "-auto-approve", "-input=false", "-no-color", cwd=prepared
    )
    if app.returncode != 0:
        pytest.fail(
            "`terraform apply` a echoue : la configuration ne converge pas.\n"
            f"{app.stderr[-1500:]}"
        )
    return prepared


def _version_json(cwd: Path) -> dict:
    proc = terraform("version", "-json", cwd=cwd)
    assert proc.returncode == 0, (
        f"`terraform version -json` a echoue dans {cwd}. {proc.stderr.strip()}"
    )
    return json.loads(proc.stdout)


# --------------------------------------------------------------------------
# 1. La CLI repond, et les trois providers sont ceux attendus.
# --------------------------------------------------------------------------
def test_la_configuration_epingle_exactement_trois_providers(prepared: Path) -> None:
    """Ce test ne prouve pas a lui seul que le verrou fait autorite : il etablit
    que la configuration s'initialise avec les trois providers attendus, sans
    quoi les preuves suivantes n'auraient rien a mesurer."""
    infos = _version_json(prepared)
    assert infos.get("terraform_version"), (
        "`terraform version -json` ne rend aucune version."
    )

    selections = infos.get("provider_selections") or {}
    assert selections, (
        "Aucun provider selectionne apres `init` : le bloc `terraform {}` "
        "declare-t-il un `required_providers` ?"
    )
    assert set(selections) == PROVIDERS_ATTENDUS, (
        f"Providers retenus : {sorted(selections)}.\nAttendus : "
        f"{sorted(PROVIDERS_ATTENDUS)}.\n\nles trois doivent etre declares "
        "ET employes : un provider declare mais dont aucune ressource ne se "
        "sert n'entre pas dans l'etat."
    )


# --------------------------------------------------------------------------
# 2. Une contrainte insatisfaisable fait REFUSER l'execution.
# --------------------------------------------------------------------------
def test_une_contrainte_de_version_impossible_fait_echouer_init(prepared: Path) -> None:
    """Preuve ACTIVE, et dans les deux sens : le contre-exemple echoue, le
    repertoire principal reussit. Sans la seconde moitie, un environnement
    casse passerait pour une contrainte qui refuse."""
    echec = prepared / "echec-version"
    assert echec.is_dir(), (
        "Le sous-repertoire `echec-version/` est absent. Il porte le "
        "contre-exemple : une configuration dont le `required_version` ne peut "
        "pas etre satisfait par la CLI installee."
    )

    refuse = terraform("init", "-no-color", "-input=false", cwd=echec)
    assert refuse.returncode != 0, (
        "`terraform init` a REUSSI dans echec-version/, alors que sa contrainte "
        "devait etre hors d'atteinte. Le `required_version` y est-il bien "
        "impossible a satisfaire ?"
    )

    ok = terraform("init", "-no-color", "-input=false", cwd=prepared)
    assert ok.returncode == 0, (
        "`terraform init` echoue AUSSI dans le repertoire principal : ce n'est "
        f"donc pas la contrainte qui refuse.\n{ok.stderr[-800:]}"
    )


# --------------------------------------------------------------------------
# 3. Le verrou est un fichier machine : on le lit comme tel.
# --------------------------------------------------------------------------
def test_le_verrou_couvre_les_trois_providers_sur_deux_plateformes(prepared: Path) -> None:
    verrou = prepared / ".terraform.lock.hcl"
    assert verrou.is_file(), (
        "`.terraform.lock.hcl` est absent : c'est `terraform init` qui le "
        "produit, et il fige les versions resolues."
    )

    blocs = dict(BLOC_VERROU.findall(verrou.read_text(encoding="utf-8")))
    assert set(blocs) == PROVIDERS_ATTENDUS, (
        f"Le verrou couvre {sorted(blocs)}, et non les trois providers attendus."
    )

    for nom, corps in sorted(blocs.items()):
        assert re.search(r'version\s*=\s*"', corps), (
            f"Le bloc de {nom} ne porte pas de `version` resolue."
        )
        assert re.search(r'constraints\s*=\s*"', corps), (
            f"Le bloc de {nom} ne porte pas de `constraints`. Elle vient du "
            "`required_providers` : sans contrainte declaree, le verrou ne "
            "retient que la version du jour."
        )
        empreintes = re.findall(r'"h1:[^"]+"', corps)
        assert len(empreintes) >= PLATEFORMES_MINIMUM, (
            f"Le bloc de {nom} ne porte que {len(empreintes)} somme(s) `h1:`. "
            "Le verrou doit couvrir au moins deux plateformes, sinon un "
            "collegue sur un autre systeme le fera changer au premier `init`. "
            "`terraform providers lock -platform=...` les ajoute."
        )


# --------------------------------------------------------------------------
# 4. LE test : le verrou fait autorite, et l'etat est converge.
# --------------------------------------------------------------------------
def test_le_verrou_fait_autorite_et_l_etat_est_converge(applied: Path) -> None:
    """La preuve qui separe un lab fait d'un lab commence.

    Les deux moitiees sont dans le MEME test, deliberement : « l'etat est
    converge » est vrai de tout apply reussi, et isolee cette assertion ne
    dirait pas si le verrou a tenu. Accolee a l'autre, elle distingue une
    configuration verrouillee d'une configuration qui marche par hasard.
    """
    avant = _version_json(applied).get("provider_selections") or {}
    assert avant, "Aucun provider selectionne avant l'effacement de .terraform/."

    shutil.rmtree(applied / ".terraform", ignore_errors=True)
    proc = terraform("init", "-no-color", "-input=false", cwd=applied)
    assert proc.returncode == 0, (
        f"`terraform init` echoue apres effacement de .terraform/.\n{proc.stderr[-800:]}"
    )

    apres = _version_json(applied).get("provider_selections") or {}
    assert apres == avant, (
        f"Les versions retenues ont change apres un nouvel `init`.\n"
        f"  avant : {avant}\n  apres : {apres}\n\n"
        "Le verrou ne fait donc pas autorite, et c'est exactement ce qu'il "
        "existe pour empecher : sans lui, chaque poste resout la contrainte le "
        "jour ou il initialise, et deux collegues n'ont pas le meme provider."
    )

    plan = terraform(
        "plan", "-no-color", "-input=false", "-detailed-exitcode", cwd=applied
    )
    assert plan.returncode != 1, f"`terraform plan` a echoue.\n{plan.stderr[-800:]}"
    assert plan.returncode == 0, (
        "`terraform plan -detailed-exitcode` rend 2 : des changements restent "
        "planifies, donc la configuration n'a pas converge."
    )
