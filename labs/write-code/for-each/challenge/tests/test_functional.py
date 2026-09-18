"""Tests fonctionnels du lab « ajouter une instance sans détruire les autres ».

Principe : on prouve l'ÉTAT produit, jamais le contenu des `.tf` de l'apprenant.

La preuve la plus forte est le **rejeu** : la configuration de l'apprenant est
replacée devant le state de DÉPART (livré en fixture), et le plan qui en résulte
ne doit rien détruire. C'est ce qui distingue un réadressage déclaratif par blocs
`moved` d'une manipulation manuelle du state, que le résultat final seul ne
permettrait pas de départager.
"""

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from conftest import (
    exiger_workdir,
    output_json,
    show_json,
    terraform,
    workdir_lab,
)

LAB = Path(__file__).resolve().parents[2]
WORKDIR = workdir_lab(__file__)
STATE_DEPART = LAB / "fixtures" / "terraform.tfstate"

SERVICES_ORIGINE = ("web", "cache", "db")
SERVICE_AJOUTE = "api"


def identites(document: dict) -> dict[str, str]:
    """Nom généré de chaque `random_pet`, indexé par clé d'instance."""
    resources = document.get("values", {}).get("root_module", {}).get("resources", [])
    return {
        str(r.get("index")): r["values"]["id"]
        for r in resources
        if r.get("mode") == "managed" and r.get("type") == "random_pet"
    }


@pytest.fixture(scope="module")
def identites_depart() -> dict[str, str]:
    """Identités enregistrées dans le state livré, avant toute migration."""
    brut = json.loads(STATE_DEPART.read_text(encoding="utf-8"))
    trouvees = {}
    for res in brut.get("resources", []):
        if res.get("type") == "random_pet":
            for inst in res.get("instances", []):
                trouvees[str(inst.get("index_key"))] = inst["attributes"]["id"]
    # Le state de depart est indexe par position : 0, 1, 2.
    return {SERVICES_ORIGINE[int(k)]: v for k, v in trouvees.items()}


@pytest.fixture(scope="module")
def applied() -> Path:
    exiger_workdir(WORKDIR, "write-code-for-each")
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(f"`terraform init` a échoué.\n{init.stderr[-1500:]}")
    apply = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if apply.returncode != 0:
        pytest.fail(
            "`terraform apply` a échoué : la configuration n'est pas encore valide.\n"
            f"{apply.stderr[-1500:]}"
        )
    return WORKDIR


@pytest.fixture(scope="module")
def etat(applied: Path) -> dict:
    return show_json(applied)


# --------------------------------------------------------------------------
# Adressage
# --------------------------------------------------------------------------

def test_plus_aucun_index_numerique(etat: dict) -> None:
    """`for_each` adresse par clé, `count` adresserait par entier."""
    resources = etat["values"]["root_module"]["resources"]
    gerees = [r for r in resources if r.get("mode") == "managed"]
    assert gerees, "Aucune ressource gérée dans le state."
    entiers = [
        f"{r['type']}[{r['index']}]" for r in gerees if isinstance(r.get("index"), int)
    ]
    assert not entiers, (
        f"Ces instances sont encore adressées par position : {entiers}. "
        "Un index entier signale un count non migré."
    )


def test_les_quatre_services_presents(etat: dict) -> None:
    attendus = set(SERVICES_ORIGINE) | {SERVICE_AJOUTE}
    obtenues = set(identites(etat))
    assert obtenues == attendus, (
        f"Clés présentes : {sorted(obtenues)}. Attendu : {sorted(attendus)}."
    )


# --------------------------------------------------------------------------
# Non destruction : la preuve par l'identité
# --------------------------------------------------------------------------

@pytest.mark.parametrize("service", SERVICES_ORIGINE)
def test_identite_preservee(etat: dict, identites_depart: dict, service: str) -> None:
    """Une identité qui change trahit une ressource détruite puis recréée."""
    avant = identites_depart[service]
    apres = identites(etat).get(service)
    assert apres == avant, (
        f"Le service « {service} » avait l'identité {avant!r}, il porte maintenant "
        f"{apres!r}. La ressource a donc été détruite puis recréée, ce que la "
        "demande interdit explicitement."
    )


