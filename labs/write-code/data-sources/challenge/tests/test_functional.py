"""Tests fonctionnels du lab « le moment où une data source est lue ».

Principe : on ne lit jamais les `.tf` de l'apprenant, et jamais une sortie
humaine. Tout se joue dans le plan converti en JSON.

La preuve du moment de lecture tient en une opposition, vérifiée sur Terraform
v1.15.4 avant l'écriture de ces tests :

- lue **au plan**   : présente dans `prior_state.values.root_module.resources`
  avec ses valeurs réelles, **absente** de `resource_changes` ;
- **reportée** à l'apply : présente dans `resource_changes` avec
  `"mode": "data"` et `"actions": ["read"]`, et les outputs qui en dérivent
  portent `after_unknown: true`.

Le point central du lab : `depends_on` **n'est pas** un critère de report. Le
critère est que la ressource visée soit configurée pour changer dans le plan
courant.
"""

import json
from pathlib import Path

import pytest

from conftest import exiger_workdir, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "write-code-data-sources"

CATALOGUE = "data.local_file.catalogue"
ORDONNE = "data.local_file.catalogue_ordonne"
RELU = "data.local_file.rapport_relu"


def plan_json(*args: str, cwd: Path | None = None) -> dict:
    """Rend le plan en JSON. Rend {} si le plan échoue."""
    rep = cwd or WORKDIR
    p = terraform("plan", "-input=false", "-no-color", "-out=tf.plan", *args, cwd=rep)
    if p.returncode != 0:
        return {}
    return json.loads(terraform("show", "-json", "tf.plan", cwd=rep).stdout)


def change(plan: dict, adresse: str) -> dict | None:
    for rc in plan.get("resource_changes", []):
        if rc["address"] == adresse:
            return rc
    return None


def dans_prior_state(plan: dict, adresse: str) -> bool:
    module = plan.get("prior_state", {}).get("values", {}).get("root_module", {})
    return any(r["address"] == adresse for r in module.get("resources", []))


def exiger_presente_au_plan(plan: dict, adresse: str) -> None:
    """Un contrôle négatif doit d'abord établir que son sujet EXISTE.

    Mesuré le 2026-09-23 : quatre tests de ce fichier étaient verts avant le
    travail, et tous pour la même raison. Ils affirment qu'une adresse n'est PAS
    reportée, ou qu'un output n'est PAS inconnu. Sur une configuration que
    l'apprenant n'a pas encore écrite, l'adresse n'apparaît nulle part : le
    symptôme est absent parce que le SUJET est absent, et le test passe sans
    rien mesurer.

    On exige donc d'abord la présence dans le `prior_state`, qui n'est peuplé
    qu'une fois la data source réellement déclarée et lue.
    """
    assert dans_prior_state(plan, adresse), (
        f"{adresse} n'apparaît pas dans l'état antérieur du plan : elle n'est "
        "pas déclarée, ou n'a jamais été lue.\n\nCe contrôle vérifie qu'elle "
        "n'est PAS reportée à l'apply : il faut d'abord qu'elle existe, sans "
        "quoi il passerait sur une configuration vide."
    )


@pytest.fixture(scope="module")
def applied() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(
            "`terraform init` a échoué. La configuration contient encore des "
            f"expressions incomplètes.\n{init.stderr[-1200:]}"
        )
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(f"`terraform apply` a échoué.\n{app.stderr[-1500:]}")
    return WORKDIR


@pytest.fixture(scope="module")
def plan_stable(applied: Path) -> dict:
    """Plan sans rien faire bouger : tout doit être lu au plan."""
    return plan_json()


@pytest.fixture(scope="module")
def plan_mouvant(applied: Path) -> dict:
    """Plan où la ressource gérée change : les data qui en dépendent décalent."""
    return plan_json("-var", "revision=2")


# --------------------------------------------------------------------------
# 1. Rien ne bouge : les trois data sources sont lues AU PLAN
# --------------------------------------------------------------------------

@pytest.mark.parametrize("adresse", [CATALOGUE, ORDONNE, RELU])
def test_a_l_arret_toutes_les_data_sources_sont_lues_au_plan(
    plan_stable: dict, adresse: str
) -> None:
    rc = change(plan_stable, adresse)
    assert rc is None, (
        f"{adresse} apparaît dans `resource_changes` alors que rien ne change "
        f"(actions = {rc['change']['actions']}). Une data source n'est reportée "
        "que si la ressource dont elle dépend est configurée pour changer dans "
        "le plan courant."
    )
    assert dans_prior_state(plan_stable, adresse), (
        f"{adresse} est absente de `prior_state` : elle n'a pas été lue pendant "
        "le plan, ou elle n'existe pas sous ce nom."
    )


