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

from conftest import exiger_workdir, message, show_json, terraform, workdir_lab

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
        pytest.fail(message(
            en=f"`terraform init` failed.\n{init.stderr[-1200:]}",
            fr=f"`terraform init` a échoué.\n{init.stderr[-1200:]}",
        ))
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", *PROD, cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(
            message(
            en="`terraform apply` in prod failed: the configuration still has "
            "incomplete expressions, or a blocking mechanism was "
            "placed where it should not be.\n"
            f"{app.stderr[-1200:]}",
            fr="`terraform apply` en prod a échoué : la configuration comporte "
            "encore des expressions incomplètes, ou un mécanisme bloquant a été "
            "placé là où il ne fallait pas.\n"
            f"{app.stderr[-1200:]}",
        )
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
    assert adresse in controles, message(
        en=f"No check recorded for {adresse}: the {mecanisme} was not "
        f"written. Addresses found: {sorted(controles)}.",
        fr=f"Aucun contrôle enregistré pour {adresse} : le {mecanisme} n'a pas été "
        f"écrit. Adresses trouvées : {sorted(controles)}.",
    )
    kind = controles[adresse]["address"]["kind"]
    assert kind == kind_attendu, message(
        en=f"{adresse} comes out with kind={kind!r}, expected {kind_attendu!r}: "
        "the check is not at the requested level.",
        fr=f"{adresse} sort en kind={kind!r}, attendu {kind_attendu!r} : "
        "le contrôle n'est pas au niveau demandé.",
    )


# --------------------------------------------------------------------------
# Validations d'entree
# --------------------------------------------------------------------------

def test_environnement_hors_enumere_refuse(applied: Path) -> None:
    """Un enuméré refusé, et surtout une valeur valide acceptée.

    Le second contrôle n'est pas décoratif : sans lui, ce test passerait au
    vert sur une configuration entièrement cassée, où tout `plan` échoue.
    """
    assert plan("-var", "environment=dev") == 0, message(
        en="`environment=dev` is refused although it is valid: the configuration "
        "does not plan, or the validation is too strict.",
        fr="`environment=dev` est refusé alors qu'il est valide : la configuration "
        "ne planifie pas, ou la validation est trop stricte.",
    )
    assert plan("-var", "environment=qa") != 0, message(
        en="`environment=qa` is accepted: the enumeration's validation is missing.",
        fr="`environment=qa` est accepté : la validation de l'énuméré est absente.",
    )


