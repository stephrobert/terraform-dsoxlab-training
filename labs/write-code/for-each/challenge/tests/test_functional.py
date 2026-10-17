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
    message,
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
        pytest.fail(message(
            en=f"`terraform init` failed.\n{init.stderr[-1500:]}",
            fr=f"`terraform init` a échoué.\n{init.stderr[-1500:]}",
        ))
    apply = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if apply.returncode != 0:
        pytest.fail(
            message(
            en="`terraform apply` failed: the configuration is not valid yet.\n"
            f"{apply.stderr[-1500:]}",
            fr="`terraform apply` a échoué : la configuration n'est pas encore valide.\n"
            f"{apply.stderr[-1500:]}",
        )
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
    assert gerees, message(
        en="No managed resource in the state.",
        fr="Aucune ressource gérée dans le state.",
    )
    entiers = [
        f"{r['type']}[{r['index']}]" for r in gerees if isinstance(r.get("index"), int)
    ]
    assert not entiers, message(
        en=f"These instances are still addressed by position: {entiers}. "
        "An integer index signals a count that was not migrated.",
        fr=f"Ces instances sont encore adressées par position : {entiers}. "
        "Un index entier signale un count non migré.",
    )


def test_les_quatre_services_presents(etat: dict) -> None:
    attendus = set(SERVICES_ORIGINE) | {SERVICE_AJOUTE}
    obtenues = set(identites(etat))
    assert obtenues == attendus, message(
        en=f"Keys present: {sorted(obtenues)}. Expected: {sorted(attendus)}.",
        fr=f"Clés présentes : {sorted(obtenues)}. Attendu : {sorted(attendus)}.",
    )


# --------------------------------------------------------------------------
# Non destruction : la preuve par l'identité
# --------------------------------------------------------------------------

@pytest.mark.parametrize("service", SERVICES_ORIGINE)
def test_identite_preservee(etat: dict, identites_depart: dict, service: str) -> None:
    """Une identité qui change trahit une ressource détruite puis recréée."""
    avant = identites_depart[service]
    apres = identites(etat).get(service)
    assert apres == avant, message(
        en=f"The service \"{service}\" had the identity {avant!r}, it now carries "
        f"{apres!r}. The resource was therefore destroyed and then recreated, which the "
        "instruction explicitly forbids.",
        fr=f"Le service « {service} » avait l'identité {avant!r}, il porte maintenant "
        f"{apres!r}. La ressource a donc été détruite puis recréée, ce que la "
        "demande interdit explicitement.",
    )


def test_service_ajoute_est_bien_nouveau(etat: dict, identites_depart: dict) -> None:
    ajoutee = identites(etat).get(SERVICE_AJOUTE)
    assert ajoutee, message(
        en=f"The service \"{SERVICE_AJOUTE}\" is absent from the state.",
        fr=f"Le service « {SERVICE_AJOUTE} » est absent du state.",
    )
    assert ajoutee not in identites_depart.values(), message(
        en="The new service reuses the identity of an existing service.",
        fr="Le nouveau service réutilise l'identité d'un service existant.",
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
        assert init.returncode == 0, message(
            en=f"cannot init the replay:\n{init.stderr[-800:]}",
            fr=f"init du rejeu impossible :\n{init.stderr[-800:]}",
        )

        plan = terraform("plan", "-out=rejeu.tfplan", "-input=false", "-no-color", cwd=tmp)
        assert plan.returncode == 0, message(
            en=f"cannot plan the replay:\n{plan.stderr[-800:]}",
            fr=f"plan du rejeu impossible :\n{plan.stderr[-800:]}",
        )

        montre = terraform("show", "-json", "rejeu.tfplan", cwd=tmp)
        montre.check_returncode()
        changements = json.loads(montre.stdout).get("resource_changes", [])

        detruits = [
            c["address"] for c in changements
            if "delete" in c.get("change", {}).get("actions", [])
        ]
        assert not detruits, message(
            en=f"Replayed against the original state, your code destroys {detruits}. "
            "The re-addressing is therefore not declarative: `moved` blocks are "
            "missing from the configuration.",
            fr=f"Rejoué devant le state d'origine, votre code détruit {detruits}. "
            "Le réadressage n'est donc pas déclaratif : il manque des blocs "
            "`moved` dans la configuration.",
        )

        readresses = [c for c in changements if c.get("previous_address")]
        assert len(readresses) >= len(SERVICES_ORIGINE), message(
            en=f"Only {len(readresses)} re-addressings are declared, "
            f"at least {len(SERVICES_ORIGINE)} expected. "
            "Every existing instance must be covered by a `moved` block.",
            fr=f"Seuls {len(readresses)} réadressages sont déclarés, "
            f"au moins {len(SERVICES_ORIGINE)} sont attendus. "
            "Chaque instance existante doit être couverte par un bloc `moved`.",
        )

        crees = [
            c["address"] for c in changements
            if c.get("change", {}).get("actions") == ["create"]
        ]
        assert len(crees) == 2, message(
            en=f"The replay creates {len(crees)} resource(s): {crees}. "
            "Exactly two are expected, one per type, for the single "
            f"service \"{SERVICE_AJOUTE}\".",
            fr=f"Le rejeu crée {len(crees)} ressource(s) : {crees}. "
            "Exactement deux sont attendues, une par type, pour le seul "
            f"service « {SERVICE_AJOUTE} ».",
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------
# Sortie et stabilité
# --------------------------------------------------------------------------

def test_output_est_une_map(applied: Path) -> None:
    """Le splat est invalide sur une ressource `for_each` : il faut un `for`."""
    valeur = output_json(applied)["identites"]["value"]
    assert isinstance(valeur, dict), message(
        en=f"The `identites` output is of type {type(valeur).__name__}. "
        "A map indexed by service name is expected, built with a "
        "`for` expression.",
        fr=f"L'output `identites` est de type {type(valeur).__name__}. "
        "Une map indexée par nom de service est attendue, construite avec une "
        "expression `for`.",
    )
    assert set(valeur) == set(SERVICES_ORIGINE) | {SERVICE_AJOUTE}, message(
        en=f"The output's keys are {sorted(valeur)}.",
        fr=f"Les clés de l'output sont {sorted(valeur)}.",
    )


def test_la_configuration_converge_et_l_etat_porte_les_quatre_services(
    applied: Path, etat: dict
) -> None:
    """L'idempotence vit ici, et plus dans un test à elle.

    Seule, elle était VRAIE AVANT LE TRAVAIL, et même nécessairement : la
    configuration de départ, indexée par `count`, converge parfaitement. Elle
    accordait des points pour n'avoir rien changé.

    Associée à l'inventaire du state, elle devient la moitié qui compte : le
    plan est vide ET il l'est sur les quatre services correctement adressés.
    C'est ce qui sépare un réadressage réussi d'une configuration restée en
    l'état.
    """
    attendues = set(SERVICES_ORIGINE) | {SERVICE_AJOUTE}
    obtenues = set(identites(etat))
    assert obtenues == attendues, message(
        en=f"The state carries the keys {sorted(obtenues)}, expected "
        f"{sorted(attendues)}. The plan can be empty and the addressing wrong: "
        "that is what the two halves check together.",
        fr=f"Le state porte les clés {sorted(obtenues)}, attendu "
        f"{sorted(attendues)}. Le plan peut être vide et l'adressage faux : "
        "c'est ce que les deux moitiés vérifient ensemble.",
    )

    proc = terraform(
        "plan", "-detailed-exitcode", "-input=false", "-no-color", cwd=applied
    )
    assert proc.returncode == 0, message(
        en=f"`terraform plan -detailed-exitcode` returns {proc.returncode}, expected 0.",
        fr=f"`terraform plan -detailed-exitcode` rend {proc.returncode}, attendu 0.",
    )
