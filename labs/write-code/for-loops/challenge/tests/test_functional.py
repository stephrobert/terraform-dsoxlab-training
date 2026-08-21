"""Tests fonctionnels du lab « transformer un catalogue avec les expressions for ».

Principe : on ne lit jamais les `.tf` de l'apprenant. On applique la
configuration, puis on décode `terraform output -json` et `terraform show -json`.

Les pièges du sujet se prouvent par la forme du résultat, pas par le code écrit :
- un `memoires` de longueur 1 trahit un splat `[*]` appliqué à la map ;
- une valeur de type liste sous chaque clé de `par_role` prouve l'ellipsis `...` ;
- l'absence du serveur sans tag dans `tags_plats` prouve l'aplatissement.

Faits vérifiés sur Terraform v1.15.4 avant écriture : `[...]` produit un tuple,
`{...}` un object, le splat sur une map rend un tuple d'un seul élément, et
`flatten([...])` fait disparaître les entrées à liste vide.
"""

from pathlib import Path

import pytest

from conftest import exiger_workdir, output_json, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "write-code-for-loops"

# État de départ connu (var.serveurs), pour formuler les attentes.
PROD = {"api", "db", "web1", "web2"}          # env == prod
PROD_ACTIFS = {"api", "db", "web1"}           # env == prod ET actif (web2 inactif)


@pytest.fixture(scope="module")
def applied() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(f"`terraform init` a échoué.\n{init.stderr[-1200:]}")
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(
            "`terraform apply` a échoué. Un `local` contient encore un `???`, ou "
            "une expression `for` est mal formée.\n"
            f"{app.stderr[-1500:]}"
        )
    return WORKDIR


@pytest.fixture(scope="module")
def sorties(applied: Path) -> dict:
    return output_json(applied)


def valeur(sorties: dict, nom: str):
    assert nom in sorties, f"L'output `{nom}` est absent."
    return sorties[nom]["value"]


# --------------------------------------------------------------------------
# 1. noms_prod : un tuple filtré
# --------------------------------------------------------------------------

def test_noms_prod_est_une_liste_des_serveurs_prod(sorties: dict) -> None:
    v = valeur(sorties, "noms_prod")
    assert isinstance(v, list), (
        f"`noms_prod` doit être un tuple (liste JSON), obtenu {type(v).__name__}. "
        "Utilisez des crochets `[for ...]`."
    )
    assert set(v) == PROD, (
        f"`noms_prod` = {v}. Attendu les serveurs dont env vaut prod : {sorted(PROD)}. "
        "La clause `if v.env == \"prod\"` filtre l'itération."
    )


def test_noms_prod_est_trie_lexicalement(sorties: dict) -> None:
    v = valeur(sorties, "noms_prod")
    assert v == sorted(v), (
        f"`noms_prod` = {v}, pas dans l'ordre lexical. Une expression `for` sur une "
        "map itère les clés triées : ne réordonnez pas à la main."
    )


# --------------------------------------------------------------------------
# 2. par_role : un object groupé par l'ellipsis
# --------------------------------------------------------------------------

def test_par_role_est_un_objet_de_listes(sorties: dict) -> None:
    v = valeur(sorties, "par_role")
    assert isinstance(v, dict), (
        f"`par_role` doit être un object (dict JSON), obtenu {type(v).__name__}. "
        "Utilisez des accolades `{for ...}`."
    )
    for role, noms in v.items():
        assert isinstance(noms, list), (
            f"La clé `{role}` porte {noms!r}, pas une liste. Sans l'ellipsis `...`, "
            "un rôle partagé écrase la clé au lieu de grouper, et Terraform lève "
            "« Duplicate object key ». Écrivez `v.role => k...`."
        )


def test_par_role_regroupe_les_roles_partages(sorties: dict) -> None:
    v = valeur(sorties, "par_role")
    assert set(v.get("frontend", [])) == {"web1", "web2"}, (
        f"`par_role[\"frontend\"]` = {v.get('frontend')}. Les deux frontends doivent "
        "être regroupés sous la même clé."
    )
    assert set(v.get("backend", [])) == {"api", "db", "cache"}, (
        f"`par_role[\"backend\"]` = {v.get('backend')}, attendu api, db, cache."
    )


# --------------------------------------------------------------------------
# 3. memoires : le piège du splat
# --------------------------------------------------------------------------

def test_memoires_a_une_entree_par_serveur(sorties: dict) -> None:
    v = valeur(sorties, "memoires")
    assert isinstance(v, list), f"`memoires` doit être une liste, obtenu {type(v).__name__}."
    assert len(v) == 6, (
        f"`memoires` a {len(v)} élément(s), attendu 6. Une longueur de 1 signe un "
        "splat `var.serveurs[*]` appliqué à la map : le splat enveloppe la map "
        "entière dans un tuple d'un seul élément. Utilisez `[for k, v in "
        "var.serveurs : v.memoire_mo]`."
    )
    assert sorted(v) == [256, 512, 512, 512, 1024, 2048], (
        f"`memoires` = {v}. Attendu les six mémoires du catalogue."
    )


# --------------------------------------------------------------------------
# 4. tags_plats : boucles imbriquées + flatten
# --------------------------------------------------------------------------

def test_tags_plats_croise_serveur_et_tag(sorties: dict) -> None:
    v = valeur(sorties, "tags_plats")
    assert isinstance(v, list), f"`tags_plats` doit être une liste, obtenu {type(v).__name__}."
    attendu = {
        "web1:dmz", "web1:prod", "web2:dmz", "api:prod",
        "cache:staging", "ci:dev",
    }
    assert set(v) == attendu, (
        f"`tags_plats` = {sorted(v)}.\nAttendu : {sorted(attendu)}. Croisez les deux "
        "niveaux puis aplatissez : `flatten([for k, v in var.serveurs : "
        "[for t in v.tags : \"${k}:${t}\"]])`."
    )


def test_le_serveur_sans_tag_est_absent(sorties: dict) -> None:
    """`db` a une liste de tags vide : l'aplatissement le fait disparaître seul."""
    v = valeur(sorties, "tags_plats")
    assert not any(s.startswith("db:") for s in v), (
        f"`tags_plats` contient une entrée pour `db`, qui n'a aucun tag : {v}. "
        "Une boucle imbriquée sur une liste vide ne produit rien, `flatten` "
        "l'absorbe. N'ajoutez pas d'entrée à la main."
    )


# --------------------------------------------------------------------------
# 5. for_each filtré : les fiches
# --------------------------------------------------------------------------

def test_une_fiche_par_serveur_prod_et_actif(applied: Path) -> None:
    resources = show_json(applied).get("values", {}).get("root_module", {}).get("resources", [])
    index = {
        r["index"]
        for r in resources
        if r.get("mode") == "managed" and r.get("type") == "local_file"
    }
    assert index == PROD_ACTIFS, (
        f"Instances de `local_file.fiche` = {sorted(index)}. Attendu les serveurs "
        f"à la fois prod et actifs : {sorted(PROD_ACTIFS)}. `web2` est prod mais "
        "inactif, il doit être exclu. Filtrez le `for_each` avec `if v.env == "
        "\"prod\" && v.actif`."
    )


# --------------------------------------------------------------------------
# 6. Idempotence
# --------------------------------------------------------------------------

def test_la_configuration_est_stable_apres_apply(applied: Path) -> None:
    p = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=applied)
    assert p.returncode == 0, (
        f"`plan -detailed-exitcode` rend {p.returncode} (2 = des changements restent "
        "planifiés). Un apply doit converger."
    )
