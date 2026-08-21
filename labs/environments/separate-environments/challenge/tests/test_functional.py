"""Tests fonctionnels du lab « deux racines, deux etats, un module partage ».

Separer des environnements par des repertoires n'a d'interet que si les etats
sont reellement independants. Ces tests le prouvent de la seule facon honnete :
en DETRUISANT dev, dans une copie du travail, et en verifiant que prod n'a pas
bouge.

Faits verifies sur Terraform 1.15.4, hors ligne, backend `local` :
- un bloc `backend` ne peut referencer aucune valeur nommee : `Error: Variables
  not allowed` / « Variables may not be used here. » ;
- la configuration PARTIELLE contourne cela sans dupliquer le fichier : le bloc
  reste vide, et `-backend-config=<fichier>.hcl` fournit le `path` a l'init ;
- Terraform enregistre la configuration de backend retenue dans
  `.terraform/terraform.tfstate`, ce qui permet de verifier quel etat chaque
  racine pilote reellement.
"""

import json
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "environments-separate-environments"

ENVIRONNEMENTS = {"dev": 1, "prod": 3}
MODULE = "modules/plaque"


def _racine(travail: Path, env: str) -> Path:
    chemin = travail / "envs" / env
    if not chemin.is_dir():
        pytest.fail(f"Le repertoire envs/{env}/ est absent de challenge/work.")
    return chemin


def _etat(travail: Path, env: str) -> dict:
    montre = terraform("show", "-json", cwd=_racine(travail, env))
    montre.check_returncode()
    return json.loads(montre.stdout)


def _ressources(etat: dict) -> list[dict]:
    valeurs = etat.get("values", {}).get("root_module", {})
    trouvees = list(valeurs.get("resources", []))
    for enfant in valeurs.get("child_modules", []):
        trouvees.extend(enfant.get("resources", []))
    return trouvees


def _backend_declare(travail: Path, env: str) -> dict:
    """Configuration de backend retenue, telle que Terraform l'a enregistree."""
    chemin = _racine(travail, env) / ".terraform" / "terraform.tfstate"
    if not chemin.is_file():
        pytest.fail(
            f"envs/{env}/.terraform/terraform.tfstate est absent : "
            "`terraform init` n'a jamais abouti dans cette racine."
        )
    return json.loads(chemin.read_text(encoding="utf-8")).get("backend", {})


@pytest.fixture(scope="module")
def racines() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    for env in ENVIRONNEMENTS:
        racine = _racine(WORKDIR, env)
        # Les plugins de provider ne sont pas du travail de l'apprenant : on les
        # reinstalle si besoin, en reprenant la configuration de backend DEJA
        # enregistree par son `init`, sans la redemander.
        if not (racine / ".terraform" / "providers").is_dir():
            init = terraform("init", "-input=false", "-no-color", cwd=racine)
            if init.returncode != 0:
                pytest.fail(
                    f"envs/{env} : `terraform init` echoue. La configuration de "
                    "backend a-t-elle ete fournie par `-backend-config` ?"
                    f"\n{init.stderr[-900:]}"
                )
    yield WORKDIR


# --------------------------------------------------------------------------
# 1. Deux racines, deux etats, a l'endroit demande
# --------------------------------------------------------------------------

def test_chaque_racine_pilote_son_propre_etat(racines: Path) -> None:
    chemins = {}
    for env in ENVIRONNEMENTS:
        backend = _backend_declare(racines, env)
        assert backend.get("type") == "local", (
            f"envs/{env} : backend `{backend.get('type')}`, attendu `local`."
        )
        chemin = (backend.get("config") or {}).get("path")
        assert chemin, (
            f"envs/{env} : aucun `path` dans la configuration de backend "
            "enregistree. Le bloc est PARTIEL : le chemin se fournit a l'init, "
            "par `-backend-config`."
        )
        chemins[env] = chemin
        assert env in chemin, (
            f"envs/{env} pilote {chemin!r}, qui ne porte pas son nom."
        )
    assert len(set(chemins.values())) == len(chemins), (
        f"Les deux racines pointent le meme etat : {chemins}. Deux repertoires "
        "qui partagent un etat ne separent rien."
    )


