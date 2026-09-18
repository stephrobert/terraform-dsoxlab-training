"""test_functional.py : getting-started/declarative-vs-imperative

Huit preuves que la convergence est une propriété, pas une opinion.

Aucun test n'ouvre les `.tf` de l'apprenant. L'idempotence et la dérive se lisent
dans le code retour de `plan -detailed-exitcode` et dans le JSON d'un plan
enregistré, jamais dans une phrase que Terraform imprime.

Le dernier test est le seul qui joue `imperatif.sh`, et il le fait dans un
répertoire jetable. Le faire tourner seul ne prouverait rien : un script qui
diverge, diverge déjà avant que l'apprenant ait travaillé. C'est la COMPARAISON
des deux comportements qui n'est atteignable qu'après le travail.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from conftest import exiger_workdir, output_json, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "getting-started-declarative-vs-imperative"

PROVIDERS_ATTENDUS = {
    "registry.terraform.io/hashicorp/local",
    "registry.terraform.io/hashicorp/null",
    "registry.terraform.io/hashicorp/random",
}
GEREES_ATTENDUES = {
    "random_string.identifiant",
    "local_file.rapport",
    "null_resource.empreinte",
}


@pytest.fixture(scope="module")
def prepared() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(
            "`terraform init` a échoué. Un `???` subsiste-t-il dans la "
            f"configuration ?\n{init.stderr[-1200:]}"
        )
    return WORKDIR


@pytest.fixture(scope="module")
def applied(prepared: Path) -> Path:
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=prepared)
    if app.returncode != 0:
        pytest.fail(f"`terraform apply` a échoué.\n{app.stderr[-1500:]}")
    return prepared


@pytest.fixture(scope="module")
def identifiant_avant(applied: Path) -> str:
    """L'identifiant relevé AVANT toute dérive, pour prouver qu'il y survit."""
    return output_json(applied)["identifiant"]["value"]


def ressources(cwd: Path) -> list[dict]:
    etat = show_json(cwd)
    return etat.get("values", {}).get("root_module", {}).get("resources", [])


# --------------------------------------------------------------------------
# 1. Le projet est initialisé, et les trois providers sont enregistrés.
# --------------------------------------------------------------------------
def test_les_trois_providers_sont_verrouilles(prepared: Path) -> None:
    verrou = prepared / ".terraform.lock.hcl"
    assert verrou.is_file(), (
        "`.terraform.lock.hcl` est absent : `terraform init` n'a pas résolu les "
        "providers."
    )
    trouves = dict(
        re.findall(
            r'provider\s+"([^"]+)"\s*\{\s*\n\s*version\s*=\s*"([^"]+)"',
            verrou.read_text(encoding="utf-8"),
        )
    )
    manquants = PROVIDERS_ATTENDUS - set(trouves)
    assert not manquants, (
        f"Le verrou ne liste pas {sorted(manquants)}. Il porte {sorted(trouves)}."
    )


# --------------------------------------------------------------------------
# 2. Trois ressources gérées, et ce sont les bonnes.
# --------------------------------------------------------------------------
def test_le_state_porte_les_trois_ressources_attendues(applied: Path) -> None:
    gerees = {r["address"] for r in ressources(applied) if r["mode"] == "managed"}
    assert gerees == GEREES_ATTENDUES, (
        f"Le state gère {sorted(gerees)}.\nAttendu exactement : "
        f"{sorted(GEREES_ATTENDUES)}."
    )

    empreinte = next(
        r for r in ressources(applied) if r["address"] == "null_resource.empreinte"
    )
    identifiant = next(
        r["values"]["result"]
        for r in ressources(applied)
        if r["address"] == "random_string.identifiant"
    )
    assert identifiant in (empreinte["values"].get("triggers") or {}).values(), (
        "Le déclencheur de `null_resource.empreinte` ne dépend pas de "
        f"l'identifiant.\nIl vaut {empreinte['values'].get('triggers')!r}.\n\n"
        "Sans cette dépendance, rien ne relie la ressource à ce qu'elle est "
        "censée suivre : elle ne serait ni remplacée quand il faut, ni épargnée "
        "quand il ne faut pas."
    )


# --------------------------------------------------------------------------
# 3. Le rapport existe, et il porte l'identifiant du state.
# --------------------------------------------------------------------------
def test_le_rapport_existe_et_porte_l_identifiant_du_state(applied: Path) -> None:
    rapport = next(
        r for r in ressources(applied) if r["address"] == "local_file.rapport"
    )
    chemin = (applied / rapport["values"]["filename"]).resolve()
    assert chemin.is_file(), (
        f"Le rapport est annoncé en {chemin}, qui n'existe pas sur le disque."
    )

    identifiant = next(
        r["values"]["result"]
        for r in ressources(applied)
        if r["address"] == "random_string.identifiant"
    )
    contenu = chemin.read_text(encoding="utf-8")
    assert identifiant in contenu, (
        f"Le rapport ne contient pas {identifiant!r}, l'identifiant du state.\n"
        f"Il contient : {contenu[:200]!r}\n\nLe contenu doit être construit par "
        "interpolation, pas saisi."
    )
    assert contenu.count(identifiant) == 1, (
        "L'identifiant apparaît plusieurs fois dans le rapport. Le fichier "
        "décrit un état, il n'empile pas un historique : c'est précisément ce "
        "que fait `imperatif.sh` avec son `>>`."
    )


# --------------------------------------------------------------------------
# 4. Les deux sorties, lues en JSON et confrontées au disque.
# --------------------------------------------------------------------------
def test_les_deux_sorties_designent_le_resultat_reel(applied: Path) -> None:
    sorties = output_json(applied)
    for attendu in ("identifiant", "chemin_rapport"):
        assert attendu in sorties, (
            f"La sortie `{attendu}` n'est pas déclarée. Présentes : "
            f"{sorted(sorties)}."
        )
        assert sorties[attendu]["value"], f"La sortie `{attendu}` est vide."

    chemin = (applied / sorties["chemin_rapport"]["value"]).resolve()
    assert chemin.is_file(), (
        f"`chemin_rapport` désigne {chemin}, qui n'existe pas."
    )
    assert sorties["identifiant"]["value"] in chemin.read_text(encoding="utf-8"), (
        "La sortie `identifiant` ne correspond pas à ce que contient le fichier "
        "désigné par `chemin_rapport`."
    )


# --------------------------------------------------------------------------
# 5. L'idempotence, par le code retour.
# --------------------------------------------------------------------------
def test_un_second_plan_n_annonce_aucune_action(applied: Path) -> None:
    plan = terraform(
        "plan", "-detailed-exitcode", "-input=false", "-no-color", cwd=applied
    )
    assert plan.returncode == 0, (
        f"`terraform plan -detailed-exitcode` rend {plan.returncode}.\n"
        "0 = aucun changement, 1 = erreur, 2 = des changements sont prévus.\n"
        f"{plan.stdout[-1200:]}"
    )


# --------------------------------------------------------------------------
# 6. La dérive : une seule création, et rien d'autre.
# --------------------------------------------------------------------------
def test_la_derive_annonce_une_seule_creation(
    applied: Path, identifiant_avant: str
) -> None:
    assert identifiant_avant, "L'identifiant n'a pas pu être relevé avant la dérive."

    chemin = (applied / output_json(applied)["chemin_rapport"]["value"]).resolve()
    chemin.unlink()

    detecte = terraform(
        "plan", "-detailed-exitcode", "-input=false", "-no-color", cwd=applied
    )
    assert detecte.returncode == 2, (
        f"Après suppression du rapport hors de Terraform, `plan "
        f"-detailed-exitcode` rend {detecte.returncode}, attendu 2. La dérive "
        "n'est pas détectée : sans correspondance dans le state, Terraform ne "
        "saurait pas qu'il manque quelque chose."
    )

    plan = terraform("plan", "-input=false", "-no-color", "-out=plan.tfplan", cwd=applied)
    assert plan.returncode == 0, f"Le plan a échoué.\n{plan.stderr[-1200:]}"
    montre = terraform("show", "-json", "plan.tfplan", cwd=applied)
    assert montre.returncode == 0, f"`show -json` du plan a échoué.\n{montre.stderr}"

    actions = {
        c["address"]: c["change"]["actions"]
        for c in json.loads(montre.stdout).get("resource_changes", [])
        if c["change"]["actions"] != ["no-op"]
    }
    assert actions == {"local_file.rapport": ["create"]}, (
        f"Le plan annonce {actions}, attendu une seule création sur "
        "`local_file.rapport`.\n\nL'identifiant ne doit pas être retiré : il n'a "
        "pas dérivé, et le remplacer changerait le contenu du rapport à recréer."
    )


# --------------------------------------------------------------------------
# 7. La convergence répare, sans toucher au code.
# --------------------------------------------------------------------------
def test_la_convergence_restaure_sans_changer_l_identifiant(
    applied: Path, identifiant_avant: str
) -> None:
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=applied)
    assert app.returncode == 0, f"La convergence a échoué.\n{app.stderr[-1500:]}"

    sorties = output_json(applied)
    assert sorties["identifiant"]["value"] == identifiant_avant, (
        f"L'identifiant vaut {sorties['identifiant']['value']!r} après la "
        f"réparation, contre {identifiant_avant!r} avant la dérive.\n\nIl a été "
        "regénéré : c'est le comportement du script impératif, pas celui qu'on "
        "attend ici. Regardez ce qui décide de sa stabilité."
    )

    chemin = (applied / sorties["chemin_rapport"]["value"]).resolve()
    assert chemin.is_file(), "Le rapport n'est pas revenu après la convergence."
    assert identifiant_avant in chemin.read_text(encoding="utf-8"), (
        "Le rapport recréé ne porte plus l'identifiant d'origine."
    )

    stable = terraform(
        "plan", "-detailed-exitcode", "-input=false", "-no-color", cwd=applied
    )
    assert stable.returncode == 0, (
        f"Après réparation, le plan rend encore {stable.returncode} : la "
        "configuration n'a pas convergé."
    )


# --------------------------------------------------------------------------
# 8. Les deux côtés : le script diverge, la configuration converge.
# --------------------------------------------------------------------------
def test_le_script_diverge_la_ou_la_configuration_converge(
    applied: Path, tmp_path: Path, identifiant_avant: str
) -> None:
    # Le script est joué dans un répertoire jetable : il fabrique ses propres
    # sorties, et le workdir de l'apprenant n'a pas à les porter.
    bac = tmp_path / "imperatif"
    bac.mkdir()
    shutil.copy2(applied / "imperatif.sh", bac / "imperatif.sh")

    releves = []
    for passage in (1, 2):
        proc = subprocess.run(
            ["bash", "imperatif.sh"], cwd=bac, capture_output=True, text=True,
            check=False,
        )
        assert proc.returncode == 0, (
            f"`imperatif.sh` a échoué au passage {passage}.\n{proc.stderr}"
        )
        releves.append((bac / "sortie-imperative" / "dernier-id.txt").read_text().strip())

    assert releves[0] != releves[1], (
        "Les deux passages du script impératif ont donné le même identifiant. "
        "Le script fourni est censé diverger : vérifiez qu'il n'a pas été "
        "modifié, il se lit et ne se corrige pas."
    )
    lignes = (bac / "sortie-imperative" / "rapport.txt").read_text().splitlines()
    assert len(lignes) == 2, (
        f"Le rapport impératif porte {len(lignes)} ligne(s) après deux passages, "
        "attendu 2 : son `>>` empile, l'état dépend du nombre d'exécutions."
    )

    # L'autre côté, et il n'est atteignable qu'après le travail : la même
    # intention, décrite au lieu d'être exécutée, ne bouge plus.
    for _ in range(2):
        rejeu = terraform(
            "apply", "-auto-approve", "-input=false", "-no-color", cwd=applied
        )
        assert rejeu.returncode == 0, f"Le rejeu a échoué.\n{rejeu.stderr[-1200:]}"

    assert output_json(applied)["identifiant"]["value"] == identifiant_avant, (
        "L'identifiant a changé après deux applications supplémentaires. La "
        "configuration se comporte comme le script : elle décrit encore des "
        "étapes, pas un état."
    )
    contenu = (applied / output_json(applied)["chemin_rapport"]["value"]).read_text(
        encoding="utf-8"
    )
    assert contenu.count(identifiant_avant) == 1, (
        "Le rapport a grossi au fil des applications. Un état ne s'empile pas."
    )
