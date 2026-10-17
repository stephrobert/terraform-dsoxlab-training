"""Tests fonctionnels du lab « count, for_each et le piege de l'index positionnel ».

Principe : on ne lit jamais le CONTENU des `.tf` de l'apprenant pour l'asserer,
et jamais une sortie humaine. On pilote Terraform dans `challenge/work` et on ne
lit que `terraform show -json` (state et plan), `output -json`, et des codes
retour. Le test de migration copie bien les `.tf` de l'apprenant dans un
repertoire temporaire, mais pour les DONNER a Terraform, pas pour les parser :
c'est Terraform qui juge, pas le test.

Faits verifies sur Terraform v1.15.4 :
- une ressource `for_each` est indexee par CLE ; retirer une cle du milieu ne
  detruit que cette cle (les autres restent no-op) ;
- une ressource `count` est indexee par ENTIER ; migrer count -> for_each SANS
  bloc `moved` detruit et recree tout (3 delete + 3 create), AVEC `moved` tout
  reste no-op et `previous_address` trace le deplacement ;
- reduire un `count` retire l'index le plus haut ;
- `count = cond ? 1 : 0` produit 0 ou 1 instance, expose par `one()` (null ou
  la valeur unique) ; le splat ne s'applique pas a une ressource `for_each`.
"""

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from conftest import (
    exiger_workdir,
    message,
    output_json,
    show_json,
    terraform,
    workdir_lab,
)

WORKDIR = workdir_lab(__file__)
LAB_ID = "write-code-count"
LAB_DIR = Path(__file__).resolve().parents[2]
REFERENCE = LAB_DIR / "challenge" / "reference"


def _plan(cwd: Path, *var: str) -> dict:
    p = terraform("plan", "-input=false", "-no-color", "-out=tfplan", *var, cwd=cwd)
    if p.returncode != 0:
        pytest.fail(message(
            en=f"`terraform plan` failed. A leftover `???`?\n{p.stderr[-1200:]}",
            fr=f"`terraform plan` a échoué. Un `???` subsiste ?\n{p.stderr[-1200:]}",
        ))
    return json.loads(terraform("show", "-json", "tfplan", cwd=cwd).stdout)


def _actions(plan: dict) -> dict[str, list[str]]:
    return {c["address"]: c["change"]["actions"] for c in plan.get("resource_changes", [])}


def _resources(cwd: Path) -> list[dict]:
    return show_json(cwd)["values"]["root_module"]["resources"]


@pytest.fixture(scope="module")
def applied() -> Path:
    """Etat de depart : rapport desactive, trois services, trois workers."""
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(message(
            en=f"`terraform init` failed.\n{init.stderr[-1200:]}",
            fr=f"`terraform init` a échoué.\n{init.stderr[-1200:]}",
        ))
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(message(
            en=f"`terraform apply` failed. A leftover `???`?\n{app.stderr[-1500:]}",
            fr=f"`terraform apply` a échoué. Un `???` restant ?\n{app.stderr[-1500:]}",
        ))
    return WORKDIR


# --------------------------------------------------------------------------
# 1. service indexe par NOM (for_each), workers par entier (count)
# --------------------------------------------------------------------------

def test_service_indexe_par_nom(applied: Path) -> None:
    services = [r for r in _resources(applied)
                if r.get("type") == "local_file" and r.get("name") == "service"]
    assert services, message(
        en="No `local_file.service` instance in the state.",
        fr="Aucune instance `local_file.service` dans le state.",
    )
    for r in services:
        assert isinstance(r.get("index"), str), message(
            en=f"The service instance has index {r.get('index')!r} (an integer). An integer "
            "index betrays a `count`: move that block to `for_each` over "
            "the set of services, to be indexed by name.",
            fr=f"L'instance service a l'index {r.get('index')!r} (entier). Un index "
            "entier trahit un `count` : migrez ce bloc vers `for_each` sur "
            "l'ensemble des services, pour être indexé par nom.",
        )
    assert {r["index"] for r in services} == {"web", "api", "cache"}, message(
        en=f"service keys = {sorted(r['index'] for r in services)}, "
        "expected web/api/cache (for_each = toset(var.services)).",
        fr=f"Clés service = {sorted(r['index'] for r in services)}, "
        "attendu web/api/cache (for_each = toset(var.services)).",
    )
    assert all(r.get("mode") == "managed" for r in services), message(
        en="Some service instances are not in `managed` mode: a `data` block "
        "reads, it does not create the files.",
        fr="Des instances service ne sont pas en mode `managed` : un bloc "
        "`data` lit, il ne crée pas les fichiers.",
    )


