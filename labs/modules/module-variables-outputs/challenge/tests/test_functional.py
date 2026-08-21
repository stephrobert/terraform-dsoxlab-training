"""Tests fonctionnels du lab « l'interface d'un module est un contrat ».

Quatre mecanismes que le tandem `type` + `default` ne couvre pas, et que les
tests prouvent par execution, en fabriquant les variantes fautives dans des
COPIES temporaires du projet.

Faits verifies sur Terraform 1.15.4 (local + random, hors ligne) :
- `optional(number, 7)` comble un attribut d'objet absent : l'appel qui ne
  fournit que `nom` obtient `retention_jours = 7` et `chiffre = true` ;
- `nullable = false` fait qu'un `etiquette = null` explicite rend le DEFAUT ;
  sans cette ligne, la meme variable ressort a `null` dans `output -json` ;
- une `validation` dont la condition ne reference que sa propre variable est
  attrapee des `terraform validate` : `valid: false`, severite `error`, summary
  `Invalid value for variable` ;
- une `precondition` sur un output arrete le plan sur `Module output value
  precondition failed` ;
- une sortie racine qui republie une valeur derivee d'un `random_password` sans
  `sensitive = true` fait echouer le plan sur `Output refers to sensitive
  values`.
"""

import json
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "modules-module-variables-outputs"

RESUME_MINIMAL = {
    "nom": "livraison",
    "retention_jours": 7,
    "chiffre": True,
    "etiquette": "artefact",
}


def _copie(source: Path, cible: Path) -> Path:
    shutil.copytree(source, cible)
    return cible


def _outputs(cwd: Path) -> dict:
    sortie = terraform("output", "-json", cwd=cwd)
    sortie.check_returncode()
    return json.loads(sortie.stdout)


@pytest.fixture(scope="module")
def applique() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(
            "`terraform init` a echoue. Des `???` restent-ils dans les fichiers "
            f"a completer ?\n{init.stderr[-1200:]}"
        )
    if "values" not in show_json(WORKDIR):
        pytest.fail(
            "Le state est vide : la configuration n'a jamais ete appliquee. "
            "Lancez `terraform apply` une fois l'interface ecrite."
        )
    yield WORKDIR


# --------------------------------------------------------------------------
# 1. Le travail est bien dans un module, appele deux fois
# --------------------------------------------------------------------------

def test_le_module_est_appele_deux_fois(applique: Path) -> None:
    enfants = show_json(applique)["values"]["root_module"].get("child_modules", [])
    adresses = {e["address"] for e in enfants}
    assert adresses == {"module.complet", "module.minimal"}, (
        f"Le state porte {sorted(adresses)}, attendu `module.complet` et "
        "`module.minimal`. Une configuration a plat, sans module, echoue ici."
    )


# --------------------------------------------------------------------------
# 2. optional() comble ce que l'appel minimal ne fournit pas
# --------------------------------------------------------------------------

def test_les_attributs_facultatifs_sont_combles(applique: Path) -> None:
    outputs = _outputs(applique)
    assert "resume_minimal" in outputs, (
        f"L'output `resume_minimal` manque. Presents : {sorted(outputs)}"
    )
    resume = outputs["resume_minimal"]["value"]
    assert resume == RESUME_MINIMAL, (
        f"`resume_minimal` vaut {resume!r},\nattendu {RESUME_MINIMAL!r}. L'appel "
        "ne fournit que `nom` : seul `optional(type, defaut)` produit ce "
        "resultat. Sans lui le plan echouerait sur un objet incomplet, et avec "
        "un `optional()` sans second argument les deux champs sortiraient a "
        "`null`."
    )


# --------------------------------------------------------------------------
# 3. nullable = false : un null explicite rend le defaut
# --------------------------------------------------------------------------

def test_un_null_explicite_rend_le_defaut(applique: Path, tmp_path: Path) -> None:
    copie = _copie(applique, tmp_path / "null-explicite")
    main = copie / "main.tf"
    main.write_text(
        main.read_text(encoding="utf-8").replace(
            'depot = { nom = "livraison" }',
            'depot     = { nom = "livraison" }\n  etiquette = null',
        ),
        encoding="utf-8",
    )
    applique_copie = terraform("apply", "-auto-approve", "-input=false",
                              "-no-color", cwd=copie)
    if applique_copie.returncode != 0:
        pytest.fail(
            "L'apply a echoue alors que l'appelant passe `etiquette = null`.\n"
            f"{applique_copie.stderr[-900:]}"
        )
    resume = _outputs(copie)["resume_minimal"]["value"]
    assert resume["etiquette"] == "artefact", (
        f"Avec `etiquette = null`, le resume porte {resume['etiquette']!r}, "
        "attendu `artefact`. Un `default` ne protege pas d'un null explicite : "
        "`nullable` vaut `true` par defaut et laisse passer la valeur nulle. "
        "C'est `nullable = false` qui substitue le defaut."
    )


