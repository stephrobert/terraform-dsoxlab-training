"""Tests fonctionnels du lab « organiser un depot Terraform ».

Le decoupage d'une configuration en fichiers est presente partout comme une
operation sans risque, au motif que `terraform validate` passe. C'est faux, et la
doc le dit : « The validate command does not check if argument values are valid
for a specific provider [...] It does not evaluate any existing state. » Un bloc
perdu au copier-colle passe donc `validate` sans un mot.

La seule preuve d'invariance est la COMPARAISON de deux plans. Ces tests
replanifient donc la configuration monolithique d'origine, telle qu'elle est
livree en fixture, et exigent que le plan de l'apprenant soit le meme.

Faits verifies sur Terraform 1.15.4, hors ligne, providers `local` et `random` :
- `terraform fmt -check` ne traite que le repertoire courant, `-recursive` est
  necessaire des qu'il y a des sous-repertoires ;
- un plan enregistre par `-out=tfplan` n'a AUCUNE extension : un `.gitignore` qui
  ne connait que `*.tfplan` ne l'attrape pas ;
- le `.terraform.lock.hcl` doit au contraire etre versionne.
"""

import json
import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, message, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "environments-organize-terraform-repo"

LAB = Path(__file__).resolve().parents[2]
FIXTURES = LAB / "fixtures" / "projet"
PROJET = "projet"

# Le socle nomme par le style guide officiel.
SOCLE = {
    "terraform.tf": "terraform",
    "providers.tf": "provider",
    "variables.tf": "variable",
    "outputs.tf": "output",
}

IGNORES = ("tfplan", "terraform.tfstate", "terraform.tfstate.backup")
VERSIONNE = ".terraform.lock.hcl"


def _projet(racine: Path) -> Path:
    chemin = racine / PROJET
    if not chemin.is_dir():
        pytest.fail(message(
            en=f"The {PROJET}/ directory is missing from challenge/work.",
            fr=f"Le répertoire {PROJET}/ est absent de challenge/work.",
        ))
    return chemin


def _plan(dossier: Path, nom: str = "analyse.tfplan") -> dict:
    plan = terraform("plan", "-input=false", "-no-color", f"-out={nom}", cwd=dossier)
    if plan.returncode != 0:
        pytest.fail(
            message(
            en=f"`terraform plan` failed in {dossier.name}.\n{plan.stderr[-1100:]}",
            fr=f"`terraform plan` a échoué dans {dossier.name}.\n{plan.stderr[-1100:]}",
        )
        )
    montre = terraform("show", "-json", nom, cwd=dossier)
    montre.check_returncode()
    return json.loads(montre.stdout)


def _empreinte(plan: dict) -> dict:
    """Ce qui doit rester identique d'un decoupage a l'autre.

    On ecarte l'horodatage, la version de Terraform et la representation de la
    CONFIGURATION, qui reflete legitimement le decoupage. Restent les valeurs
    planifiees, les changements de ressources et ceux des sorties : le fond.
    """
    return {
        "planned_values": plan.get("planned_values"),
        "resource_changes": sorted(
            plan.get("resource_changes", []), key=lambda c: c["address"]
        ),
        "output_changes": plan.get("output_changes"),
        "variables": plan.get("variables"),
    }


def _git(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )


@pytest.fixture(scope="module")
def racine() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=_projet(WORKDIR))
    if init.returncode != 0:
        pytest.fail(message(
            en=f"`terraform init` failed.\n{init.stderr[-1100:]}",
            fr=f"`terraform init` a échoué.\n{init.stderr[-1100:]}",
        ))
    yield WORKDIR


@pytest.fixture(scope="module")
def decoupe(racine: Path) -> Iterator[Path]:
    """Le decoupage a eu lieu : sans lui, l'invariance ne prouve rien.

    Un `challenge/work` intact a evidemment le meme plan que lui-meme, passe
    `validate` et passe `fmt`. Ces trois controles n'ont de sens qu'une fois les
    fichiers du socle en place.
    """
    projet = _projet(racine)
    manquants = [nom for nom in SOCLE if not (projet / nom).is_file()]
    if manquants:
        pytest.fail(
            message(
            en=f"The split did not happen, {sorted(manquants)} are missing: "
            "comparing the plan with itself would prove nothing.",
            fr=f"Le découpage n'a pas eu lieu, {sorted(manquants)} manquent : "
            "comparer le plan à lui-même ne prouverait rien.",
        )
        )
    yield racine


