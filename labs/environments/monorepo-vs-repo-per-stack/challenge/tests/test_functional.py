"""Tests fonctionnels du lab « decouper un monorepo en deux stacks ».

Les tests n'ouvrent jamais un `.tf` de l'apprenant : ils lisent l'etat
structure, `terraform show -json` et `terraform output -json`.

Faits verifies sur Terraform 1.15.4, hors ligne, providers `local` et `random` :

- un `version` pose a cote d'un `source` LOCAL fait echouer l'init
  (`Error: Invalid registry module source address`), l'argument ne valant que
  pour un module de registre ;
- seules les sorties de la RACINE traversent : une sortie de module imbrique
  non re-exportee rend `Error: Unsupported attribute` cote consommateur ;
- le CIDR est tire au sort a l'apply, donc l'egalite entre les deux stacks ne
  peut pas etre obtenue en recopiant une valeur.
"""

import json
import os
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "environments-monorepo-vs-repo-per-stack"

AMONT = "stacks/plateforme"
AVAL = "stacks/applicatif"


# ── Helpers ─────────────────────────────────────────────────────────────────


def _tf(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["terraform", *args], cwd=cwd, capture_output=True, text=True,
        env=os.environ.copy(),
    )


def _stack(travail: Path, nom: str) -> Path:
    chemin = travail / nom
    if not chemin.is_dir():
        pytest.fail(f"Le repertoire {nom}/ est absent de challenge/work.")
    return chemin


def _etat(travail: Path, nom: str) -> dict:
    montre = _tf("show", "-json", cwd=_stack(travail, nom))
    if montre.returncode != 0:
        pytest.fail(
            f"`terraform show -json` echoue dans {nom}/. La stack a-t-elle ete "
            f"initialisee et appliquee ?\n{montre.stderr[-700:]}"
        )
    return json.loads(montre.stdout or "{}")


def _ressources(etat: dict) -> list[dict]:
    return list(etat.get("values", {}).get("root_module", {}).get("resources", []))


def _toutes_ressources(etat: dict) -> list[dict]:
    """Ressources de la racine ET des modules imbriques."""
    racine = etat.get("values", {}).get("root_module", {})
    trouvees = list(racine.get("resources", []))
    for enfant in racine.get("child_modules", []):
        trouvees.extend(enfant.get("resources", []))
    return trouvees


def _sorties(travail: Path, nom: str) -> dict:
    rendu = _tf("output", "-json", cwd=_stack(travail, nom))
    if rendu.returncode != 0:
        pytest.fail(f"`terraform output -json` echoue dans {nom}/.\n{rendu.stderr[-700:]}")
    return json.loads(rendu.stdout or "{}")


@pytest.fixture(scope="module")
def travail() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    for nom in (AMONT, AVAL):
        stack = WORKDIR / nom
        if stack.is_dir() and not (stack / ".terraform" / "providers").is_dir():
            init = _tf("init", "-input=false", "-no-color", cwd=stack)
            if init.returncode != 0:
                pytest.fail(
                    f"`terraform init` echoue dans {nom}/.\n{init.stderr[-800:]}"
                )
    yield WORKDIR


# ── 1. La stack amont ───────────────────────────────────────────────────────


def test_la_plateforme_suit_le_module_et_son_secret(travail: Path) -> None:
    gerees = [
        r for r in _toutes_ressources(_etat(travail, AMONT))
        if r.get("mode") == "managed"
    ]
    assert gerees, (
        "La plateforme ne suit aucune ressource : elle n'a pas ete appliquee. "
        "Un `version` a cote d'un `source` local empeche deja l'init."
    )
    adresses = {r["address"] for r in gerees}
    assert any("random_password.db" in a for a in adresses), (
        f"`random_password.db` est absent de l'etat de la plateforme : "
        f"{sorted(adresses)}"
    )
    assert any("module.reseau" in a for a in adresses), (
        f"Aucune ressource du module `reseau` dans l'etat : {sorted(adresses)}"
    )


def test_la_plateforme_reexporte_ses_deux_sorties(travail: Path) -> None:
    sorties = _sorties(travail, AMONT)
    for attendu in ("network_name", "network_cidr"):
        assert attendu in sorties, (
            f"La plateforme n'expose pas `{attendu}` a sa RACINE. Une sortie de "
            "module imbrique n'est pas lisible depuis une autre configuration : "
            "elle doit etre re-exportee explicitement."
        )
        assert sorties[attendu].get("value"), f"`{attendu}` est vide."


