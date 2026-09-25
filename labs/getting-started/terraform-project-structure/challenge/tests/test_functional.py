"""Tests fonctionnels du lab « decouper un monolithe sans bouger le plan ».

Terraform evalue TOUS les fichiers `.tf` d'un repertoire comme un document
unique : le nom des fichiers et leur ordre n'ont aucun effet fonctionnel.
Decouper doit donc produire exactement le meme plan, et c'est cela qu'on prouve,
pas la presence de fichiers bien nommes.

## La preuve d'invariance, et pourquoi elle ne peut pas venir de l'apprenant

Un plan de reference fige par l'apprenant ne prouverait rien : rien n'obligerait
a l'avoir pris AVANT le decoupage. Les tests RECONSTRUISENT donc le plan du
monolithe, dans un repertoire temporaire, depuis la copie de reference fournie,
et le comparent au plan de la configuration decoupee.

## La preuve du decoupage, par ablation

Mesure du 2026-09-24 : `terraform show -json` n'expose AUCUNE position source.
Ni `configuration.root_module.resources`, ni les variables ne disent de quel
fichier elles viennent. Un premier jet de ce lab promettait cette preuve : elle
n'existe pas.

Ce qui existe, et qui ne demande d'ouvrir aucun `.tf` : retirer un fichier dans
une copie, et constater ce qui casse. Sans `variables.tf`, `validate` refuse.
Sans `main.tf`, le plan ne porte plus aucune ressource. C'est une preuve par
ablation, et elle porte sur le comportement, pas sur le texte.

## Ce qui empeche d'etre vert sans travail

Le monolithe seul produit deja un plan valide. Mais `tout.tf` doit avoir
disparu, les six fichiers exister, l'ablation de chacun casser quelque chose, et
les quatre valeurs effectives respecter la precedence : rien de tout cela n'est
vrai au depart.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from conftest import exiger_workdir, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "getting-started-terraform-project-structure"

MONOLITHE = "tout.tf"
REFERENCE = "reference/monolithe.tf.txt"

FICHIERS_ATTENDUS = (
    "terraform.tf",
    "providers.tf",
    "variables.tf",
    "locals.tf",
    "main.tf",
    "outputs.tf",
)

# Les valeurs d'entree du lab, et leur source. L'environnement fait partie de
# l'enonce : sans lui, la marche decisive ne se joue pas.
REVISION = "depuis-ligne-de-commande"
ENVIRONNEMENT_DU_LAB = {"TF_VAR_projet": "depuis-env"}

# Ce que chaque variable doit valoir, et pourquoi. Mesure sur la configuration
# cible le 2026-09-24.
VALEURS_ATTENDUES = {
    "projet_effectif": ("depuis-tfvars", "terraform.tfvars bat TF_VAR_"),
    "environnement_effectif": ("depuis-auto", "un *.auto.tfvars bat terraform.tfvars"),
    "region_effective": ("eu-ouest", "personne ne la pose : son default gagne"),
    "revision_effective": (REVISION, "-var bat toutes les autres sources"),
}

ADRESSES_ATTENDUES = {"random_pet.empreinte", "local_file.rapport", "null_resource.sceau"}

# Les champs qu'un plan porte et qui changent d'une execution a l'autre : les
# comparer ferait echouer le lab pour une raison qui n'est pas la sienne.
VOLATILS = {"id", "keepers", "triggers"}


def _tf(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["terraform", *args],
        cwd=cwd or WORKDIR,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, **ENVIRONNEMENT_DU_LAB},
    )


@pytest.fixture(scope="module")
def joue() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    init = _tf("init", "-input=false", "-no-color")
    assert init.returncode == 0, f"`terraform init` a echoue.\n{init.stderr[-1000:]}"
    return WORKDIR


def _exiger_decoupage_fait(repertoire: Path) -> None:
    """Refuse de mesurer quoi que ce soit tant que le decoupage n'est pas fait.

    Sans cette garde, trois tests etaient VERTS a vide, mesure du 2026-09-24 :
    le monolithe seul produit deja un plan identique a lui-meme, valide deja, et
    refuse deja un doublon. Ils ne mesuraient donc pas le travail demande, ils
    constataient l'etat de depart.

    C'est le defaut le plus couteux du domaine, et il ne se voit qu'en jouant le
    lab sans rien faire.
    """
    assert not (repertoire / MONOLITHE).exists(), (
        f"`{MONOLITHE}` est toujours la : le decoupage n'a pas eu lieu.\n\n"
        "Ce test ne mesure rien tant que le monolithe est en place."
    )
    manquants = [nom for nom in FICHIERS_ATTENDUS if not (repertoire / nom).is_file()]
    assert not manquants, (
        f"Le decoupage est incomplet, il manque {manquants}."
    )


def _plan_json(repertoire: Path) -> dict:
    """Le plan d'un repertoire, enregistre puis relu en JSON."""
    plan = _tf("plan", "-out=comparaison.tfplan", "-input=false", "-no-color",
               "-var", f"revision={REVISION}", cwd=repertoire)
    assert plan.returncode == 0, (
        f"Le plan a echoue dans {repertoire.name}.\n{plan.stderr[-1000:]}"
    )
    montre = _tf("show", "-json", "comparaison.tfplan", cwd=repertoire)
    montre.check_returncode()
    return json.loads(montre.stdout)