# --------------------------------------------------------------------------
# 4. La validation rejette une valeur hors bornes
# --------------------------------------------------------------------------

def test_une_longueur_hors_bornes_est_refusee(applique: Path, tmp_path: Path) -> None:
    copie = _copie(applique, tmp_path / "hors-bornes")
    main = copie / "main.tf"
    main.write_text(
        main.read_text(encoding="utf-8").replace(
            "longueur_secret = 24", "longueur_secret = 8"
        ),
        encoding="utf-8",
    )
    valide = terraform("validate", "-json", cwd=copie)
    document = json.loads(valide.stdout)
    assert document.get("valid") is False, (
        "`terraform validate` accepte `longueur_secret = 8`. La variable doit "
        "porter un bloc `validation` qui refuse les valeurs hors de 12 a 64."
    )
    resumes = {
        d.get("summary") for d in document.get("diagnostics", [])
        if d.get("severity") == "error"
    }
    assert "Invalid value for variable" in resumes, (
        f"Diagnostics releves : {sorted(resumes)}. Attendu une erreur "
        "`Invalid value for variable`."
    )


# --------------------------------------------------------------------------
# 5. Le secret traverse la frontiere sans etre expose
# --------------------------------------------------------------------------

def test_le_secret_est_marque_sensible(applique: Path) -> None:
    outputs = _outputs(applique)
    assert "secret_partage" in outputs, (
        f"L'output `secret_partage` manque. Presents : {sorted(outputs)}"
    )
    assert outputs["secret_partage"]["sensitive"] is True, (
        "`secret_partage` n'est pas marque sensible. Terraform exige qu'une "
        "sortie racine portant une donnee sensible le declare : sans cela, le "
        "plan echoue sur `Output refers to sensitive values`."
    )
    assert len(outputs["secret_partage"]["value"]) == 24, (
        "Le secret ne fait pas la longueur demandee par l'appel complet "
        f"({len(outputs['secret_partage']['value'])} au lieu de 24)."
    )


def test_sans_marquage_le_plan_est_refuse(applique: Path, tmp_path: Path) -> None:
    """Contre-test : la sensibilite remonte du module, elle ne s'oublie pas."""
    copie = _copie(applique, tmp_path / "sans-marquage")
    outputs_tf = copie / "outputs.tf"
    contenu = outputs_tf.read_text(encoding="utf-8")
    outputs_tf.write_text(
        contenu.replace("sensitive = true", "").replace("sensitive   = true", ""),
        encoding="utf-8",
    )
    plan = terraform("plan", "-input=false", "-no-color", cwd=copie)
    assert plan.returncode != 0, (
        "Un output racine republiant un secret sans `sensitive = true` devrait "
        "faire echouer le plan. Si ce test passe, le secret n'est pas marque "
        "dans le module enfant non plus, et rien ne protege la valeur."
    )
    assert "sensitive" in plan.stderr.lower(), (
        f"Le refus attendu mentionne les valeurs sensibles. Releve :\n"
        f"{plan.stderr[-600:]}"
    )


# --------------------------------------------------------------------------
# 6. Une sortie qui refuse de se publier
# --------------------------------------------------------------------------

def test_la_sortie_chemin_refuse_un_depot_non_chiffre(
    applique: Path, tmp_path: Path
) -> None:
    copie = _copie(applique, tmp_path / "non-chiffre")
    main = copie / "main.tf"
    main.write_text(
        main.read_text(encoding="utf-8").replace(
            "chiffre         = true", "chiffre         = false"
        ),
        encoding="utf-8",
    )
    (copie / "chemin.tf").write_text(
        'output "chemin_complet" {\n  value = module.complet.chemin\n}\n',
        encoding="utf-8",
    )
    plan = terraform("plan", "-input=false", "-no-color", cwd=copie)
    assert plan.returncode != 0, (
        "Le plan devrait echouer quand le depot n'est pas chiffre : la sortie "
        "`chemin` doit porter une `precondition` qui l'en empeche."
    )
    assert "precondition" in plan.stderr.lower(), (
        "Le refus attendu vient d'une precondition d'output. Releve :\n"
        f"{plan.stderr[-700:]}"
    )


# --------------------------------------------------------------------------
# 7. Le projet converge
# --------------------------------------------------------------------------

def test_plus_aucun_changement_en_attente(applique: Path) -> None:
    plan = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color",
                     cwd=applique)
    assert plan.returncode == 0, (
        f"plan -detailed-exitcode rend {plan.returncode}, attendu 0.\n"
        f"{plan.stdout[-900:]}"
    )