def test_depends_on_ne_reporte_pas_a_lui_seul(plan_stable: dict) -> None:
    """Le point central du lab, et l'erreur que le guide d'origine propageait.

    `catalogue_ordonne` porte un `depends_on` explicite vers une ressource
    gérée. Tant que cette ressource est stable, la lecture reste au plan.
    """
    exiger_presente_au_plan(plan_stable, ORDONNE)
    assert change(plan_stable, ORDONNE) is None, (
        "`catalogue_ordonne` est reportée alors que `random_pet.empreinte` est "
        "stable. Si ce test échoue avec une configuration correcte, c'est que "
        "le comportement de Terraform a changé : `depends_on` seul ne reporte "
        "pas la lecture, seul un changement en attente le fait."
    )


# --------------------------------------------------------------------------
# 2. La ressource gérée change : le report devient visible
# --------------------------------------------------------------------------

def test_la_data_qui_relit_une_ressource_en_mouvement_est_reportee(
    plan_mouvant: dict,
) -> None:
    rc = change(plan_mouvant, RELU)
    assert rc is not None, (
        "`rapport_relu` reste lue au plan alors que `local_file.rapport` change. "
        "Son argument `filename` doit référencer l'attribut de la ressource "
        "gérée, et non recomposer le chemin à la main."
    )
    assert rc.get("mode") == "data", f"mode = {rc.get('mode')!r}, attendu \"data\"."
    assert rc["change"]["actions"] == ["read"], (
        f"actions = {rc['change']['actions']}, attendu [\"read\"]. C'est la "
        "signature d'une lecture reportée."
    )


def test_le_catalogue_reste_lu_au_plan_meme_quand_le_reste_bouge(
    plan_mouvant: dict,
) -> None:
    """Contrôle négatif : sans lui, un plan globalement décalé ferait passer le
    test précédent sans rien prouver de spécifique."""
    exiger_presente_au_plan(plan_mouvant, CATALOGUE)
    assert change(plan_mouvant, CATALOGUE) is None, (
        "`catalogue` est reportée alors que son argument ne dépend d'aucune "
        "ressource gérée. Vérifiez qu'il n'utilise que `path.module`."
    )


def test_l_output_derive_d_une_lecture_reportee_est_inconnu(plan_mouvant: dict) -> None:
    sortie = plan_mouvant.get("output_changes", {}).get("rapport", {})
    assert sortie.get("after_unknown") is True, (
        f"after_unknown = {sortie.get('after_unknown')!r}. L'output `rapport` "
        "doit dériver de `data.local_file.rapport_relu`, dont la valeur n'est "
        "pas connue au plan quand la ressource change."
    )


def test_l_output_derive_d_une_lecture_au_plan_est_connu(plan_mouvant: dict) -> None:
    sorties = plan_mouvant.get("output_changes", {})
    assert "catalogue" in sorties, (
        f"L'output `catalogue` n'est pas déclaré. Présents : {sorted(sorties)}."
        "\n\nCe contrôle vérifie que sa valeur est CONNUE au plan : un output "
        "absent n'est pas un output connu."
    )
    sortie = sorties["catalogue"]
    assert sortie.get("after") not in (None, ""), (
        "L'output `catalogue` est déclaré mais sa valeur planifiée est vide. "
        "Il doit dériver de la data source dont l'argument est connu."
    )
    assert sortie.get("after_unknown") is not True, (
        "L'output `catalogue` est inconnu au plan. Il doit dériver de la data "
        "source dont l'argument est connu."
    )


# --------------------------------------------------------------------------
# 3. Vocabulaire du state : managed contre data
# --------------------------------------------------------------------------

