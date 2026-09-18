"""test_functional.py : getting-started/terraform-overview

Huit preuves que Terraform a une mémoire, et que cette mémoire est le state.

Aucun test n'ouvre les fichiers `.tf` de l'apprenant, et aucun ne lit une sortie
destinée à un humain pour en tirer un état : tout passe par du JSON structuré et
des codes retour. La seule sortie humaine consultée l'est pour vérifier qu'elle
MASQUE quelque chose, ce qui est précisément son rôle.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path

import pytest

from conftest import exiger_workdir, output_json, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "getting-started-terraform-overview"

PROVIDERS_ATTENDUS = {
    "registry.terraform.io/hashicorp/local",
    "registry.terraform.io/hashicorp/null",
    "registry.terraform.io/hashicorp/random",
}
GEREES_ATTENDUES = {"random_pet.nom", "local_file.rapport"}
TEMOIN = "inventaire.txt"


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


def ressources(cwd: Path) -> list[dict]:
    """Les ressources du state résolu, gérées comme lues."""
    etat = show_json(cwd)
    return etat.get("values", {}).get("root_module", {}).get("resources", [])


# --------------------------------------------------------------------------
# 1. Les trois providers déclarés sont installés ET verrouillés.
# --------------------------------------------------------------------------
def test_les_trois_providers_sont_verrouilles(prepared: Path) -> None:
    verrou = prepared / ".terraform.lock.hcl"
    assert verrou.is_file(), (
        "`.terraform.lock.hcl` est absent : `terraform init` n'a pas résolu les "
        "providers. Sans verrou, rien ne garantit qu'un autre poste installera "
        "les mêmes versions."
    )

    texte = verrou.read_text(encoding="utf-8")
    trouves = dict(
        re.findall(
            r'provider\s+"([^"]+)"\s*\{\s*\n\s*version\s*=\s*"([^"]+)"', texte
        )
    )
    manquants = PROVIDERS_ATTENDUS - set(trouves)
    assert not manquants, (
        f"Le verrou ne liste pas {sorted(manquants)}.\nIl porte {sorted(trouves)}.\n\n"
        "`required_providers` suffit à faire verrouiller un provider : `null` "
        "n'est utilisé par aucune ressource et doit tout de même y figurer."
    )
    sans_version = [nom for nom, v in trouves.items() if not v.strip()]
    assert not sans_version, (
        f"Ces providers sont verrouillés sans version résolue : {sans_version}."
    )


# --------------------------------------------------------------------------
# 2. Le state porte exactement deux ressources gérées, et pas une de plus.
# --------------------------------------------------------------------------
def test_le_state_porte_exactement_deux_ressources_gerees(applied: Path) -> None:
    gerees = {r["address"] for r in ressources(applied) if r["mode"] == "managed"}
    assert gerees == GEREES_ATTENDUES, (
        f"Le state gère {sorted(gerees)}.\nAttendu exactement : "
        f"{sorted(GEREES_ATTENDUES)}.\n\nLe mode `managed` désigne ce que "
        "Terraform a créé et détruira. Tout ce qui s'y trouve en trop est une "
        "ressource dont il se croit responsable."
    )


# --------------------------------------------------------------------------
# 3. La donnée seulement lue ne se confond pas avec une ressource gérée.
# --------------------------------------------------------------------------
def test_la_source_de_donnees_est_distincte_des_ressources_gerees(
    applied: Path,
) -> None:
    lues = [r for r in ressources(applied) if r["mode"] == "data"]
    assert len(lues) == 1, (
        f"Le state porte {len(lues)} entrée(s) en mode `data`, une seule est "
        f"attendue : {[r['address'] for r in lues]}."
    )

    donnee = lues[0]
    assert donnee["type"] == "local_file", (
        f"La source de données est de type {donnee['type']}, attendu `local_file`."
    )
    assert TEMOIN in donnee["values"]["filename"], (
        f"La source de données lit {donnee['values']['filename']!r}, "
        f"attendu un chemin vers {TEMOIN!r}."
    )

    assert donnee["values"]["content"], (
        "La source de données a été résolue mais son contenu est vide : le "
        "fichier lu n'est pas celui du lab."
    )


# --------------------------------------------------------------------------
# 4. Le rapport a été PRODUIT par Terraform, pas saisi.
# --------------------------------------------------------------------------
def test_le_rapport_porte_l_identifiant_produit_par_terraform(applied: Path) -> None:
    sorties = output_json(applied)
    for attendu in ("nom_animal", "chemin_rapport", "nom_majuscule"):
        assert attendu in sorties, (
            f"La sortie `{attendu}` n'est pas déclarée. Les sorties présentes "
            f"sont {sorted(sorties)}."
        )

    chemin = (applied / sorties["chemin_rapport"]["value"]).resolve()
    assert chemin.is_file(), (
        f"`chemin_rapport` désigne {chemin}, qui n'existe pas sur le disque. "
        "La sortie doit pointer le fichier réellement écrit."
    )

    identifiant = next(
        r["values"]["id"]
        for r in ressources(applied)
        if r["address"] == "random_pet.nom"
    )
    contenu = chemin.read_text(encoding="utf-8")
    assert identifiant in contenu, (
        f"Le rapport ne contient pas {identifiant!r}, l'identifiant que le "
        f"provider a généré.\nIl contient :\n{contenu[:200]!r}\n\n"
        "Le contenu doit être construit par interpolation depuis "
        "`random_pet.nom.id`. Une valeur recopiée à la main donnerait le même "
        "fichier, mais aucune dépendance entre les deux ressources."
    )
    assert sorties["nom_animal"]["value"] == identifiant, (
        "La sortie `nom_animal` ne vaut pas l'identifiant du state."
    )


# --------------------------------------------------------------------------
# 5. `sensitive` masque l'affichage, et RIEN d'autre.
# --------------------------------------------------------------------------
def test_la_sortie_sensible_est_masquee_a_l_ecran_mais_en_clair_dans_le_state(
    applied: Path,
) -> None:
    sorties = output_json(applied)
    assert sorties["nom_majuscule"]["sensitive"] is True, (
        "`nom_majuscule` n'est pas déclarée sensible. C'est `sensitive = true` "
        "qui demande à Terraform de ne pas l'afficher."
    )

    humaine = terraform("output", "-no-color", cwd=applied)
    assert humaine.returncode == 0, f"`terraform output` a échoué.\n{humaine.stderr}"
    ligne = next(
        (
            sortie
            for sortie in humaine.stdout.splitlines()
            if sortie.startswith("nom_majuscule")
        ),
        "",
    )
    assert "<sensitive>" in ligne, (
        f"L'affichage rend {ligne!r} : la valeur n'est pas masquée."
    )

    valeur = sorties["nom_majuscule"]["value"]
    assert ligne and valeur not in ligne, (
        "La valeur sensible apparaît dans la sortie destinée à un humain."
    )

    # L'autre moitié, et c'est elle qui enseigne : le masquage s'arrête à
    # l'écran. Le state porte la valeur EN CLAIR.
    etat = json.loads((applied / "terraform.tfstate").read_text(encoding="utf-8"))
    assert etat["outputs"]["nom_majuscule"]["value"] == valeur, (
        "La valeur sensible ne figure pas en clair dans `terraform.tfstate`. "
        "Elle devrait : `sensitive` ne chiffre rien."
    )
    assert valeur == sorties["nom_animal"]["value"].upper(), (
        "`nom_majuscule` doit dériver de `nom_animal` par `upper()`, pas être "
        "saisie."
    )


# --------------------------------------------------------------------------
# 6. Idempotence, par le code retour et non par une lecture de texte.
# --------------------------------------------------------------------------
def test_une_seconde_application_n_annonce_aucun_changement(applied: Path) -> None:
    plan = terraform(
        "plan", "-detailed-exitcode", "-input=false", "-no-color", cwd=applied
    )
    assert plan.returncode == 0, (
        f"`terraform plan -detailed-exitcode` rend {plan.returncode}.\n"
        "0 = aucun changement, 1 = erreur, 2 = des changements sont prévus.\n"
        f"{plan.stdout[-1200:]}\n\nConfiguration, state et disque doivent être "
        "alignés après une première application."
    )


# --------------------------------------------------------------------------
# 7. La dérive est détectée, et l'identité des ressources intactes survit.
# --------------------------------------------------------------------------
def test_la_derive_est_detectee_et_l_identite_survit(
    applied: Path, tmp_path: Path
) -> None:
    # On travaille sur une COPIE, state compris : le travail de l'apprenant
    # n'est jamais modifié par un test.
    copie = tmp_path / "derive"
    shutil.copytree(applied, copie)

    sorties = output_json(applied)
    rapport = (copie / sorties["chemin_rapport"]["value"]).resolve()
    rapport.unlink()

    plan = terraform(
        "plan", "-input=false", "-no-color", "-out=plan.tfplan", cwd=copie
    )
    assert plan.returncode == 0, f"Le plan a échoué.\n{plan.stderr[-1200:]}"

    montre = terraform("show", "-json", "plan.tfplan", cwd=copie)
    assert montre.returncode == 0, f"`show -json` du plan a échoué.\n{montre.stderr}"
    actions = {
        c["address"]: c["change"]["actions"]
        for c in json.loads(montre.stdout).get("resource_changes", [])
    }

    assert actions.get("local_file.rapport") == ["create"], (
        f"Le plan annonce {actions.get('local_file.rapport')} pour le rapport "
        "supprimé, attendu `['create']`. Sans correspondance dans le state, "
        "Terraform ne saurait pas qu'il manque quelque chose."
    )
    assert actions.get("random_pet.nom") == ["no-op"], (
        f"Le plan annonce {actions.get('random_pet.nom')} pour le nom généré, "
        "attendu `['no-op']`.\n\nC'est le point du lab : une dérive sur une "
        "ressource ne détruit pas l'identité des autres. Un `random_pet` "
        "recréé changerait de nom, et le rapport avec."
    )


# --------------------------------------------------------------------------
# 8. Les deux côtés à la fois : ce que le state reflète, et ce qu'il ignore.
# --------------------------------------------------------------------------
def test_le_state_reflete_le_disque_et_ignore_ce_que_personne_n_a_declare(
    applied: Path,
) -> None:
    rapport = next(
        r for r in ressources(applied) if r["address"] == "local_file.rapport"
    )
    chemin = (applied / rapport["values"]["filename"]).resolve()
    octets = chemin.read_bytes()

    # Le provider `local` fait de l'identifiant le sha1 du contenu. L'invariant
    # ne tient donc que si le state décrit le fichier RÉEL : un state édité à la
    # main, ou un fichier retouché après coup, le casse.
    #
    # `usedforsecurity=False` : on ne protège rien ici, on REPRODUIT le calcul
    # d'un identifiant choisi par le provider. Le nier ferait échouer le test
    # sur une propriété qui n'est pas la sienne.
    empreinte = hashlib.sha1(octets, usedforsecurity=False).hexdigest()
    assert rapport["values"]["id"] == empreinte, (
        "L'identifiant du rapport dans le state n'est pas le sha1 de son "
        "contenu sur le disque. Le state ne décrit plus la réalité : il a été "
        "édité à la main, ou le fichier a été retouché hors de Terraform."
    )
    assert rapport["values"]["content"] == octets.decode("utf-8"), (
        "Le `content` mémorisé diffère du contenu réel du fichier."
    )

    # L'autre côté : un objet que personne n'a déclaré reste invisible. Le
    # témoin existe bel et bien sur le disque, et aucune ressource gérée ne le
    # revendique.
    temoin = applied / TEMOIN
    assert temoin.is_file(), (
        f"{TEMOIN} a disparu du répertoire de travail. Il sert de témoin : il "
        "doit rester là, écrit à la main, sans être géré."
    )
    revendique = [
        r["address"]
        for r in ressources(applied)
        if r["mode"] == "managed" and TEMOIN in json.dumps(r["values"])
    ]
    assert not revendique, (
        f"{revendique} revendique(nt) {TEMOIN} en mode `managed`. Un fichier "
        "écrit à la main ne doit pas devenir une ressource gérée : Terraform le "
        "détruirait au premier `destroy`. Le lire par une source de données, "
        "oui ; le gérer, non."
    )