def test_les_deux_fichiers_d_etat_existent(racines: Path) -> None:
    for env in ENVIRONNEMENTS:
        chemin = (_backend_declare(racines, env)["config"])["path"]
        racine = _racine(racines, env)
        fichier = (racine / chemin).resolve()
        assert fichier.is_file(), (
            f"envs/{env} : l'etat {fichier} n'existe pas. La racine a-t-elle ete "
            "appliquee ?"
        )
        assert not fichier.is_relative_to(racine.resolve()), (
            f"L'etat de {env} vit dans la racine elle-meme : le lab demande un "
            "repertoire d'etats commun, hors des racines."
        )


# --------------------------------------------------------------------------
# 2. Chaque environnement a ses propres ressources
# --------------------------------------------------------------------------

def test_chaque_environnement_produit_son_compte(racines: Path) -> None:
    for env, attendu in ENVIRONNEMENTS.items():
        etat = _etat(racines, env)
        ressources = _ressources(etat)
        assert len(ressources) == attendu, (
            f"envs/{env} : {len(ressources)} ressource(s) dans l'etat, attendu "
            f"{attendu}."
        )
        sorties = etat["values"]["outputs"]
        assert sorties["environnement"]["value"] == env, (
            f"envs/{env} expose environnement = "
            f"{sorties['environnement']['value']!r}."
        )
        for chemin in sorties["plaques"]["value"]:
            assert f"/{env}-" in chemin, (
                f"envs/{env} produit {chemin!r}, qui ne porte pas son "
                "environnement."
            )


def test_les_deux_racines_partagent_le_meme_module(racines: Path) -> None:
    dossiers = set()
    for env in ENVIRONNEMENTS:
        registre = _racine(racines, env) / ".terraform" / "modules" / "modules.json"
        assert registre.is_file(), f"envs/{env} : modules.json absent."
        entrees = [
            m for m in json.loads(registre.read_text(encoding="utf-8"))["Modules"]
            if m["Key"]
        ]
        assert entrees, f"envs/{env} n'appelle aucun module."
        for entree in entrees:
            assert entree["Source"].startswith("../"), (
                f"envs/{env} : `Source` vaut {entree['Source']!r}, attendu un "
                "chemin relatif remontant vers le module partage."
            )
            dossiers.add(Path(entree["Dir"]).name)
    assert dossiers == {Path(MODULE).name}, (
        f"Les racines lisent {sorted(dossiers)} : elles doivent partager le MEME "
        f"module, {MODULE}, et non une copie chacune."
    )


# --------------------------------------------------------------------------
# 3. La preuve : detruire dev ne touche pas prod
# --------------------------------------------------------------------------

def test_detruire_dev_ne_touche_pas_prod(racines: Path, tmp_path: Path) -> None:
    copie = tmp_path / "isolation"
    shutil.copytree(racines, copie)

    avant = _ressources(_etat(copie, "prod"))
    assert avant, "L'etat de prod est vide avant l'essai."

    detruit = terraform("destroy", "-auto-approve", "-input=false", "-no-color",
                        cwd=_racine(copie, "dev"))
    assert detruit.returncode == 0, (
        f"`terraform destroy` a echoue dans dev.\n{detruit.stderr[-900:]}"
    )

    assert not _ressources(_etat(copie, "dev")), (
        "L'etat de dev contient encore des ressources apres son destroy."
    )
    apres = _ressources(_etat(copie, "prod"))
    assert [r["address"] for r in apres] == [r["address"] for r in avant], (
        "Detruire dev a modifie l'etat de prod. Les deux racines partagent donc "
        "un etat, ce que la separation en repertoires devait justement empecher."
    )


# --------------------------------------------------------------------------
# 4. Les deux environnements ont converge
# --------------------------------------------------------------------------

def test_les_deux_environnements_ont_converge(racines: Path) -> None:
    for env in ENVIRONNEMENTS:
        plan = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color",
                         cwd=_racine(racines, env))
        assert plan.returncode == 0, (
            f"envs/{env} : plan -detailed-exitcode rend {plan.returncode}, "
            f"attendu 0.\n{plan.stdout[-700:]}"
        )