def _empreinte(plan: dict) -> dict[str, dict]:
    """Ce qu'un plan dit, debarrasse de ce qui change a chaque execution."""
    empreinte = {}
    for changement in plan.get("resource_changes", []):
        apres = dict(changement["change"].get("after") or {})
        for champ in VOLATILS:
            apres.pop(champ, None)
        empreinte[changement["address"]] = {
            "actions": changement["change"]["actions"],
            "after": apres,
        }
    return empreinte


# --------------------------------------------------------------------------
# 1. Le monolithe a disparu, et les six fichiers existent.
# --------------------------------------------------------------------------
def test_le_monolithe_a_ete_decoupe_et_non_recopie(joue: Path) -> None:
    """Decouper, c'est deplacer. Copier declarerait chaque nom deux fois.

    Terraform refuserait alors : `Duplicate variable declaration`. Ce test le
    constate avant les autres, parce qu'un monolithe laisse en place rend tout
    le reste incomprehensible.
    """
    assert not (joue / MONOLITHE).exists(), (
        f"`{MONOLITHE}` est toujours la.\n\nDecouper, c'est DEPLACER : tant que "
        "le monolithe existe a cote des fichiers thematiques, chaque nom est "
        "declare deux fois et Terraform refuse."
    )

    manquants = [nom for nom in FICHIERS_ATTENDUS if not (joue / nom).is_file()]
    assert not manquants, (
        f"Ces fichiers manquent : {manquants}.\nAttendus : "
        f"{list(FICHIERS_ATTENDUS)}."
    )


