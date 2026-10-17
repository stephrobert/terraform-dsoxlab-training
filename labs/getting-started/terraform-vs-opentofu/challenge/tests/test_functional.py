"""test_functional.py : getting-started/terraform-vs-opentofu

Huit preuves que « les deux outils sont compatibles » est vrai à moitié.

Les cinq premières se jouent avec le binaire présent. Les trois dernières
exigent le second et, s'il manque, SKIPPENT explicitement : un lab ne recale pas
un apprenant pour un outil qu'il n'a pas installé.

Aucun test n'ouvre les `.tf`. Le sourcing se lit dans `version -json`, les
contraintes dans le fichier de verrouillage, qu'aucun humain n'écrit.
"""

from __future__ import annotations

import json
import re
import shutil
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
LAB_ID = "getting-started-terraform-vs-opentofu"

PROVIDERS = ("local", "null", "random")
GEREES_ATTENDUES = {
    "random_pet.nom",
    "local_file.rapport",
    "null_resource.empreinte",
}
REGISTRE_TERRAFORM = "registry.terraform.io"
REGISTRE_OPENTOFU = "registry.opentofu.org"

SECOND_OUTIL = "tofu"


@pytest.fixture(scope="module")
def prepared() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(message(
            en=f"`terraform init` failed.\n{init.stderr[-1200:]}",
            fr=f"`terraform init` a échoué.\n{init.stderr[-1200:]}",
        ))
    return WORKDIR


@pytest.fixture(scope="module")
def verrou_regenere(prepared: Path, tmp_path_factory) -> Path:
    """Un verrou reconstruit depuis zéro, dans une copie, pour l'observer.

    Mesuré le 2026-09-18, et c'est un faux négatif qu'on répare ici :
    `constraints` n'est écrit dans `.terraform.lock.hcl` qu'à la CRÉATION de
    l'entrée. Un apprenant qui lance `terraform init` avant d'écrire ses
    contraintes garde un verrou sans `constraints`, et plus rien ne l'y ajoute :
    ni un `init` ordinaire, ni même un `init -upgrade`. Vérifié dans les deux
    cas. Son travail devenait invisible, et le lab le recalait à 6/8 alors que
    sa configuration était juste.

    On travaille donc sur une copie, où le verrou est supprimé puis reconstruit.
    La reconstruction re-résout depuis SA configuration : sans déclaration, le
    verrou revient sans contrainte, et la mesure garde tout son sens.
    """
    copie = tmp_path_factory.mktemp("verrou") / "work"
    shutil.copytree(prepared, copie)
    (copie / ".terraform.lock.hcl").unlink(missing_ok=True)
    init = terraform("init", "-input=false", "-no-color", cwd=copie)
    if init.returncode != 0:
        pytest.fail(
            message(
            en=f"Rebuilding the lock failed.\n{init.stderr[-1200:]}",
            fr=f"La reconstruction du verrou a échoué.\n{init.stderr[-1200:]}",
        )
        )
    return copie


@pytest.fixture(scope="module")
def applied(prepared: Path) -> Path:
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=prepared)
    if app.returncode != 0:
        pytest.fail(
            message(
            en="`terraform apply` failed.\n\nIf the message mentions \"Provider "
            "configuration not present\", it is because the provider named by "
            "alias in main.tf is not configured yet: that is the whole "
            f"work of the lab.\n{app.stderr[-1500:]}",
            fr="`terraform apply` a échoué.\n\nSi le message parle de « Provider "
            "configuration not present », c'est que le provider désigné par "
            "alias dans main.tf n'est pas encore configuré : c'est tout le "
            f"travail du lab.\n{app.stderr[-1500:]}",
        )
        )
    return prepared


