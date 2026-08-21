"""Tests fonctionnels du lab « l'adresse est l'identite dans le state ».

Le test ne fait confiance a rien : il reconstruit la table
(adresse -> id, mode) depuis `terraform show -json`, en descendant recursivement
les `child_modules`, puis resout LUI MEME chaque identifiant publie vers
l'adresse de l'instance qui le porte, et compare aux reponses de l'apprenant.
Aucune adresse n'est ecrite en dur cote resultat attendu.

Principe : on n'ouvre jamais un `.tf`, et on ne parse aucune sortie humaine.
Seuls comptent `show -json`, `output -json` et des codes de retour.

Faits verifies sur Terraform 1.15.4 (local + random, hors ligne) :
- une adresse de ressource SANS index rend TOUTES ses instances
  (`state list random_pet.worker` -> les 6), ce n'est pas un filtre unitaire ;
- une adresse de MODULE est un filtre valide (`state list module.stockage` ->
  les 7 entrees du module, code 0) ;
- la sortie est triee par PROFONDEUR DE MODULE puis alphabetiquement : les
  entrees de la racine sortent avant `module.stockage.*` ;
- quatre diagnostics distincts, tous en code 1 : `Unknown resource`,
  `Unknown resource instance`, `Unknown module`, `Invalid address` ;
- `-id` sans correspondance ne produit AUCUNE erreur : sortie vide, code 0 ;
- l'adresse d'une data source DANS un module est
  `module.stockage.data.local_file.relecture` : elle ne commence pas par
  « data », ce qui fait mentir `state list | grep -v ^data | wc -l` (25 au lieu
  de 24 sur ce lab).
"""

from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, output_json, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "state-terraform-state-list"


def _instances(cwd: Path) -> list[dict]:
    """Toutes les instances du state, racine ET modules enfants."""

    def descendre(module: dict) -> Iterator[dict]:
        yield from module.get("resources", [])
        for enfant in module.get("child_modules", []):
            yield from descendre(enfant)

    return list(descendre(show_json(cwd)["values"]["root_module"]))


def _adresse_portant(instances: list[dict], identifiant: str, famille: str) -> str | None:
    """Adresse de l'instance de `famille` dont l'attribut id vaut `identifiant`."""
    for inst in instances:
        if inst["address"].startswith(famille) and inst["values"].get("id") == identifiant:
            return inst["address"]
    return None


@pytest.fixture(scope="module")
def applied() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(
            "`terraform init` a echoue. Un `???` restant dans "
            f"reponses.auto.tfvars ?\n{init.stderr[-1200:]}"
        )
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(
            "`terraform apply` a echoue. Les cinq reponses doivent etre des "
            "valeurs valides (quatre chaines et un nombre)."
            f"\n{app.stderr[-1500:]}"
        )
    yield WORKDIR
    terraform("destroy", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)


@pytest.fixture(scope="module")
def verite(applied: Path) -> dict:
    """La table de verite, reconstruite depuis le JSON du state."""
    instances = _instances(applied)
    sorties = {nom: bloc["value"] for nom, bloc in output_json(applied).items()}
    return {
        "cwd": applied,
        "instances": instances,
        "sorties": sorties,
        "managees": [i for i in instances if i.get("mode") == "managed"],
        "data": [i for i in instances if i.get("mode") == "data"],
    }


def _reponse(verite: dict, nom: str) -> object:
    sorties = verite["sorties"]
    if nom not in sorties:
        pytest.fail(f"L'output `{nom}` est absent : reponses.auto.tfvars est incomplet.")
    return sorties[nom]


# --------------------------------------------------------------------------
# 1. Le projet est applique, avec les trois familles et le module
# --------------------------------------------------------------------------

def test_les_trois_familles_sont_au_state(verite: dict) -> None:
    adresses = {i["address"] for i in verite["instances"]}
    workers = {a for a in adresses if a.startswith("random_pet.worker[")}
    services = {a for a in adresses if a.startswith("random_pet.service[")}
    archives = {a for a in adresses if a.startswith("module.stockage.random_pet.archive[")}

    assert len(workers) == 6, f"{len(workers)} instances de worker, attendu 6."
    assert len(services) == 8, f"{len(services)} instances de service, attendu 8."
    assert len(archives) == 5, f"{len(archives)} archives dans le module, attendu 5."
    assert len(verite["data"]) == 2, (
        f"{len(verite['data'])} data sources, attendu 2 : une a la racine, une "
        "dans le module."
    )


