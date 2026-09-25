"""Tests fonctionnels du lab « variables, locals et la precedence reelle ».

Quatre marches, verifiees DANS L'ORDRE, du plus faible au plus fort :

    default  <  TF_VAR_  <  terraform.tfvars  <  *.auto.tfvars  <  -var

La marche decisive est la deuxieme : `terraform.tfvars` BAT la variable
d'environnement. C'est le rang que presque tout le monde place trop haut, et
s'en apercevoir en production coute une soiree.

Aucun provider distant, aucune VM : le lab tourne partout ou `terraform` est sur
le PATH. Aucun test n'ouvre les `.tf` de l'apprenant, et aucun ne parse un
message d'erreur humain. On ne lit que du JSON et des codes retour : un message
de validation est une chaine que son auteur choisit, en faire un critere
reviendrait a noter la redaction.
"""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "first-infra-variables-outputs"

REGION = "eu-west-1"
AUTO_TFVARS = "env.auto.tfvars"
ECARTE = "env.auto.tfvars.ecarte"

SORTIES_ATTENDUES = {
    "env_effectif",
    "region_effective",
    "stack_name",
    "sizing_total_mb",
    "manifest_path",
}


def _tf(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["terraform", *args],
        cwd=WORKDIR, capture_output=True, text=True, check=False,
        env={**os.environ, "TF_VAR_region": REGION, **(env or {})},
    )


@pytest.fixture(scope="module")
def applique() -> Iterator[None]:
    exiger_workdir(WORKDIR, LAB_ID)

    init = _tf("init", "-input=false", "-no-color")
    if init.returncode != 0:
        pytest.fail(f"`terraform init` a echoue.\n{init.stderr[-1200:]}")

    app = _tf("apply", "-auto-approve", "-input=false", "-no-color")
    if app.returncode != 0:
        pytest.fail(
            "`terraform apply` a echoue. Des `???` subsistent-ils ?\n"
            f"{(app.stderr or app.stdout)[-1800:]}"
        )
    try:
        yield
    finally:
        # Le fichier `auto` est deplace par un test : on le remet quoi qu'il
        # arrive, sinon le lab rejoue ne mesure plus la meme chose.
        ecarte = WORKDIR / ECARTE
        if ecarte.exists():
            ecarte.rename(WORKDIR / AUTO_TFVARS)
        _tf("destroy", "-auto-approve", "-input=false", "-no-color")


def _sorties() -> dict:
    proc = _tf("output", "-json")
    proc.check_returncode()
    return json.loads(proc.stdout or "{}")


def _valeur(nom: str):
    sorties = _sorties()
    assert nom in sorties, (
        f"L'output `{nom}` n'est pas declare. Presents : {sorted(sorties)}."
    )
    return sorties[nom]["value"]


# --------------------------------------------------------------------------
# 1. Les cinq sorties existent.
# --------------------------------------------------------------------------
def test_les_cinq_sorties_sont_declarees(applique: None) -> None:
    presentes = set(_sorties())
    manquantes = SORTIES_ATTENDUES - presentes
    assert not manquantes, (
        f"Ces sorties manquent : {sorted(manquantes)}.\nPresentes : "
        f"{sorted(presentes)}."
    )


# --------------------------------------------------------------------------
# 2. `TF_VAR_` couvre une variable SANS default.
# --------------------------------------------------------------------------
def test_une_variable_sans_default_se_fournit_par_l_environnement(
    applique: None,
) -> None:
    assert _valeur("region_effective") == REGION, (
        f"`region_effective` vaut {_valeur('region_effective')!r}, attendu "
        f"{REGION!r}.\n\n`region` n'a PAS de default : elle ne peut venir que "
        "de l'exterieur, et `TF_VAR_region` suffit."
    )