def test_workers_en_count(applied: Path) -> None:
    workers = [r for r in _resources(applied)
               if r.get("type") == "random_pet" and r.get("name") == "worker"]
    assert len(workers) == 3, message(
        en=f"{len(workers)} workers, 3 expected (count = var.workers).",
        fr=f"{len(workers)} workers, attendu 3 (count = var.workers).",
    )
    for r in workers:
        assert isinstance(r.get("index"), int) and not isinstance(r.get("index"), bool), message(
            en=f"worker has index {r.get('index')!r}. Interchangeable copies "
            "are expressed with `count` (integer index), not `for_each`.",
            fr=f"worker a l'index {r.get('index')!r}. Des copies interchangeables "
            "s'expriment avec `count` (index entier), pas `for_each`.",
        )


# --------------------------------------------------------------------------
# 2. LE PIEGE : retirer un service du milieu ne touche QUE lui
# --------------------------------------------------------------------------

def test_retrait_service_ne_touche_que_la_cible(applied: Path) -> None:
    """Retire `api` (au milieu). En for_each keye par nom, seule la cle `api`
    est detruite ; web et cache restent no-op. Une solution `count` recreerait
    l'index decale et detruirait le dernier : ce test l'interdit."""
    plan = _plan(applied, "-var", 'services=["web","cache"]')
    svc = {a: acts for a, acts in _actions(plan).items()
           if a.startswith("local_file.service")}
    recrees = [a for a, acts in svc.items() if acts == ["delete", "create"]]
    crees = [a for a, acts in svc.items() if acts == ["create"]]
    detruits = [a for a, acts in svc.items() if acts == ["delete"]]
    assert recrees == [], message(
        en=f"Removing the middle one: {recrees} are recreated. That is the index-shift "
        "trap of `count`: move to `for_each` keyed by name.",
        fr=f"Retrait du milieu : {recrees} sont recréés. C'est le piège du décalage "
        "d'index de `count` : passez à `for_each` keyé par nom.",
    )
    assert crees == [], message(
        en=f"Removing the middle one: {crees} are created, no creation expected.",
        fr=f"Retrait du milieu : {crees} sont créés, aucune création attendue.",
    )
    assert detruits == ['local_file.service["api"]'], message(
        en=f"Destroyed = {detruits}, only the 'api' key expected. web and cache stay intact.",
        fr=f"Détruits = {detruits}, attendu la seule clé 'api'. web et cache restent intacts.",
    )


# --------------------------------------------------------------------------
# 3. La migration count -> for_each est NON DESTRUCTRICE (blocs moved)
# --------------------------------------------------------------------------

