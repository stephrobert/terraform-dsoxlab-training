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

from conftest import exiger_workdir, message, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "environments-monorepo-vs-repo-per-stack"

AMONT = "stacks/plateforme"
AVAL = "stacks/applicatif"


# ── Helpers ─────────────────────────────────────────────────────────────────


def _tf(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["terraform", *args], cwd=cwd, capture_output=True, text=True,
        env=os.environ.copy(),
        check=False,
    )


def _stack(travail: Path, nom: str) -> Path:
    chemin = travail / nom
    if not chemin.is_dir():
        pytest.fail(message(
            en=f"The {nom}/ directory is missing from challenge/work.",
            fr=f"Le répertoire {nom}/ est absent de challenge/work.",
        ))
    return chemin


def _etat(travail: Path, nom: str) -> dict:
    montre = _tf("show", "-json", cwd=_stack(travail, nom))
    if montre.returncode != 0:
        pytest.fail(
            message(
            en=f"`terraform show -json` fails in {nom}/. Has the stack been "
            f"initialised and applied?\n{montre.stderr[-700:]}",
            fr=f"`terraform show -json` échoue dans {nom}/. La stack a-t-elle été "
            f"initialisée et appliquée ?\n{montre.stderr[-700:]}",
        )
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
        pytest.fail(message(
            en=f"`terraform output -json` fails in {nom}/.\n{rendu.stderr[-700:]}",
            fr=f"`terraform output -json` échoue dans {nom}/.\n{rendu.stderr[-700:]}",
        ))
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
                    message(
                    en=f"`terraform init` fails in {nom}/.\n{init.stderr[-800:]}",
                    fr=f"`terraform init` échoue dans {nom}/.\n{init.stderr[-800:]}",
                )
                )
    yield WORKDIR


# ── 1. La stack amont ───────────────────────────────────────────────────────


def test_la_plateforme_suit_le_module_et_son_secret(travail: Path) -> None:
    gerees = [
        r for r in _toutes_ressources(_etat(travail, AMONT))
        if r.get("mode") == "managed"
    ]
    assert gerees, message(
        en="The platform tracks no resource: it was not applied. "
        "A `version` next to a local `source` already prevents the init.",
        fr="La plateforme ne suit aucune ressource : elle n'a pas été appliquée. "
        "Un `version` à côté d'un `source` local empêche déjà l'init.",
    )
    adresses = {r["address"] for r in gerees}
    assert any("random_password.db" in a for a in adresses), message(
        en=f"`random_password.db` is absent from the platform's state: "
        f"{sorted(adresses)}",
        fr=f"`random_password.db` est absent de l'état de la plateforme : "
        f"{sorted(adresses)}",
    )
    assert any("module.reseau" in a for a in adresses), message(
        en=f"No resource of the `reseau` module in the state: {sorted(adresses)}",
        fr=f"Aucune ressource du module `reseau` dans l'état : {sorted(adresses)}",
    )


def test_la_plateforme_reexporte_ses_deux_sorties(travail: Path) -> None:
    sorties = _sorties(travail, AMONT)
    for attendu in ("network_name", "network_cidr"):
        assert attendu in sorties, message(
            en=f"The platform does not expose `{attendu}` at its ROOT. A nested "
            "module's output is not readable from another configuration: "
            "it must be re-exported explicitly.",
            fr=f"La plateforme n'expose pas `{attendu}` à sa RACINE. Une sortie de "
            "module imbriqué n'est pas lisible depuis une autre configuration : "
            "elle doit être ré-exportée explicitement.",
        )
        assert sorties[attendu].get("value"), message(
            en=f"`{attendu}` is empty.",
            fr=f"`{attendu}` est vide.",
        )


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
            message(
            en="No `random_password` found in the platform's state: the "
            "secret check would prove nothing.",
            fr="Aucun `random_password` trouvé dans l'état de la plateforme : le "
            "contrôle du secret ne prouverait rien.",
        )
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
        assert all(secret not in publiee for publiee in publiees), message(
            en="The generated password appears in the platform's ROOT outputs. "
            "But \"any user or server which has enough access to "
            "read the root module output values will also always have access "
            "to the full state snapshot data\". A secret is not published, "
            "even marked `sensitive`.",
            fr="Le mot de passe généré apparaît dans les sorties RACINE de la "
            "plateforme. Or « any user or server which has enough access to "
            "read the root module output values will also always have access "
            "to the full state snapshot data ». Un secret ne se publie pas, "
            "même marqué `sensitive`.",
        )