def verrou(cwd: Path) -> dict[str, dict[str, str]]:
    """Le fichier de verrouillage, lu par adresse pleinement qualifiée.

    Il est écrit par l'outil, jamais à la main : c'est donc une observation de
    l'état, et non une lecture du code de l'apprenant.
    """
    fichier = cwd / ".terraform.lock.hcl"
    if not fichier.is_file():
        return {}
    trouves = {}
    for bloc in re.finditer(
        r'provider\s+"([^"]+)"\s*\{(.*?)\n\}', fichier.read_text(encoding="utf-8"),
        re.DOTALL,
    ):
        adresse, corps = bloc.group(1), bloc.group(2)
        version = re.search(r'version\s*=\s*"([^"]+)"', corps)
        contrainte = re.search(r'constraints\s*=\s*"([^"]+)"', corps)
        trouves[adresse] = {
            "version": version.group(1) if version else "",
            "constraints": contrainte.group(1) if contrainte else "",
        }
    return trouves


def satisfait(version: str, contrainte: str) -> bool:
    """`~> 2.5` accepte 2.5.0 et 2.9.1, jamais 3.0.0."""
    if not contrainte.startswith("~>"):
        return False
    borne = [int(n) for n in contrainte[2:].strip().split(".")]
    reelle = [int(n) for n in version.split(".")]
    if reelle[: len(borne) - 1] != borne[: len(borne) - 1]:
        return False
    return reelle[len(borne) - 1] >= borne[-1]


def outil_second_present() -> bool:
    return shutil.which(SECOND_OUTIL) is not None


# --------------------------------------------------------------------------
# 1. Les contraintes sont pessimistes, et aucune n'est flottante.
# --------------------------------------------------------------------------
def test_les_trois_providers_portent_une_contrainte_pessimiste(
    verrou_regenere: Path,
) -> None:
    verrouille = verrou(verrou_regenere)
    assert verrouille, message(
        en="`.terraform.lock.hcl` is missing or unreadable: `terraform init` did "
        "not resolve the providers.",
        fr="`.terraform.lock.hcl` est absent ou illisible : `terraform init` n'a "
        "pas résolu les providers.",
    )

    for court in PROVIDERS:
        adresse = f"{REGISTRE_TERRAFORM}/hashicorp/{court}"
        assert adresse in verrouille, message(
            en=f"{adresse} is not locked. The lock carries "
            f"{sorted(verrouille)}.",
            fr=f"{adresse} n'est pas verrouillé. Le verrou porte "
            f"{sorted(verrouille)}.",
        )
        contrainte = verrouille[adresse]["constraints"]
        assert contrainte, message(
            en=f"{court} is locked WITHOUT a constraint. That is the signature of "
            "implicit sourcing: the provider was guessed, not declared. A "
            "configuration without `required_providers` applies perfectly well, and "
            "is portable nowhere.",
            fr=f"{court} est verrouillé SANS contrainte. C'est la signature du "
            "sourcing implicite : le provider a été deviné, pas déclaré. Une "
            "configuration sans `required_providers` s'applique très bien, et "
            "n'est portable nulle part.",
        )
        assert contrainte.startswith("~>"), message(
            en=f"The constraint of {court} is {contrainte!r}, a pessimistic "
            "`~> x.y` constraint was expected. A pinned version forbids "
            "patches, a floating version lets each binary resolve "
            "whatever it likes.",
            fr=f"La contrainte de {court} vaut {contrainte!r}, attendu une "
            "contrainte pessimiste `~> x.y`. Une version figée interdit les "
            "correctifs, une version flottante laisse chaque binaire résoudre "
            "ce qu'il veut.",
        )


# --------------------------------------------------------------------------
# 2. Le sourcing est explicite, et les versions retenues le respectent.
# --------------------------------------------------------------------------
def test_le_sourcing_est_pleinement_qualifie(verrou_regenere: Path) -> None:
    proc = terraform("version", "-json", cwd=verrou_regenere)
    assert proc.returncode == 0, message(
        en=f"`terraform version -json` failed.\n{proc.stderr}",
        fr=f"`terraform version -json` a échoué.\n{proc.stderr}",
    )
    choisis = json.loads(proc.stdout).get("provider_selections", {})

    verrouille = verrou(verrou_regenere)
    for court in PROVIDERS:
        adresse = f"{REGISTRE_TERRAFORM}/hashicorp/{court}"
        assert adresse in choisis, message(
            en=f"{adresse} does not appear in `provider_selections`, which carries "
            f"{sorted(choisis)}.",
            fr=f"{adresse} n'apparaît pas dans `provider_selections`, qui porte "
            f"{sorted(choisis)}.",
        )
        contrainte = verrouille[adresse]["constraints"]
        assert satisfait(choisis[adresse], contrainte), message(
            en=f"{court} {choisis[adresse]} does not satisfy {contrainte!r}.",
            fr=f"{court} {choisis[adresse]} ne satisfait pas {contrainte!r}.",
        )


