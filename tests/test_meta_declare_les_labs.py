"""Tout lab livré est déclaré dans `meta.yml`, et réciproquement.

POURQUOI CE MODULE EXISTE

Le catalogue a **deux descriptions**, et le trou est entre les deux.
`labs/*/lab.yaml` dit ce qui existe ; `meta.yml` dit dans quel ordre le jouer.
Chaque outil lit la sienne et a raison de son côté : `dsoxlab validate-structure`
énumère les répertoires de `labs/`, `gen_catalog.py` construit la table depuis
`meta.yml`, et rien ne comparait les deux.

Le catalogue Kubernetes a payé ce trou le 2026-09-16 : deux labs validés ont
disparu de `meta.yml` après une manipulation de branches. Ils restaient dans la
table de couverture, construite depuis les `lab.yaml`, mais plus dans le
parcours recommandé. Un apprenant qui suit le parcours ne les aurait jamais
joués, et rien ne pouvait le signaler.

Le contrôle porte donc sur l'ÉCART entre les deux sources, dans les deux sens :

- un lab sur disque mais non déclaré est invisible du parcours ;
- un lab déclaré mais absent du disque casse le parcours.

Une différence avec la version Kubernetes, et elle compte : là-bas, un lab est un
répertoire directement sous `labs/`. Ici, les labs sont rangés par section,
`labs/<section>/<lab>/`, parfois sur trois niveaux
(`labs/write-code/sensitive-data/<lab>/`). L'énumération suit donc les `lab.yaml`
où qu'ils soient, et compare des chemins relatifs, pas des noms.

    pytest tests/test_meta_declare_les_labs.py -v
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "scripts"))
from lecture_yaml import lire_yaml  # noqa: E402

META = RACINE / "meta.yml"
LABS = RACINE / "labs"


def _declares() -> list[str]:
    """Les labs que `meta.yml` déclare, dans l'ordre, section par section."""
    donnees = lire_yaml(META)
    declares: list[str] = []
    for section in donnees.get("sections") or []:
        declares += [str(lab) for lab in (section.get("labs") or [])]
    return declares


def _sur_disque() -> set[str]:
    """Les labs réellement livrés, par leur chemin relatif à `labs/`.

    On énumère les RÉPERTOIRES porteurs d'un `lab.yaml`, et non les `lab.yaml`
    d'une liste connue d'avance : on ne peut pas constater l'absence d'un
    fichier en partant de ce fichier.
    """
    return {str(c.parent.relative_to(LABS)) for c in LABS.rglob("lab.yaml")}


def test_le_parcours_n_est_pas_vide() -> None:
    """Garde-fou : un `meta.yml` aux sections vides rendrait tout le reste vert."""
    declares = _declares()
    assert len(declares) > 50, (
        f"Seulement {len(declares)} lab(s) déclaré(s) dans meta.yml : les "
        "sections sont vides ou le parcours est cassé, et l'apprenant se "
        "retrouve devant un catalogue sans ordre."
    )


def test_chaque_lab_livre_est_declare_dans_le_parcours() -> None:
    oublies = sorted(_sur_disque() - set(_declares()))
    assert not oublies, (
        "Lab(s) livré(s) mais absent(s) du parcours de meta.yml :\n  "
        + "\n  ".join(oublies)
        + "\n\nIls existent sur le disque et `dsoxlab validate-structure` les "
        "voit, mais ils ne figurent ni dans la table des README, générée depuis "
        "meta.yml, ni dans le parcours. Un apprenant qui suit le parcours ne "
        "les jouera jamais."
    )


def test_chaque_lab_declare_existe_vraiment() -> None:
    fantomes = [lab for lab in _declares() if lab not in _sur_disque()]
    assert not fantomes, (
        "Lab(s) déclaré(s) dans meta.yml mais absent(s) de labs/ :\n  "
        + "\n  ".join(fantomes)
        + "\n\nSoit le lab a été renommé sans que meta.yml suive, soit ses "
        "fichiers ont été perdus. Le second cas est arrivé dans le catalogue "
        "jumeau : un répertoire de lab peut survivre à une manipulation de "
        "branches avec son seul sous-dossier challenge/, ce qui ne se voit pas "
        "dans un `ls`."
    )


def test_aucun_lab_n_est_declare_deux_fois() -> None:
    """Un lab dans deux sections apparaîtrait deux fois dans la table, avec deux
    places différentes dans le parcours, ce qui n'a pas de sens."""
    doublons = sorted(lab for lab, n in Counter(_declares()).items() if n > 1)
    assert not doublons, f"Lab(s) déclaré(s) plusieurs fois : {', '.join(doublons)}."


#: Ce qu'un lab de CE dépôt porte forcément. Pas de `setup.yaml` ni de
#: `cleanup.yaml`, contrairement aux catalogues Ansible, Linux et Kubernetes :
#: tous les labs sont en `runtime: shell`, l'état de départ vient de
#: `runtime.fixtures` et `dsoxlab clean` retire le répertoire de travail.
ATTENDUS = (
    "lab.yaml",
    "lab.fr.yaml",
    "scenario.md",
    "scenario.fr.md",
    "README.md",
    "README.fr.md",
    "challenge/README.md",
    "challenge/README.fr.md",
    "challenge/hints.yaml",
    "challenge/tests/test_functional.py",
)


def test_aucun_repertoire_de_lab_n_est_ampute() -> None:
    """Un répertoire de lab incomplet est INVISIBLE pour le reste de l'outillage.

    C'est ce qui le rend dangereux : `validate-structure` comme les contrôles de
    complétude énumèrent les labs par leur `lab.yaml`, donc un lab qui a perdu
    le sien n'existe plus pour eux. Le contrôle part donc du parcours, qui lui
    se souvient du lab.
    """
    amputes: dict[str, list[str]] = {}
    for rel in _declares():
        dossier = LABS / rel
        if not dossier.is_dir():
            continue  # déjà signalé par le test des fantômes
        manquants = [f for f in ATTENDUS if not (dossier / f).exists()]
        if manquants:
            amputes[rel] = manquants

    assert not amputes, (
        "Répertoire(s) de lab incomplet(s) :\n"
        + "\n".join(f"  {rel} : {', '.join(m)}" for rel, m in sorted(amputes.items()))
        + "\n\nUn lab amputé de son lab.yaml disparaît de tous les contrôles qui "
        "énumèrent les labs par ce fichier, sans que rien ne le signale."
    )
