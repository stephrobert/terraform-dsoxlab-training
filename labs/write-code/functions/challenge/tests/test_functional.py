"""Tests fonctionnels du lab « fonctions HCL ».

Principe : on prouve l'ÉTAT produit, jamais le contenu des fichiers `.tf` de
l'apprenant. Tout passe par les sorties structurées de Terraform
(`output -json`, `show -json`, `plan -detailed-exitcode`).

Contrôle négatif : sur le workdir livré, les `???` rendent la configuration
invalide, `terraform apply` échoue, et la fixture `applied` fait échouer
l'ensemble des tests.
"""

import json
from pathlib import Path

import pytest

from conftest import (
    exiger_workdir,
    message,
    output_json,
    show_json,
    terraform,
    workdir_lab,
)

WORKDIR = workdir_lab(__file__)


@pytest.fixture(scope="module")
def applied() -> Path:
    """Initialise et applique la configuration de l'apprenant, une seule fois."""
    exiger_workdir(WORKDIR, "write-code-functions")

    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(
            message(
            en="`terraform init` failed. If the error mentions \"Unknown provider\", "
            "the declaration of the built-in provider is missing from versions.tf.\n"
            f"{init.stderr[-1500:]}",
            fr="`terraform init` a échoué. Si l'erreur mentionne « Unknown provider », "
            "il manque la déclaration du provider intégré dans versions.tf.\n"
            f"{init.stderr[-1500:]}",
        )
        )

    apply = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if apply.returncode != 0:
        pytest.fail(
            message(
            en="`terraform apply` failed: the configuration still has "
            "incomplete expressions.\n"
            f"{apply.stderr[-1500:]}",
            fr="`terraform apply` a échoué : la configuration comporte encore des "
            "expressions incomplètes.\n"
            f"{apply.stderr[-1500:]}",
        )
        )
    return WORKDIR


@pytest.fixture(scope="module")
def outputs(applied: Path) -> dict:
    return {k: v["value"] for k, v in output_json(applied).items()}


@pytest.fixture(scope="module")
def instances(applied: Path) -> list[dict]:
    """Les instances gérées de type `local_file` présentes dans le state."""
    state = show_json(applied)
    resources = state.get("values", {}).get("root_module", {}).get("resources", [])
    return [
        r for r in resources
        if r.get("mode") == "managed" and r.get("type") == "local_file"
    ]


# --------------------------------------------------------------------------
# Déduplication et adressage par clé
# --------------------------------------------------------------------------

def test_environnements_dedupliques(outputs: dict) -> None:
    """Le CSV contient un doublon : la collection doit être dédupliquée."""
    assert sorted(outputs["env_uniques"]) == ["dev", "prod", "staging"], message(
        en="env_uniques must be exactly dev, prod and staging. "
        "The CSV contains \"prod\" twice: a plain list will not do.",
        fr="env_uniques doit valoir exactement dev, prod et staging. "
        "Le CSV contient « prod » deux fois : une simple liste ne convient pas.",
    )


def test_trois_fichiers_adresses_par_cle(instances: list[dict]) -> None:
    """`for_each` sur un set produit des clés, `count` produirait des entiers."""
    assert len(instances) == 3, message(
        en=f"3 local_file expected, found {len(instances)}.",
        fr=f"Attendu 3 local_file, trouvé {len(instances)}.",
    )
    index = sorted(str(r.get("index")) for r in instances)
    assert index == ["dev", "prod", "staging"], message(
        en=f"The instances are addressed by {index}. Keys "
        "dev, prod and staging were expected. A numeric index betrays a count or a "
        "for_each over a list that was not deduplicated.",
        fr=f"Les instances sont adressées par {index}. Attendu des clés "
        "dev, prod et staging. Un index numérique trahit un count ou un "
        "for_each sur une liste non dédupliquée.",
    )


# --------------------------------------------------------------------------
# Les pièges de fonctions
# --------------------------------------------------------------------------

def test_acces_par_position_reboucle_en_modulo(outputs: dict) -> None:
    """element() hors bornes calcule un modulo, pas un repli sur le premier."""
    assert outputs["env_recycle"] == "staging", message(
        en=f"env_recycle is {outputs['env_recycle']!r}, expected 'staging'. "
        "On the sorted list [dev, prod, staging], index 5 gives 5 % 3 = 2.",
        fr=f"env_recycle vaut {outputs['env_recycle']!r}, attendu 'staging'. "
        "Sur la liste triée [dev, prod, staging], l'index 5 donne 5 % 3 = 2.",
    )


def test_lecture_de_map_avec_repli(outputs: dict) -> None:
    """« qa » est absent de la table : la lecture doit retomber sur le défaut."""
    assert outputs["taille"] == "small", message(
        en=f"taille is {outputs['taille']!r}, expected 'small'. "
        "The \"qa\" key is absent from the table: with no fallback value, "
        "the lookup raises an error instead of returning null.",
        fr=f"taille vaut {outputs['taille']!r}, attendu 'small'. "
        "La clé « qa » est absente de la table : sans valeur de repli, "
        "la lecture lève une erreur au lieu de rendre null.",
    )


