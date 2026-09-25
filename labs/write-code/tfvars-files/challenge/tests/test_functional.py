"""Tests fonctionnels du lab « la faute de frappe qui ne casse rien ».

Principe : on ne lit jamais le CONTENU des `.tf` de l'apprenant, seulement
`terraform output -json`, le manifeste écrit sur le disque, et des codes retour.

Faits vérifiés sur Terraform v1.15.4 :

- une variable non déclarée dans un `.tfvars` ne fait qu'un AVERTISSEMENT : le
  plan réussit, mais la vraie variable reste à son défaut. C'est le piège du
  lab, et c'est ce qui le rend invisible ;
- `terraform.tfvars.json` l'emporte sur `terraform.tfvars`, niveau de précédence
  distinct.

Réécrit le 2026-09-23. Les deux tests précédents `test_region_depuis_tfvars` et
`test_configuration_stable_apres_apply` étaient VERTS AVANT LE TRAVAIL, et
accordaient 50/100 à un candidat qui n'ouvrait pas l'éditeur :

- la région venait du `terraform.tfvars` que le SETUP avait posé ;
- la configuration convergeait déjà, faute de frappe comprise, puisque c'est
  précisément ce qui rend cette faute indétectable.

Les deux moitiés n'ont pas été supprimées : elles sont fusionnées là où elles ne
peuvent être atteintes qu'après le travail, et où elles prennent tout leur sens.
"""

import json
import shutil
from pathlib import Path

import pytest

from conftest import exiger_workdir, output_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "write-code-tfvars-files"

BUCKET_ATTENDU = "prod"
BUCKET_PAR_DEFAUT = "app-defaut"
REGION_ATTENDUE = "eu-west-3"
REPLICAS_ATTENDUS = 5


@pytest.fixture(scope="module")
def applied() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(f"`terraform init` a echoue.\n{init.stderr[-1200:]}")
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(f"`terraform apply` a echoue.\n{app.stderr[-1500:]}")
    return WORKDIR


# --------------------------------------------------------------------------
# 1. La faute de frappe est corrigee : bucket vaut "prod", pas le defaut.
# --------------------------------------------------------------------------
def test_bucket_prend_la_valeur(applied: Path) -> None:
    v = output_json(applied)["bucket"]["value"]
    assert v == BUCKET_ATTENDU, (
        f"`bucket` = {v!r}, attendu {BUCKET_ATTENDU!r}. Le terraform.tfvars "
        'fourni ecrit `bukcet = "prod"` (faute de frappe) : une variable non '
        "declaree dans un .tfvars ne fait qu'un warning, bucket reste alors a "
        f"son defaut {BUCKET_PAR_DEFAUT!r}. Corrigez le nom en `bucket`."
    )


# --------------------------------------------------------------------------
# 2. tfvars.json l'emporte sur tfvars : replicas = 5, pas 2.
# --------------------------------------------------------------------------
def test_replicas_depuis_json(applied: Path) -> None:
    v = output_json(applied)["replicas"]["value"]
    assert v == REPLICAS_ATTENDUS, (
        f"`replicas` = {v!r}, attendu {REPLICAS_ATTENDUS}. terraform.tfvars "
        "pose replicas = 2 ; creez un terraform.tfvars.json posant replicas = 5 : "
        "la variante JSON l'emporte sur terraform.tfvars."
    )
    assert isinstance(v, (int, float)) and not isinstance(v, bool), (
        "`replicas` doit rester un nombre."
    )


