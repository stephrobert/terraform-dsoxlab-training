"""Tests fonctionnels du lab « refactorer sans detruire ».

Trois objets existent deja, enregistres aux ANCIENNES adresses. Le code, lui, a
ete refactore. Les tests prouvent que la reconciliation a rattache les objets
EXISTANTS aux nouvelles adresses, sans les recreer, et que le passage dans le
module a bien ete fait en DECLARATIF.

Le discriminant est le champ `previous_address` du plan JSON : Terraform ne
l'ecrit que lorsqu'un bloc `moved` a ete pris en compte. `terraform state mv` ne
le produit jamais. Un apprenant qui reglerait le troisieme deplacement en
imperatif obtiendrait donc les bonnes adresses, mais echouerait ici.

Comme le deplacement est deja applique dans le state final, le test le REJOUE
dans une copie : il y ramene l'objet a son ancienne adresse, replanifie, et
verifie que le bloc `moved` produit a nouveau un `no-op` porteur de
`previous_address`. Le meme mecanisme sert au controle negatif : bloc retire, le
plan repasse en destroy + create.

Faits verifies sur Terraform 1.15.4 (provider random, hors ligne) :
- sans reconciliation, le plan annonce « 3 to add, 0 to change, 3 to destroy » ;
- `state mv` repond `Move "..." to "..."` puis
  `Successfully moved 1 object(s).` ;
- avec le bloc `moved`, le plan annonce
  « 0 to add, 0 to change, 0 to destroy » et la ligne
  `# <ancienne> has moved to <nouvelle>` ;
- le JSON du plan porte alors `previous_address` avec `actions == ["no-op"]` ;
- bloc `moved` retire, le meme plan repasse en `delete` + `create` : c'est le
  « breaking change » que documente HashiCorp.
"""

import json
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, message, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "state-terraform-state-mv"

ADRESSES_ATTENDUES = {
    "random_pet.frontend",
    "random_integer.frontend_port",
    "module.secret.random_string.this",
}
ANCIENNES_ADRESSES = {
    "random_pet.web",
    "random_integer.web_port",
    "random_string.db_secret",
}
REFERENCE = Path("reference") / "etat-initial.tfstate"


def _identifiants_du_state(fichier: Path) -> dict[str, str]:
    """Adresse -> identifiant, lu directement dans un fichier de state."""
    donnees = json.loads(fichier.read_text(encoding="utf-8"))
    trouves: dict[str, str] = {}
    for ressource in donnees.get("resources", []):
        prefixe = ressource.get("module")
        adresse = ".".join(
            partie for partie in (prefixe, ressource["type"], ressource["name"]) if partie
        )
        for instance in ressource.get("instances", []):
            trouves[adresse] = instance["attributes"].get("id")
    return trouves


def _adresses_du_json(cwd: Path) -> dict[str, str]:
    """Adresse -> identifiant, depuis show -json, modules compris."""

    def descendre(module: dict) -> Iterator[dict]:
        yield from module.get("resources", [])
        for enfant in module.get("child_modules", []):
            yield from descendre(enfant)

    racine = show_json(cwd)["values"]["root_module"]
    return {
        r["address"]: r["values"].get("id")
        for r in descendre(racine)
        if r.get("mode") == "managed"
    }


def _plan_json(cwd: Path, nom: str = "controle.tfplan") -> dict:
    """Enregistre un plan et rend son JSON."""
    plan = terraform("plan", "-input=false", "-no-color", f"-out={nom}", cwd=cwd)
    if plan.returncode != 0:
        pytest.fail(message(
            en=f"`terraform plan -out` failed.\n{plan.stderr[-1200:]}",
            fr=f"`terraform plan -out` a échoué.\n{plan.stderr[-1200:]}",
        ))
    montre = terraform("show", "-json", nom, cwd=cwd)
    montre.check_returncode()
    return json.loads(montre.stdout)


def _deplacements(plan: dict) -> list[dict]:
    """Entrees du plan portant un `previous_address` : les vrais deplacements."""
    return [c for c in plan.get("resource_changes", []) if c.get("previous_address")]