def test_le_state_distingue_ressources_gerees_et_data_resources(applied: Path) -> None:
    """`mode` est le vocabulaire officiel, et celui de l'examen.

    Il interdit de faire passer une ressource gérée pour une data source :
    recopier le contenu du catalogue dans un `local_file` produirait
    `mode: managed` et ferait échouer ce test.
    """
    module = show_json(applied).get("values", {}).get("root_module", {})
    modes = {r["address"]: r.get("mode") for r in module.get("resources", [])}

    for adresse in (CATALOGUE, ORDONNE, RELU):
        assert modes.get(adresse) == "data", (
            f"{adresse} porte mode = {modes.get(adresse)!r}. Une data resource "
            "vaut \"data\" ; \"managed\" signifie que vous avez déclaré une "
            "ressource là où une lecture était demandée."
        )
    assert modes.get("local_file.rapport") == "managed", (
        "`local_file.rapport` doit rester une ressource gérée."
    )


# --------------------------------------------------------------------------
# 4. Dérive par la donnée externe, et destruction
# --------------------------------------------------------------------------

def test_stable_au_repos_et_en_ecart_des_que_le_fichier_lu_change(
    applied: Path,
) -> None:
    """La stabilité vit ici, et plus dans un test à elle.

    Seule, elle était vraie avant le travail : une configuration qui ne déclare
    presque rien converge parfaitement. Encadrant l'écart, elle devient la
    moitié qui donne son sens à l'autre : le plan passe de 0 à 2 puis revient à
    0, et c'est le fichier LU qui commande, sans qu'une ligne de `.tf` ait bougé.

    Sans le retour à 0, un plan durablement décalé ferait passer le milieu sans
    rien prouver de spécifique.
    """
    catalogue = applied / "catalogue.txt"
    original = catalogue.read_text(encoding="utf-8")

    repos = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color",
                      cwd=applied)
    assert repos.returncode == 0, (
        f"`plan -detailed-exitcode` rend {repos.returncode} au repos (2 = des "
        "changements restent planifiés). Un apply doit converger."
    )

    try:
        catalogue.write_text(original + "ajout=externe\n", encoding="utf-8")
        ecart = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color",
                          cwd=applied)
        assert ecart.returncode == 2, (
            f"`plan -detailed-exitcode` rend {ecart.returncode}, attendu 2. "
            "Modifier le fichier lu par une data source doit produire un plan "
            "non vide, sans qu'aucun fichier `.tf` n'ait bougé.\n\nUn retour 0 "
            "ici signifie que la valeur lue n'irrigue rien : la data source est "
            "déclarée, mais personne ne s'en sert."
        )
    finally:
        catalogue.write_text(original, encoding="utf-8")

    retour = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color",
                       cwd=applied)
    assert retour.returncode == 0, (
        f"Le fichier remis à l'identique, le plan rend encore {retour.returncode}. "
        "L'écart venait donc d'autre chose que de la lecture."
    )


def test_le_plan_de_destruction_ignore_les_data_sources(applied: Path) -> None:
    """Terraform ne détruit pas ce qu'il n'a jamais créé.

    Nuance à ne pas confondre : les data resources n'apparaissent dans aucune
    action de destruction, mais elles disparaissent tout de même du state avec
    le reste. Elles ne « survivent » pas à un destroy.
    """
    plan = plan_json("-destroy", cwd=applied)

    # Un contrôle négatif doit d'abord établir que son sujet existe.
    #
    # Première tentative, le 2026-09-23 : exiger que `local_file.rapport` soit
    # bien détruite. Insuffisant, et le sens « 0 » l'a montré tout de suite : les
    # fixtures la déclarent déjà, donc la garde passait sans le travail. La garde
    # doit porter sur ce que SEUL le travail produit, c'est-à-dire les data
    # sources dont on vérifie justement qu'elles sont épargnées.
    module = show_json(applied).get("values", {}).get("root_module", {})
    lues = {
        r["address"] for r in module.get("resources", []) if r.get("mode") == "data"
    }
    manquantes = {CATALOGUE, ORDONNE, RELU} - lues
    assert not manquantes, (
        f"Ces data sources n'existent pas dans le state : {sorted(manquantes)}."
        "\n\nCe contrôle vérifie que la destruction les ÉPARGNE : il faut "
        "d'abord qu'elles soient là, sans quoi il passerait sur une "
        "configuration qui n'en déclare aucune."
    )

    data_detruites = [rc["address"] for rc in plan.get("resource_changes", [])
                      if rc.get("mode") == "data"]
    assert not data_detruites, (
        f"Le plan de destruction porte des entrées `mode: data` : {data_detruites}. "
        "Terraform ne planifie aucune action de destruction sur une data source."
    )