# --------------------------------------------------------------------------
# 2. LA preuve : le plan n'a pas bouge d'un iota.
# --------------------------------------------------------------------------
def test_le_plan_est_identique_a_celui_du_monolithe(joue: Path, tmp_path: Path) -> None:
    """Reconstruit depuis la copie de reference, jamais depuis un plan fourni.

    C'est ce qui rend la preuve reelle : un plan que l'apprenant aurait fige
    lui-meme ne garantirait pas d'avoir ete pris AVANT le decoupage.
    """
    _exiger_decoupage_fait(joue)

    origine = tmp_path / "monolithe"
    origine.mkdir()
    shutil.copy2(joue / REFERENCE, origine / "tout.tf")
    for valeurs in ("terraform.tfvars", "env.auto.tfvars"):
        source = joue / valeurs
        if source.is_file():
            shutil.copy2(source, origine / valeurs)

    init = _tf("init", "-input=false", "-no-color", cwd=origine)
    assert init.returncode == 0, (
        f"Impossible de rejouer le monolithe de reference.\n{init.stderr[-800:]}"
    )

    # La configuration decoupee est planifiee dans une COPIE SANS STATE, comme
    # le monolithe. Sans cela, un test qui a deja applique ferait annoncer
    # `no-op` d'un cote et `create` de l'autre, et l'invariance semblerait
    # rompue alors que rien n'a bouge. Mesure du 2026-09-24.
    decoupee = tmp_path / "decoupee"
    shutil.copytree(
        joue, decoupee,
        ignore=shutil.ignore_patterns("*.tfplan", "*.tfstate*", "rapport.txt"),
    )
    init_decoupee = _tf("init", "-input=false", "-no-color", cwd=decoupee)
    assert init_decoupee.returncode == 0, (
        f"`init` a echoue sur la copie.\n{init_decoupee.stderr[-800:]}"
    )

    attendu = _empreinte(_plan_json(origine))
    obtenu = _empreinte(_plan_json(decoupee))

    assert set(obtenu) == set(attendu), (
        f"Le plan porte {sorted(obtenu)}.\nLe monolithe produisait "
        f"{sorted(attendu)}.\n\nUn bloc a ete perdu ou ajoute pendant le "
        "decoupage : deplacer ne doit rien changer."
    )

    for adresse in sorted(attendu):
        assert obtenu[adresse]["actions"] == attendu[adresse]["actions"], (
            f"{adresse} : le plan annonce {obtenu[adresse]['actions']}, le "
            f"monolithe annoncait {attendu[adresse]['actions']}."
        )
        divergents = {
            champ
            for champ in set(attendu[adresse]["after"]) | set(obtenu[adresse]["after"])
            if attendu[adresse]["after"].get(champ) != obtenu[adresse]["after"].get(champ)
        }
        assert not divergents, (
            f"{adresse} : ces valeurs ont change pendant le decoupage : "
            f"{sorted(divergents)}.\n\nAttendu "
            f"{ {c: attendu[adresse]['after'].get(c) for c in divergents} }\n"
            f"Obtenu  { {c: obtenu[adresse]['after'].get(c) for c in divergents} }"
        )


# --------------------------------------------------------------------------
# 3. Le decoupage est reel, prouve par ablation.
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "fichier, ce_qui_doit_casser",
    [
        ("variables.tf", "validate"),
        ("locals.tf", "validate"),
        ("main.tf", "ressources"),
        ("outputs.tf", "sorties"),
    ],
)
def test_chaque_fichier_porte_reellement_son_contenu(
    joue: Path, tmp_path: Path, fichier: str, ce_qui_doit_casser: str
) -> None:
    """Retirer un fichier doit casser quelque chose de precis.

    Mesure du 2026-09-24 : `terraform show -json` n'expose aucune position
    source, donc rien ne dit d'ou vient un bloc. L'ablation, elle, le dit : si
    retirer `variables.tf` ne change rien, les variables ne sont pas dedans.

    Aucun `.tf` n'est ouvert : on observe ce qui casse, pas ce qui est ecrit.
    """
    copie = tmp_path / f"sans-{fichier}"
    shutil.copytree(joue, copie, ignore=shutil.ignore_patterns("*.tfplan", "*.tfstate*"))
    (copie / fichier).unlink()

    if ce_qui_doit_casser == "validate":
        rapport = json.loads(_tf("validate", "-json", cwd=copie).stdout or "{}")
        assert rapport.get("valid") is False, (
            f"Retirer `{fichier}` ne casse rien : `validate` passe toujours.\n\n"
            f"Ce fichier ne porte donc pas ce qu'il devrait. Le decoupage attendu "
            "met chaque nature de bloc dans son fichier."
        )
        return

    plan = _plan_json(copie)
    if ce_qui_doit_casser == "ressources":
        adresses = {c["address"] for c in plan.get("resource_changes", [])}
        assert not adresses, (
            f"Retirer `{fichier}` laisse encore {sorted(adresses)} au plan.\n\n"
            "Les ressources ne sont donc pas toutes dans ce fichier."
        )
    else:
        assert not plan.get("output_changes"), (
            f"Retirer `{fichier}` laisse encore des sorties au plan : "
            f"{sorted(plan.get('output_changes', {}))}.\n\nLes `output` ne sont "
            "donc pas tous dans ce fichier."
        )