@pytest.fixture(scope="module")
def applied() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(
            message(
            en="`terraform init` failed. A leftover `???` in moved.tf?"
            f"\n{init.stderr[-1200:]}",
            fr="`terraform init` a échoué. Un `???` restant dans moved.tf ?"
            f"\n{init.stderr[-1200:]}",
        )
        )
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(
            message(
            en="`terraform apply` failed. Is the reconciliation finished?"
            f"\n{app.stderr[-1500:]}",
            fr="`terraform apply` a échoué. La réconciliation est-elle terminée ?"
            f"\n{app.stderr[-1500:]}",
        )
        )
    yield WORKDIR
    terraform("destroy", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)


# --------------------------------------------------------------------------
# 1. Les objets sont aux nouvelles adresses, et nulle part ailleurs
# --------------------------------------------------------------------------

def test_les_objets_sont_aux_nouvelles_adresses(applied: Path) -> None:
    presentes = set(_adresses_du_json(applied))
    manquantes = ADRESSES_ATTENDUES - presentes
    assert not manquantes, message(
        en=f"These addresses are missing from the state: {sorted(manquantes)}. "
        f"Addresses found: {sorted(presentes)}",
        fr=f"Ces adresses manquent au state : {sorted(manquantes)}. "
        f"Adresses trouvées : {sorted(presentes)}",
    )
    restantes = ANCIENNES_ADRESSES & presentes
    assert not restantes, message(
        en=f"These old addresses remain: {sorted(restantes)}. The "
        "reconciliation is incomplete.",
        fr=f"Ces anciennes adresses subsistent : {sorted(restantes)}. La "
        "réconciliation est incomplète.",
    )
    assert presentes == ADRESSES_ATTENDUES, message(
        en=f"The state carries {sorted(presentes)}, exactly "
        f"{sorted(ADRESSES_ATTENDUES)} expected.",
        fr=f"Le state porte {sorted(presentes)}, attendu exactement "
        f"{sorted(ADRESSES_ATTENDUES)}.",
    )


# --------------------------------------------------------------------------
# 2. Ce sont les MEMES objets : rien n'a ete recree
# --------------------------------------------------------------------------

def test_les_valeurs_dorigine_ont_survecu(applied: Path) -> None:
    reference = applied / REFERENCE
    assert reference.is_file(), message(
        en=f"{REFERENCE} is missing: it is the reference for the starting values, it "
        "must not be deleted.",
        fr=f"{REFERENCE} est absent : c'est la référence des valeurs de départ, il "
        "ne faut pas le supprimer.",
    )
    avant = _identifiants_du_state(reference)
    apres = _adresses_du_json(applied)

    assert set(avant) == ANCIENNES_ADRESSES, message(
        en=f"The reference state carries {sorted(avant)}, the three old "
        "addresses were expected: it was modified.",
        fr=f"L'état de référence porte {sorted(avant)}, attendu les trois anciennes "
        "adresses : il a été modifié.",
    )
    perdus = set(avant.values()) - set(apres.values())
    assert not perdus, message(
        en=f"These original identifiers have disappeared: {sorted(perdus)}. The objects "
        "were therefore DESTROYED and then RECREATED instead of being moved: "
        "random_pet, random_integer and random_string draw fresh values at "
        f"every creation.\n  before: {avant}\n  after : {apres}",
        fr=f"Ces identifiants d'origine ont disparu : {sorted(perdus)}. Les objets "
        "ont donc été DÉTRUITS puis RECRÉÉS au lieu d'être déplacés : "
        "random_pet, random_integer et random_string tirent des valeurs neuves à "
        f"chaque création.\n  avant : {avant}\n  après : {apres}",
    )


# --------------------------------------------------------------------------
# 3. Code et state convergent
# --------------------------------------------------------------------------

def test_plus_aucun_changement_en_attente(applied: Path) -> None:
    plan = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color",
                     cwd=applied)
    assert plan.returncode == 0, message(
        en=f"plan -detailed-exitcode returns {plan.returncode}, expected 0. Code 2 "
        "signals pending changes, hence an incomplete "
        f"reconciliation.\n{plan.stdout[-1200:]}",
        fr=f"plan -detailed-exitcode rend {plan.returncode}, attendu 0. Le code 2 "
        "signale des changements en attente, donc une réconciliation "
        f"incomplète.\n{plan.stdout[-1200:]}",
    )


# --------------------------------------------------------------------------
# 4. Le troisieme deplacement a ete fait en DECLARATIF
# --------------------------------------------------------------------------

