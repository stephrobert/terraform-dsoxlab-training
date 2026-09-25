#!/usr/bin/env python3
"""Dit où Terraform trouvera votre jeton HCP Terraform, ou pourquoi il n'en trouve pas.

Raison d'être : le message que Terraform rend quand un jeton manque nomme le
symptôme, pas la cause.

    Error: Required token could not be found

Il ne dit ni où Terraform a cherché, ni lequel des emplacements possibles
l'emporte quand plusieurs sont remplis. Or ils ne sont pas équivalents, et c'est
ce qui coûte le plus de temps : **une variable d'environnement passe devant le
fichier de credentials**, y compris quand on a pris soin de neutraliser ce
dernier. Mesuré le 2026-09-25 sur Terraform 1.16.1, sur une même configuration
correcte :

    fichier de credentials seul              -> le jeton du fichier est employé
    TF_CLI_CONFIG_FILE vers un fichier vide  -> « Required token could not be found »
    ... et TF_TOKEN_app_terraform_io posée   -> le jeton de la variable est employé

Ce script regarde donc tous les emplacements, dit lequel gagne, et peut vérifier
le jeton auprès de l'API. **Il n'affiche jamais la valeur d'un jeton**, seulement
sa longueur et une empreinte tronquée, de quoi comparer deux jetons sans en
divulguer aucun.

Usage :

    python3 scripts/diagnostic-jeton-hcp.py              # où est le jeton
    python3 scripts/diagnostic-jeton-hcp.py --verifier   # + appel à l'API
    python3 scripts/diagnostic-jeton-hcp.py --hote app.terraform.io
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

HOTE_PAR_DEFAUT = "app.terraform.io"

# Mesuré le 2026-09-25 : l'API rend 401 aussi bien sans en-tête d'autorisation
# qu'avec un jeton invalide, avec le même corps. Un 401 ne distingue donc pas
# « pas de jeton » de « mauvais jeton », et le script s'appuie sur ce qu'il a
# trouvé localement pour le dire.
CHEMIN_API = "/api/v2/account/details"


def nom_de_variable(hote: str) -> str:
    """`TF_TOKEN_` suivi du nom d'hôte, ses points devenus des tirets bas.

    `app.terraform.io` donne donc `TF_TOKEN_app_terraform_io`.
    """
    return "TF_TOKEN_" + hote.replace(".", "_").replace("-", "__")


def empreinte(jeton: str) -> str:
    """De quoi comparer deux jetons sans en divulguer aucun."""
    return hashlib.sha256(jeton.encode()).hexdigest()[:12]


# Un jeton d'API HCP Terraform porte un `.atlasv1.` et avoisine 90 caractères.
# Ce contrôle est né d'un cas réel, le 2026-09-25 : un jeton de 22 caractères
# posé dans le fichier, refusé par l'API avec un 401 que rien ne distinguait
# d'une révocation. C'était une copie tronquée, et l'API ne pouvait pas le dire.
MARQUE_DE_FORME = ".atlasv1."
LONGUEUR_PLAUSIBLE = 60

# La page « Tokens » de HCP Terraform affiche DEUX choses, et une seule est un
# jeton d'API. Celle qui est visible en permanence est le jeton OAuth de la
# GitHub App, préfixé `ghaot-` ; le jeton d'API, lui, se crée par un bouton et
# ne s'affiche qu'une fois. La confusion s'est produite le 2026-09-25, et rien
# sur la page ne la prévient.
PREFIXES_TROMPEURS = {
    "ghaot-": (
        "c'est le jeton OAuth de la GitHub App, affiché en permanence sur la "
        "page « Tokens ». Le jeton d'API se crée avec le bouton « Create an "
        "API token » et ne s'affiche qu'une fois"
    ),
    "ghp_": "c'est un jeton GitHub personnel, sans rapport avec HCP Terraform",
    "hvs.": "c'est un jeton Vault, sans rapport avec HCP Terraform",
}


def defauts_de_forme(jeton: str) -> list[str]:
    """Ce qui, dans la FORME du jeton, explique un refus sans appeler l'API.

    Volontairement indicatif : la forme d'un jeton peut changer, et un jeton
    valide qui ne ressemblerait plus à rien ne doit pas être déclaré faux. Ces
    remarques s'affichent, elles ne décident pas.
    """
    remarques = []
    for prefixe, explication in PREFIXES_TROMPEURS.items():
        if jeton.startswith(prefixe):
            remarques.append(f"il commence par `{prefixe}` : {explication}")

    if jeton != jeton.strip():
        remarques.append(
            "il porte une espace ou un retour à la ligne en trop, ce qui suffit "
            "à le faire refuser"
        )
    if MARQUE_DE_FORME not in jeton:
        remarques.append(
            f"il ne contient pas `{MARQUE_DE_FORME}`, que porte un jeton d'API "
            "HCP Terraform"
        )
    if len(jeton.strip()) < LONGUEUR_PLAUSIBLE:
        remarques.append(
            f"il fait {len(jeton.strip())} caractères, là où un jeton d'API en "
            "fait environ 90 : la copie est probablement incomplète"
        )
    return remarques


def _lire_credentials_json(chemin: Path, hote: str) -> str | None:
    try:
        contenu = json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return ((contenu.get("credentials") or {}).get(hote) or {}).get("token")


def sources(hote: str) -> list[dict]:
    """Tous les emplacements, dans l'ordre de priorité de Terraform.

    L'ordre compte : le premier qui porte un jeton est celui que Terraform
    emploie, et les suivants ne servent plus à rien.
    """
    trouvees: list[dict] = []

    variable = nom_de_variable(hote)
    trouvees.append(
        {
            "nom": f"variable d'environnement {variable}",
            "detail": "elle passe devant tout le reste",
            "jeton": os.environ.get(variable),
        }
    )

    config_cli = os.environ.get("TF_CLI_CONFIG_FILE")
    if config_cli:
        chemin = Path(config_cli)
        trouvees.append(
            {
                "nom": f"TF_CLI_CONFIG_FILE, soit {chemin}",
                "detail": (
                    "elle REMPLACE le fichier de configuration par défaut : un "
                    "fichier vide neutralise donc les credentials du poste"
                ),
                "jeton": _jeton_dans_un_tfrc(chemin, hote),
                "existe": chemin.exists(),
            }
        )

    defaut_json = Path.home() / ".terraform.d" / "credentials.tfrc.json"
    trouvees.append(
        {
            "nom": f"{defaut_json}",
            "detail": "ce qu'écrit `terraform login`",
            "jeton": _lire_credentials_json(defaut_json, hote)
            if defaut_json.is_file()
            else None,
            "existe": defaut_json.exists(),
        }
    )

    terraformrc = Path.home() / ".terraformrc"
    trouvees.append(
        {
            "nom": f"{terraformrc}",
            "detail": "forme historique, un bloc `credentials`",
            "jeton": _jeton_dans_un_tfrc(terraformrc, hote),
            "existe": terraformrc.exists(),
        }
    )

    return trouvees


def _jeton_dans_un_tfrc(chemin: Path, hote: str) -> str | None:
    """Le jeton d'un fichier HCL `credentials "<hôte>" { token = "..." }`.

    Une lecture volontairement sommaire : ce script diagnostique, il ne
    remplace pas l'analyseur de Terraform. Un fichier exotique sera signalé
    comme « présent, jeton non lu », ce qui reste une information utile.
    """
    if not chemin.is_file():
        return None
    try:
        texte = chemin.read_text(encoding="utf-8")
    except OSError:
        return None

    debut = texte.find(f'credentials "{hote}"')
    if debut == -1:
        return None
    fin = texte.find("}", debut)
    bloc = texte[debut : fin if fin != -1 else len(texte)]
    for ligne in bloc.splitlines():
        if "token" in ligne and "=" in ligne:
            valeur = ligne.split("=", 1)[1].strip().strip('"')
            return valeur or None
    return None


def verifier(jeton: str, hote: str) -> tuple[bool, str]:
    """Interroge l'API, et rend ce qu'elle dit."""
    requete = urllib.request.Request(
        f"https://{hote}{CHEMIN_API}",
        headers={
            "Authorization": f"Bearer {jeton}",
            "Content-Type": "application/vnd.api+json",
        },
    )
    try:
        with urllib.request.urlopen(requete, timeout=20) as reponse:
            donnees = json.loads(reponse.read().decode("utf-8"))
    except urllib.error.HTTPError as erreur:
        if erreur.code == 401:
            return False, (
                "l'API répond 401 unauthorized : le jeton est refusé. Il a pu "
                "être révoqué, expirer, ou appartenir à un autre hôte"
            )
        return False, f"l'API répond {erreur.code} : {erreur.reason}"
    except urllib.error.URLError as erreur:
        return False, f"l'API est injoignable : {erreur.reason}"

    attributs = (donnees.get("data") or {}).get("attributes") or {}
    qui = attributs.get("username") or attributs.get("email") or "compte inconnu"
    return True, f"le jeton est accepté, il appartient à {qui}"


def principal() -> int:
    analyseur = argparse.ArgumentParser(
        description="Où Terraform trouvera votre jeton HCP Terraform.",
    )
    analyseur.add_argument("--hote", default=HOTE_PAR_DEFAUT)
    analyseur.add_argument(
        "--verifier",
        action="store_true",
        help="interroge l'API pour dire si le jeton est encore accepté",
    )
    arguments = analyseur.parse_args()
    hote = arguments.hote

    print(f"Hôte visé : {hote}")
    print(f"Variable attendue : {nom_de_variable(hote)}\n")

    trouvees = sources(hote)
    gagnante = None

    for source in trouvees:
        jeton = source.get("jeton")
        if jeton and gagnante is None:
            gagnante = source
            marque = "==>"
        elif jeton:
            marque = "  ~"  # porte un jeton, mais un autre passe devant
        else:
            marque = "   "

        if jeton:
            etat = f"jeton trouvé, {len(jeton)} caractères, empreinte {empreinte(jeton)}"
        elif source.get("existe") is False:
            etat = "absent"
        elif source.get("existe") is True:
            etat = "présent, aucun jeton pour cet hôte"
        else:
            etat = "non définie"

        print(f"{marque} {source['nom']}")
        print(f"      {etat}")
        print(f"      ({source['detail']})")

    print()

    if gagnante is None:
        print("Aucun jeton trouvé. Terraform répondra :")
        print("    Error: Required token could not be found\n")
        print("Pour en poser un :")
        print("    terraform login                     # écrit le fichier tout seul")
        print(f"    export {nom_de_variable(hote)}=<jeton>   # le temps d'une session")
        print("\nLe guide complet : docs/hcp-token.fr.md")
        return 1

    print(f"Terraform emploiera : {gagnante['nom']}")

    remarques = defauts_de_forme(gagnante["jeton"])
    if remarques:
        print("\nMais sa FORME est douteuse, avant même d'interroger l'API :")
        for remarque in remarques:
            print(f"    - {remarque}")
        print(
            "\nUn jeton d'API se présente comme `<identifiant>.atlasv1.<partie "
            "secrète>`.\nReprenez-le en entier : la page ne le montre qu'une "
            "fois, et une fois fermée\nil faut en créer un autre, ce qui prend "
            "dix secondes."
        )

    autres = [s for s in trouvees if s.get("jeton") and s is not gagnante]
    if autres:
        print(
            "\nAttention : d'autres emplacements portent aussi un jeton, et ils "
            "sont ignorés.\nC'est la cause la plus fréquente d'un « jeton mis à "
            "jour qui ne change rien » :"
        )
        for source in autres:
            print(f"    - {source['nom']}")

    if arguments.verifier:
        accepte, message = verifier(gagnante["jeton"], hote)
        print(f"\nVérification auprès de l'API : {message}")
        return 0 if accepte else 2

    print("\nAjoutez --verifier pour demander à l'API si ce jeton est encore accepté.")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