# --------------------------------------------------------------------------
# 3. Le state porte les trois ressources, et le rapport existe.
# --------------------------------------------------------------------------
def test_le_state_porte_les_trois_ressources_et_le_rapport(applied: Path) -> None:
    etat = show_json(applied)
    ressources = etat.get("values", {}).get("root_module", {}).get("resources", [])
    gerees = {r["address"] for r in ressources if r["mode"] == "managed"}
    assert gerees == GEREES_ATTENDUES, message(
        en=f"The state manages {sorted(gerees)}.\nExpected: {sorted(GEREES_ATTENDUES)}.",
        fr=f"Le state gère {sorted(gerees)}.\nAttendu : {sorted(GEREES_ATTENDUES)}.",
    )

    identifiant = next(
        r["values"]["id"] for r in ressources if r["address"] == "random_pet.nom"
    )
    assert identifiant, message(
        en="The identifier of the `random_pet` is empty.",
        fr="L'identifiant du `random_pet` est vide.",
    )

    rapport = next(r for r in ressources if r["address"] == "local_file.rapport")
    chemin = (applied / rapport["values"]["filename"]).resolve()
    assert chemin.is_file(), message(
        en=f"The report announced at {chemin} does not exist.",
        fr=f"Le rapport annoncé en {chemin} n'existe pas.",
    )
    assert identifiant in chemin.read_text(encoding="utf-8"), message(
        en="The report does not carry the identifier from the state.",
        fr="Le rapport ne porte pas l'identifiant du state.",
    )


# --------------------------------------------------------------------------
# 4. La sortie vaut ce que dit le state.
# --------------------------------------------------------------------------
def test_la_sortie_vaut_l_identifiant_du_state(applied: Path) -> None:
    sorties = output_json(applied)
    assert "nom_animal" in sorties, message(
        en=f"The `nom_animal` output is missing. Present: {sorted(sorties)}.",
        fr=f"La sortie `nom_animal` est absente. Présentes : {sorted(sorties)}.",
    )
    ressources = show_json(applied)["values"]["root_module"]["resources"]
    identifiant = next(
        r["values"]["id"] for r in ressources if r["address"] == "random_pet.nom"
    )
    assert sorties["nom_animal"]["value"] == identifiant, message(
        en=f"`nom_animal` is {sorties['nom_animal']['value']!r}, the state carries "
        f"{identifiant!r}.",
        fr=f"`nom_animal` vaut {sorties['nom_animal']['value']!r}, le state porte "
        f"{identifiant!r}.",
    )


# --------------------------------------------------------------------------
# 5. L'idempotence, par le code retour.
# --------------------------------------------------------------------------
def test_le_plan_ne_propose_rien_juste_apres_l_application(applied: Path) -> None:
    plan = terraform(
        "plan", "-detailed-exitcode", "-input=false", "-no-color", cwd=applied
    )
    assert plan.returncode == 0, message(
        en=f"`plan -detailed-exitcode` returns {plan.returncode}, expected 0.\n"
        f"{plan.stdout[-1200:]}",
        fr=f"`plan -detailed-exitcode` rend {plan.returncode}, attendu 0.\n"
        f"{plan.stdout[-1200:]}",
    )


