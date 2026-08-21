"""Tests fonctionnels du lab « la configuration qui refuse les valeurs absurdes ».

Principe : on ne lit jamais les `.tf` de l'apprenant. On lance Terraform avec
différentes variables et on n'exploite que des **codes retour** et le tableau
`checks` de `terraform show -json`.

Le champ `kind` de ce tableau est la pièce maîtresse : il prouve quel mécanisme
a réellement été écrit. Une `validation` sort en `kind: var`, une `precondition`
ou une `postcondition` en `kind: resource`, un bloc `check` en `kind: check`.
Placer un contrôle au mauvais niveau se voit donc immédiatement.
"""

import json
from pathlib import Path

import pytest

from conftest import exiger_workdir, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "write-code-conditionals"

PROD = ("-var", "environment=prod", "-var", "backup_bucket=lab-backup")


def plan(*args: str) -> int:
    """Code retour d'un `terraform plan` avec les variables données."""
    return terraform("plan", "-input=false", "-no-color", *args, cwd=WORKDIR).returncode


@pytest.fixture(scope="module")
def applied() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(f"`terraform init` a échoué.\n{init.stderr[-1200:]}")
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", *PROD, cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(
            "`terraform apply` en prod a échoué : la configuration comporte "
            "encore des expressions incomplètes, ou un mécanisme bloquant a été "
            "placé là où il ne fallait pas.\n"
            f"{app.stderr[-1200:]}"
        )
    return WORKDIR


@pytest.fixture(scope="module")
def controles(applied: Path) -> dict[str, dict]:
    """Le tableau `checks`, indexé par adresse affichable."""
    return {
        c["address"].get("to_display", ""): c
        for c in show_json(applied).get("checks", [])
    }


# --------------------------------------------------------------------------
# Les quatre mecanismes sont-ils reellement ecrits, et au bon niveau ?
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "adresse,kind_attendu,mecanisme",
    [
        ("var.environment", "var", "bloc validation sur environment"),
        ("var.backup_bucket", "var", "bloc validation croisée sur backup_bucket"),
        ("local_file.manifest", "resource", "precondition et postcondition"),
        ("check.budget_prod", "check", "bloc check"),
    ],
)
def test_mecanisme_present(controles: dict, adresse: str, kind_attendu: str, mecanisme: str) -> None:
    assert adresse in controles, (
        f"Aucun contrôle enregistré pour {adresse} : le {mecanisme} n'a pas été "
        f"écrit. Adresses trouvées : {sorted(controles)}."
    )
    kind = controles[adresse]["address"]["kind"]
    assert kind == kind_attendu, (
        f"{adresse} sort en kind={kind!r}, attendu {kind_attendu!r} : "
        "le contrôle n'est pas au niveau demandé."
    )


# --------------------------------------------------------------------------
# Validations d'entree
# --------------------------------------------------------------------------

def test_environnement_hors_enumere_refuse(applied: Path) -> None:
    """Un enuméré refusé, et surtout une valeur valide acceptée.

    Le second contrôle n'est pas décoratif : sans lui, ce test passerait au
    vert sur une configuration entièrement cassée, où tout `plan` échoue.
    """
    assert plan("-var", "environment=dev") == 0, (
        "`environment=dev` est refusé alors qu'il est valide : la configuration "
        "ne planifie pas, ou la validation est trop stricte."
    )
    assert plan("-var", "environment=qa") != 0, (
        "`environment=qa` est accepté : la validation de l'énuméré est absente."
    )


def test_backup_bucket_obligatoire_en_prod_seulement(applied: Path) -> None:
    assert plan("-var", "environment=prod", "-var", "backup_bucket=") != 0, (
        "backup_bucket vide est accepté en prod : la validation croisée manque."
    )
    assert plan("-var", "environment=dev", "-var", "backup_bucket=") == 0, (
        "backup_bucket vide est refusé en dev, alors qu'il ne doit l'être qu'en "
        "prod. La condition n'est pas conditionnée à l'environnement."
    )


# --------------------------------------------------------------------------
# Expressions conditionnelles
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "env,memoire,vcpu,extra",
    [
        ("dev", 512, 1, []),
        ("staging", 512, 2, []),
        ("prod", 2048, 4, ["-var", "backup_bucket=b"]),
    ],
)
def test_valeurs_calculees(applied: Path, env: str, memoire: int, vcpu: int, extra: list) -> None:
    app = terraform(
        "apply", "-auto-approve", "-input=false", "-no-color",
        "-var", f"environment={env}", *extra, cwd=applied,
    )
    assert app.returncode == 0, f"apply en {env} a échoué.\n{app.stderr[-800:]}"
    sortie = terraform("output", "-json", cwd=applied)
    sortie.check_returncode()
    outs = json.loads(sortie.stdout)
    assert outs["memory_mib"]["value"] == memoire, (
        f"En {env}, memory_mib vaut {outs['memory_mib']['value']}, attendu {memoire}."
    )
    assert outs["vcpu"]["value"] == vcpu, (
        f"En {env}, vcpu vaut {outs['vcpu']['value']}, attendu {vcpu}."
    )