# --------------------------------------------------------------------------
# 3. La marche decisive : terraform.tfvars BAT TF_VAR_.
# --------------------------------------------------------------------------
def test_le_fichier_tfvars_bat_la_variable_d_environnement(applique: None) -> None:
    """Le rang que presque tout le monde place trop haut.

    On ecarte `env.auto.tfvars`, plus fort encore, pour que la comparaison
    porte sur les deux seules sources qui restent : `TF_VAR_env` et
    `terraform.tfvars`.
    """
    auto = WORKDIR / AUTO_TFVARS
    assert auto.is_file(), (
        f"`{AUTO_TFVARS}` est absent : le lab demande de le creer."
    )
    ecarte = WORKDIR / ECARTE
    auto.rename(ecarte)
    try:
        applique_bis = _tf(
            "apply", "-auto-approve", "-input=false", "-no-color",
            env={"TF_VAR_env": "dev"},
        )
        assert applique_bis.returncode == 0, (
            f"L'application a echoue.\n{(applique_bis.stderr or applique_bis.stdout)[-1200:]}"
        )
        obtenu = _valeur("env_effectif")
        assert obtenu == "staging", (
            f"`env_effectif` vaut {obtenu!r} alors que `TF_VAR_env=dev` etait "
            "pose et que `terraform.tfvars` dit `staging`.\n\nAttendu "
            "`staging` : un fichier de valeurs BAT la variable d'environnement. "
            "`TF_VAR_` se situe juste au-dessus du `default`, et en dessous de "
            "tout fichier. C'est le rang le plus souvent mal place."
        )
    finally:
        ecarte.rename(auto)


# --------------------------------------------------------------------------
# 4. Et `*.auto.tfvars` bat `terraform.tfvars`.
# --------------------------------------------------------------------------
def test_le_fichier_auto_bat_terraform_tfvars(applique: None) -> None:
    applique_bis = _tf(
        "apply", "-auto-approve", "-input=false", "-no-color",
        env={"TF_VAR_env": "dev"},
    )
    assert applique_bis.returncode == 0, (
        f"L'application a echoue.\n{(applique_bis.stderr or applique_bis.stdout)[-1200:]}"
    )
    obtenu = _valeur("env_effectif")
    assert obtenu == "prod", (
        f"`env_effectif` vaut {obtenu!r}, attendu `prod`.\n\n"
        f"`{AUTO_TFVARS}` est charge AUTOMATIQUEMENT, apres "
        "`terraform.tfvars`, et gagne donc contre lui. C'est la marche la plus "
        "discrete : son nom ne le dit pas, et aucune commande ne le mentionne."
    )


# --------------------------------------------------------------------------
# 5. La ligne de commande bat tout le reste.
# --------------------------------------------------------------------------
def test_la_ligne_de_commande_bat_toutes_les_autres_sources(applique: None) -> None:
    applique_bis = _tf(
        "apply", "-auto-approve", "-input=false", "-no-color", "-var", "env=dev",
        env={"TF_VAR_env": "staging"},
    )
    assert applique_bis.returncode == 0, (
        f"L'application a echoue.\n{(applique_bis.stderr or applique_bis.stdout)[-1200:]}"
    )
    assert _valeur("env_effectif") == "dev", (
        f"`env_effectif` vaut {_valeur('env_effectif')!r} alors que `-var "
        "env=dev` a ete fourni, contre un `TF_VAR_env`, un `terraform.tfvars` "
        f"et un `{AUTO_TFVARS}`. La ligne de commande gagne toujours."
    )

    # On remet la configuration dans l'etat que les fichiers decrivent, pour
    # que les tests suivants mesurent la configuration et non nos restes.
    remise = _tf("apply", "-auto-approve", "-input=false", "-no-color")
    assert remise.returncode == 0, f"La remise en etat a echoue.\n{remise.stderr[-1000:]}"


