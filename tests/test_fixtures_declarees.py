"""Chaque fichier de `fixtures/` est déclaré dans `runtime.fixtures`, et réciproquement.

POURQUOI CE MODULE EXISTE

Le point de départ d'un lab a deux descriptions, et le trou est entre les deux.
Le dossier `fixtures/` contient les fichiers ; la liste `runtime.fixtures` du
`lab.yaml` dit lesquels `dsoxlab run` copie dans `challenge/work`. Un fichier
présent mais non déclaré n'atteint **jamais** l'apprenant.

Ce dépôt l'a payé deux fois.

Le 2026-07-28, sept labs étaient injouables, tous marqués faits : le défaut se
cachait d'autant mieux que `scripts/verify-solutions.py` et le mode formateur
du `conftest.py` copient, eux, le répertoire **entier**. La solution passait au
vert pendant que le parcours apprenant était cassé.

Le 2026-10-09, l'épreuve de niveau C rangeait deux templates Ansible
(`equipe-web.tf.j2`, `equipe-data.tf.j2`) dans `fixtures/` alors que son
`setup.yaml` les lit en `src:`. Les déclarer aurait fait copier des `.j2` non
rendus chez l'apprenant ; les laisser là faisait échouer le contrat. La bonne
place était `templates/`.

POURQUOI ICI, PUISQUE L'OUTIL LE FAIT DÉJÀ

`dsoxlab validate-structure` tient cette règle depuis la 0.1.76, et c'est lui
qui a attrapé le cas du 2026-10-09. Ce test ne le remplace pas : il met le
contrôle **dans le catalogue**, donc en CI, sans dépendre de la version de
l'outil installée sur le poste de qui écrit un lab. Le jour où un contributeur
travaille avec une dsoxlab plus ancienne, la règle tient encore.

CE QU'IL NE FAIT PAS

Il n'exempte pas les fichiers cachés, et c'est délibéré : deux labs déclarent
une fixture cachée à dessein — `.terraform.lock.hcl` pour `workspace`,
`.gitignore` pour `terraform-in-automation`. Les écarter du balayage ferait
passer ces deux déclarations pour des fantômes, c'est-à-dire inventerait un
défaut là où il n'y en a pas.

    pytest tests/test_fixtures_declarees.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "scripts"))
from lecture_yaml import lire_yaml  # noqa: E402

LABS = sorted(p.parent for p in (RACINE / "labs").rglob("lab.yaml"))


@pytest.mark.parametrize("lab", LABS, ids=lambda p: str(p.relative_to(RACINE / "labs")))
def test_les_fixtures_declarees_sont_celles_du_dossier(lab: Path) -> None:
    runtime = (lire_yaml(lab / "lab.yaml") or {}).get("runtime") or {}
    declarees = set(runtime.get("fixtures") or [])
    dossier = lab / "fixtures"
    if not declarees and not dossier.is_dir():
        pytest.skip("lab sans fixtures")

    presentes = (
        {
            str(p.relative_to(dossier))
            for p in dossier.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts
        }
        if dossier.is_dir()
        else set()
    )

    oubliees = sorted(presentes - declarees)
    fantomes = sorted(declarees - presentes)

    assert not oubliees, (
        f"{lab.relative_to(RACINE / 'labs')} : des fichiers de `fixtures/` ne "
        f"sont pas dans `runtime.fixtures`, donc `dsoxlab run` ne les copiera "
        f"pas : {', '.join(oubliees)}\n\n"
        "Déclarez-les, ou sortez-les de `fixtures/` s'ils servent à autre chose "
        "— un template lu par `setup.yaml` vit dans `templates/`."
    )
    assert not fantomes, (
        f"{lab.relative_to(RACINE / 'labs')} : `runtime.fixtures` déclare des "
        f"fichiers absents de `fixtures/`, et `dsoxlab run` échouera en les "
        f"nommant : {', '.join(fantomes)}"
    )


def test_le_controle_voit_des_labs() -> None:
    """Un glob cassé rendrait toute la suite verte sans rien mesurer."""
    avec_fixtures = [lab for lab in LABS if (lab / "fixtures").is_dir()]
    assert len(LABS) >= 80, f"Seuls {len(LABS)} labs trouvés : le glob a dérivé."
    assert len(avec_fixtures) >= 50, (
        f"Seuls {len(avec_fixtures)} labs portent un dossier `fixtures/`, ce qui "
        "est trop peu pour ce catalogue."
    )
