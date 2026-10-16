"""Tests fonctionnels du lab « prouver un module avec terraform test ».

Le livrable de ce lab est une suite `.tftest.hcl`. On ne peut donc pas se
contenter de la lire : une suite qui n'asserte rien passerait au vert. Les tests
ci-dessous la MUTENT. Ils copient le module dans un repertoire temporaire, y
cassent UN comportement a la fois, et exigent que la suite de l'apprenant s'en
apercoive. Une suite qui survit a une mutation ne teste pas ce qu'elle pretend.

Faits verifies sur Terraform 1.15.4, hors ligne, module sans provider :
- `terraform test` s'execute contre la configuration du repertoire COURANT :
  une suite placee dans `<module>/tests/` teste le module lui-meme, sans
  configuration racine enveloppante ;
- le flux `-json` est un JSONL d'evenements types, dont `test_summary` qui porte
  `status`, `passed`, `failed`, `errored` et `skipped` ;
- le code de retour vaut 0 si tout passe, 1 des qu'un run echoue ;
- retirer la `validation` du module fait echouer un run `expect_failures` sur
  `Error: Missing expected failure` ;
- un `-filter` qui ne correspond a aucun fichier rend `Success! 0 passed, 0
  failed.` et sort en 0 : une suite absente ne se distingue pas d'une suite
  verte, d'ou les mutations.
"""

import json
import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, message, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "modules-test-module"

MODULE = "etiquette"
RUNS_ATTENDUS = 4

# Chaque mutation casse UN comportement du module. La suite doit tomber.
MUTATIONS = (
    (
        "la validation du prefixe",
        "variables.tf",
        """
  validation {
    condition     = length(var.prefixe) >= 3
    error_message = "Le prefixe doit contenir au moins 3 caracteres."
  }
""",
        "",
        "Aucun run n'exige l'echec d'un prefixe trop court. Un module qui REFUSE "
        "une entree invalide se prouve avec `expect_failures`, pas avec une "
        "assertion : il n'y a rien a asserer quand rien ne doit etre produit.",
    ),
    (
        "le defaut du suffixe",
        "variables.tf",
        'description = "Suffixe facultatif, ajoute derriere un tiret."\n  default     = ""',
        'description = "Suffixe facultatif, ajoute derriere un tiret."\n  default     = "zzz"',
        "Aucun run ne verifie l'etiquette produite quand l'appelant ne passe QUE "
        "le prefixe. C'est pourtant le comportement par defaut du module.",
    ),
    (
        "le separateur du suffixe",
        "main.tf",
        '"${var.prefixe}-${var.suffixe}"',
        '"${var.prefixe}_${var.suffixe}"',
        "Aucun run ne verifie l'etiquette produite avec un suffixe. Le tiret fait "
        "partie du contrat du module.",
    ),
    (
        "le passage en majuscules",
        "main.tf",
        "var.majuscules ? upper(local.compose) : local.compose",
        "local.compose",
        "Aucun run ne verifie l'effet de `majuscules = true`. Une entree qui ne "
        "sert a rien dans les tests n'est pas couverte.",
    ),
)


def _module(racine: Path) -> Path:
    chemin = racine / MODULE
    if not chemin.is_dir():
        pytest.fail(message(
            en=f"The module's directory {MODULE}/ is missing from challenge/work.",
            fr=f"Le répertoire du module {MODULE}/ est absent de challenge/work.",
        ))
    return chemin


def _lancer_test(module: Path) -> subprocess.CompletedProcess[str]:
    return terraform("test", "-no-color", cwd=module)


def _resume(module: Path) -> dict:
    """Evenement `test_summary` du flux JSONL de `terraform test -json`."""
    proc = terraform("test", "-json", cwd=module)
    resume = None
    for brute in proc.stdout.splitlines():
        ligne = brute.strip()
        if not ligne:
            continue
        try:
            evenement = json.loads(ligne)
        except json.JSONDecodeError:
            continue
        if evenement.get("type") == "test_summary":
            resume = evenement["test_summary"]
    if resume is None:
        pytest.fail(
            message(
            en="The `terraform test -json` stream contains no "
            f"`test_summary` event.\n{proc.stdout[-800:]}\n{proc.stderr[-800:]}",
            fr="Le flux `terraform test -json` ne contient aucun événement "
            f"`test_summary`.\n{proc.stdout[-800:]}\n{proc.stderr[-800:]}",
        )
        )
    return resume