# --------------------------------------------------------------------------
# 6. Les validations refusent, et par le CODE RETOUR seulement.
# --------------------------------------------------------------------------
def test_les_validations_refusent_les_valeurs_hors_plage(applique: None) -> None:
    """On ne lit pas le message : c'est une chaine que son auteur choisit.

    En faire un critere reviendrait a noter la redaction plutot que la regle.
    Seul le code retour dit si Terraform a refuse.
    """
    for variable, valeur in (("env", "qa"), ("replicas", "0")):
        refus = _tf("plan", "-input=false", "-no-color", "-var", f"{variable}={valeur}")
        assert refus.returncode != 0, (
            f"`plan -var {variable}={valeur}` REUSSIT, alors que cette valeur "
            "est hors des bornes annoncees.\n\nLe bloc `validation` manque, ou "
            "sa condition est trop large."
        )

    # Contre-controle : une valeur admise doit passer. Sans lui, une condition
    # qui refuse TOUT ferait passer le test precedent pour la mauvaise raison.
    for variable, valeur in (("env", "staging"), ("replicas", "3")):
        accepte = _tf("plan", "-input=false", "-no-color", "-var", f"{variable}={valeur}")
        assert accepte.returncode == 0, (
            f"`plan -var {variable}={valeur}` echoue alors que cette valeur est "
            f"admise.\n\nLa condition est trop stricte.\n{accepte.stderr[-800:]}"
        )


# --------------------------------------------------------------------------
# 7. Le type complexe est REELLEMENT consomme.
# --------------------------------------------------------------------------
def test_le_sizing_est_consomme_et_pas_seulement_declare(applique: None) -> None:
    """Un `object` declare et jamais lu ne prouve rien.

    Il pourrait etre une `map`, ou n'avoir aucun type : rien ne le distinguerait.
    `sizing_total_mb` force a en LIRE un attribut et a le combiner avec une
    autre variable.
    """
    total = _valeur("sizing_total_mb")
    assert isinstance(total, (int, float)) and not isinstance(total, bool), (
        f"`sizing_total_mb` vaut {total!r}, de type {type(total).__name__}. Un "
        "nombre est attendu : la memoire multipliee par les replicas."
    )

    etat = json.loads(_tf("show", "-json").stdout)
    variables = etat.get("values", {}).get("root_module", {})
    manifeste = next(
        (r for r in variables.get("resources", [])
         if r["type"] == "local_file" and r["mode"] == "managed"),
        None,
    )
    assert manifeste, "Aucune ressource `local_file` dans le state."

    ecrit = json.loads(manifeste["values"]["content"])
    attendu = ecrit["sizing"]["memory_mb"] * ecrit["replicas"]
    assert total == attendu, (
        f"`sizing_total_mb` vaut {total}, alors que le manifeste porte "
        f"{ecrit['sizing']['memory_mb']} Mio par exemplaire et "
        f"{ecrit['replicas']} exemplaires, soit {attendu}."
    )


# --------------------------------------------------------------------------
# 8. Les deux cotes : le local est calcule, et il arrive jusqu'au disque.
# --------------------------------------------------------------------------
def test_le_stack_name_est_calcule_et_nomme_le_fichier(applique: None) -> None:
    """Le test qui relie tout le reste.

    Un `local` se calcule et ne se fournit pas : personne ne peut le
    surcharger, ni par fichier ni par `-var`. On verifie donc qu'il DERIVE bien
    des valeurs effectives, et qu'il arrive jusqu'au nom du fichier ecrit.

    La convergence seule aurait ete vraie de toute configuration appliquee ;
    accolee a cela, elle prouve que le manifeste correspond a ce que les
    sorties annoncent.
    """
    attendu = f"app-{_valeur('env_effectif')}-{_valeur('region_effective')}"
    assert _valeur("stack_name") == attendu, (
        f"`stack_name` vaut {_valeur('stack_name')!r}, attendu {attendu!r}.\n\n"
        "Il doit DERIVER des valeurs effectives : un local qu'on fournit de "
        "l'exterieur n'est plus un local."
    )

    chemin = Path(_valeur("manifest_path"))
    if not chemin.is_absolute():
        chemin = WORKDIR / chemin
    assert chemin.is_file(), f"Le manifeste annonce en {chemin} n'existe pas."
    assert attendu in chemin.name, (
        f"Le fichier s'appelle {chemin.name!r} et ne porte pas {attendu!r}."
    )

    stable = _tf("plan", "-detailed-exitcode", "-input=false", "-no-color")
    assert stable.returncode == 0, (
        f"`plan -detailed-exitcode` rend {stable.returncode}, attendu 0.\n"
        f"{stable.stdout[-1000:]}"
    )