def test_service_ajoute_est_bien_nouveau(etat: dict, identites_depart: dict) -> None:
    ajoutee = identites(etat).get(SERVICE_AJOUTE)
    assert ajoutee, f"Le service « {SERVICE_AJOUTE} » est absent du state."
    assert ajoutee not in identites_depart.values(), (
        "Le nouveau service réutilise l'identité d'un service existant."
    )


# --------------------------------------------------------------------------
# Réadressage déclaratif : le rejeu depuis le state de départ
# --------------------------------------------------------------------------

def test_readressage_declaratif(applied: Path) -> None:
    """Rejoué devant le state d'origine, le code ne doit rien détruire.

    Un réadressage fait à la main avec `terraform state mv` ne laisse aucune
    trace dans la configuration : rejoué ici, il produirait des destructions.
    Seuls des blocs `moved` versionnés passent ce test.
    """
    tmp = Path(tempfile.mkdtemp(prefix="rejeu-foreach-"))
    try:
        for fichier in applied.iterdir():
            if fichier.is_file() and fichier.suffix in {".tf", ".tftpl"}:
                shutil.copy2(fichier, tmp / fichier.name)
        shutil.copy2(STATE_DEPART, tmp / "terraform.tfstate")

        # Les fichiers deja produits doivent accompagner le state, sinon le
        # provider local constate leur disparition et planifie leur recreation :
        # le rejeu ne refleterait plus la situation reelle de l'apprenant.
        produits = applied / "out"
        if produits.is_dir():
            shutil.copytree(produits, tmp / "out")

        init = terraform("init", "-input=false", "-no-color", cwd=tmp)
        assert init.returncode == 0, f"init du rejeu impossible :\n{init.stderr[-800:]}"

        plan = terraform("plan", "-out=rejeu.tfplan", "-input=false", "-no-color", cwd=tmp)
        assert plan.returncode == 0, f"plan du rejeu impossible :\n{plan.stderr[-800:]}"

        montre = terraform("show", "-json", "rejeu.tfplan", cwd=tmp)
        montre.check_returncode()
        changements = json.loads(montre.stdout).get("resource_changes", [])

        detruits = [
            c["address"] for c in changements
            if "delete" in c.get("change", {}).get("actions", [])
        ]
        assert not detruits, (
            f"Rejoué devant le state d'origine, votre code détruit {detruits}. "
            "Le réadressage n'est donc pas déclaratif : il manque des blocs "
            "`moved` dans la configuration."
        )

        readresses = [c for c in changements if c.get("previous_address")]
        assert len(readresses) >= len(SERVICES_ORIGINE), (
            f"Seuls {len(readresses)} réadressages sont déclarés, "
            f"au moins {len(SERVICES_ORIGINE)} sont attendus. "
            "Chaque instance existante doit être couverte par un bloc `moved`."
        )

        crees = [
            c["address"] for c in changements
            if c.get("change", {}).get("actions") == ["create"]
        ]
        assert len(crees) == 2, (
            f"Le rejeu crée {len(crees)} ressource(s) : {crees}. "
            "Exactement deux sont attendues, une par type, pour le seul "
            f"service « {SERVICE_AJOUTE} »."
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------
# Sortie et stabilité
# --------------------------------------------------------------------------

def test_output_est_une_map(applied: Path) -> None:
    """Le splat est invalide sur une ressource `for_each` : il faut un `for`."""
    valeur = output_json(applied)["identites"]["value"]
    assert isinstance(valeur, dict), (
        f"L'output `identites` est de type {type(valeur).__name__}. "
        "Une map indexée par nom de service est attendue, construite avec une "
        "expression `for`."
    )
    assert set(valeur) == set(SERVICES_ORIGINE) | {SERVICE_AJOUTE}, (
        f"Les clés de l'output sont {sorted(valeur)}."
    )


def test_configuration_idempotente(applied: Path) -> None:
    proc = terraform(
        "plan", "-detailed-exitcode", "-input=false", "-no-color", cwd=applied
    )
    assert proc.returncode == 0, (
        f"`terraform plan -detailed-exitcode` rend {proc.returncode}, attendu 0."
    )
