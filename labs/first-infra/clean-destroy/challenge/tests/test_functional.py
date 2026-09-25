"""Tests fonctionnels du lab « detruire proprement, et ce que cela recouvre ».

Detruire n'est pas une seule operation. Ce lab en fait constater quatre, qui ne
se ressemblent pas :

  - le `destroy` global, qu'un garde-fou peut REFUSER ;
  - le `destroy -target`, qui ne retire que ce qu'on nomme ;
  - le retrait d'une ressource DU CODE, qui la detruit au prochain apply sans
    qu'aucun `destroy` ne soit lance ;
  - le `destroy` complet, qui vide le state SANS supprimer son fichier.

Aucun cloud, aucune VM, aucun appel reseau : tout est deterministe et rejouable.
Aucun test ne relit les `.tf` de l'apprenant, et aucun ne parse une sortie
humaine : seuls des codes de retour et du JSON.

## Un piege mesure, et qui surprend

`terraform plan -destroy` sur une configuration portant `prevent_destroy` sort
en rc=1 ET ECRIT QUAND MEME le fichier demande par `-out`. Ce plan est
INCOMPLET : trois ressources sur quatre, la ressource protegee entrainant ses
dependances hors du plan.

Un fichier de plan qui existe alors que la commande a echoue est exactement le
genre de chose dont personne ne se mefie. C'est pourquoi le lab demande
d'exporter le plan APRES avoir leve la protection, et pourquoi le test compte
les adresses plutot que de se contenter de l'existence du fichier.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from conftest import exiger_workdir, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "first-infra-clean-destroy"

ARTEFACTS = "artefacts"
RC_PREVENT = f"{ARTEFACTS}/rc-prevent-destroy.txt"
PLAN_DESTROY = f"{ARTEFACTS}/plan-destroy.json"

SUFFIXE = "random_pet.suffixe"
INVENTAIRE = "local_file.inventaire"
EMPREINTE = "null_resource.empreinte"
TEMOIN = "random_pet.temoin"
TOUTES = {SUFFIXE, INVENTAIRE, EMPREINTE, TEMOIN}


def _tf(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["terraform", *args], cwd=WORKDIR, capture_output=True, text=True, check=False
    )


@pytest.fixture(scope="module")
def joue() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    return WORKDIR


def _charger(nom: str) -> dict:
    chemin = WORKDIR / nom
    assert chemin.is_file(), (
        f"`{nom}` est absent. Le lab demande de le produire : c'est la trace de "
        "ce que vous avez constate, et la seule que les tests puissent lire."
    )
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erreur:
        pytest.fail(f"`{nom}` n'est pas du JSON valide : {erreur}")


def _gerees() -> set[str]:
    proc = _tf("show", "-json")
    proc.check_returncode()
    racine = json.loads(proc.stdout).get("values", {}).get("root_module", {})
    return {r["address"] for r in racine.get("resources", []) if r["mode"] == "managed"}


# --------------------------------------------------------------------------
# 1. Le garde-fou a REFUSE, et rien n'a ete detruit.
# --------------------------------------------------------------------------
def test_le_destroy_global_a_ete_refuse(joue: Path) -> None:
    """Le code de retour, et non le message.

    Le texte d'une erreur Terraform change avec les versions ; un code de
    retour non nul, non. C'est la seule preuve stable qu'un `destroy` a ete
    refuse plutot qu'accepte.
    """
    chemin = joue / RC_PREVENT
    assert chemin.is_file(), (
        f"`{RC_PREVENT}` est absent. Lancez le `destroy` global et conservez son "
        "code de retour : c'est la preuve que le garde-fou a mordu."
    )
    brut = chemin.read_text(encoding="utf-8").strip()
    assert brut.isdigit(), f"`{RC_PREVENT}` contient {brut!r}, un code attendu."
    assert int(brut) != 0, (
        f"Le code de retour releve vaut {brut}, donc le `destroy` a REUSSI.\n\n"
        "`prevent_destroy` devait le faire echouer. Ce n'est pas un verrou sur "
        "l'objet : c'est un refus de PLANIFIER, et il porte sur tout plan qui "
        "emporterait la ressource, y compris un destroy global lance sans y "
        "penser."
    )


# --------------------------------------------------------------------------
# 2. Le plan de destruction porte les QUATRE adresses.
# --------------------------------------------------------------------------
def test_le_plan_de_destruction_annonce_les_quatre_suppressions(joue: Path) -> None:
    """Compter les adresses, et non se contenter du fichier.

    Mesure : `plan -destroy` avec `prevent_destroy` sort en rc=1 et ECRIT QUAND
    MEME le fichier demande par `-out`. Ce plan ne porte que trois ressources
    sur quatre. Un test qui verifierait seulement l'existence du fichier
    passerait sur ce plan mutile.
    """
    plan = _charger(PLAN_DESTROY)
    actions = {
        c["address"]: c["change"]["actions"] for c in plan.get("resource_changes", [])
    }
    assert set(actions) == TOUTES, (
        f"Le plan porte {sorted(actions)}.\nAttendu les quatre : {sorted(TOUTES)}."
        "\n\nUn plan pris AVANT la levee de `prevent_destroy` est incomplet : "
        "il sort en erreur, ecrit quand meme un fichier, et omet la ressource "
        "protegee ainsi que ce dont elle depend."
    )
    for adresse, verbe in actions.items():
        assert verbe == ["delete"], (
            f"{adresse} porte l'action {verbe}, attendu `['delete']` dans un "
            "plan de destruction."
        )


# --------------------------------------------------------------------------
# 3. Le destroy CIBLE n'a retire que ce qu'on lui a nomme.
# --------------------------------------------------------------------------
def test_le_destroy_cible_n_a_retire_que_la_ressource_nommee(joue: Path) -> None:
    """Ce qui distingue `-target` d'un destroy lance dans l'urgence.

    Le state final est vide, donc on ne peut pas l'observer directement : c'est
    le PLAN DE DESTRUCTION, pris quand les quatre ressources vivaient encore,
    qui atteste que le ciblage avait quelque chose a epargner.
    """
    plan = _charger(PLAN_DESTROY)
    presentes = {c["address"] for c in plan.get("resource_changes", [])}
    assert EMPREINTE in presentes, (
        f"`{EMPREINTE}` n'apparait pas dans le plan de destruction : elle "
        "n'existait donc plus au moment ou il a ete pris, et le ciblage a eu "
        "lieu trop tot."
    )
    autres = presentes - {EMPREINTE}
    assert autres == TOUTES - {EMPREINTE}, (
        f"Les trois autres ressources devraient figurer au plan, il porte "
        f"{sorted(autres)}.\n\nUn `destroy -target` ne retire QUE ce qu'on "
        "nomme : les trois autres devaient rester gerees."
    )


# --------------------------------------------------------------------------
# 4. Le state est vide, et son FICHIER existe toujours.
# --------------------------------------------------------------------------
def test_le_state_est_vide_mais_son_fichier_subsiste(joue: Path) -> None:
    """Deux choses que l'on confond, et la seconde coute cher.

    Un `destroy` complet vide le state de ses ressources. Il ne supprime PAS le
    fichier, et c'est voulu : le fichier porte le `lineage` du projet, son
    `serial`, et sa disparition ferait repartir Terraform de zero. Beaucoup le
    suppriment par reflexe « pour faire propre ».
    """
    restantes = _gerees()
    assert not restantes, (
        f"Le state porte encore {sorted(restantes)}. Le `destroy` complet n'a "
        "pas eu lieu, ou il a echoue."
    )

    fichier = joue / "terraform.tfstate"
    assert fichier.is_file(), (
        "`terraform.tfstate` a disparu du disque.\n\nUn `destroy` vide le state, "
        "il ne supprime pas son fichier. Celui-ci porte le `lineage` du projet "
        "et son `serial` : le supprimer fait repartir Terraform de zero, et lui "
        "fait perdre le lien avec tout ce qui aurait survecu."
    )

    contenu = json.loads(fichier.read_text(encoding="utf-8"))
    assert contenu.get("lineage"), (
        "Le fichier de state ne porte plus de `lineage` : il a ete recree, pas "
        "vide."
    )


# --------------------------------------------------------------------------
# 5. Les deux cotes : plus rien a detruire, et plus rien sur le disque.
# --------------------------------------------------------------------------
def test_plus_rien_a_faire_et_aucun_artefact_de_terraform_ne_subsiste(
    joue: Path,
) -> None:
    """La convergence seule serait vraie d'un repertoire vide.

    Accolee a la disparition des fichiers produits, elle prouve que le cycle
    est alle jusqu'au bout : le state dit qu'il n'y a plus rien, ET le disque
    le confirme.

    Les artefacts que le lab demande de produire, eux, doivent SURVIVRE : ce
    sont des traces de constatation, pas des ressources.
    """
    # Le plan annonce des CREATIONS, et c'est normal : la configuration decrit
    # encore des ressources que le `destroy` vient d'emporter. Attendre un plan
    # vide serait une erreur, et c'en etait une : ce test exigeait un code 0 et
    # recalait une solution juste.
    #
    # Ce qui compte est qu'il n'annonce plus AUCUNE destruction : s'il en
    # restait une, quelque chose aurait survecu au `destroy`.
    plan = _tf("plan", "-input=false", "-no-color", "-out=verification.tfplan")
    assert plan.returncode == 0, f"Le plan a echoue :\n{plan.stderr[-800:]}"

    montre = _tf("show", "-json", "verification.tfplan")
    montre.check_returncode()
    restent_a_detruire = [
        c["address"]
        for c in json.loads(montre.stdout).get("resource_changes", [])
        if "delete" in c["change"]["actions"]
    ]
    assert not restent_a_detruire, (
        f"Le plan annonce encore la destruction de {restent_a_detruire}.\n\n"
        "Ces ressources ont survecu au `destroy` complet : elles sont toujours "
        "dans le state."
    )

    inventaires = list(joue.glob("inventaire-*.txt"))
    assert not inventaires, (
        f"Ces fichiers ont survecu au `destroy` : {[f.name for f in inventaires]}."
        "\n\nTerraform les gerait : leur disparition fait partie de la "
        "destruction. S'ils sont la, le `local_file` n'a jamais ete detruit."
    )

    for artefact in (RC_PREVENT, PLAN_DESTROY):
        assert (joue / artefact).is_file(), (
            f"`{artefact}` a disparu.\n\nLes artefacts sont des traces de ce que "
            "vous avez constate, pas des ressources : ils doivent survivre au "
            "`destroy`."
        )
