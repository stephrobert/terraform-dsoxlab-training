"""test_functional.py : getting-started/providers-resources-data-sources

Huit preuves de la différence entre ce que Terraform gère et ce qu'il lit.

Tant qu'on n'a pas vu un `destroy` effacer les objets gérés sans toucher à ce
que la source de données lisait, on croit qu'un bloc `data` est une resource en
lecture seule. Les deux conséquences réelles sont ici : une source de données ne
crée rien, et elle est RELUE à chaque plan, donc elle peut faire bouger un plan
alors que le code n'a pas bougé d'une ligne.

Rien n'est lu dans les `.tf` de l'apprenant. Les deux tests destructeurs, celui
qui modifie le catalogue et celui qui détruit, travaillent sur une copie : un
test ne casse pas ce qu'il mesure.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pytest

from conftest import exiger_workdir, output_json, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "getting-started-providers-resources-data-sources"

PROVIDERS = ("local", "null", "random")
REGISTRE = "registry.terraform.io"

CATALOGUE = "catalogue.txt"
RESUME = "resume.txt"

GEREES_ATTENDUES = {
    "random_pet.reference",
    "local_file.resume",
    "null_resource.empreinte",
}
ADRESSE_LUE = "data.local_file.catalogue"


@pytest.fixture(scope="module")
def prepared() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(
            "`terraform init` a échoué. Un `???` subsiste-t-il dans la "
            f"configuration ?\n{init.stderr[-1200:]}"
        )
    return WORKDIR


@pytest.fixture(scope="module")
def applied(prepared: Path) -> Path:
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=prepared)
    if app.returncode != 0:
        pytest.fail(f"`terraform apply` a échoué.\n{app.stderr[-1500:]}")
    return prepared


@pytest.fixture(scope="module")
def verrou_regenere(prepared: Path, tmp_path_factory) -> Path:
    """Un verrou reconstruit depuis zéro, pour lire ses contraintes.

    `constraints` n'est inscrit dans `.terraform.lock.hcl` qu'à la CRÉATION de
    l'entrée : un apprenant qui lance `init` avant d'écrire ses contraintes
    garde un verrou sans elles, et rien ne les y ajoute, pas même
    `init -upgrade`. Mesuré sur le lab terraform-vs-opentofu, où ce défaut
    recalait un travail juste.
    """
    copie = tmp_path_factory.mktemp("verrou") / "work"
    shutil.copytree(prepared, copie)
    (copie / ".terraform.lock.hcl").unlink(missing_ok=True)
    init = terraform("init", "-input=false", "-no-color", cwd=copie)
    if init.returncode != 0:
        pytest.fail(f"La reconstruction du verrou a échoué.\n{init.stderr[-1200:]}")
    return copie


def ressources(cwd: Path) -> list[dict]:
    etat = show_json(cwd)
    return etat.get("values", {}).get("root_module", {}).get("resources", [])


# --------------------------------------------------------------------------
# 1. Les trois providers sont déclarés, avec une contrainte pessimiste.
# --------------------------------------------------------------------------
def test_les_trois_providers_portent_une_contrainte_pessimiste(
    verrou_regenere: Path,
) -> None:
    texte = (verrou_regenere / ".terraform.lock.hcl").read_text(encoding="utf-8")
    trouves = {
        bloc.group(1): (re.search(r'constraints\s*=\s*"([^"]+)"', bloc.group(2)) or [None])
        for bloc in re.finditer(r'provider\s+"([^"]+)"\s*\{(.*?)\n\}', texte, re.DOTALL)
    }
    for court in PROVIDERS:
        adresse = f"{REGISTRE}/hashicorp/{court}"
        assert adresse in trouves, (
            f"{adresse} n'est pas verrouillé. Le verrou porte {sorted(trouves)}."
        )
        trouve = trouves[adresse]
        contrainte = trouve.group(1) if hasattr(trouve, "group") else None
        assert contrainte, (
            f"{court} est verrouillé SANS contrainte : il a été deviné, pas "
            "déclaré dans `required_providers`."
        )
        assert contrainte.startswith("~>"), (
            f"La contrainte de {court} vaut {contrainte!r}, attendu une "
            "contrainte pessimiste `~> x.y`."
        )


# --------------------------------------------------------------------------
# 2. La preuve centrale : le state sépare les deux natures.
# --------------------------------------------------------------------------
def test_le_state_separe_ce_qui_est_gere_de_ce_qui_est_lu(applied: Path) -> None:
    inventaire = ressources(applied)
    gerees = {r["address"] for r in inventaire if r["mode"] == "managed"}
    lues = {r["address"] for r in inventaire if r["mode"] == "data"}

    assert gerees == GEREES_ATTENDUES, (
        f"Le state gère {sorted(gerees)}.\nAttendu exactement : "
        f"{sorted(GEREES_ATTENDUES)}.\n\nSi `local_file.catalogue` apparaît ici, "
        "le bloc a été écrit en `resource` : Terraform se croit propriétaire "
        "d'un fichier qu'il n'a pas créé, et l'effacera au premier `destroy`."
    )
    assert lues == {ADRESSE_LUE}, (
        f"Le state lit {sorted(lues)}, attendu exactement {{{ADRESSE_LUE!r}}}.\n\n"
        "Un bloc `data` entre bien dans le state, mais en mode `data` : "
        "Terraform ne le crée pas et ne le détruira jamais."
    )


# --------------------------------------------------------------------------
# 3. La dépendance est DÉDUITE du code, pas écrite à la main.
# --------------------------------------------------------------------------
def test_le_resume_derive_de_ce_que_la_source_de_donnees_a_lu(applied: Path) -> None:
    inventaire = ressources(applied)
    lu = next(r for r in inventaire if r["address"] == ADRESSE_LUE)
    lignes_reelles = len(
        [ligne for ligne in lu["values"]["content"].strip().splitlines() if ligne.strip()]
    )

    resume = next(r for r in inventaire if r["address"] == "local_file.resume")
    chemin = (applied / resume["values"]["filename"]).resolve()
    assert chemin.is_file(), f"Le résumé annoncé en {chemin} n'existe pas."

    contenu = chemin.read_text(encoding="utf-8")
    assert str(lignes_reelles) in contenu, (
        f"Le résumé ne porte pas le nombre de lignes du catalogue "
        f"({lignes_reelles}).\nIl contient :\n{contenu}\n\n"
        "Le contenu doit dériver de `data.local_file.catalogue.content`, jamais "
        "être saisi à la main."
    )

    reference = next(
        r["values"]["id"] for r in inventaire if r["address"] == "random_pet.reference"
    )
    assert reference in contenu, (
        f"Le résumé ne porte pas la référence générée ({reference!r}). Il doit "
        "dépendre des deux : de ce qui est lu, et de ce qui est produit."
    )


# --------------------------------------------------------------------------
# 4. Le déclencheur dépend des deux natures à la fois.
# --------------------------------------------------------------------------
def test_le_declencheur_depend_de_la_resource_et_de_la_source_de_donnees(
    applied: Path,
) -> None:
    inventaire = ressources(applied)
    declencheurs = next(
        r for r in inventaire if r["address"] == "null_resource.empreinte"
    )["values"].get("triggers") or {}
    assert declencheurs, "`null_resource.empreinte` n'a aucun `triggers`."

    reference = next(
        r["values"]["id"] for r in inventaire if r["address"] == "random_pet.reference"
    )
    assert reference in declencheurs.values(), (
        f"Le déclencheur ne porte pas la référence produite ({reference!r}). "
        f"Il vaut {declencheurs!r}."
    )

    lu = next(r for r in inventaire if r["address"] == ADRESSE_LUE)["values"]
    empreintes_possibles = {
        lu.get("content"), lu.get("content_sha1"), lu.get("content_sha256"),
        lu.get("content_md5"), lu.get("content_base64sha256"),
    }
    assert empreintes_possibles & set(declencheurs.values()), (
        f"Le déclencheur ne porte rien qui vienne de la source de données. "
        f"Il vaut {declencheurs!r}.\n\nIl doit dépendre de ce qui est LU autant "
        "que de ce qui est produit : sans cela, une modification du catalogue "
        "ne le ferait pas réagir."
    )


# --------------------------------------------------------------------------
# 5. Les deux sorties, une par nature.
# --------------------------------------------------------------------------
def test_les_deux_sorties_exposent_chacune_une_nature(applied: Path) -> None:
    sorties = output_json(applied)
    for attendu in ("reference_generee", "lignes_du_catalogue"):
        assert attendu in sorties, (
            f"La sortie `{attendu}` est absente. Présentes : {sorted(sorties)}."
        )

    inventaire = ressources(applied)
    reference = next(
        r["values"]["id"] for r in inventaire if r["address"] == "random_pet.reference"
    )
    assert sorties["reference_generee"]["value"] == reference, (
        "`reference_generee` ne vaut pas l'identifiant produit par la resource."
    )

    lu = next(r for r in inventaire if r["address"] == ADRESSE_LUE)
    lignes_reelles = len(
        [ligne for ligne in lu["values"]["content"].strip().splitlines() if ligne.strip()]
    )
    assert int(sorties["lignes_du_catalogue"]["value"]) == lignes_reelles, (
        f"`lignes_du_catalogue` vaut "
        f"{sorties['lignes_du_catalogue']['value']!r}, le catalogue en compte "
        f"{lignes_reelles}."
    )


# --------------------------------------------------------------------------
# 6. Juste après l'apply, rien n'est en attente.
# --------------------------------------------------------------------------
def test_aucun_changement_juste_apres_l_application(applied: Path) -> None:
    plan = terraform(
        "plan", "-detailed-exitcode", "-input=false", "-no-color", cwd=applied
    )
    assert plan.returncode == 0, (
        f"`plan -detailed-exitcode` rend {plan.returncode}, attendu 0.\n"
        f"{plan.stdout[-1200:]}"
    )

    enregistre = terraform(
        "plan", "-input=false", "-no-color", "-out=verification.tfplan", cwd=applied
    )
    assert enregistre.returncode == 0, f"Le plan a échoué.\n{enregistre.stderr[-1200:]}"
    montre = terraform("show", "-json", "verification.tfplan", cwd=applied)
    actions = {
        c["address"]: c["change"]["actions"]
        for c in json.loads(montre.stdout).get("resource_changes", [])
        if c["change"]["actions"] != ["no-op"]
    }
    assert not actions, f"Le plan enregistré annonce encore {actions}."


# --------------------------------------------------------------------------
# 7. La source de données est RELUE : le plan bouge sans que le code bouge.
# --------------------------------------------------------------------------
def test_modifier_le_catalogue_fait_bouger_le_plan_sans_toucher_au_code(
    applied: Path, tmp_path: Path
) -> None:
    copie = tmp_path / "relecture"
    shutil.copytree(applied, copie)

    catalogue = copie / CATALOGUE
    catalogue.write_text(
        catalogue.read_text(encoding="utf-8") + "reference-05  onduleur      6 kVA\n",
        encoding="utf-8",
    )

    plan = terraform(
        "plan", "-detailed-exitcode", "-input=false", "-no-color", cwd=copie
    )
    assert plan.returncode == 2, (
        f"`plan -detailed-exitcode` rend {plan.returncode} après modification du "
        "catalogue, attendu 2.\n\nUn retour 0 signifie que la valeur lue "
        "n'irrigue rien : la source de données est déclarée, mais personne ne "
        "s'en sert. Une source de données est RELUE à chaque plan, et c'est "
        "pour cela qu'un plan peut bouger alors qu'aucun `.tf` n'a changé.\n"
        f"{plan.stdout[-1200:]}"
    )


# --------------------------------------------------------------------------
# 8. Les deux côtés : ce que `destroy` emporte, et ce qu'il n'a pas le droit
#    de toucher.
# --------------------------------------------------------------------------
def test_le_destroy_efface_le_gere_et_epargne_ce_qui_etait_seulement_lu(
    applied: Path, tmp_path: Path
) -> None:
    copie = tmp_path / "destruction"
    shutil.copytree(applied, copie)

    avant = (copie / CATALOGUE).read_bytes()
    assert (copie / RESUME).is_file(), (
        f"`{RESUME}` devrait exister avant le `destroy`."
    )

    detruit = terraform(
        "destroy", "-auto-approve", "-input=false", "-no-color", cwd=copie
    )
    assert detruit.returncode == 0, f"`destroy` a échoué.\n{detruit.stderr[-1500:]}"

    restants = [r["address"] for r in ressources(copie) if r["mode"] == "managed"]
    assert not restants, f"Le state porte encore {restants} après le `destroy`."

    assert not (copie / RESUME).exists(), (
        f"`{RESUME}` existe encore après le `destroy`. Terraform devait "
        "l'effacer : c'est lui qui l'avait créé."
    )

    # Et la moitié qui donne tout son sens à la première : l'objet seulement LU
    # est intact, octet pour octet.
    assert (copie / CATALOGUE).is_file(), (
        f"`{CATALOGUE}` a été SUPPRIMÉ par le `destroy`.\n\nC'est la "
        "conséquence exacte d'avoir écrit `resource` au lieu de `data` : "
        "Terraform s'est cru propriétaire d'un fichier qu'il n'a jamais créé."
    )
    assert (copie / CATALOGUE).read_bytes() == avant, (
        f"`{CATALOGUE}` a été modifié par le `destroy`. Une source de données "
        "n'écrit jamais."
    )
