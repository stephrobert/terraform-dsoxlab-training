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

from conftest import exiger_workdir, message, terraform, workdir_lab

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
            message(
            en="`terraform init` failed in challenge/work. Does the "
            "`terraform {}` block declare its `required_providers`?\n"
            f"{init.stderr[-1200:]}",
            fr="`terraform init` a échoué dans challenge/work. Le bloc "
            "`terraform {}` déclare-t-il bien ses `required_providers` ?\n"
            f"{init.stderr[-1200:]}",
        )
        )
    return WORKDIR


@pytest.fixture(scope="module")
def applied(prepared: Path) -> Path:
    app = terraform(
        "apply", "-auto-approve", "-input=false", "-no-color", cwd=prepared
    )
    if app.returncode != 0:
        pytest.fail(
            message(
            en="`terraform apply` failed: the configuration does not converge.\n"
            f"{app.stderr[-1500:]}",
            fr="`terraform apply` a échoué : la configuration ne converge pas.\n"
            f"{app.stderr[-1500:]}",
        )
        )
    return prepared


def _version_json(cwd: Path) -> dict:
    proc = terraform("version", "-json", cwd=cwd)
    assert proc.returncode == 0, message(
        en=f"`terraform version -json` failed in {cwd}. {proc.stderr.strip()}",
        fr=f"`terraform version -json` a échoué dans {cwd}. {proc.stderr.strip()}",
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
    assert infos.get("terraform_version"), message(
        en="`terraform version -json` returns no version.",
        fr="`terraform version -json` ne rend aucune version.",
    )

    selections = infos.get("provider_selections") or {}
    assert selections, message(
        en="No provider selected after `init`: does the `terraform {}` block "
        "declare a `required_providers`?",
        fr="Aucun provider sélectionné après `init` : le bloc `terraform {}` "
        "déclare-t-il un `required_providers` ?",
    )
    assert set(selections) == PROVIDERS_ATTENDUS, message(
        en=f"Providers kept: {sorted(selections)}.\nExpected: "
        f"{sorted(PROVIDERS_ATTENDUS)}.\n\nAll three must be declared "
        "AND used: a provider that is declared but used by no resource "
        "does not enter the state.",
        fr=f"Providers retenus : {sorted(selections)}.\nAttendus : "
        f"{sorted(PROVIDERS_ATTENDUS)}.\n\nles trois doivent être déclarés "
        "ET employés : un provider déclaré mais dont aucune ressource ne se "
        "sert n'entre pas dans l'état.",
    )


# --------------------------------------------------------------------------
# 2. Une contrainte insatisfaisable fait REFUSER l'execution.
# --------------------------------------------------------------------------
def test_une_contrainte_de_version_impossible_fait_echouer_init(prepared: Path) -> None:
    """Preuve ACTIVE, et dans les deux sens : le contre-exemple echoue, le
    repertoire principal reussit. Sans la seconde moitie, un environnement
    casse passerait pour une contrainte qui refuse."""
    echec = prepared / "echec-version"
    assert echec.is_dir(), message(
        en="The `echec-version/` sub-directory is missing. It carries the "
        "counter-example: a configuration whose `required_version` cannot "
        "be satisfied by the installed CLI.",
        fr="Le sous-répertoire `echec-version/` est absent. Il porte le "
        "contre-exemple : une configuration dont le `required_version` ne peut "
        "pas être satisfait par la CLI installée.",
    )

    refuse = terraform("init", "-no-color", "-input=false", cwd=echec)
    assert refuse.returncode != 0, message(
        en="`terraform init` SUCCEEDED in echec-version/, although its constraint "
        "was supposed to be out of reach. Is the `required_version` there really "
        "impossible to satisfy?",
        fr="`terraform init` a RÉUSSI dans echec-version/, alors que sa contrainte "
        "devait être hors d'atteinte. Le `required_version` y est-il bien "
        "impossible à satisfaire ?",
    )

    ok = terraform("init", "-no-color", "-input=false", cwd=prepared)
    assert ok.returncode == 0, message(
        en="`terraform init` fails in the main directory TOO: it is therefore "
        f"not the constraint that refuses.\n{ok.stderr[-800:]}",
        fr="`terraform init` échoue AUSSI dans le répertoire principal : ce n'est "
        f"donc pas la contrainte qui refuse.\n{ok.stderr[-800:]}",
    )


# --------------------------------------------------------------------------
# 3. Le verrou est un fichier machine : on le lit comme tel.
# --------------------------------------------------------------------------
def test_le_verrou_couvre_les_trois_providers_sur_deux_plateformes(prepared: Path) -> None:
    verrou = prepared / ".terraform.lock.hcl"
    assert verrou.is_file(), message(
        en="`.terraform.lock.hcl` is missing: it is `terraform init` that "
        "produces it, and it freezes the resolved versions.",
        fr="`.terraform.lock.hcl` est absent : c'est `terraform init` qui le "
        "produit, et il fige les versions résolues.",
    )

    blocs = dict(BLOC_VERROU.findall(verrou.read_text(encoding="utf-8")))
    assert set(blocs) == PROVIDERS_ATTENDUS, message(
        en=f"The lock covers {sorted(blocs)}, and not the three expected providers.",
        fr=f"Le verrou couvre {sorted(blocs)}, et non les trois providers attendus.",
    )

    for nom, corps in sorted(blocs.items()):
        assert re.search(r'version\s*=\s*"', corps), message(
            en=f"The block of {nom} carries no resolved `version`.",
            fr=f"Le bloc de {nom} ne porte pas de `version` résolue.",
        )
        assert re.search(r'constraints\s*=\s*"', corps), message(
            en=f"The block of {nom} carries no `constraints`. It comes from the "
            "`required_providers`: with no declared constraint, the lock only "
            "keeps the version of the day.",
            fr=f"Le bloc de {nom} ne porte pas de `constraints`. Elle vient du "
            "`required_providers` : sans contrainte déclarée, le verrou ne "
            "retient que la version du jour.",
        )
        empreintes = re.findall(r'"h1:[^"]+"', corps)
        assert len(empreintes) >= PLATEFORMES_MINIMUM, message(
            en=f"The block of {nom} carries only {len(empreintes)} `h1:` checksum(s). "
            "The lock must cover at least two platforms, otherwise a "
            "colleague on another system will change it at the first `init`. "
            "`terraform providers lock -platform=…` adds them.",
            fr=f"Le bloc de {nom} ne porte que {len(empreintes)} somme(s) `h1:`. "
            "Le verrou doit couvrir au moins deux plateformes, sinon un "
            "collègue sur un autre système le fera changer au premier `init`. "
            "`terraform providers lock -platform=...` les ajoute.",
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
    assert avant, message(
        en="No provider selected before deleting .terraform/.",
        fr="Aucun provider sélectionné avant l'effacement de .terraform/.",
    )

    shutil.rmtree(applied / ".terraform", ignore_errors=True)
    proc = terraform("init", "-no-color", "-input=false", cwd=applied)
    assert proc.returncode == 0, message(
        en=f"`terraform init` fails after deleting .terraform/.\n{proc.stderr[-800:]}",
        fr=f"`terraform init` échoue après effacement de .terraform/.\n{proc.stderr[-800:]}",
    )

    apres = _version_json(applied).get("provider_selections") or {}
    assert apres == avant, message(
        en=f"The versions kept changed after a new `init`.\n"
        f"  before: {avant}\n  after : {apres}\n\n"
        "The lock therefore does not have authority, and that is exactly what it "
        "exists to prevent: without it, each machine resolves the constraint on the "
        "day it initialises, and two colleagues do not have the same provider.",
        fr=f"Les versions retenues ont changé après un nouvel `init`.\n"
        f"  avant : {avant}\n  après : {apres}\n\n"
        "Le verrou ne fait donc pas autorité, et c'est exactement ce qu'il "
        "existe pour empêcher : sans lui, chaque poste résout la contrainte le "
        "jour où il initialise, et deux collègues n'ont pas le même provider.",
    )

    plan = terraform(
        "plan", "-no-color", "-input=false", "-detailed-exitcode", cwd=applied
    )
    assert plan.returncode != 1, message(
        en=f"`terraform plan` failed.\n{plan.stderr[-800:]}",
        fr=f"`terraform plan` a échoué.\n{plan.stderr[-800:]}",
    )
    assert plan.returncode == 0, message(
        en="`terraform plan -detailed-exitcode` returns 2: changes remain "
        "planned, so the configuration has not converged.",
        fr="`terraform plan -detailed-exitcode` rend 2 : des changements restent "
        "planifiés, donc la configuration n'a pas convergé.",
    )
