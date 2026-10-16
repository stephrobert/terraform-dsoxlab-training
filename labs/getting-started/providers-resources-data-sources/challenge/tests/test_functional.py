"""Tests fonctionnels du lab « ce que Terraform gere, ce qu'il se contente de lire ».

Tant qu'on n'a pas vu un `destroy` effacer les objets geres sans toucher a ce
que la data source lisait, on croit qu'un bloc `data` est une resource en
lecture seule.

## La preuve centrale

`terraform show -json` separe les deux natures sans ambiguite : un bloc cree
sort en `"mode": "managed"`, un bloc de lecture en `"mode": "data"`. Aucun
`.tf` n'est relu, et recopier le contenu du catalogue dans une ressource au lieu
de le lire produirait `managed` la ou `data` est attendu.

## Les deux consequences que le lab impose

Une data source ne cree rien : apres le `destroy`, le fichier qu'elle lisait est
toujours la, octet pour octet.

Et elle est relue a CHAQUE plan : modifier ce fichier, sans toucher une ligne de
HCL, fait passer `plan -detailed-exitcode` de 0 a 2. Un retour 0 dans ce cas
signifierait que la valeur lue n'irrigue rien.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from conftest import exiger_workdir, message, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "getting-started-providers-resources-data-sources"

CATALOGUE = "catalogue.txt"
ADRESSE_DATA = "data.local_file.catalogue"

GEREES_ATTENDUES = {"local_file.resume", "null_resource.sceau", "random_pet.empreinte"}
PROVIDERS_ATTENDUS = {
    "registry.terraform.io/hashicorp/local",
    "registry.terraform.io/hashicorp/null",
    "registry.terraform.io/hashicorp/random",
}


def _tf(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["terraform", *args], cwd=cwd or WORKDIR, capture_output=True, text=True, check=False
    )


@pytest.fixture(scope="module")
def joue() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)

    init = _tf("init", "-input=false", "-no-color")
    assert init.returncode == 0, message(
        en="`terraform init` failed.\n\nThe `required_providers` block is "
        "probably incomplete: `init` can install nothing as long as it does not "
        f"know what.\n\n{init.stderr[-1000:]}",
        fr="`terraform init` a échoué.\n\nLe bloc `required_providers` est "
        "probablement incomplet : `init` ne peut rien installer tant qu'il ne "
        f"sait pas quoi.\n\n{init.stderr[-1000:]}",
    )

    applique = _tf("apply", "-auto-approve", "-input=false", "-no-color")
    assert applique.returncode == 0, message(
        en=f"`terraform apply` failed.\n{applique.stderr[-1000:]}",
        fr=f"`terraform apply` a échoué.\n{applique.stderr[-1000:]}",
    )
    return WORKDIR


@pytest.fixture(scope="module")
def etat(joue: Path) -> dict:
    proc = _tf("show", "-json")
    proc.check_returncode()
    return json.loads(proc.stdout)


def _par_mode(etat: dict) -> dict[str, set[str]]:
    racine = etat.get("values", {}).get("root_module", {})
    trouve: dict[str, set[str]] = {"managed": set(), "data": set()}
    for r in racine.get("resources", []):
        trouve.setdefault(r["mode"], set()).add(r["address"])
    return trouve


# --------------------------------------------------------------------------
# 1. Les providers sont contraints, et installes.
# --------------------------------------------------------------------------
def test_les_trois_providers_sont_contraints_et_installes(joue: Path) -> None:
    """`version -json` dit ce qui est REELLEMENT en place, pas ce qui est ecrit."""
    proc = _tf("version", "-json")
    proc.check_returncode()
    installes = set(json.loads(proc.stdout).get("provider_selections", {}))

    manquants = PROVIDERS_ATTENDUS - installes
    assert not manquants, message(
        en=f"These providers are not installed: {sorted(manquants)}.\n"
        f"Installed: {sorted(installes)}.",
        fr=f"Ces providers ne sont pas installés : {sorted(manquants)}.\n"
        f"Installés : {sorted(installes)}.",
    )

    verrou = joue / ".terraform.lock.hcl"
    assert verrou.is_file(), message(
        en="`.terraform.lock.hcl` is missing: `init` did not succeed.",
        fr="`.terraform.lock.hcl` est absent : `init` n'a pas abouti.",
    )
    contenu = verrou.read_text(encoding="utf-8")
    for provider in PROVIDERS_ATTENDUS:
        assert 'constraints' in contenu and provider in contenu, message(
            en=f"The lock carries no constraint for {provider}.\n\nA "
            "version constraint is expected, not a free installation.",
            fr=f"Le verrou ne porte pas de contrainte pour {provider}.\n\nUne "
            "contrainte de version est attendue, pas une installation libre.",
        )


# --------------------------------------------------------------------------
# 2. La preuve centrale : deux natures, deux modes.
# --------------------------------------------------------------------------
def test_le_catalogue_est_lu_et_non_gere(etat: dict) -> None:
    """Recopier le contenu au lieu de le lire produirait `managed` ici."""
    modes = _par_mode(etat)

    assert ADRESSE_DATA in modes["data"], message(
        en=f"`{ADRESSE_DATA}` is not in `mode: data`.\n"
        f"Addresses in data: {sorted(modes['data']) or 'none'}\n"
        f"Addresses in managed: {sorted(modes['managed'])}\n\n"
        "The catalogue already exists on disk: Terraform must READ it. A "
        "block that writes it manages it, and would destroy it at `destroy`.",
        fr=f"`{ADRESSE_DATA}` n'est pas en `mode: data`.\n"
        f"Adresses en data : {sorted(modes['data']) or 'aucune'}\n"
        f"Adresses en managed : {sorted(modes['managed'])}\n\n"
        "Le catalogue existe déjà sur le disque : Terraform doit le LIRE. Un "
        "bloc qui l'écrit le gère, et le détruirait au `destroy`.",
    )
    assert ADRESSE_DATA not in modes["managed"], message(
        en=f"`{ADRESSE_DATA}` appears as `managed`: that block creates the file instead "
        "of reading it.",
        fr=f"`{ADRESSE_DATA}` figure en `managed` : ce bloc crée le fichier au lieu "
        "de le lire.",
    )


def test_les_trois_objets_geres_sont_presents(etat: dict) -> None:
    modes = _par_mode(etat)
    assert modes["managed"] == GEREES_ATTENDUES, message(
        en=f"Managed objects: {sorted(modes['managed'])}.\n"
        f"Expected: {sorted(GEREES_ATTENDUES)}.",
        fr=f"Objets gérés : {sorted(modes['managed'])}.\n"
        f"Attendus : {sorted(GEREES_ATTENDUES)}.",
    )


# --------------------------------------------------------------------------
# 3. La dependance vient de la REFERENCE, et la valeur irrigue vraiment.
# --------------------------------------------------------------------------
def test_ce_qui_est_ecrit_derive_de_ce_qui_est_lu(joue: Path, etat: dict) -> None:
    """Le `triggers` du sceau doit porter le contenu REEL du catalogue.

    Une valeur recopiee a la main passerait ce test aujourd'hui et tomberait sur
    le suivant, qui change le fichier.
    """
    racine = etat["values"]["root_module"]["resources"]
    sceau = next((r for r in racine if r["address"] == "null_resource.sceau"), None)
    assert sceau is not None, message(
        en="`null_resource.sceau` is absent from the state.",
        fr="`null_resource.sceau` est absent du state.",
    )

    declencheurs = sceau["values"].get("triggers") or {}
    assert len(declencheurs) >= 2, message(
        en=f"`triggers` carries {len(declencheurs)} entry(ies), two expected: the "
        "value drawn at random AND what the catalogue contains.",
        fr=f"`triggers` porte {len(declencheurs)} entrée(s), deux attendues : la "
        "valeur tirée au sort ET ce que le catalogue contient.",
    )

    contenu = (joue / CATALOGUE).read_text(encoding="utf-8")
    assert contenu in declencheurs.values(), message(
        en="No `triggers` carries the catalogue's content.\n\nIt must come from "
        "the data source, by reference: that is what creates the dependency.",
        fr="Aucun `triggers` ne porte le contenu du catalogue.\n\nIl doit venir de "
        "la data source, par référence : c'est elle qui crée la dépendance.",
    )

    empreinte = next(
        (r["values"]["id"] for r in racine if r["address"] == "random_pet.empreinte"), None
    )
    assert empreinte in declencheurs.values(), message(
        en="No `triggers` carries the `random_pet`'s identifier.\n\nThat "
        "value is only known after creation: referencing it is the only "
        "way to obtain it.",
        fr="Aucun `triggers` ne porte l'identifiant du `random_pet`.\n\nCette "
        "valeur n'est connue qu'après création : la référencer est la seule "
        "façon de l'obtenir.",
    )


def test_les_deux_sorties_viennent_de_deux_natures(joue: Path) -> None:
    proc = _tf("output", "-json")
    proc.check_returncode()
    sorties = json.loads(proc.stdout or "{}")

    for nom in ("empreinte", "catalogue_lu"):
        assert nom in sorties, message(
            en=f"The output `{nom}` is missing. Present: {sorted(sorties)}.",
            fr=f"La sortie `{nom}` est absente. Présentes : {sorted(sorties)}.",
        )
        assert sorties[nom]["value"], message(
            en=f"The output `{nom}` is empty.",
            fr=f"La sortie `{nom}` est vide.",
        )

    contenu = (joue / CATALOGUE).read_text(encoding="utf-8")
    assert sorties["catalogue_lu"]["value"] == contenu, message(
        en="`catalogue_lu` does not return the file's content.\n\nIt must come from "
        "the data source, not from a value written by hand.",
        fr="`catalogue_lu` ne rend pas le contenu du fichier.\n\nElle doit venir de "
        "la data source, pas d'une valeur écrite à la main.",
    )


# --------------------------------------------------------------------------
# 4. Une data source est relue a CHAQUE plan.
# --------------------------------------------------------------------------
def test_modifier_le_fichier_lu_fait_bouger_le_plan(joue: Path) -> None:
    """Aucun `.tf` n'est touche, et pourtant le plan change.

    C'est la seconde consequence, celle qu'on ne voit pas venir : une data
    source n'est pas un cache. Elle est relue a chaque plan, et ce qu'elle
    irrigue bouge avec elle.

    Le fichier est remis dans son etat d'origine a la fin, quoi qu'il arrive :
    sans cela, le test laisserait le lab en derive et fausserait les suivants.
    """
    stable = _tf("plan", "-detailed-exitcode", "-input=false", "-no-color")
    assert stable.returncode == 0, message(
        en=f"Before any modification, `plan -detailed-exitcode` returns "
        f"{stable.returncode}, expected 0.\n{stable.stdout[-800:]}",
        fr=f"Avant toute modification, `plan -detailed-exitcode` rend "
        f"{stable.returncode}, attendu 0.\n{stable.stdout[-800:]}",
    )

    catalogue = joue / CATALOGUE
    origine = catalogue.read_text(encoding="utf-8")
    try:
        catalogue.write_text(origine + "revision=4\n", encoding="utf-8")
        apres = _tf("plan", "-detailed-exitcode", "-input=false", "-no-color")
        assert apres.returncode == 2, message(
            en=f"After modifying `{CATALOGUE}`, with no `.tf` having "
            f"moved, `plan -detailed-exitcode` returns {apres.returncode}, "
            "expected 2.\n\n"
            + (
                "A 0 means that what the data source reads feeds nothing: "
                "the value read must feed at least one resource."
                if apres.returncode == 0
                else "A 1 signals an error."
            ),
            fr=f"Après modification de `{CATALOGUE}`, sans qu'aucun `.tf` ait "
            f"bougé, `plan -detailed-exitcode` rend {apres.returncode}, "
            "attendu 2.\n\n"
            + (
                "Un 0 signifie que ce que la data source lit n'irrigue rien : "
                "la valeur lue doit alimenter au moins une ressource."
                if apres.returncode == 0
                else "Un 1 signale une erreur."
            ),
        )
    finally:
        catalogue.write_text(origine, encoding="utf-8")
        _tf("apply", "-auto-approve", "-input=false", "-no-color")


# --------------------------------------------------------------------------
# 5. Les deux cotes du destroy, et c'est lui qui tranche.
# --------------------------------------------------------------------------
def test_le_destroy_emporte_le_gere_et_laisse_le_lu(joue: Path, tmp_path: Path) -> None:
    """Le `destroy` se joue dans une COPIE, pour ne pas vider le lab.

    Les tests de ce catalogue peuvent etre relances ; un destroy joue dans le
    repertoire de l'apprenant obligerait a tout reappliquer entre deux
    executions.
    """
    copie = tmp_path / "destruction"
    shutil.copytree(joue, copie)

    empreinte_avant = (copie / CATALOGUE).read_bytes()

    detruit = _tf("destroy", "-auto-approve", "-input=false", "-no-color", cwd=copie)
    assert detruit.returncode == 0, message(
        en=f"`destroy` failed.\n{detruit.stderr[-1000:]}",
        fr=f"`destroy` a échoué.\n{detruit.stderr[-1000:]}",
    )

    montre = _tf("show", "-json", cwd=copie)
    montre.check_returncode()
    restantes = (
        json.loads(montre.stdout).get("values", {}).get("root_module", {}).get("resources", [])
    )
    assert not restantes, message(
        en=f"The state still carries {[r['address'] for r in restantes]} after the "
        "destroy.",
        fr=f"Le state porte encore {[r['address'] for r in restantes]} après le "
        "destroy.",
    )

    assert not (copie / "resume.txt").exists(), message(
        en="`resume.txt` survived the destroy: Terraform managed it, so it had to "
        "disappear with the rest.",
        fr="`resume.txt` a survécu au destroy : Terraform le gérait, il devait "
        "disparaître avec le reste.",
    )

    catalogue = copie / CATALOGUE
    assert catalogue.is_file(), message(
        en=f"`{CATALOGUE}` has DISAPPEARED.\n\nTerraform does not destroy what it never "
        "created. If it is gone, then a `resource` block managed it instead "
        "of a `data` block.",
        fr=f"`{CATALOGUE}` a DISPARU.\n\nTerraform ne détruit pas ce qu'il n'a "
        "jamais créé. S'il est parti, c'est qu'un bloc `resource` le gérait au "
        "lieu d'un bloc `data`.",
    )
    assert catalogue.read_bytes() == empreinte_avant, message(
        en=f"`{CATALOGUE}` was modified by the destroy; byte for byte it "
        "had to stay identical.",
        fr=f"`{CATALOGUE}` a été modifié par le destroy, octet pour octet il "
        "devait rester identique.",
    )