@pytest.fixture(scope="module")
def temoin(tmp_path_factory: pytest.TempPathFactory) -> Iterator[dict]:
    """Plan de la configuration monolithique d'origine, rejouee a l'identique."""
    copie = tmp_path_factory.mktemp("monolithe") / "projet"
    shutil.copytree(FIXTURES, copie)
    init = terraform("init", "-input=false", "-no-color", cwd=copie)
    if init.returncode != 0:
        pytest.fail(
            message(
            en=f"`terraform init` failed on the original fixture.\n{init.stderr[-800:]}",
            fr=f"`terraform init` a échoué sur la fixture d'origine.\n{init.stderr[-800:]}",
        )
        )
    yield _empreinte(_plan(copie))


# --------------------------------------------------------------------------
# 1. Le plan n'a pas bouge
# --------------------------------------------------------------------------

def test_le_plan_est_identique_a_celui_du_monolithe(decoupe: Path, temoin: dict) -> None:
    obtenu = _empreinte(_plan(_projet(decoupe)))
    for cle, attendu in temoin.items():
        assert obtenu[cle] == attendu, message(
            en=f"The split changed `{cle}` in the plan. A green `terraform validate` "
            "proves nothing here: it looks neither at the state, nor at the value of the "
            "arguments. Only comparing two plans establishes invariance.",
            fr=f"Le découpage a changé `{cle}` du plan. Un `terraform validate` vert "
            "ne prouve rien ici : il ne regarde ni l'état, ni la valeur des "
            "arguments. Seule la comparaison de deux plans établit l'invariance.",
        )


def test_la_configuration_reste_valide(decoupe: Path) -> None:
    validate = terraform("validate", "-no-color", cwd=_projet(decoupe))
    assert validate.returncode == 0, message(
        en=f"`terraform validate` fails.\n{validate.stdout[-800:]}",
        fr=f"`terraform validate` échoue.\n{validate.stdout[-800:]}",
    )


# --------------------------------------------------------------------------
# 2. Le socle de fichiers du style guide
# --------------------------------------------------------------------------

def test_le_socle_de_fichiers_est_en_place(racine: Path) -> None:
    projet = _projet(racine)
    manquants = [nom for nom in SOCLE if not (projet / nom).is_file()]
    assert not manquants, message(
        en=f"{sorted(manquants)} are missing. The style guide names those files, and they "
        "are not the ones you would think: the `terraform` block lives in "
        "`terraform.tf`, not in a `versions.tf` that appears nowhere in "
        "the official documentation.",
        fr=f"{sorted(manquants)} manquent. Le style guide nomme ces fichiers, et ce "
        "ne sont pas ceux qu'on croit : le bloc `terraform` vit dans "
        "`terraform.tf`, pas dans un `versions.tf` qui n'apparaît nulle part dans "
        "la documentation officielle.",
    )


def test_chaque_bloc_est_dans_son_fichier(racine: Path) -> None:
    projet = _projet(racine)
    for nom, bloc in SOCLE.items():
        contenu = (projet / nom).read_text(encoding="utf-8")
        assert f"{bloc} " in contenu, message(
            en=f"{nom} contains no `{bloc}` block.",
            fr=f"{nom} ne contient aucun bloc `{bloc}`.",
        )

    autres = {f.name for f in projet.glob("*.tf") if f.name not in SOCLE}
    assert autres, message(
        en="No file outside the base: the `resource` blocks must stay in a "
        "`main.tf`, which the base does not replace.",
        fr="Aucun fichier hors du socle : les `resource` doivent rester dans un "
        "`main.tf`, que le socle ne remplace pas.",
    )

    terraform_tf = (projet / "terraform.tf").read_text(encoding="utf-8")
    assert terraform_tf.count("terraform {") == 1, message(
        en="`terraform.tf` must contain a SINGLE `terraform` block.",
        fr="`terraform.tf` doit contenir UN SEUL bloc `terraform`.",
    )
    assert 'provider "' not in terraform_tf, message(
        en="`terraform.tf` still contains a `provider` block: the documentation "
        "reserves a file for it, `providers.tf`.",
        fr="`terraform.tf` contient encore un bloc `provider` : la documentation lui "
        "réserve un fichier, `providers.tf`.",
    )