def test_override_memoire_prioritaire(applied: Path) -> None:
    terraform("apply", "-auto-approve", "-input=false", "-no-color",
              "-var", "memory_mib_override=768", cwd=applied).check_returncode()
    outs = json.loads(terraform("output", "-json", cwd=applied).stdout)
    assert outs["memory_mib"]["value"] == 768, (
        "memory_mib_override n'a pas la priorité sur la valeur par défaut."
    )


def test_output_disparait_quand_null(applied: Path) -> None:
    """Un local valant null retire son output du document, il ne vaut pas null."""
    terraform("apply", "-auto-approve", "-input=false", "-no-color",
              "-var", "enable_second_disk=false", cwd=applied).check_returncode()
    outs = json.loads(terraform("output", "-json", cwd=applied).stdout)
    assert "second_disk_name" not in outs, (
        "La clé second_disk_name est présente alors que le disque est désactivé. "
        "Le local doit valoir null, ce qui retire l'output du document."
    )

    terraform("apply", "-auto-approve", "-input=false", "-no-color",
              "-var", "enable_second_disk=true", cwd=applied).check_returncode()
    outs = json.loads(terraform("output", "-json", cwd=applied).stdout)
    assert outs.get("second_disk_name", {}).get("value"), (
        "La clé second_disk_name est absente alors que le disque est activé."
    )


# --------------------------------------------------------------------------
# Ce qu'une validation ne peut PAS faire
# --------------------------------------------------------------------------

def test_precondition_sur_valeur_calculee(applied: Path) -> None:
    """Le rapport porte sur deux locals : seule une precondition peut le voir."""
    assert plan("-var", "memory_mib_override=64") != 0, (
        "memory_mib_override=64 est accepté. Avec 1 vCPU, cela fait 64 MiB par "
        "vCPU, sous le seuil de 256. Aucun bloc validation ne peut porter ce "
        "contrôle : il doit vivre dans une precondition."
    )
    assert plan("-var", "memory_mib_override=512") == 0, (
        "memory_mib_override=512 est refusé alors qu'il respecte le seuil : "
        "la precondition est trop stricte."
    )


def test_postcondition_sur_contenu_ecrit(applied: Path) -> None:
    """Le manifest réellement écrit doit se décoder et porter la clé env."""
    etat = show_json(applied)
    ressources = etat["values"]["root_module"]["resources"]
    manifest = next(
        (r for r in ressources if r.get("mode") == "managed" and r.get("type") == "local_file"),
        None,
    )
    assert manifest is not None, "Aucune ressource local_file gérée dans le state."
    contenu = json.loads(manifest["values"]["content"])
    for cle in ("env", "memory_mib", "vcpu"):
        assert cle in contenu, (
            f"Le manifest écrit ne porte pas la clé {cle!r}. Contenu : {contenu}."
        )


# --------------------------------------------------------------------------
# La marche decisive : bloquant contre non bloquant
# --------------------------------------------------------------------------

def test_check_echoue_sans_bloquer_apply(applied: Path) -> None:
    """En prod, le budget est dépassé : le check doit échouer, l'apply réussir."""
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", *PROD, cwd=applied)
    assert app.returncode == 0, (
        "`terraform apply` en prod échoue. Le dépassement de budget doit "
        "produire un simple avertissement : un bloc check, pas une "
        "precondition."
    )
    controles = {
        c["address"].get("to_display", ""): c for c in show_json(applied).get("checks", [])
    }
    budget = controles.get("check.budget_prod")
    assert budget is not None, "Le bloc check budget_prod est absent."
    assert budget["status"] == "fail", (
        f"check.budget_prod est en {budget['status']!r} alors qu'en prod la "
        "mémoire vaut 2048 MiB, au dessus du seuil de 1024. L'assertion ne "
        "porte pas sur la bonne valeur."
    )


def test_configuration_idempotente(applied: Path) -> None:
    terraform("apply", "-auto-approve", "-input=false", "-no-color", *PROD, cwd=applied)
    code = terraform(
        "plan", "-detailed-exitcode", "-input=false", "-no-color", *PROD, cwd=applied
    ).returncode
    assert code == 0, (
        f"`plan -detailed-exitcode` rend {code}, attendu 0. Un code 2 sans "
        "changement annoncé trahit une data source placée dans le bloc check, "
        "relue à chaque plan."
    )