def _muter(module: Path, tmp: Path, fichier: str, avant: str, apres: str) -> Path:
    """Copie du module avec UN comportement casse, sans toucher au workdir."""
    copie = tmp / "mutant"
    if copie.exists():
        shutil.rmtree(copie)
    shutil.copytree(module, copie)
    cible = copie / fichier
    texte = cible.read_text(encoding="utf-8")
    assert avant in texte, message(
        en=f"The module {fichier} was modified: the expected fragment cannot be found. "
        "The module was to stay intact, only the test suite is to be written.",
        fr=f"Le module {fichier} a été modifié : le fragment attendu est introuvable. "
        "Le module devait rester intact, seule la suite de tests est à écrire.",
    )
    cible.write_text(texte.replace(avant, apres, 1), encoding="utf-8")
    return copie


@pytest.fixture(scope="module")
def racine() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    yield WORKDIR


@pytest.fixture(scope="module")
def suite_verte(racine: Path) -> Iterator[Path]:
    """Module intact, suite au vert : sans cela, muter ne prouve rien.

    Une suite absente ou qui ne compile pas fait echouer TOUS les mutants, et
    les tests de mutation passeraient alors sans qu'une seule assertion ait ete
    ecrite. Ce temoin ferme la porte.
    """
    module = _module(racine)
    proc = _lancer_test(module)
    if proc.returncode != 0:
        pytest.fail(
            message(
            en="The suite does not pass on the INTACT module: the mutations would "
            "prove nothing. First make `terraform test` pass in "
            f"{MODULE}/.\n{proc.stdout[-1200:]}",
            fr="La suite ne passe pas sur le module INTACT : les mutations ne "
            "prouveraient rien. Faites d'abord passer `terraform test` dans "
            f"{MODULE}/.\n{proc.stdout[-1200:]}",
        )
        )
    yield module


# --------------------------------------------------------------------------
# 1. La suite existe, au bon endroit, et elle passe
# --------------------------------------------------------------------------

def test_la_suite_vit_au_bon_endroit_et_elle_passe(racine: Path) -> None:
    """L'emplacement de la suite vit ici, et plus dans un test a lui.

    Seul, il etait VERT AVANT LE TRAVAIL : les fixtures posent deja un
    `etiquette/tests/etiquette.tftest.hcl`, et constater sa presence revenait a
    constater le setup. L'apprenant n'a pas a creer ce fichier, il a a le faire
    PASSER.

    L'emplacement reste a verifier, et pour une bonne raison : `terraform test`
    ne dit rien quand il ne trouve aucune suite. Il affiche `Success! 0 passed,
    0 failed.` et sort en 0. Une suite rangee ailleurs donnerait donc un succes
    qui ne teste rien, et c'est exactement le piege que ce controle ferme.
    """
    tests = _module(racine) / "tests"
    suites = sorted(tests.glob("*.tftest.hcl")) if tests.is_dir() else []
    assert suites, message(
        en=f"No `*.tftest.hcl` file in {MODULE}/tests/. `terraform test` "
        "looks for its suites there, and says nothing when it finds none: it "
        "prints `Success! 0 passed, 0 failed.` and exits 0.",
        fr=f"Aucun fichier `*.tftest.hcl` dans {MODULE}/tests/. `terraform test` "
        "cherche ses suites là, et ne dit rien quand il n'en trouve aucune : il "
        "affiche `Success! 0 passed, 0 failed.` et sort en 0.",
    )

    proc = _lancer_test(_module(racine))
    assert proc.returncode == 0, message(
        en=f"`terraform test` exits with {proc.returncode}, expected 0.\n"
        f"{proc.stdout[-1200:]}",
        fr=f"`terraform test` sort en {proc.returncode}, attendu 0.\n"
        f"{proc.stdout[-1200:]}",
    )