# --------------------------------------------------------------------------
# 2. Une adresse indexee par POSITION
# --------------------------------------------------------------------------

def test_adresse_indexee_par_position(verite: dict) -> None:
    attendue = _adresse_portant(
        verite["instances"], _reponse(verite, "id_worker_recherche"), "random_pet.worker"
    )
    assert attendue is not None, "Aucune instance de worker ne porte l'id publie."
    declaree = _reponse(verite, "adresse_worker")
    assert declaree == attendue, (
        f"adresse_worker declaree {declaree!r}, mais l'id publie est porte par "
        f"{attendue!r}. Une adresse de ressource sans index designe TOUTES ses "
        "instances : c'est l'index entre crochets qui identifie celle-ci."
    )


# --------------------------------------------------------------------------
# 3. Une adresse indexee par CLE
# --------------------------------------------------------------------------

def test_adresse_indexee_par_cle(verite: dict) -> None:
    attendue = _adresse_portant(
        verite["instances"], _reponse(verite, "id_service_recherche"), "random_pet.service"
    )
    assert attendue is not None, "Aucune instance de service ne porte l'id publie."
    declaree = _reponse(verite, "adresse_service")
    assert declaree == attendue, (
        f"adresse_service declaree {declaree!r}, attendu {attendue!r}. Une "
        "instance de for_each s'adresse par sa cle entre crochets ET entre "
        "guillemets."
    )


# --------------------------------------------------------------------------
# 4. Une adresse QUALIFIEE PAR LE MODULE
# --------------------------------------------------------------------------

def test_adresse_qualifiee_par_le_module(verite: dict) -> None:
    attendue = _adresse_portant(
        verite["instances"],
        _reponse(verite, "id_archive_recherche"),
        "module.stockage.random_pet.archive",
    )
    assert attendue is not None, "Aucune archive du module ne porte l'id publie."
    declaree = _reponse(verite, "adresse_archive")
    assert declaree == attendue, (
        f"adresse_archive declaree {declaree!r}, attendu {attendue!r}. Une "
        "instance logee dans un module porte le prefixe `module.<nom>.` : sans "
        "lui, l'adresse ne designe rien."
    )


# --------------------------------------------------------------------------
# 5. La data source du module, celle qui ne commence pas par « data »
# --------------------------------------------------------------------------

def test_data_source_du_module(verite: dict) -> None:
    dans_module = [i for i in verite["data"] if i["address"].startswith("module.")]
    assert len(dans_module) == 1, (
        f"{len(dans_module)} data source(s) dans un module, attendu 1."
    )
    attendue = dans_module[0]["address"]
    declaree = _reponse(verite, "adresse_data_module")
    assert declaree == attendue, (
        f"adresse_data_module declaree {declaree!r}, attendu {attendue!r}. "
        "C'est une data source, mais son adresse commence par le prefixe de "
        "module : `grep -v ^data` ne l'attrape donc pas."
    )


# --------------------------------------------------------------------------
# 6. Le comptage : le JSON contre la recette au grep
# --------------------------------------------------------------------------

def test_comptage_des_ressources_managees(verite: dict) -> None:
    attendu = len(verite["managees"])
    declare = _reponse(verite, "nombre_managees")
    assert int(declare) == attendu, (  # type: ignore[call-overload]
        f"nombre_managees declare {declare}, attendu {attendu}. La recette "
        "`state list | grep -v ^data | wc -l` rend un de plus, parce qu'elle "
        "compte la data source du module comme une ressource geree."
    )


def test_la_recette_au_grep_se_trompe_bien(verite: dict) -> None:
    """Le lab n'a d'interet que si la recette fautive donne un AUTRE chiffre."""
    liste = terraform("state", "list", cwd=verite["cwd"])
    liste.check_returncode()
    lignes = [ligne for ligne in liste.stdout.splitlines() if ligne.strip()]
    recette = len([ligne for ligne in lignes if not ligne.startswith("data")])
    vrai = len(verite["managees"])
    assert recette == vrai + 1, (
        f"La recette au grep rend {recette} et le vrai comptage {vrai} : l'ecart "
        "attendu est de 1, celui de la data source du module. Sans cet ecart, le "
        "lab ne demontre plus rien."
    )


# --------------------------------------------------------------------------
# 7. Ce que la commande fait vraiment : filtres et diagnostics
# --------------------------------------------------------------------------

