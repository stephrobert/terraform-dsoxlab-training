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

from conftest import exiger_workdir, message, show_json, terraform, workdir_lab

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
            message(
            en="`terraform init` failed. Are there leftover `???` in the files "
            f"to complete?\n{init.stderr[-1200:]}",
            fr="`terraform init` a échoué. Des `???` restent-ils dans les fichiers "
            f"à compléter ?\n{init.stderr[-1200:]}",
        )
        )
    if "values" not in show_json(WORKDIR):
        pytest.fail(
            message(
            en="The state is empty: the configuration was never applied. "
            "Run `terraform apply` once the interface is written.",
            fr="Le state est vide : la configuration n'a jamais été appliquée. "
            "Lancez `terraform apply` une fois l'interface écrite.",
        )
        )
    yield WORKDIR


# --------------------------------------------------------------------------
# 1. Le travail est bien dans un module, appele deux fois
# --------------------------------------------------------------------------

def test_le_module_est_appele_deux_fois(applique: Path) -> None:
    enfants = show_json(applique)["values"]["root_module"].get("child_modules", [])
    adresses = {e["address"] for e in enfants}
    assert adresses == {"module.complet", "module.minimal"}, message(
        en=f"The state carries {sorted(adresses)}, expected `module.complet` and "
        "`module.minimal`. A flat configuration, with no module, fails here.",
        fr=f"Le state porte {sorted(adresses)}, attendu `module.complet` et "
        "`module.minimal`. Une configuration à plat, sans module, échoue ici.",
    )


# --------------------------------------------------------------------------
# 2. optional() comble ce que l'appel minimal ne fournit pas
# --------------------------------------------------------------------------