def test_le_bloc_moved_est_toujours_la_et_agit(applied: Path, tmp_path: Path) -> None:
    """Le rejeu : on ramene l'objet a son ancienne adresse, on replanifie.

    Terraform n'ecrit `previous_address` que si un bloc `moved` a ete pris en
    compte. C'est ce qui distingue la methode declarative de `state mv`.
    """
    copie = tmp_path / "rejeu"
    shutil.copytree(applied, copie)

    retour = terraform(
        "state", "mv", "-no-color",
        "module.secret.random_string.this", "random_string.db_secret", cwd=copie,
    )
    if retour.returncode != 0:
        pytest.fail(
            message(
            en="Cannot bring the object back to its old address for the replay."
            f"\n{retour.stderr[-800:]}",
            fr="Impossible de ramener l'objet à son ancienne adresse pour le rejeu."
            f"\n{retour.stderr[-800:]}",
        )
        )

    deplacements = _deplacements(_plan_json(copie))
    assert deplacements, message(
        en="The plan carries NO `previous_address`: the `moved` block is absent "
        "from the code, or it does not name the right pair of addresses. The two "
        "renames at the root are done imperatively, but the move into "
        "the module must stay declarative.",
        fr="Le plan ne porte AUCUN `previous_address` : le bloc `moved` est absent "
        "du code, ou il ne désigne pas le bon couple d'adresses. Les deux "
        "renommages à la racine se font en impératif, mais le passage dans le "
        "module doit rester déclaratif.",
    )
    cible = [d for d in deplacements
             if d["address"] == "module.secret.random_string.this"]
    assert cible, message(
        en=f"previous_address found, but on {[d['address'] for d in deplacements]} "
        "instead of module.secret.random_string.this.",
        fr=f"previous_address trouvé, mais sur {[d['address'] for d in deplacements]} "
        "au lieu de module.secret.random_string.this.",
    )
    entree = cible[0]
    assert entree["previous_address"] == "random_string.db_secret", message(
        en=f"previous_address is {entree['previous_address']!r}, expected "
        "'random_string.db_secret'.",
        fr=f"previous_address vaut {entree['previous_address']!r}, attendu "
        "'random_string.db_secret'.",
    )
    assert entree["change"]["actions"] == ["no-op"], message(
        en=f"actions is {entree['change']['actions']}, expected ['no-op']: a "
        "move destroys and creates nothing.",
        fr=f"actions vaut {entree['change']['actions']}, attendu ['no-op'] : un "
        "déplacement ne détruit ni ne crée rien.",
    )


def test_retirer_le_bloc_moved_casse_le_deplacement(applied: Path, tmp_path: Path) -> None:
    """Controle negatif : c'est le « breaking change » documente par HashiCorp."""
    copie = tmp_path / "sans-moved"
    shutil.copytree(applied, copie)
    terraform("state", "mv", "-no-color",
              "module.secret.random_string.this", "random_string.db_secret", cwd=copie)

    moved = copie / "moved.tf"
    assert moved.is_file(), message(
        en="moved.tf is missing from the workdir: the `moved` block must stay in the "
        "code after the apply, and removing it is a breaking change.",
        fr="moved.tf est absent du workdir : le bloc `moved` doit rester dans le "
        "code après l'apply, son retrait est un changement cassant.",
    )
    moved.unlink()

    plan = _plan_json(copie, "sans-moved.tfplan")
    assert not _deplacements(plan), message(
        en="Without the `moved` block, the plan should carry no "
        "`previous_address`.",
        fr="Sans le bloc `moved`, le plan ne devrait porter aucun "
        "`previous_address`.",
    )
    actions = {
        c["address"]: c["change"]["actions"]
        for c in plan.get("resource_changes", [])
        if c["change"]["actions"] != ["no-op"]
    }
    assert actions.get("random_string.db_secret") == ["delete"], message(
        en=f"Without the block, the old address should be destroyed. Actions: {actions}",
        fr=f"Sans le bloc, l'ancienne adresse devrait être détruite. Actions : {actions}",
    )
    assert actions.get("module.secret.random_string.this") == ["create"], message(
        en=f"Without the block, the new address should be created. Actions: {actions}",
        fr=f"Sans le bloc, la nouvelle adresse devrait être créée. Actions : {actions}",
    )