def test_variables_et_sorties_sont_triees(racine: Path) -> None:
    projet = _projet(racine)
    for nom, bloc in (("variables.tf", "variable"), ("outputs.tf", "output")):
        contenu = (projet / nom).read_text(encoding="utf-8")
        declares = [
            ligne.split('"')[1]
            for ligne in contenu.splitlines()
            if ligne.startswith(f'{bloc} "')
        ]
        assert declares, message(
            en=f"{nom} declares no `{bloc}` block.",
            fr=f"{nom} ne déclare aucun bloc `{bloc}`.",
        )
        assert declares == sorted(declares), message(
            en=f"{nom} declares {declares}: the style guide asks for "
            f"ALPHABETICAL order, \"all {bloc} blocks in alphabetical order\".",
            fr=f"{nom} déclare {declares} : le style guide demande l'ordre "
            f"ALPHABÉTIQUE, « all {bloc} blocks in alphabetical order ».",
        )


# --------------------------------------------------------------------------
# 3. Le formatage, sur toute l'arborescence
# --------------------------------------------------------------------------

def test_l_arborescence_entiere_est_formatee(decoupe: Path) -> None:
    fmt = terraform("fmt", "-check", "-recursive", "-no-color", cwd=decoupe)
    assert fmt.returncode == 0, message(
        en=f"`terraform fmt -check -recursive` returns {fmt.returncode} and reports "
        f"{fmt.stdout.strip().splitlines()}. Without `-recursive`, the command only "
        "looks at the current directory: a CI check stays "
        "green with badly formatted sub-directories.",
        fr=f"`terraform fmt -check -recursive` rend {fmt.returncode} et signale "
        f"{fmt.stdout.strip().splitlines()}. Sans `-recursive`, la commande ne "
        "regarde que le répertoire courant : un contrôle d'intégration reste "
        "vert avec des sous-répertoires mal formatés.",
    )


# --------------------------------------------------------------------------
# 4. Le depot ignore ce qu'il faut, et versionne le reste
# --------------------------------------------------------------------------

@pytest.fixture(scope="module")
def depot(racine: Path, tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    """Un depot jetable pour faire TRAVAILLER le .gitignore de l'apprenant.

    Un `.gitignore` ne se verifie pas en le lisant : `git check-ignore` rend le
    verdict que git appliquerait vraiment, motifs de negation compris. Le depot
    est cree dans une copie, le workdir n'est pas touche.
    """
    gitignore = racine / ".gitignore"
    if not gitignore.is_file():
        pytest.fail(
            message(
            en="No `.gitignore` at the root of `challenge/work`: the repository "
            "would commit the state, the working directory and the saved plans.",
            fr="Aucun `.gitignore` à la racine de `challenge/work` : le dépôt "
            "committerait l'état, le répertoire de travail et les plans enregistrés.",
        )
        )
    copie = tmp_path_factory.mktemp("depot") / "travail"
    shutil.copytree(racine, copie, ignore=shutil.ignore_patterns(".git"))
    _git("init", "-q", "-b", "main", cwd=copie).check_returncode()
    yield copie


def test_le_depot_ignore_les_artefacts(depot: Path) -> None:
    for chemin in IGNORES:
        verdict = _git("check-ignore", "-q", f"{PROJET}/{chemin}", cwd=depot)
        assert verdict.returncode == 0, message(
            en=f"`{chemin}` is NOT ignored. Mind the saved plan: "
            "`terraform plan -out=tfplan` produces a file with NO extension, "
            "which a `*.tfplan` pattern does not catch, and which contains the "
            "resolved values, secrets included.",
            fr=f"`{chemin}` n'est PAS ignoré. Attention au plan enregistré : "
            "`terraform plan -out=tfplan` produit un fichier SANS extension, "
            "qu'un motif `*.tfplan` n'attrape pas, et qui contient les valeurs "
            "résolues, secrets compris.",
        )
    verdict = _git("check-ignore", "-q", f"{PROJET}/.terraform/", cwd=depot)
    assert verdict.returncode == 0, message(
        en="`.terraform/` is not ignored.",
        fr="`.terraform/` n'est pas ignoré.",
    )


def test_le_verrou_reste_versionne(depot: Path) -> None:
    verdict = _git("check-ignore", "-q", f"{PROJET}/{VERSIONNE}", cwd=depot)
    assert verdict.returncode != 0, message(
        en=f"`{VERSIONNE}` is ignored. On the contrary, it must be COMMITTED: it is what "
        "guarantees that the whole team uses the same provider versions.",
        fr=f"`{VERSIONNE}` est ignoré. Il doit au contraire être COMMITÉ : c'est lui "
        "qui garantit que toute l'équipe emploie les mêmes versions de providers.",
    )