def test_un_nom_declare_deux_fois_casse_la_configuration(
    joue: Path, tmp_path: Path
) -> None:
    """Le corollaire du decoupage, et la raison pour laquelle on deplace.

    Le test pose un fichier de trop, constate le refus, le retire, et confirme
    le retour au vert : sans cette seconde moitie, il prouverait seulement que
    quelque chose casse, pas que c'est CE doublon qui cassait.
    """
    _exiger_decoupage_fait(joue)

    copie = tmp_path / "doublon"
    shutil.copytree(joue, copie, ignore=shutil.ignore_patterns("*.tfplan", "*.tfstate*"))

    avant = json.loads(_tf("validate", "-json", cwd=copie).stdout or "{}")
    assert avant.get("valid") is True, (
        f"La configuration ne valide pas avant meme le doublon.\n{avant}"
    )

    intrus = copie / "zz_doublon.tf"
    intrus.write_text(
        'variable "projet" {\n  type    = string\n  default = "en-double"\n}\n',
        encoding="utf-8",
    )
    pendant = json.loads(_tf("validate", "-json", cwd=copie).stdout or "{}")
    assert pendant.get("valid") is False, (
        "Declarer `projet` une seconde fois n'a rien casse.\n\nTerraform devrait "
        "refuser : un nom ne se declare qu'une fois par repertoire, quel que "
        "soit le fichier."
    )

    intrus.unlink()
    apres = json.loads(_tf("validate", "-json", cwd=copie).stdout or "{}")
    assert apres.get("valid") is True, (
        "La configuration ne revient pas au vert une fois le doublon retire : "
        "l'echec venait d'autre chose."
    )


# --------------------------------------------------------------------------
# 4. La precedence, mesuree sur les valeurs effectives.
# --------------------------------------------------------------------------
def test_chaque_variable_prend_la_valeur_de_la_source_qui_gagne(joue: Path) -> None:
    applique = _tf("apply", "-auto-approve", "-input=false", "-no-color",
                   "-var", f"revision={REVISION}")
    assert applique.returncode == 0, (
        f"`terraform apply` a echoue.\n{applique.stderr[-1000:]}"
    )

    proc = _tf("output", "-json")
    proc.check_returncode()
    sorties = json.loads(proc.stdout or "{}")

    for nom, (attendue, pourquoi) in VALEURS_ATTENDUES.items():
        assert nom in sorties, (
            f"La sortie `{nom}` est absente. Presentes : {sorted(sorties)}."
        )
        obtenue = sorties[nom]["value"]
        assert obtenue == attendue, (
            f"`{nom}` vaut {obtenue!r}, attendu {attendue!r}.\n\n{pourquoi}.\n\n"
            "Rappel de l'ordre, du plus faible au plus fort :\n"
            "  default  <  TF_VAR_  <  terraform.tfvars  <  *.auto.tfvars  <  -var"
        )


def test_la_configuration_converge(joue: Path) -> None:
    _exiger_decoupage_fait(joue)

    plan = _tf("plan", "-detailed-exitcode", "-input=false", "-no-color",
               "-var", f"revision={REVISION}")
    assert plan.returncode == 0, (
        f"`plan -detailed-exitcode` rend {plan.returncode}, attendu 0.\n"
        + plan.stdout[-800:]
    )