def test_les_attributs_facultatifs_sont_combles(applique: Path) -> None:
    outputs = _outputs(applique)
    assert "resume_minimal" in outputs, message(
        en=f"The `resume_minimal` output is missing. Present: {sorted(outputs)}",
        fr=f"L'output `resume_minimal` manque. Présents : {sorted(outputs)}",
    )
    resume = outputs["resume_minimal"]["value"]
    assert resume == RESUME_MINIMAL, message(
        en=f"`resume_minimal` is {resume!r},\nexpected {RESUME_MINIMAL!r}. The call "
        "only provides `nom`: only `optional(type, default)` produces that "
        "result. Without it the plan would fail on an incomplete object, and with "
        "an `optional()` without a second argument both fields would come out as "
        "`null`.",
        fr=f"`resume_minimal` vaut {resume!r},\nattendu {RESUME_MINIMAL!r}. L'appel "
        "ne fournit que `nom` : seul `optional(type, defaut)` produit ce "
        "résultat. Sans lui le plan échouerait sur un objet incomplet, et avec "
        "un `optional()` sans second argument les deux champs sortiraient à "
        "`null`.",
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
            message(
            en="The apply failed although the caller passes `etiquette = null`.\n"
            f"{applique_copie.stderr[-900:]}",
            fr="L'apply a échoué alors que l'appelant passe `etiquette = null`.\n"
            f"{applique_copie.stderr[-900:]}",
        )
        )
    resume = _outputs(copie)["resume_minimal"]["value"]
    assert resume["etiquette"] == "artefact", message(
        en=f"With `etiquette = null`, the summary carries {resume['etiquette']!r}, "
        "expected `artefact`. A `default` does not protect from an explicit null: "
        "`nullable` defaults to `true` and lets the null value through. "
        "It is `nullable = false` that substitutes the default.",
        fr=f"Avec `etiquette = null`, le résumé porte {resume['etiquette']!r}, "
        "attendu `artefact`. Un `default` ne protège pas d'un null explicite : "
        "`nullable` vaut `true` par défaut et laisse passer la valeur nulle. "
        "C'est `nullable = false` qui substitue le défaut.",
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
    assert document.get("valid") is False, message(
        en="`terraform validate` accepts `longueur_secret = 8`. The variable must "
        "carry a `validation` block refusing values outside 12 to 64.",
        fr="`terraform validate` accepte `longueur_secret = 8`. La variable doit "
        "porter un bloc `validation` qui refuse les valeurs hors de 12 à 64.",
    )
    resumes = {
        d.get("summary") for d in document.get("diagnostics", [])
        if d.get("severity") == "error"
    }
    assert "Invalid value for variable" in resumes, message(
        en=f"Diagnostics recorded: {sorted(resumes)}. An `Invalid value for variable` "
        "error was expected.",
        fr=f"Diagnostics relevés : {sorted(resumes)}. Attendu une erreur "
        "`Invalid value for variable`.",
    )


# --------------------------------------------------------------------------
# 5. Le secret traverse la frontiere sans etre expose
# --------------------------------------------------------------------------

def test_le_secret_est_marque_sensible(applique: Path) -> None:
    outputs = _outputs(applique)
    assert "secret_partage" in outputs, message(
        en=f"The `secret_partage` output is missing. Present: {sorted(outputs)}",
        fr=f"L'output `secret_partage` manque. Présents : {sorted(outputs)}",
    )
    assert outputs["secret_partage"]["sensitive"] is True, message(
        en="`secret_partage` is not marked sensitive. Terraform requires a "
        "root output carrying sensitive data to declare it: without that, the "
        "plan fails on `Output refers to sensitive values`.",
        fr="`secret_partage` n'est pas marqué sensible. Terraform exige qu'une "
        "sortie racine portant une donnée sensible le déclare : sans cela, le "
        "plan échoue sur `Output refers to sensitive values`.",
    )
    assert len(outputs["secret_partage"]["value"]) == 24, message(
        en="The secret is not the length asked for by the complete call "
        f"({len(outputs['secret_partage']['value'])} instead of 24).",
        fr="Le secret ne fait pas la longueur demandée par l'appel complet "
        f"({len(outputs['secret_partage']['value'])} au lieu de 24).",
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
    assert plan.returncode != 0, message(
        en="A root output republishing a secret without `sensitive = true` should "
        "make the plan fail. If this test passes, the secret is not marked "
        "in the child module either, and nothing protects the value.",
        fr="Un output racine republiant un secret sans `sensitive = true` devrait "
        "faire échouer le plan. Si ce test passe, le secret n'est pas marqué "
        "dans le module enfant non plus, et rien ne protège la valeur.",
    )
    assert "sensitive" in plan.stderr.lower(), message(
        en=f"The expected refusal mentions sensitive values. Recorded:\n"
        f"{plan.stderr[-600:]}",
        fr=f"Le refus attendu mentionne les valeurs sensibles. Relevé :\n"
        f"{plan.stderr[-600:]}",
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
    assert plan.returncode != 0, message(
        en="The plan should fail when the store is not encrypted: the `chemin` "
        "output must carry a `precondition` preventing it.",
        fr="Le plan devrait échouer quand le dépôt n'est pas chiffré : la sortie "
        "`chemin` doit porter une `precondition` qui l'en empêche.",
    )
    assert "precondition" in plan.stderr.lower(), message(
        en="The expected refusal comes from an output precondition. Recorded:\n"
        f"{plan.stderr[-700:]}",
        fr="Le refus attendu vient d'une precondition d'output. Relevé :\n"
        f"{plan.stderr[-700:]}",
    )


# --------------------------------------------------------------------------
# 7. Le projet converge
# --------------------------------------------------------------------------

def test_plus_aucun_changement_en_attente(applique: Path) -> None:
    plan = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color",
                     cwd=applique)
    assert plan.returncode == 0, message(
        en=f"plan -detailed-exitcode returns {plan.returncode}, expected 0.\n"
        f"{plan.stdout[-900:]}",
        fr=f"plan -detailed-exitcode rend {plan.returncode}, attendu 0.\n"
        f"{plan.stdout[-900:]}",
    )
