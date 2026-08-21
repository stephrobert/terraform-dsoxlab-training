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
# 2. La bonne sauvegarde a ete choisie
# --------------------------------------------------------------------------

def test_le_state_porte_le_lineage_du_projet(restaure: Path) -> None:
    attendu = _charger(restaure / REFERENCE)["lineage"]
    courant = _state_courant(restaure)["lineage"]
    assert courant == attendu, (
        f"Le state courant porte le lineage {courant!r}, attendu {attendu!r}. "
        "Une sauvegarde venue d'un autre projet a ete poussee : Terraform le "
        "refuse par `cannot import state with lineage ... over unrelated "
        "state`, et `-force` passe outre sans rien demander."
    )


def test_les_trois_ressources_sont_de_nouveau_gerees(restaure: Path) -> None:
    gerees = _ressources_gerees(_state_courant(restaure))
    assert gerees == ADRESSES, (
        f"Le state decrit {sorted(gerees)}, attendu {sorted(ADRESSES)}."
    )


# --------------------------------------------------------------------------
# 3. La restauration est passee par un push, pas par une copie
# --------------------------------------------------------------------------

def test_la_restauration_est_passee_par_state_push(restaure: Path) -> None:
    attendu = _charger(restaure / REFERENCE)
    sauvegarde = _sauvegarde_restaurable(restaure, attendu["lineage"])
    courant = _state_courant(restaure)
    assert _ressources_gerees(courant) == ADRESSES, (
        "La restauration n'a pas eu lieu : le state ne decrit pas encore les "
        f"trois ressources, mais {sorted(_ressources_gerees(courant))}. Ce "
        "controle ne peut se prononcer qu'apres."
    )
    assert courant["serial"] > sauvegarde["serial"], (
        f"Le serial courant vaut {courant['serial']}, celui de la sauvegarde "
        f"restaurable {sauvegarde['serial']}. Un `terraform state push` repart "
        "du serial de la sauvegarde et l'incremente : le state restaure porte "
        "donc toujours un serial SUPERIEUR. Un serial egal signe une copie de "
        "fichier posee par-dessus `terraform.tfstate`, ce qui contourne tout "
        "garde-fou."
    )


# --------------------------------------------------------------------------
# 4. Le code et le state convergent
# --------------------------------------------------------------------------

def test_plus_aucun_changement_en_attente(restaure: Path) -> None:
    plan = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color",
                     cwd=restaure)
    assert plan.returncode == 0, (
        f"plan -detailed-exitcode rend {plan.returncode}, attendu 0. Un code 2 "
        "signale une sauvegarde PERIMEE : son contenu ne correspond plus au "
        "fichier reel, et Terraform propose un remplacement.\n"
        f"{plan.stdout[-900:]}"
    )


# --------------------------------------------------------------------------
# 5. L'infrastructure n'a pas ete touchee
# --------------------------------------------------------------------------

def test_les_artefacts_n_ont_pas_ete_recrees(restaure: Path) -> None:
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
        "date de modification est posterieure a la mise en place du lab. Un "
        "`apply` sur le state ampute recree le fichier manquant au lieu de "
        "reparer le state : l'infrastructure etait pourtant intacte."
    )


# --------------------------------------------------------------------------
# 6. Le garde-fou du lineage, prouve par execution
# --------------------------------------------------------------------------

def test_une_sauvegarde_etrangere_est_refusee(restaure: Path, tmp_path: Path) -> None:
    """Ce test ne note pas le travail : il verifie que le garde-fou existe."""
    attendu = _charger(restaure / REFERENCE)["lineage"]
    etrangeres = [
        chemin
        for chemin in sorted((restaure / "sauvegardes").glob("sauvegarde-*.json"))
        if _charger(chemin).get("lineage") != attendu
    ]
    if not etrangeres:
        pytest.fail("Aucune sauvegarde au lineage etranger : fixtures modifiees.")

    copie = tmp_path / "garde-fou"
    shutil.copytree(restaure, copie)
    pousse = terraform(
        "state", "push", str(etrangeres[0].relative_to(restaure)), cwd=copie
    )
    assert pousse.returncode != 0, (
        "Pousser une sauvegarde au lineage etranger devrait echouer. Si ce test "
        "passe, Terraform a change et le lab doit etre revu."
    )
    assert "unrelated state" in pousse.stderr, (
        "Le refus attendu mentionne `over unrelated state`. Releve :\n"
        f"{pousse.stderr[-600:]}"
    )