def test_le_secret_ne_sort_pas_de_la_plateforme(travail: Path) -> None:
    """Publier une sortie, c'est publier tout l'etat : le secret reste dedans."""
    etat = _etat(travail, AMONT)
    mots_de_passe = [
        r["values"]["result"]
        for r in _toutes_ressources(etat)
        if r.get("type") == "random_password" and "result" in r.get("values", {})
    ]
    if not mots_de_passe:
        pytest.fail(
            "Aucun `random_password` trouve dans l'etat de la plateforme : le "
            "controle du secret ne prouverait rien."
        )

    # Les valeurs sont comparees DECODEES, jamais sur le texte JSON brut : un
    # mot de passe genere avec `special = true` contient des caracteres que
    # JSON echappe (`"` devient `\\"`), si bien qu'une recherche de sous-chaine
    # dans la sortie brute ne le retrouve pas et laisse passer un secret publie.
    publiees = []
    for detail in _sorties(travail, AMONT).values():
        valeur = detail.get("value")
        if isinstance(valeur, str):
            publiees.append(valeur)
        elif isinstance(valeur, (list, dict)):
            publiees.append(json.dumps(valeur))

    for secret in mots_de_passe:
        assert all(secret not in publiee for publiee in publiees), (
            "Le mot de passe genere apparait dans les sorties RACINE de la "
            "plateforme. Or « any user or server which has enough access to "
            "read the root module output values will also always have access "
            "to the full state snapshot data ». Un secret ne se publie pas, "
            "meme marque `sensitive`."
        )


# ── 2. La stack aval lit l'amont ────────────────────────────────────────────


def test_l_applicatif_lit_l_etat_de_la_plateforme(travail: Path) -> None:
    donnees = [r for r in _ressources(_etat(travail, AVAL)) if r.get("mode") == "data"]
    assert donnees, (
        "L'etat de la stack applicative ne contient aucune source de donnees : "
        "elle ne lit donc rien de la plateforme."
    )
    distants = [d for d in donnees if d.get("type") == "terraform_remote_state"]
    assert distants, (
        f"Aucune source `terraform_remote_state` : types trouves "
        f"{[d.get('type') for d in donnees]}."
    )


def test_le_cidr_est_le_meme_des_deux_cotes(travail: Path) -> None:
    amont = _sorties(travail, AMONT)["network_cidr"]["value"]
    aval = _sorties(travail, AVAL)
    assert "network_cidr" in aval, "La stack applicative n'expose pas `network_cidr`."
    assert aval["network_cidr"]["value"] == amont, (
        f"La stack applicative expose {aval['network_cidr']['value']!r} alors "
        f"que la plateforme produit {amont!r}. Le CIDR etant tire au sort a "
        "l'apply, il ne peut pas etre recopie : il doit etre LU."
    )


def test_le_fichier_produit_porte_la_valeur_amont(travail: Path) -> None:
    cidr = _sorties(travail, AMONT)["network_cidr"]["value"]
    nom = _sorties(travail, AMONT)["network_name"]["value"]
    produit = _stack(travail, AVAL) / "produits" / "app.conf"
    assert produit.is_file(), (
        f"{AVAL}/produits/app.conf n'existe pas : la stack applicative n'a pas "
        "ete appliquee."
    )
    contenu = produit.read_text(encoding="utf-8")
    assert cidr in contenu, (
        f"Le fichier produit ne contient pas le CIDR de la plateforme "
        f"({cidr!r}) :\n{contenu!r}"
    )
    assert nom in contenu, (
        f"Le fichier produit ne contient pas le nom de reseau amont ({nom!r}) :"
        f"\n{contenu!r}"
    )


# ── 3. Les deux stacks ont converge ─────────────────────────────────────────


def test_les_deux_stacks_sont_idempotentes(travail: Path) -> None:
    for nom in (AMONT, AVAL):
        plan = _tf(
            "plan", "-input=false", "-detailed-exitcode", "-no-color",
            cwd=_stack(travail, nom),
        )
        assert plan.returncode == 0, (
            f"{nom} : `plan -detailed-exitcode` rend {plan.returncode}, attendu "
            f"0.\n{(plan.stdout + plan.stderr)[-600:]}"
        )