def test_backup_bucket_obligatoire_en_prod_seulement(applied: Path) -> None:
    assert plan("-var", "environment=prod", "-var", "backup_bucket=") != 0, message(
        en="an empty backup_bucket is accepted in prod: the cross validation is missing.",
        fr="backup_bucket vide est accepté en prod : la validation croisée manque.",
    )
    assert plan("-var", "environment=dev", "-var", "backup_bucket=") == 0, message(
        en="an empty backup_bucket is refused in dev, although it should only be refused in "
        "prod. The condition is not conditioned on the environment.",
        fr="backup_bucket vide est refusé en dev, alors qu'il ne doit l'être qu'en "
        "prod. La condition n'est pas conditionnée à l'environnement.",
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
    assert app.returncode == 0, message(
        en=f"apply in {env} failed.\n{app.stderr[-800:]}",
        fr=f"apply en {env} a échoué.\n{app.stderr[-800:]}",
    )
    sortie = terraform("output", "-json", cwd=applied)
    sortie.check_returncode()
    outs = json.loads(sortie.stdout)
    assert outs["memory_mib"]["value"] == memoire, message(
        en=f"In {env}, memory_mib is {outs['memory_mib']['value']}, expected {memoire}.",
        fr=f"En {env}, memory_mib vaut {outs['memory_mib']['value']}, attendu {memoire}.",
    )
    assert outs["vcpu"]["value"] == vcpu, message(
        en=f"In {env}, vcpu is {outs['vcpu']['value']}, expected {vcpu}.",
        fr=f"En {env}, vcpu vaut {outs['vcpu']['value']}, attendu {vcpu}.",
    )


def test_override_memoire_prioritaire(applied: Path) -> None:
    terraform("apply", "-auto-approve", "-input=false", "-no-color",
              "-var", "memory_mib_override=768", cwd=applied).check_returncode()
    outs = json.loads(terraform("output", "-json", cwd=applied).stdout)
    assert outs["memory_mib"]["value"] == 768, message(
        en="memory_mib_override does not take precedence over the default value.",
        fr="memory_mib_override n'a pas la priorité sur la valeur par défaut.",
    )


def test_output_disparait_quand_null(applied: Path) -> None:
    """Un local valant null retire son output du document, il ne vaut pas null."""
    terraform("apply", "-auto-approve", "-input=false", "-no-color",
              "-var", "enable_second_disk=false", cwd=applied).check_returncode()
    outs = json.loads(terraform("output", "-json", cwd=applied).stdout)
    assert "second_disk_name" not in outs, message(
        en="The second_disk_name key is present although the disk is disabled. "
        "The local must be null, which removes the output from the document.",
        fr="La clé second_disk_name est présente alors que le disque est désactivé. "
        "Le local doit valoir null, ce qui retire l'output du document.",
    )

    terraform("apply", "-auto-approve", "-input=false", "-no-color",
              "-var", "enable_second_disk=true", cwd=applied).check_returncode()
    outs = json.loads(terraform("output", "-json", cwd=applied).stdout)
    assert outs.get("second_disk_name", {}).get("value"), message(
        en="The second_disk_name key is missing although the disk is enabled.",
        fr="La clé second_disk_name est absente alors que le disque est activé.",
    )


# --------------------------------------------------------------------------
# Ce qu'une validation ne peut PAS faire
# --------------------------------------------------------------------------

def test_precondition_sur_valeur_calculee(applied: Path) -> None:
    """Le rapport porte sur deux locals : seule une precondition peut le voir."""
    assert plan("-var", "memory_mib_override=64") != 0, message(
        en="memory_mib_override=64 is accepted. With 1 vCPU, that makes 64 MiB per "
        "vCPU, below the threshold of 256. No validation block can carry that "
        "check: it must live in a precondition.",
        fr="memory_mib_override=64 est accepté. Avec 1 vCPU, cela fait 64 MiB par "
        "vCPU, sous le seuil de 256. Aucun bloc validation ne peut porter ce "
        "contrôle : il doit vivre dans une precondition.",
    )
    assert plan("-var", "memory_mib_override=512") == 0, message(
        en="memory_mib_override=512 is refused although it respects the threshold: "
        "the precondition is too strict.",
        fr="memory_mib_override=512 est refusé alors qu'il respecte le seuil : "
        "la precondition est trop stricte.",
    )


def test_postcondition_sur_contenu_ecrit(applied: Path) -> None:
    """Le manifest réellement écrit doit se décoder et porter la clé env."""
    etat = show_json(applied)
    ressources = etat["values"]["root_module"]["resources"]
    manifest = next(
        (r for r in ressources if r.get("mode") == "managed" and r.get("type") == "local_file"),
        None,
    )
    assert manifest is not None, message(
        en="No managed local_file resource in the state.",
        fr="Aucune ressource local_file gérée dans le state.",
    )
    contenu = json.loads(manifest["values"]["content"])
    for cle in ("env", "memory_mib", "vcpu"):
        assert cle in contenu, message(
            en=f"The manifest written does not carry the key {cle!r}. Contents: {contenu}.",
            fr=f"Le manifest écrit ne porte pas la clé {cle!r}. Contenu : {contenu}.",
        )


# --------------------------------------------------------------------------
# La marche decisive : bloquant contre non bloquant
# --------------------------------------------------------------------------

def test_check_echoue_sans_bloquer_apply(applied: Path) -> None:
    """En prod, le budget est dépassé : le check doit échouer, l'apply réussir."""
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", *PROD, cwd=applied)
    assert app.returncode == 0, message(
        en="`terraform apply` in prod fails. Going over budget must "
        "produce a mere warning: a check block, not a "
        "precondition.",
        fr="`terraform apply` en prod échoue. Le dépassement de budget doit "
        "produire un simple avertissement : un bloc check, pas une "
        "precondition.",
    )
    controles = {
        c["address"].get("to_display", ""): c for c in show_json(applied).get("checks", [])
    }
    budget = controles.get("check.budget_prod")
    assert budget is not None, message(
        en="The budget_prod check block is missing.",
        fr="Le bloc check budget_prod est absent.",
    )
    assert budget["status"] == "fail", message(
        en=f"check.budget_prod is {budget['status']!r} although in prod the "
        "memory is 2048 MiB, above the threshold of 1024. The assertion does "
        "not cover the right value.",
        fr=f"check.budget_prod est en {budget['status']!r} alors qu'en prod la "
        "mémoire vaut 2048 MiB, au dessus du seuil de 1024. L'assertion ne "
        "porte pas sur la bonne valeur.",
    )


def test_configuration_idempotente(applied: Path) -> None:
    terraform("apply", "-auto-approve", "-input=false", "-no-color", *PROD, cwd=applied)
    code = terraform(
        "plan", "-detailed-exitcode", "-input=false", "-no-color", *PROD, cwd=applied
    ).returncode
    assert code == 0, message(
        en=f"`plan -detailed-exitcode` returns {code}, expected 0. A code 2 with no "
        "announced change betrays a data source placed inside the check block, "
        "re-read at every plan.",
        fr=f"`plan -detailed-exitcode` rend {code}, attendu 0. Un code 2 sans "
        "changement annoncé trahit une data source placée dans le bloc check, "
        "relue à chaque plan.",
    )
