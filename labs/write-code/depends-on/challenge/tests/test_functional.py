"""Tests fonctionnels du lab « depends_on ne se pose pas là où une référence suffit ».

Principe : on ne lit jamais les `.tf` de l'apprenant. On applique la
configuration, puis on lit la section `configuration` du plan JSON, qui expose
pour chaque bloc ses `depends_on` et les `references` de ses expressions.

Le test central est la **règle croisée** : pour aucun bloc, un `depends_on` ne
doit désigner une ressource que le bloc référence déjà par ailleurs. C'est ce
qui refuse le `depends_on` de confort, où qu'il soit posé.

Faits vérifiés sur Terraform v1.15.4 avant écriture : une référence d'attribut
ordonne l'application (elle attend la fin de l'amont, pas seulement un nom
connu), et `configuration.root_module.resources[].expressions[].references`
expose ces références dans le plan JSON.
"""

import json
from pathlib import Path

import pytest

from conftest import exiger_workdir, output_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "write-code-depends-on"


def config_resources(cwd: Path) -> dict[str, dict]:
    p = terraform("plan", "-input=false", "-no-color", "-out=tfplan", cwd=cwd)
    if p.returncode != 0:
        pytest.fail(f"`terraform plan` a échoué.\n{p.stderr[-1200:]}")
    plan = json.loads(terraform("show", "-json", "tfplan", cwd=cwd).stdout)
    res = plan["configuration"]["root_module"]["resources"]
    return {r["address"]: r for r in res}


def references_de(bloc: dict) -> set[str]:
    """Toutes les références d'un bloc, arguments et provisioners confondus."""
    refs: set[str] = set()
    for e in bloc.get("expressions", {}).values():
        if isinstance(e, dict):
            refs |= set(e.get("references", []))
    for pr in bloc.get("provisioners", []):
        for e in pr.get("expressions", {}).values():
            if isinstance(e, dict):
                refs |= set(e.get("references", []))
    return refs


def ressources_referencees(bloc: dict) -> set[str]:
    """Les adresses de ressources (a.b) citées, sans l'attribut final."""
    return {".".join(r.split(".")[:2]) for r in references_de(bloc)}


@pytest.fixture(scope="module")
def applied() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(f"`terraform init` a échoué.\n{init.stderr[-1200:]}")
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(
            "`terraform apply` a échoué. Un `???` subsiste, ou `publication` n'est "
            "pas reliée au socle (son provisioner cherche `.pret` avant qu'il "
            "existe).\n"
            f"{app.stderr[-1500:]}"
        )
    return WORKDIR


@pytest.fixture(scope="module")
def config(applied: Path) -> dict[str, dict]:
    return config_resources(applied)


# --------------------------------------------------------------------------
# 1. L'état du système : la copie a bien eu lieu
# --------------------------------------------------------------------------

def test_le_fichier_publie_reprend_le_manifeste(applied: Path) -> None:
    racine = applied / "livraison"
    manifeste = racine / "manifeste.json"
    publie = racine / "publie.json"
    assert publie.is_file(), (
        "`livraison/publie.json` est absent : la copie n'a pas eu lieu. "
        "`publication` doit s'exécuter après le socle et après le manifeste."
    )
    assert publie.read_text() == manifeste.read_text(), (
        "`publie.json` diffère de `manifeste.json` : la copie n'a pas repris le "
        "bon contenu."
    )


# --------------------------------------------------------------------------
# 2. Le manifeste : référence, pas depends_on
# --------------------------------------------------------------------------

def test_le_manifeste_n_a_plus_de_depends_on(config: dict) -> None:
    m = config["local_file.manifeste"]
    assert not m.get("depends_on"), (
        f"`local_file.manifeste` porte encore depends_on = {m.get('depends_on')}. "
        "Son `content` référence déjà `random_pet.nom.id`, ce qui ordonne les deux "
        "ressources : le `depends_on` est redondant, supprimez-le."
    )
    assert "random_pet.nom" in ressources_referencees(m), (
        "`local_file.manifeste` ne référence plus `random_pet.nom` : l'ordre ne "
        "serait plus garanti."
    )


# --------------------------------------------------------------------------
# 3-4. La publication : une implicite (manifeste), une explicite (socle)
# --------------------------------------------------------------------------

def test_la_publication_reference_le_manifeste(config: dict) -> None:
    p = config["null_resource.publication"]
    assert "local_file.manifeste" in ressources_referencees(p), (
        "La commande de `null_resource.publication` n'interpole pas "
        "`local_file.manifeste.filename` : le chemin du manifeste est encore écrit "
        "en dur. Remplacez-le par une référence."
    )


def test_la_publication_depend_du_socle_et_de_lui_seul(config: dict) -> None:
    p = config["null_resource.publication"]
    deps = set(p.get("depends_on", []))
    assert deps == {"null_resource.socle"}, (
        f"`null_resource.publication` porte depends_on = {sorted(deps)}, attendu "
        "exactement null_resource.socle. Le socle est la seule dépendance "
        "qu'aucune référence ne peut exprimer."
    )


# --------------------------------------------------------------------------
# 5. La data source : depends_on explicite
# --------------------------------------------------------------------------

def test_la_data_source_depend_de_la_publication(config: dict) -> None:
    d = config["data.local_file.publie"]
    assert "null_resource.publication" in set(d.get("depends_on", [])), (
        "`data.local_file.publie` ne porte pas `depends_on = "
        "[null_resource.publication]`. Son chemin est littéral : rien d'autre "
        "n'indique qu'il faut attendre la copie."
    )


# --------------------------------------------------------------------------
# 6. La règle croisée : aucun depends_on ne double une référence
# --------------------------------------------------------------------------

def test_aucun_depends_on_ne_double_une_reference(config: dict) -> None:
    fautes = {}
    for adresse, bloc in config.items():
        deps = set(bloc.get("depends_on", []))
        double = deps & ressources_referencees(bloc)
        if double:
            fautes[adresse] = sorted(double)
    assert not fautes, (
        f"Des blocs déclarent en `depends_on` une ressource qu'ils référencent "
        f"déjà : {fautes}. Un `depends_on` de confort abîme le plan sans rien "
        "ordonner de plus."
    )


# --------------------------------------------------------------------------
# 7. Les outputs
# --------------------------------------------------------------------------

def test_outputs_cables(applied: Path) -> None:
    sorties = output_json(applied)
    nom = sorties["nom_livraison"]["value"]
    taille = sorties["taille_publie"]["value"]
    assert isinstance(nom, str) and nom, f"`nom_livraison` = {nom!r}, attendu une chaîne non vide."
    assert isinstance(taille, int) and taille > 0, (
        f"`taille_publie` = {taille!r}, attendu un entier strictement positif."
    )


# --------------------------------------------------------------------------
# 8. Idempotence
# --------------------------------------------------------------------------

def test_la_configuration_est_stable_apres_apply(applied: Path) -> None:
    p = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=applied)
    assert p.returncode == 0, (
        f"`plan -detailed-exitcode` rend {p.returncode} (2 = des changements "
        "restent planifiés). Un apply doit converger."
    )