# ── 2. La stack aval lit l'amont ────────────────────────────────────────────


def test_l_applicatif_lit_l_etat_de_la_plateforme(travail: Path) -> None:
    donnees = [r for r in _ressources(_etat(travail, AVAL)) if r.get("mode") == "data"]
    assert donnees, message(
        en="The application stack's state contains no data source: "
        "it therefore reads nothing from the platform.",
        fr="L'état de la stack applicative ne contient aucune source de données : "
        "elle ne lit donc rien de la plateforme.",
    )
    distants = [d for d in donnees if d.get("type") == "terraform_remote_state"]
    assert distants, message(
        en=f"No `terraform_remote_state` source: types found "
        f"{[d.get('type') for d in donnees]}.",
        fr=f"Aucune source `terraform_remote_state` : types trouvés "
        f"{[d.get('type') for d in donnees]}.",
    )


def test_le_cidr_est_le_meme_des_deux_cotes(travail: Path) -> None:
    amont = _sorties(travail, AMONT)["network_cidr"]["value"]
    aval = _sorties(travail, AVAL)
    assert "network_cidr" in aval, message(
        en="The application stack does not expose `network_cidr`.",
        fr="La stack applicative n'expose pas `network_cidr`.",
    )
    assert aval["network_cidr"]["value"] == amont, message(
        en=f"The application stack exposes {aval['network_cidr']['value']!r} while "
        f"the platform produces {amont!r}. Since the CIDR is drawn at random at "
        "apply time, it cannot be copied: it must be READ.",
        fr=f"La stack applicative expose {aval['network_cidr']['value']!r} alors "
        f"que la plateforme produit {amont!r}. Le CIDR étant tiré au sort à "
        "l'apply, il ne peut pas être recopié : il doit être LU.",
    )


def test_le_fichier_produit_porte_la_valeur_amont(travail: Path) -> None:
    cidr = _sorties(travail, AMONT)["network_cidr"]["value"]
    nom = _sorties(travail, AMONT)["network_name"]["value"]
    produit = _stack(travail, AVAL) / "produits" / "app.conf"
    assert produit.is_file(), message(
        en=f"{AVAL}/produits/app.conf does not exist: the application stack was not "
        "applied.",
        fr=f"{AVAL}/produits/app.conf n'existe pas : la stack applicative n'a pas "
        "été appliquée.",
    )
    contenu = produit.read_text(encoding="utf-8")
    assert cidr in contenu, message(
        en=f"The file produced does not contain the platform's CIDR "
        f"({cidr!r}):\n{contenu!r}",
        fr=f"Le fichier produit ne contient pas le CIDR de la plateforme "
        f"({cidr!r}) :\n{contenu!r}",
    )
    assert nom in contenu, message(
        en=f"The file produced does not contain the upstream network name ({nom!r}):"
        f"\n{contenu!r}",
        fr=f"Le fichier produit ne contient pas le nom de réseau amont ({nom!r}) :"
        f"\n{contenu!r}",
    )


# ── 3. Les deux stacks ont converge ─────────────────────────────────────────


def test_les_deux_stacks_sont_idempotentes(travail: Path) -> None:
    for nom in (AMONT, AVAL):
        plan = _tf(
            "plan", "-input=false", "-detailed-exitcode", "-no-color",
            cwd=_stack(travail, nom),
        )
        assert plan.returncode == 0, message(
            en=f"{nom}: `plan -detailed-exitcode` returns {plan.returncode}, expected "
            f"0.\n{(plan.stdout + plan.stderr)[-600:]}",
            fr=f"{nom} : `plan -detailed-exitcode` rend {plan.returncode}, attendu "
            f"0.\n{(plan.stdout + plan.stderr)[-600:]}",
        )
