"""Non-régression du lab state-backends : un échec ne touche jamais au workdir.

Le défaut corrigé (mesuré sur dsoxlab 0.11.2, Terraform 1.16.1) : la fixture
renommait `backend.tf` dans `challenge/work`, puis initialisait et migrait sur
place. Une solution juste passait au premier `check` et bloquait tous les
suivants (« Backend configuration changed ») ; un échec avant le `yield`
laissait `backend.tf` renommé en `backend.tf.aside`. Dans dsoxlab, une fixture
en erreur s'affiche « non évalué » sans message : l'apprenant restait bloqué
sans savoir pourquoi (22 tentatives sur 66 en production, 2026-11-20 au 25).

La CI n'a pas Terraform. Ce test pose donc un FAUX `terraform` sur le PATH,
qui échoue à l'étape choisie, et joue la vraie suite du lab contre une copie
de la solution. Il exige, pour chaque étape :

- que le workdir soit identique, octet pour octet, avant et après ;
- qu'aucun test ne sorte en ERROR (erreur de fixture = « non évalué ») ;
- que l'échec nomme son étape, pour que l'apprenant sache quoi corriger.
"""

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SUITE = REPO / "labs" / "state" / "backends" / "challenge" / "tests" / "test_functional.py"

FAUX_TERRAFORM = """#!/usr/bin/env python3
import os, sys
args = sys.argv[1:]
etape = os.environ["FAUX_TF_ECHOUE_SUR"]
if args[:1] == ["init"]:
    if "-migrate-state" in args:
        if etape == "migration":
            sys.exit("Error: migration simulee")
    elif etape == "init":
        sys.exit("Error: init simule")
    sys.exit(0)
if args[:1] == ["apply"]:
    if etape == "apply":
        sys.exit("Error: apply simule")
    sys.exit(0)
if args[:2] == ["state", "pull"]:
    print('{"lineage": "faux"}')
    sys.exit(0)
sys.exit("Error: commande non simulee")
"""

SOLUTION = {
    "backend.tf": 'terraform {\n  backend "local" {}\n}\n',
    "dev.local.tfbackend": 'path = "etat/dev/terraform.tfstate"\n',
    "prod.local.tfbackend": 'path = "etat/prod/terraform.tfstate"\n',
}


def _empreinte(racine: Path) -> dict[str, str]:
    return {
        str(f.relative_to(racine)): hashlib.sha256(f.read_bytes()).hexdigest()
        for f in sorted(racine.rglob("*")) if f.is_file()
    }


@pytest.mark.parametrize(("etape", "mot"), [
    ("init", "Étape 1"),
    ("apply", "Étape 2"),
    ("migration", "Étape 3"),
], ids=["init", "apply", "migration"])
def test_un_echec_nomme_son_etape_et_laisse_le_workdir_intact(
    tmp_path: Path, etape: str, mot: str
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    faux = bin_dir / "terraform"
    faux.write_text(FAUX_TERRAFORM, encoding="utf-8")
    faux.chmod(0o755)

    work = tmp_path / "work"
    work.mkdir()
    for fixture in (SUITE.parents[2] / "fixtures").iterdir():
        (work / fixture.name).write_bytes(fixture.read_bytes())
    for nom, contenu in SOLUTION.items():
        (work / nom).write_text(contenu, encoding="utf-8")
    avant = _empreinte(work)

    env = dict(
        os.environ,
        PATH=f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        LAB_WORKDIR=str(work),
        LAB_NO_REPLAY="1",
        DSOXLAB_LANG="fr",
        FAUX_TF_ECHOUE_SUR=etape,
    )
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(SUITE), "-q", "--no-header", "-rA",
         "-p", "no:cacheprovider"],
        cwd=REPO, env=env, capture_output=True, text=True, check=False,
    )
    sortie = proc.stdout + proc.stderr

    assert _empreinte(work) == avant, (
        f"Un échec à l'étape « {etape} » a modifié challenge/work. La validation "
        "doit se jouer dans une copie : l'apprenant retrouverait sinon son dossier "
        f"changé, et le check suivant bloqué.\n{sortie[-2000:]}"
    )
    erreurs = [ligne for ligne in sortie.splitlines() if ligne.startswith("ERROR ")]
    assert not erreurs, (
        f"Échec à l'étape « {etape} » rendu en erreur de fixture : dsoxlab "
        "l'affiche « non évalué » sans aucun message.\n" + "\n".join(erreurs)
    )
    for test in ("test_migration_conserve_le_lineage", "test_backend_resolu_sur_dev",
                 "test_idempotence"):
        assert f"FAILED labs/state/backends/challenge/tests/test_functional.py::{test}" in sortie, (
            f"{test} devait échouer quand l'étape « {etape} » échoue.\n{sortie[-2000:]}"
        )
    assert mot in sortie, (
        f"Le message ne nomme pas l'étape en échec ({mot!r} attendu).\n{sortie[-2000:]}"
    )
