"""Tests fonctionnels du lab « restaurer un state ampute ».

Le state ment, l'infrastructure est intacte. Toute la difficulte est de choisir
la bonne sauvegarde parmi trois candidates, puis de la reinjecter SANS que
Terraform ne recree quoi que ce soit. Les tests interrogent donc le state
structure et le systeme de fichiers, jamais un `.tf` ni une sortie humaine.

Faits verifies sur Terraform 1.15.4 (provider local, hors ligne) :
- `terraform state push` refuse un serial plus ancien : `Failed to write state:
  cannot import state with serial 4 over newer state with serial 5` ;
- il refuse aussi un lineage etranger : `cannot import state with lineage "..."
  over unrelated state with lineage "..."` ;
- `-force` passe outre les DEUX garde-fous, sans confirmation ;
- apres un `push -force`, le state porte le serial de la SAUVEGARDE incremente
  de un, et non celui du state remplace : un serial 1 pousse sur un serial 15
  donne 2, mesure. C'est ce qui distingue un vrai `push` d'une copie de fichier
  posee par-dessus `terraform.tfstate`, laquelle laisserait le serial de la
  sauvegarde inchange ;
- restaurer la sauvegarde perimee laisse un ecart reel : le plan annonce
  `local_file.deux must be replaced` et `plan -detailed-exitcode` rend 2.

Reecrit le 2026-09-23. TROIS tests etaient VERTS AVANT LE TRAVAIL et
accordaient 43/100 a un candidat qui n'avait rien fait :

- « le state porte le lineage du projet » : le state AMPUTE porte deja le bon
  lineage. Il est incomplet, pas etranger ;
- « les artefacts n'ont pas ete recrees » : ils sont intacts au depart, et c'est
  precisement la premisse du lab, pas son resultat ;
- « une sauvegarde etrangere est refusee » : ce test l'avouait dans son propre
  commentaire, il verifiait un comportement de Terraform.

Aucune de ces trois moities n'a ete supprimee. Chacune est fusionnee la ou elle
ne peut etre atteinte qu'apres le travail, et ou elle distingue une restauration
reussie d'une reparation en trompe-l'oeil.
"""

import json
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "state-backup-restore-state"

ADRESSES = {"local_file.un", "local_file.deux", "local_file.trois"}
ARTEFACTS = {
    "un.txt": "artefact un\n",
    "deux.txt": "artefact deux\n",
    "trois.txt": "artefact trois\n",
}
REFERENCE = "reference/etat-initial.json"
AVANT = "sauvegardes/avant-restauration.json"
# Tolerance entre la date d'un artefact et celle de la reference, toutes deux
# posees par la copie des fixtures. Un fichier reecrit par Terraform date, lui,
# de la session en cours.
MARGE_SECONDES = 120


def _charger(chemin: Path) -> dict:
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erreur:
        pytest.fail(f"{chemin.name} n'est pas un JSON valide : {erreur}")


def _state_courant(cwd: Path) -> dict:
    pull = terraform("state", "pull", cwd=cwd)
    pull.check_returncode()
    return json.loads(pull.stdout)


def _ressources_gerees(document: dict) -> set[str]:
    adresses = set()
    for ressource in document.get("resources", []):
        if ressource.get("mode") != "managed":
            continue
        adresses.add(f"{ressource['type']}.{ressource['name']}")
    return adresses


def _sauvegarde_restaurable(cwd: Path, lineage: str) -> dict:
    """La candidate au bon lineage et au serial le plus eleve."""
    candidates = [
        _charger(chemin)
        for chemin in sorted((cwd / "sauvegardes").glob("sauvegarde-*.json"))
    ]
    valides = [d for d in candidates if d.get("lineage") == lineage]
    if not valides:
        pytest.fail(
            "Aucune sauvegarde ne porte le lineage du projet. Les fixtures du "
            "lab ont ete modifiees."
        )
    return max(valides, key=lambda d: d["serial"])


def _exiger_restauration_faite(cwd: Path) -> dict:
    """Garde commune : sans restauration, les controles suivants ne disent rien."""
    courant = _state_courant(cwd)
    gerees = _ressources_gerees(courant)
    assert gerees == ADRESSES, (
        f"Le state decrit {sorted(gerees)}, attendu {sorted(ADRESSES)}. La "
        "restauration n'a pas eu lieu : ce controle ne peut se prononcer "
        "qu'apres."
    )
    return courant


@pytest.fixture(scope="module")
def restaure() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(f"`terraform init` a echoue.\n{init.stderr[-1200:]}")
    yield WORKDIR


# --------------------------------------------------------------------------
# 1. Le reflexe prealable : photographier l'etat endommage
# --------------------------------------------------------------------------

def test_l_etat_endommage_a_ete_sauvegarde_avant_toute_ecriture(restaure: Path) -> None:
    chemin = restaure / AVANT
    assert chemin.is_file(), (
        f"{AVANT} est absent. Avant de pousser quoi que ce soit, on photographie "
        f"l'etat endommage : `terraform state pull > {AVANT}`. Un `push` ne se "
        "rejoue pas."
    )
    photo = _charger(chemin)
    attendu = _charger(restaure / REFERENCE)
    assert photo.get("lineage") == attendu["lineage"], (
        "La photo ne porte pas le lineage du projet : elle ne vient pas de ce "
        "state."
    )
    gerees = _ressources_gerees(photo)
    assert gerees == {"local_file.un", "local_file.deux"}, (
        f"La photo decrit {sorted(gerees)}, alors que l'etat endommage portait "
        "exactement local_file.un et local_file.deux. Un fichier pris APRES la "
        "restauration ne prouve rien."
    )


# --------------------------------------------------------------------------
# 2. Les trois ressources sont revenues, ET elles viennent du bon projet
# --------------------------------------------------------------------------