def test_migration_moved_non_destructive(applied: Path) -> None:
    """Reconstitue l'etat AVANT (version count de reference), puis superpose la
    configuration migree de l'apprenant. Avec les bons blocs `moved`, le plan
    est entierement no-op et chaque service porte un `previous_address` en
    `local_file.service[<entier>]`. Sans `moved`, ce serait 3 delete + 3 create."""
    tmp = Path(tempfile.mkdtemp(prefix="moved-"))
    try:
        (tmp / "out").mkdir(exist_ok=True)
        for nom in ("versions.tf", "variables.tf", "workers.tf", "rapport.tf"):
            shutil.copy2(WORKDIR / nom, tmp / nom)
        shutil.copy2(REFERENCE / "main.tf", tmp / "main.tf")
        if (WORKDIR / ".terraform").is_dir():
            shutil.copytree(WORKDIR / ".terraform", tmp / ".terraform")
        if (WORKDIR / ".terraform.lock.hcl").is_file():
            shutil.copy2(WORKDIR / ".terraform.lock.hcl", tmp / ".terraform.lock.hcl")

        init = terraform("init", "-input=false", "-no-color", cwd=tmp)
        assert init.returncode == 0, message(
            en=f"init of the reference failed.\n{init.stderr[-800:]}",
            fr=f"init de la référence a échoué.\n{init.stderr[-800:]}",
        )
        app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=tmp)
        assert app.returncode == 0, message(
            en=f"apply of the reference failed.\n{app.stderr[-800:]}",
            fr=f"apply de la référence a échoué.\n{app.stderr[-800:]}",
        )

        # Superpose la configuration migree de l'apprenant (for_each + moved).
        shutil.copy2(WORKDIR / "main.tf", tmp / "main.tf")
        shutil.copy2(WORKDIR / "outputs.tf", tmp / "outputs.tf")

        plan = _plan(tmp)
        vus = 0
        for c in plan.get("resource_changes", []):
            if not c["address"].startswith("local_file.service"):
                continue
            vus += 1
            assert c["change"]["actions"] == ["no-op"], message(
                en=f"{c['address']} = {c['change']['actions']} during the migration. "
                "The count -> for_each migration destroys objects: the `moved` blocks "
                "tying each old index to its key are missing (or wrong).",
                fr=f"{c['address']} = {c['change']['actions']} lors de la migration. "
                "La migration count -> for_each détruit des objets : il manque (ou "
                "sont faux) les blocs `moved` reliant chaque ancien index à sa clé.",
            )
            prev = c.get("previous_address", "")
            assert prev.startswith("local_file.service["), message(
                en=f"{c['address']} has no `previous_address` at local_file.service[N]. "
                "The matching `moved` block is missing.",
                fr=f"{c['address']} n'a pas de `previous_address` en local_file.service[N]. "
                "Le bloc `moved` correspondant manque.",
            )
        assert vus == 3, message(
            en=f"{vus} service instances in the migration plan, 3 expected.",
            fr=f"{vus} instances service dans le plan de migration, attendu 3.",
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------
# 4. Reduire count retire l'index le plus haut
# --------------------------------------------------------------------------

def test_reduction_workers_retire_le_dernier(applied: Path) -> None:
    plan = _plan(applied, "-var", "workers=2")
    w = {a: acts for a, acts in _actions(plan).items()
         if a.startswith("random_pet.worker")}
    detruits = [a for a, acts in w.items() if "delete" in acts]
    assert detruits == ["random_pet.worker[2]"], message(
        en=f"workers=2 destroys {detruits}, only the highest index "
        "random_pet.worker[2] expected.",
        fr=f"workers=2 détruit {detruits}, attendu le seul index le plus haut "
        "random_pet.worker[2].",
    )


# --------------------------------------------------------------------------
# 5. Sorties : splat, expression for, one()
# --------------------------------------------------------------------------

def test_sorties_cablees(applied: Path) -> None:
    outs = output_json(applied)
    noms = outs["noms_workers"]["value"]
    assert isinstance(noms, list) and len(noms) == 3, message(
        en=f"`noms_workers` = {noms!r}, a list of 3 expected (splat "
        "random_pet.worker[*].id).",
        fr=f"`noms_workers` = {noms!r}, attendu une liste de 3 (splat "
        "random_pet.worker[*].id).",
    )
    chemins = outs["chemins_services"]["value"]
    assert isinstance(chemins, dict) and set(chemins) == {"web", "api", "cache"}, message(
        en=f"`chemins_services` = {chemins!r}, a map keyed web/api/cache expected. "
        "The splat does not work on a for_each resource: use a "
        "`for` expression over the map.",
        fr=f"`chemins_services` = {chemins!r}, attendu une map keyée web/api/cache. "
        "Le splat ne marche pas sur une ressource for_each : utilisez une "
        "expression `for` sur la map.",
    )
    # rapport desactive : la sortie vaut null, donc absente de output -json.
    assert outs.get("rapport", {}).get("value") is None, message(
        en="`rapport` should be null by default (feature disabled, "
        "one() over 0 instances).",
        fr="`rapport` devrait être null par défaut (feature désactivée, "
        "one() sur 0 instance).",
    )


def test_rapport_conditionnel(applied: Path) -> None:
    plan = _plan(applied, "-var", "rapport=true")
    assert _actions(plan).get("local_file.rapport[0]") == ["create"], message(
        en="Enabling `rapport` must create `local_file.rapport[0]` "
        "(count = var.rapport ? 1 : 0).",
        fr="Activer `rapport` doit créer `local_file.rapport[0]` "
        "(count = var.rapport ? 1 : 0).",
    )


# --------------------------------------------------------------------------
# 6. Idempotence
# --------------------------------------------------------------------------

def test_configuration_stable_apres_apply(applied: Path) -> None:
    p = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=applied)
    assert p.returncode == 0, message(
        en=f"`plan -detailed-exitcode` returns {p.returncode} (2 = changes "
        "remain planned). An apply must converge.",
        fr=f"`plan -detailed-exitcode` rend {p.returncode} (2 = des changements "
        "restent planifiés). Un apply doit converger.",
    )