# --------------------------------------------------------------------------
# 6. Le second outil lit le MÊME state, sans rien détruire.
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def copie_pour_le_second_outil(applied: Path, tmp_path_factory) -> Path:
    """Le second outil travaille sur une copie, et pour une bonne raison.

    Son `init` RÉÉCRIT le fichier de verrouillage sur son propre registre.
    Le faire dans le répertoire de l'apprenant rendrait son `terraform` inutile
    jusqu'à un `init -upgrade`. Un test ne casse pas ce qu'il mesure.
    """
    if not outil_second_present():
        pytest.skip(
            f"{SECOND_OUTIL} n'est pas installé : la démonstration croisée est "
            "ignorée, jamais comptée en échec."
        )
    copie = tmp_path_factory.mktemp("croise") / "work"
    shutil.copytree(applied, copie)
    init = _second(copie, "init", "-input=false", "-no-color")
    assert init.returncode == 0, message(
        en=f"`{SECOND_OUTIL} init` failed on the state produced by terraform.\n"
        f"{init.stderr[-1500:]}",
        fr=f"`{SECOND_OUTIL} init` a échoué sur le state produit par terraform.\n"
        f"{init.stderr[-1500:]}",
    )
    return copie


def _second(cwd: Path, *args: str):
    import subprocess

    return subprocess.run(
        [SECOND_OUTIL, *args], cwd=cwd, capture_output=True, text=True, check=False
    )


def test_le_second_outil_reprend_le_state_sans_rien_detruire(
    copie_pour_le_second_outil: Path, applied: Path
) -> None:
    plan = _second(
        copie_pour_le_second_outil,
        "plan", "-detailed-exitcode", "-input=false", "-no-color",
    )
    assert plan.returncode == 0, message(
        en=f"`{SECOND_OUTIL} plan -detailed-exitcode` returns {plan.returncode}, "
        "expected 0. The second tool proposes to modify an infrastructure "
        f"it did not create.\n{plan.stdout[-1500:]}",
        fr=f"`{SECOND_OUTIL} plan -detailed-exitcode` rend {plan.returncode}, "
        "attendu 0. Le second outil propose de modifier une infrastructure "
        f"qu'il n'a pas créée.\n{plan.stdout[-1500:]}",
    )

    sien = _second(copie_pour_le_second_outil, "output", "-json")
    assert sien.returncode == 0, message(
        en=f"`{SECOND_OUTIL} output -json` failed.\n{sien.stderr}",
        fr=f"`{SECOND_OUTIL} output -json` a échoué.\n{sien.stderr}",
    )
    assert (
        json.loads(sien.stdout)["nom_animal"]["value"]
        == output_json(applied)["nom_animal"]["value"]
    ), message(
        en="The two tools do not read the same value from the same state.",
        fr="Les deux outils ne lisent pas la même valeur dans le même state.",
    )


# --------------------------------------------------------------------------
# 7. Le même provider, la même version, un autre registre.
# --------------------------------------------------------------------------
def test_le_second_outil_resout_sur_son_propre_registre(
    copie_pour_le_second_outil: Path, prepared: Path
) -> None:
    proc = _second(copie_pour_le_second_outil, "version", "-json")
    assert proc.returncode == 0, message(
        en=f"`{SECOND_OUTIL} version -json` failed.\n{proc.stderr}",
        fr=f"`{SECOND_OUTIL} version -json` a échoué.\n{proc.stderr}",
    )
    siens = json.loads(proc.stdout).get("provider_selections", {})

    nôtres = json.loads(
        terraform("version", "-json", cwd=prepared).stdout
    ).get("provider_selections", {})

    for court in PROVIDERS:
        chez_lui = f"{REGISTRE_OPENTOFU}/hashicorp/{court}"
        chez_nous = f"{REGISTRE_TERRAFORM}/hashicorp/{court}"
        assert chez_lui in siens, message(
            en=f"{chez_lui} does not appear in the selections of {SECOND_OUTIL}, "
            f"which carry {sorted(siens)}.",
            fr=f"{chez_lui} n'apparaît pas dans les sélections de {SECOND_OUTIL}, "
            f"qui portent {sorted(siens)}.",
        )
        assert siens[chez_lui] == nôtres[chez_nous], message(
            en=f"{court} is {siens[chez_lui]} with {SECOND_OUTIL} and "
            f"{nôtres[chez_nous]} with terraform. The pessimistic constraint must "
            "give the same version on both sides.",
            fr=f"{court} vaut {siens[chez_lui]} chez {SECOND_OUTIL} et "
            f"{nôtres[chez_nous]} chez terraform. La contrainte pessimiste doit "
            "donner la même version des deux côtés.",
        )