def test_une_adresse_sans_index_rend_toutes_les_instances(verite: dict) -> None:
    proc = terraform("state", "list", "random_pet.worker", cwd=verite["cwd"])
    proc.check_returncode()
    lignes = [ligne for ligne in proc.stdout.splitlines() if ligne.strip()]
    assert len(lignes) == 6, (
        f"`state list random_pet.worker` rend {len(lignes)} ligne(s), attendu 6 : "
        "l'argument filtre une FAMILLE d'instances, pas une ressource unique."
    )


def test_une_adresse_de_module_est_un_filtre_valide(verite: dict) -> None:
    proc = terraform("state", "list", "module.stockage", cwd=verite["cwd"])
    assert proc.returncode == 0, (
        f"`state list module.stockage` rend {proc.returncode} : une adresse de "
        f"module est pourtant un filtre accepte.\n{proc.stderr[-500:]}"
    )
    lignes = [ligne for ligne in proc.stdout.splitlines() if ligne.strip()]
    assert len(lignes) == 7, (
        f"{len(lignes)} entree(s) pour module.stockage, attendu 7 (5 archives, "
        "1 local_file, 1 data source)."
    )


def test_ordre_par_profondeur_de_module(verite: dict) -> None:
    """La sortie n'est pas triee alphabetiquement : la racine passe devant."""
    proc = terraform("state", "list", cwd=verite["cwd"])
    proc.check_returncode()
    lignes = [ligne for ligne in proc.stdout.splitlines() if ligne.strip()]
    premier_module = next(i for i, l in enumerate(lignes) if l.startswith("module."))
    racine_apres = [l for l in lignes[premier_module:] if not l.startswith("module.")]
    assert not racine_apres, (
        "Des entrees de la racine apparaissent apres celles du module : "
        f"{racine_apres[:3]}. L'ordre est la profondeur de module, puis "
        "l'alphabetique."
    )
    assert lignes[-1].startswith("module."), (
        "La derniere entree devrait appartenir au module le plus profond."
    )


def test_les_quatre_diagnostics_distincts(verite: dict) -> None:
    cas = {
        "random_pet.inexistant": "Unknown resource",
        'random_pet.service["nope"]': "Unknown resource instance",
        "module.inexistant": "Unknown module",
        "random_pet": "Invalid address",
    }
    for adresse, attendu in cas.items():
        proc = terraform("state", "list", "-no-color", adresse, cwd=verite["cwd"])
        assert proc.returncode == 1, (
            f"`state list {adresse}` rend {proc.returncode}, attendu 1."
        )
        sortie = proc.stdout + proc.stderr
        assert attendu in sortie, (
            f"`state list {adresse}` devrait diagnostiquer « {attendu} », "
            f"sortie obtenue :\n{sortie[-400:]}"
        )


def test_id_sans_correspondance_ne_leve_pas(verite: dict) -> None:
    """L'asymetrie qui decide de la facon de scripter la commande."""
    proc = terraform("state", "list", "-id=aucune-chance-que-cet-id-existe",
                     cwd=verite["cwd"])
    assert proc.returncode == 0, (
        f"`state list -id=<inconnu>` rend {proc.returncode}, attendu 0 : "
        "contrairement a une adresse, un -id sans correspondance ne produit "
        "aucune erreur."
    )
    assert proc.stdout.strip() == "", (
        f"Sortie attendue vide, obtenue : {proc.stdout[:200]!r}"
    )


def test_id_retrouve_bien_l_instance_cherchee(verite: dict) -> None:
    """C'est le geste que le lab enseigne : de l'id vers l'adresse."""
    cible = _reponse(verite, "adresse_worker")
    identifiant = _reponse(verite, "id_worker_recherche")
    proc = terraform("state", "list", f"-id={identifiant}", cwd=verite["cwd"])
    proc.check_returncode()
    lignes = [ligne.strip() for ligne in proc.stdout.splitlines() if ligne.strip()]
    assert cible in lignes, (
        f"`state list -id={identifiant}` rend {lignes}, qui ne contient pas "
        f"{cible!r}."
    )


# --------------------------------------------------------------------------
# 8. Renseigner les reponses n'a rien fait bouger
# --------------------------------------------------------------------------

def test_idempotence(verite: dict) -> None:
    proc = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color",
                     cwd=verite["cwd"])
    assert proc.returncode == 0, (
        f"plan -detailed-exitcode rend {proc.returncode}, attendu 0 : lire le "
        "state ne doit rien changer a l'infrastructure."
    )