def test_les_trois_ressources_sont_gerees_et_le_lineage_est_celui_du_projet(
    restaure: Path,
) -> None:
    """La verification du lineage vit ici, et pas dans un test a elle.

    Seule, elle etait vraie avant le travail : le state AMPUTE portait deja le
    bon lineage, puisqu'il est incomplet et non etranger. Associee au retour des
    trois ressources, elle devient decisive : elle distingue une restauration
    depuis la bonne sauvegarde d'une restauration depuis celle d'un AUTRE
    projet, qui aurait elle aussi rendu trois ressources au state.
    """
    courant = _exiger_restauration_faite(restaure)
    attendu = _charger(restaure / REFERENCE)["lineage"]
    assert courant["lineage"] == attendu, (
        f"Le state courant porte le lineage {courant['lineage']!r}, attendu "
        f"{attendu!r}. Une sauvegarde venue d'un autre projet a ete poussee : "
        "Terraform le refuse par `cannot import state with lineage ... over "
        "unrelated state`, et `-force` passe outre sans rien demander."
    )


# --------------------------------------------------------------------------
# 3. La restauration est passee par un push, et le garde-fou existait bien
# --------------------------------------------------------------------------

def test_la_restauration_est_passee_par_state_push_et_non_par_une_copie(
    restaure: Path, tmp_path: Path
) -> None:
    """Le garde-fou du lineage est eprouve ici, une fois la restauration faite.

    Seul, ce controle ne notait pas le travail : il verifiait un comportement de
    Terraform, vrai avant comme apres. Place apres la preuve du `push`, il
    etablit ce qui compte vraiment : le garde-fou etait la, il a bien fallu
    choisir la bonne sauvegarde pour passer.
    """
    attendu = _charger(restaure / REFERENCE)
    sauvegarde = _sauvegarde_restaurable(restaure, attendu["lineage"])
    courant = _exiger_restauration_faite(restaure)

    assert courant["serial"] > sauvegarde["serial"], (
        f"Le serial courant vaut {courant['serial']}, celui de la sauvegarde "
        f"restaurable {sauvegarde['serial']}. Un `terraform state push` repart "
        "du serial de la sauvegarde et l'incremente : le state restaure porte "
        "donc toujours un serial SUPERIEUR. Un serial egal signe une copie de "
        "fichier posee par-dessus `terraform.tfstate`, ce qui contourne tout "
        "garde-fou."
    )

    etrangeres = [
        chemin
        for chemin in sorted((restaure / "sauvegardes").glob("sauvegarde-*.json"))
        if _charger(chemin).get("lineage") != attendu["lineage"]
    ]
    if not etrangeres:
        pytest.fail("Aucune sauvegarde au lineage etranger : fixtures modifiees.")

    copie = tmp_path / "garde-fou"
    shutil.copytree(restaure, copie)
    pousse = terraform(
        "state", "push", str(etrangeres[0].relative_to(restaure)), cwd=copie
    )
    assert pousse.returncode != 0, (
        "Pousser une sauvegarde au lineage etranger devrait echouer. Si ce "
        "controle passe, Terraform a change et le lab doit etre revu."
    )
    assert "unrelated state" in pousse.stderr, (
        "Le refus attendu mentionne `over unrelated state`. Releve :\n"
        f"{pousse.stderr[-600:]}"
    )


# --------------------------------------------------------------------------
# 4. Les deux cotes : le state converge, ET rien n'a ete reecrit pour cela
# --------------------------------------------------------------------------

def test_le_code_converge_sans_que_terraform_ait_rien_recree(restaure: Path) -> None:
    """L'integrite des artefacts vit ici, et c'est le coeur du lab.

    Seule, elle etait vraie avant le travail : les artefacts sont intacts au
    depart, c'est la PREMISSE du lab et non son resultat. Associee a la
    convergence, elle separe les deux facons d'obtenir un plan vide :

    - reparer le state, ce qui est demande ;
    - lancer un `apply` sur le state ampute, qui converge lui aussi... en
      RECREANT le fichier manquant. L'infrastructure etait pourtant intacte, et
      sur un vrai systeme cette recreation est une destruction.
    """
    plan = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color",
                     cwd=restaure)
    assert plan.returncode == 0, (
        f"plan -detailed-exitcode rend {plan.returncode}, attendu 0. Un code 2 "
        "signale une sauvegarde PERIMEE : son contenu ne correspond plus au "
        "fichier reel, et Terraform propose un remplacement.\n"
        f"{plan.stdout[-900:]}"
    )

    repere = (restaure / REFERENCE).stat().st_mtime
    manquants, contenus, recrees = [], [], []
    for nom, attendu in ARTEFACTS.items():
        chemin = restaure / "artefacts" / nom
        if not chemin.is_file():
            manquants.append(nom)
            continue
        if chemin.read_text(encoding="utf-8") != attendu:
            contenus.append(nom)
        if chemin.stat().st_mtime > repere + MARGE_SECONDES:
            recrees.append(nom)
    assert not manquants, f"Ces artefacts ont disparu : {sorted(manquants)}."
    assert not contenus, (
        f"Le contenu de ces artefacts a change : {sorted(contenus)}. La "
        "restauration ne doit rien reecrire."
    )
    assert not recrees, (
        f"Ces artefacts ont ete RECREES par Terraform : {sorted(recrees)}. Leur "
        "date de modification est posterieure a la mise en place du lab.\n\n"
        "Le plan est vide, mais il l'est pour la mauvaise raison : un `apply` "
        "sur le state ampute recree le fichier manquant au lieu de reparer le "
        "state. L'infrastructure etait intacte, et sur un vrai systeme cette "
        "recreation est une destruction."
    )
