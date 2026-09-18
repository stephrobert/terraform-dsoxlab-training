"""test_functional.py : getting-started/terraform-workflow

Huit preuves qu'un plan a été relu avant d'être appliqué.

Aucun test ne lit les `.tf` de l'apprenant, ni la sortie humaine d'une commande.
Le plan enregistré est rouvert PAR L'OUTIL : un `tfplan` fabriqué à la main ne
passe pas `terraform show -json`.

La vérité n'est jamais tirée d'`analyse.json` : elle est recalculée depuis
`resource_changes[].change.actions`, puis comparée au classement de l'apprenant.
Une action `update` vaut mise à jour en place ; toute séquence contenant à la
fois `delete` et `create`, dans n'importe quel ordre, vaut remplacement.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from conftest import exiger_workdir, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "getting-started-terraform-workflow"

PLAN_ENREGISTRE = "tfplan"
PLAN_JSON = "plan.json"
ANALYSE = "analyse.json"
ETIQUETTE_CIBLE = "v2"

CLE_MISE_A_JOUR = "mise_a_jour_en_place"
CLE_REMPLACEMENT = "remplacement"


@pytest.fixture(scope="module")
def joue() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    return WORKDIR


def plan_relu_par_l_outil(cwd: Path) -> dict:
    """Le plan enregistré, rouvert par Terraform lui-même.

    C'est ce qui distingue un vrai plan d'un fichier posé là : le format est
    binaire et versionné, et seul l'outil sait le lire.
    """
    proc = terraform("show", "-json", PLAN_ENREGISTRE, cwd=cwd)
    assert proc.returncode == 0, (
        f"`terraform show -json {PLAN_ENREGISTRE}` a échoué. Le fichier n'est "
        f"pas un plan enregistré par `terraform plan -out={PLAN_ENREGISTRE}`.\n"
        f"{proc.stderr[-1200:]}"
    )
    return json.loads(proc.stdout)


def classement_reel(plan: dict) -> dict[str, set[str]]:
    """La vérité, recalculée depuis les actions du plan."""
    reel = {CLE_MISE_A_JOUR: set(), CLE_REMPLACEMENT: set()}
    for changement in plan.get("resource_changes", []):
        actions = changement["change"]["actions"]
        if "delete" in actions and "create" in actions:
            reel[CLE_REMPLACEMENT].add(changement["address"])
        elif actions == ["update"]:
            reel[CLE_MISE_A_JOUR].add(changement["address"])
    return reel


# --------------------------------------------------------------------------
# 1. Le plan a bien été ENREGISTRÉ, et l'outil sait le rouvrir.
# --------------------------------------------------------------------------
def test_le_plan_enregistre_est_relisible_par_l_outil(joue: Path) -> None:
    fichier = joue / PLAN_ENREGISTRE
    assert fichier.is_file(), (
        f"`{PLAN_ENREGISTRE}` est absent. Un plan se conserve avec "
        f"`terraform plan -out={PLAN_ENREGISTRE}` : sans lui, il n'y a rien à "
        "relire, et `apply` replanifie à sa guise."
    )
    plan = plan_relu_par_l_outil(joue)
    assert plan.get("resource_changes"), (
        "Le plan enregistré n'annonce aucun changement de ressource. Il a été "
        "pris avant que la valeur demandée ne soit changée."
    )


# --------------------------------------------------------------------------
# 2. La conversion JSON correspond bien à CE plan.
# --------------------------------------------------------------------------
def test_la_conversion_json_correspond_au_plan_enregistre(joue: Path) -> None:
    fichier = joue / PLAN_JSON
    assert fichier.is_file(), (
        f"`{PLAN_JSON}` est absent. Il s'obtient avec "
        f"`terraform show -json {PLAN_ENREGISTRE} > {PLAN_JSON}`."
    )
    try:
        converti = json.loads(fichier.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erreur:
        pytest.fail(f"`{PLAN_JSON}` n'est pas du JSON valide : {erreur}")

    attendu = plan_relu_par_l_outil(joue)
    actions_converties = {
        c["address"]: c["change"]["actions"]
        for c in converti.get("resource_changes", [])
    }
    actions_attendues = {
        c["address"]: c["change"]["actions"]
        for c in attendu.get("resource_changes", [])
    }
    assert actions_converties == actions_attendues, (
        f"`{PLAN_JSON}` ne décrit pas le même plan que `{PLAN_ENREGISTRE}`.\n"
        f"Converti : {actions_converties}\nAttendu : {actions_attendues}\n\n"
        "Le fichier a été produit depuis un autre plan, ou édité après coup."
    )


# --------------------------------------------------------------------------
# 3. L'analyse existe, est bien formée, et couvre tout le plan.
# --------------------------------------------------------------------------
def test_l_analyse_couvre_exactement_les_adresses_qui_changent(joue: Path) -> None:
    fichier = joue / ANALYSE
    assert fichier.is_file(), (
        f"`{ANALYSE}` est absent. C'est votre classement : quelles adresses "
        "seront mises à jour en place, lesquelles seront détruites puis "
        "recréées."
    )
    try:
        analyse = json.loads(fichier.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erreur:
        pytest.fail(f"`{ANALYSE}` n'est pas du JSON valide : {erreur}")

    for cle in (CLE_MISE_A_JOUR, CLE_REMPLACEMENT):
        assert cle in analyse, (
            f"`{ANALYSE}` ne porte pas la clé `{cle}`. Les deux clés attendues "
            f"sont `{CLE_MISE_A_JOUR}` et `{CLE_REMPLACEMENT}`, chacune avec une "
            "liste d'adresses."
        )
        assert isinstance(analyse[cle], list), (
            f"`{cle}` doit porter une liste d'adresses, pas un "
            f"{type(analyse[cle]).__name__}."
        )

    reel = classement_reel(plan_relu_par_l_outil(joue))
    toutes_reelles = reel[CLE_MISE_A_JOUR] | reel[CLE_REMPLACEMENT]
    toutes_classees = set(analyse[CLE_MISE_A_JOUR]) | set(analyse[CLE_REMPLACEMENT])

    oubliees = toutes_reelles - toutes_classees
    assert not oubliees, (
        f"Ces adresses changent dans le plan et ne sont classées nulle part : "
        f"{sorted(oubliees)}."
    )
    inventees = toutes_classees - toutes_reelles
    assert not inventees, (
        f"Ces adresses sont classées mais ne changent pas dans le plan : "
        f"{sorted(inventees)}."
    )


# --------------------------------------------------------------------------
# 4. Le classement est exact, adresse par adresse.
# --------------------------------------------------------------------------
def test_le_classement_distingue_correctement_les_deux_familles(joue: Path) -> None:
    analyse = json.loads((joue / ANALYSE).read_text(encoding="utf-8"))
    reel = classement_reel(plan_relu_par_l_outil(joue))

    mal_classees_en_place = set(analyse[CLE_MISE_A_JOUR]) - reel[CLE_MISE_A_JOUR]
    assert not mal_classees_en_place, (
        f"{sorted(mal_classees_en_place)} sont annoncées en mise à jour en "
        "place, alors que le plan prévoit de les détruire puis de les "
        "recréer.\n\nC'est l'erreur qui coûte cher : un remplacement fait "
        "disparaître un objet existant, avec tout ce qu'il porte."
    )
    mal_classees_remplacees = set(analyse[CLE_REMPLACEMENT]) - reel[CLE_REMPLACEMENT]
    assert not mal_classees_remplacees, (
        f"{sorted(mal_classees_remplacees)} sont annoncées en remplacement, "
        "alors que le plan les met à jour en place."
    )
    assert set(analyse[CLE_MISE_A_JOUR]) == reel[CLE_MISE_A_JOUR], (
        f"Mise à jour en place : classé {sorted(analyse[CLE_MISE_A_JOUR])}, "
        f"réel {sorted(reel[CLE_MISE_A_JOUR])}."
    )
    assert set(analyse[CLE_REMPLACEMENT]) == reel[CLE_REMPLACEMENT], (
        f"Remplacement : classé {sorted(analyse[CLE_REMPLACEMENT])}, "
        f"réel {sorted(reel[CLE_REMPLACEMENT])}."
    )


# --------------------------------------------------------------------------
# 5. L'état final porte bien la valeur cible.
# --------------------------------------------------------------------------
def test_l_etat_final_porte_la_valeur_cible(joue: Path) -> None:
    ressources = show_json(joue)["values"]["root_module"]["resources"]
    configuration = next(
        (r for r in ressources if r["address"] == "terraform_data.configuration"),
        None,
    )
    assert configuration is not None, (
        "`terraform_data.configuration` est absente du state : la "
        "configuration n'a jamais été appliquée."
    )
    assert configuration["values"]["input"] == ETIQUETTE_CIBLE, (
        f"L'état porte {configuration['values']['input']!r}, attendu "
        f"{ETIQUETTE_CIBLE!r}. Le changement demandé n'a pas été appliqué."
    )

    rapport = next(r for r in ressources if r["address"] == "local_file.rapport")
    chemin = (joue / rapport["values"]["filename"]).resolve()
    assert chemin.is_file(), f"Le rapport annoncé en {chemin} n'existe pas."
    assert ETIQUETTE_CIBLE in chemin.read_text(encoding="utf-8"), (
        "Le fichier sur le disque ne porte pas la valeur cible."
    )


# --------------------------------------------------------------------------
# 6. Plus rien n'est en attente.
# --------------------------------------------------------------------------
def test_plus_aucun_changement_n_est_en_attente(joue: Path) -> None:
    plan = terraform(
        "plan", "-detailed-exitcode", "-input=false", "-no-color", cwd=joue
    )
    assert plan.returncode == 0, (
        f"`plan -detailed-exitcode` rend {plan.returncode}, attendu 0.\n"
        "0 = diff vide, 1 = erreur, 2 = un changement reste en attente.\n"
        f"{plan.stdout[-1200:]}"
    )


# --------------------------------------------------------------------------
# 7. Le plan enregistré a bien été CONSOMMÉ, et non contourné.
# --------------------------------------------------------------------------
def test_le_plan_enregistre_a_ete_applique_et_est_desormais_perime(
    joue: Path, tmp_path: Path
) -> None:
    # Sur une copie : si le plan n'avait jamais été appliqué, le rejouer ici
    # modifierait réellement l'état, et le test casserait ce qu'il mesure.
    copie = tmp_path / "perime"
    shutil.copytree(joue, copie)

    rejeu = terraform("apply", "-input=false", "-no-color", PLAN_ENREGISTRE, cwd=copie)
    assert rejeu.returncode != 0, (
        "Le plan enregistré s'applique encore : il n'a donc jamais été "
        "consommé.\n\nLa configuration a été appliquée autrement, sans doute "
        f"par un `terraform apply` ordinaire. Or `apply {PLAN_ENREGISTRE}` "
        "est la seule forme qui garantisse que ce qui s'applique est "
        "exactement ce qui a été relu."
    )
    message = (rejeu.stderr + rejeu.stdout).lower()
    assert "stale" in message or "périmé" in message or "saved plan" in message, (
        "Le rejeu échoue, mais pas parce que le plan est périmé :\n"
        f"{rejeu.stderr[-1200:]}"
    )


# --------------------------------------------------------------------------
# 8. Les deux côtés : ce qu'un remplacement emporte, et ce qu'il épargne.
# --------------------------------------------------------------------------
def test_la_mise_a_jour_garde_son_identite_la_ou_le_remplacement_la_perd(
    joue: Path,
) -> None:
    plan = plan_relu_par_l_outil(joue)
    changements = {c["address"]: c["change"] for c in plan.get("resource_changes", [])}
    reel = classement_reel(plan)

    assert reel[CLE_MISE_A_JOUR], (
        "Le plan ne contient aucune mise à jour en place : il n'y a rien à "
        "distinguer, et ce lab ne mesure plus rien."
    )
    assert reel[CLE_REMPLACEMENT], "Le plan ne contient aucun remplacement."

    # Une mise à jour en place conserve l'identifiant : l'objet est le même.
    for adresse in sorted(reel[CLE_MISE_A_JOUR]):
        avant, apres = changements[adresse]["before"], changements[adresse]["after"]
        assert avant.get("id") == apres.get("id"), (
            f"{adresse} est annoncée en mise à jour, mais son identifiant "
            f"passe de {avant.get('id')!r} à {apres.get('id')!r}. Une mise à "
            "jour en place ne change pas d'objet."
        )

    # Un remplacement ne peut PAS annoncer son futur identifiant : l'objet
    # n'existe pas encore. C'est la trace, dans le plan, de ce qui va être perdu.
    inconnus = plan.get("resource_changes", [])
    apres_inconnu = {
        c["address"]
        for c in inconnus
        if "id" in (c["change"].get("after_unknown") or {})
    }
    perdus = reel[CLE_REMPLACEMENT] & apres_inconnu
    assert perdus == reel[CLE_REMPLACEMENT], (
        f"{sorted(reel[CLE_REMPLACEMENT] - perdus)} sont annoncées en "
        "remplacement sans que leur identifiant futur soit inconnu.\n\n"
        "C'est contradictoire : un objet détruit puis recréé ne peut pas "
        "promettre son identifiant à l'avance."
    )

    # Et l'état final confirme : l'objet mis à jour est resté le même.
    ressources = {
        r["address"]: r["values"]
        for r in show_json(joue)["values"]["root_module"]["resources"]
    }
    for adresse in sorted(reel[CLE_MISE_A_JOUR]):
        assert ressources[adresse].get("id") == changements[adresse]["before"].get("id"), (
            f"Après l'application, {adresse} ne porte plus l'identifiant "
            "qu'elle avait avant. Elle a donc été remplacée malgré tout."
        )