# --------------------------------------------------------------------------
# 8. Les deux côtés : le state est portable, le verrou ne l'est pas.
# --------------------------------------------------------------------------
def test_le_verrou_reecrit_arrete_terraform_jusqu_a_un_upgrade(
    copie_pour_le_second_outil: Path,
) -> None:
    copie = copie_pour_le_second_outil

    # Ce que le passage du second outil a laissé derrière lui.
    adresses = set(verrou(copie))
    assert any(a.startswith(REGISTRE_OPENTOFU) for a in adresses), message(
        en=f"After `{SECOND_OUTIL} init`, the lock carries no "
        f"{REGISTRE_OPENTOFU} address. It carries {sorted(adresses)}.",
        fr=f"Après `{SECOND_OUTIL} init`, le verrou ne porte aucune adresse "
        f"{REGISTRE_OPENTOFU}. Il porte {sorted(adresses)}.",
    )
    assert not any(a.startswith(REGISTRE_TERRAFORM) for a in adresses), message(
        en="The lock still carries terraform addresses: the expected rewrite "
        "did not happen, and the rest of the test measures nothing.",
        fr="Le verrou porte encore des adresses terraform : la réécriture "
        "attendue n'a pas eu lieu, et le reste du test ne mesure rien.",
    )

    # Le state, lui, est parfaitement lisible : c'est la moitié qui rassure.
    arrete = terraform("plan", "-detailed-exitcode", "-input=false", "-no-color", cwd=copie)
    assert arrete.returncode == 1, message(
        en=f"terraform returns {arrete.returncode} on a lock rewritten by "
        f"{SECOND_OUTIL}, expected 1.\n\nThis is the heart of the lab: portability "
        "covers the STATE, not the lock file. The state is "
        "read back without harm, the lock is rewritten against the other registry, and "
        "terraform stops dead.\n"
        f"{arrete.stderr[-800:]}",
        fr=f"terraform rend {arrete.returncode} sur un verrou réécrit par "
        f"{SECOND_OUTIL}, attendu 1.\n\nC'est le cœur du lab : la portabilité "
        "porte sur le STATE, pas sur le fichier de verrouillage. Le state est "
        "relu sans dommage, le verrou est réécrit sur l'autre registre, et "
        "terraform s'arrête net.\n"
        f"{arrete.stderr[-800:]}",
    )
    assert "lock file" in arrete.stderr.lower(), message(
        en=f"terraform stops for a reason other than the lock:\n"
        f"{arrete.stderr[-800:]}",
        fr=f"terraform s'arrête pour une autre raison que le verrou :\n"
        f"{arrete.stderr[-800:]}",
    )

    # Et la moitié qui répare : un init -upgrade reprend la main, sans que le
    # state ni l'infrastructure n'aient bougé d'un octet.
    reprise = terraform("init", "-upgrade", "-input=false", "-no-color", cwd=copie)
    assert reprise.returncode == 0, message(
        en=f"`terraform init -upgrade` does not take over.\n{reprise.stderr[-1200:]}",
        fr=f"`terraform init -upgrade` ne reprend pas la main.\n{reprise.stderr[-1200:]}",
    )
    stable = terraform("plan", "-detailed-exitcode", "-input=false", "-no-color", cwd=copie)
    assert stable.returncode == 0, message(
        en=f"After `init -upgrade`, the plan returns {stable.returncode}, expected 0. "
        "The round trip between the two tools would therefore have changed something, "
        "which would ruin the compatibility argument.\n"
        f"{stable.stdout[-1200:]}",
        fr=f"Après `init -upgrade`, le plan rend {stable.returncode}, attendu 0. "
        "L'aller-retour entre les deux outils aurait donc modifié quelque "
        "chose, ce qui ruinerait l'argument de compatibilité.\n"
        f"{stable.stdout[-1200:]}",
    )