def test_le_resume_json_annonce_quatre_runs_verts(racine: Path) -> None:
    resume = _resume(_module(racine))
    assert resume["status"] == "pass", message(
        en=f"The JSON summary announces `{resume['status']}`: {resume}",
        fr=f"Le résumé JSON annonce `{resume['status']}` : {resume}",
    )
    assert resume["failed"] == 0 and resume["errored"] == 0, message(
        en=f"The JSON summary counts failures: {resume}",
        fr=f"Le résumé JSON compte des échecs : {resume}",
    )
    assert resume["passed"] >= RUNS_ATTENDUS, message(
        en=f"The JSON summary counts {resume['passed']} successful run(s), at "
        f"least {RUNS_ATTENDUS} expected: the four behaviours of CIBLE.md must "
        "each have their own.",
        fr=f"Le résumé JSON compte {resume['passed']} run(s) réussi(s), attendu au "
        f"moins {RUNS_ATTENDUS} : les quatre comportements de CIBLE.md doivent "
        "chacun avoir le leur.",
    )


# --------------------------------------------------------------------------
# 2. Les mutations : une suite qui ne detecte rien ne prouve rien
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "libelle,fichier,avant,apres,indice",
    MUTATIONS,
    ids=[m[0].replace(" ", "-") for m in MUTATIONS],
)
def test_la_suite_detecte_la_mutation(
    suite_verte: Path, tmp_path: Path, libelle: str, fichier: str,
    avant: str, apres: str, indice: str,
) -> None:
    mutant = _muter(suite_verte, tmp_path, fichier, avant, apres)
    proc = _lancer_test(mutant)
    assert proc.returncode != 0, message(
        en=f"The module was broken on {libelle}, and the suite passes anyway. "
        f"{indice}\n{proc.stdout[-900:]}",
        fr=f"Le module a été cassé sur {libelle}, et la suite passe quand même. "
        f"{indice}\n{proc.stdout[-900:]}",
    )


def test_l_echec_attendu_est_bien_declare(suite_verte: Path, tmp_path: Path) -> None:
    """La mutation de la validation doit tomber sur `Missing expected failure`."""
    _, fichier, avant, apres, _ = MUTATIONS[0]
    mutant = _muter(suite_verte, tmp_path, fichier, avant, apres)
    proc = _lancer_test(mutant)
    assert "Missing expected failure" in proc.stdout + proc.stderr, message(
        en="The suite does fail when the validation disappears, but not on "
        "`Error: Missing expected failure`. The refusal of an invalid input is "
        "proven with `expect_failures`, which names the object expected to fail.\n"
        f"{proc.stdout[-900:]}",
        fr="La suite tombe bien quand la validation disparaît, mais pas sur "
        "`Error: Missing expected failure`. Le refus d'une entrée invalide se "
        "prouve avec `expect_failures`, qui nomme l'objet attendu en échec.\n"
        f"{proc.stdout[-900:]}",
    )


# --------------------------------------------------------------------------
# 3. La suite est rejouable : elle ne laisse aucun etat derriere elle
# --------------------------------------------------------------------------

def test_la_suite_est_rejouable_et_ne_laisse_pas_d_etat(racine: Path) -> None:
    module = _module(racine)
    premier = _lancer_test(module)
    second = _lancer_test(module)
    assert premier.returncode == 0 and second.returncode == 0, message(
        en="The suite does not pass twice in a row: it depends on state left "
        f"by its own run.\n{second.stdout[-900:]}",
        fr="La suite ne passe pas deux fois de suite : elle dépend d'un état laissé "
        f"par son propre passage.\n{second.stdout[-900:]}",
    )
    restes = sorted(p.name for p in module.glob("*.tfstate*"))
    assert not restes, message(
        en=f"The module's directory contains {restes} after the tests. "
        "`terraform test` manages its own state and destroys it at teardown.",
        fr=f"Le répertoire du module contient {restes} après les tests. "
        "`terraform test` gère son état lui-même et le détruit au teardown.",
    )