# --------------------------------------------------------------------------
# 3. Pourquoi cette faute est INVISIBLE, prouve par contraste.
# --------------------------------------------------------------------------
def test_la_faute_de_frappe_ne_leve_aucune_erreur_et_laisse_le_reste_marcher(
    applied: Path, tmp_path: Path
) -> None:
    """La moitie « la region vient du fichier » vit ici, et pas ailleurs.

    Seule, elle etait vraie avant le travail : le setup avait pose le fichier.
    Ici elle sert a etablir ce qui fait tout le danger de cette faute : le
    fichier EST lu, la region arrive bien, et pourtant la ligne fautive est
    passee sous silence. Un fichier a moitie applique ne ressemble pas a un
    fichier ignore.
    """
    corrige = output_json(applied)
    assert corrige["region"]["value"] == REGION_ATTENDUE, (
        f"`region` = {corrige['region']['value']!r}, attendu "
        f"{REGION_ATTENDUE!r} : elle vient du meme terraform.tfvars."
    )
    assert corrige["bucket"]["value"] == BUCKET_ATTENDU, (
        "Ce test compare l'etat corrige a l'etat fautif : corrigez d'abord le "
        "nom de la variable."
    )

    # On refait la faute sur une COPIE : le travail de l'apprenant n'est jamais
    # modifie par un test.
    copie = tmp_path / "refaute"
    shutil.copytree(applied, copie)
    tfvars = copie / "terraform.tfvars"
    tfvars.write_text(
        tfvars.read_text(encoding="utf-8").replace("bucket =", "bukcet ="),
        encoding="utf-8",
    )

    rejoue = terraform(
        "apply", "-auto-approve", "-input=false", "-no-color", cwd=copie
    )
    assert rejoue.returncode == 0, (
        "Avec la faute de frappe, `terraform apply` devrait REUSSIR. C'est tout "
        "le sujet du lab : une variable non declaree dans un .tfvars ne leve "
        f"qu'un avertissement.\n{rejoue.stderr[-1200:]}"
    )

    fautif = json.loads(terraform("output", "-json", cwd=copie).stdout)
    assert fautif["bucket"]["value"] == BUCKET_PAR_DEFAUT, (
        f"Avec la faute, `bucket` vaut {fautif['bucket']['value']!r} et non "
        f"{BUCKET_PAR_DEFAUT!r}. La ligne fautive semble donc avoir ete prise "
        "en compte, ce qui contredit le mecanisme enseigne."
    )
    assert fautif["region"]["value"] == REGION_ATTENDUE, (
        "Avec la faute, la region ne vient plus du fichier. Le fichier entier "
        "aurait donc ete rejete, alors que Terraform n'ignore QUE la ligne "
        "fautive : c'est ce qui rend l'erreur si difficile a voir."
    )


# --------------------------------------------------------------------------
# 4. Les deux cotes : les trois valeurs sur le disque, et la convergence.
# --------------------------------------------------------------------------
def test_le_manifeste_porte_les_trois_valeurs_et_la_configuration_converge(
    applied: Path,
) -> None:
    """La convergence seule etait vraie avant le travail.

    Elle l'etait meme NECESSAIREMENT : une configuration qui applique un defaut
    converge parfaitement. Ce qu'elle vaut, elle ne le vaut qu'associee aux
    valeurs attendues : ensemble, elles distinguent une correction reussie d'une
    configuration qui tourne sur ses defauts.
    """
    manifeste = applied / "out" / "manifest.json"
    assert manifeste.is_file(), (
        f"Le manifeste est absent de {manifeste}. `main.tf` devait l'ecrire."
    )
    ecrit = json.loads(manifeste.read_text(encoding="utf-8"))
    attendu = {
        "region": REGION_ATTENDUE,
        "bucket": BUCKET_ATTENDU,
        "replicas": REPLICAS_ATTENDUS,
    }
    assert ecrit == attendu, (
        f"Le manifeste porte {ecrit}, attendu {attendu}.\n\nLes valeurs doivent "
        "arriver jusqu'au disque, pas seulement jusqu'aux outputs."
    )

    p = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=applied)
    assert p.returncode == 0, (
        f"`plan -detailed-exitcode` rend {p.returncode} (2 = des changements "
        "restent planifies). Un apply doit converger."
    )