def test_fusion_de_maps_dans_le_bon_ordre(outputs: dict) -> None:
    """La map passée en dernier l'emporte sur les clés en collision."""
    tags = outputs["tags_effectifs"]
    assert set(tags) == {"projet", "equipe", "env"}, message(
        en=f"tags_effectifs carries the keys {sorted(tags)}, "
        "expected projet, equipe and env.",
        fr=f"tags_effectifs porte les clés {sorted(tags)}, "
        "attendu projet, equipe et env.",
    )
    assert tags["env"] == "qa", message(
        en=f"tags_effectifs['env'] is {tags['env']!r}, expected 'qa'. "
        "The added map must be passed as the last argument.",
        fr=f"tags_effectifs['env'] vaut {tags['env']!r}, attendu 'qa'. "
        "La map ajoutée doit être passée en dernier argument.",
    )


def test_arrondi_vers_le_haut(outputs: dict) -> None:
    """1536 Mio font 1,5 Gio : l'arrondi ne doit pas tronquer vers le bas."""
    assert outputs["memory_gib"] == 2, message(
        en=f"memory_gib is {outputs['memory_gib']}, expected 2. "
        "1536 / 1024 gives 1.5: rounding down would produce 1.",
        fr=f"memory_gib vaut {outputs['memory_gib']}, attendu 2. "
        "1536 / 1024 donne 1.5 : un arrondi vers le bas produirait 1.",
    )


# --------------------------------------------------------------------------
# Rendu du template : le piège de l'échappement
# --------------------------------------------------------------------------

@pytest.mark.parametrize("env", ["dev", "prod", "staging"])
def test_template_rendu_sans_corruption(instances: list[dict], env: str) -> None:
    """Seul `${` s'échappe : `$HOME` et `$(date)` doivent rester intacts."""
    inst = next((r for r in instances if str(r.get("index")) == env), None)
    assert inst is not None, message(
        en=f"No local_file instance for the {env} environment.",
        fr=f"Aucune instance local_file pour l'environnement {env}.",
    )
    content = inst["values"]["content"]

    assert f"node-{env}" in content, message(
        en=f"The rendering of {env} does not contain 'node-{env}': "
        "the hostname marker was not substituted.",
        fr=f"Le rendu de {env} ne contient pas 'node-{env}' : "
        "le marqueur hostname n'a pas été substitué.",
    )
    assert "${AUTRE}" in content, message(
        en="The rendering must contain the literal text ${AUTRE}, "
        "produced by the escaped sequence $${AUTRE}.",
        fr="Le rendu doit contenir le texte littéral ${AUTRE}, "
        "produit par la séquence échappée $${AUTRE}.",
    )
    assert "$HOME" in content and "$$HOME" not in content, message(
        en="The rendering must contain $HOME intact. The presence of $$HOME signals "
        "that every $ was escaped: bash would read $$ as the PID.",
        fr="Le rendu doit contenir $HOME intact. La présence de $$HOME signale "
        "que tous les $ ont été échappés : bash lirait $$ comme le PID.",
    )
    assert "$(date)" in content and "$$(date)" not in content, message(
        en="The rendering must contain $(date) intact, otherwise command "
        "substitution is destroyed when the script runs.",
        fr="Le rendu doit contenir $(date) intact, sinon la substitution de "
        "commande est détruite à l'exécution du script.",
    )


# --------------------------------------------------------------------------
# Fonction de provider
# --------------------------------------------------------------------------

def test_fonction_de_provider(outputs: dict) -> None:
    """`encode_tfvars` vient du provider intégré, pas du langage."""
    rendu = outputs["tfvars_rendu"]
    lignes = [ligne.strip() for ligne in rendu.strip().splitlines() if ligne.strip()]
    assert lignes == ['env = "qa"', "gib = 2"], message(
        en=f"tfvars_rendu is {rendu!r}. The two assignments were expected, "
        'env = "qa" and gib = 2, produced by '
        "provider::terraform::encode_tfvars.",
        fr=f"tfvars_rendu vaut {rendu!r}. Attendu les deux affectations "
        'env = "qa" et gib = 2, produites par '
        "provider::terraform::encode_tfvars.",
    )


# --------------------------------------------------------------------------
# Stabilité
# --------------------------------------------------------------------------

def test_configuration_idempotente(applied: Path) -> None:
    """Un second plan ne doit annoncer aucun changement."""
    proc = terraform(
        "plan", "-detailed-exitcode", "-input=false", "-no-color", cwd=applied
    )
    assert proc.returncode == 0, message(
        en=f"`terraform plan -detailed-exitcode` returns {proc.returncode}, expected 0. "
        "Code 2 signals an unstable expression, a timestamp for instance.",
        fr=f"`terraform plan -detailed-exitcode` rend {proc.returncode}, attendu 0. "
        "Le code 2 signale une expression instable, par exemple un horodatage.",
    )


def test_aucune_valeur_en_dur_dans_le_state(applied: Path) -> None:
    """Les valeurs doivent dériver des variables, pas être écrites en dur."""
    state = json.dumps(show_json(applied))
    assert "prod,dev,prod,staging" not in state, message(
        en="The raw CSV appears in the state: the value was copied "
        "instead of being derived from var.environments_csv.",
        fr="Le CSV brut apparaît dans le state : la valeur a été recopiée "
        "au lieu d'être dérivée de var.environments_csv.",
    )
