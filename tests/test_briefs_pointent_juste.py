"""Méta-tests du dépôt : un énoncé ne doit pas envoyer l'apprenant nulle part.

## D'où vient ce contrôle

De l'issue #237 de dsoxlab, corrigée en 0.1.90 : `dsoxlab challenge` annonçait
`<lab>/challenge` en dur, alors que le travail se fait dans
`<lab>/<runtime.workdir>`. Un apprenant a suivi cette ligne, l'a croisée avec un
énoncé parlant de `reponses/cours.txt`, en a conclu `challenge/reponses/`, et a
perdu une demi-heure sur son premier lab en suivant l'outil à la lettre.

Mesuré côté dsoxlab : les mêmes trois fichiers valaient **0/100** à la racine et
**100/100** sous le workdir. La ligne n'était pas imprécise, elle désignait un
endroit où rien n'est lu.

Le correctif a été accompagné d'un garde-fou côté moteur, qui vérifie que
l'énoncé du lab de démonstration cite bien les fichiers que son test lit. Ce
fichier-ci applique la même idée à ce catalogue, par l'autre bout : tout chemin
qu'un énoncé cite doit exister quelque part.

## Ce qu'il vérifie, et ce qu'il ne peut pas

Il vérifie qu'un chemin cité entre accents graves existe : soit c'est le
répertoire de travail que le lab déclare, soit c'est un fichier ou un dossier
réellement présent dans le lab ou ses fixtures.

Il ne vérifie pas que l'énoncé cite TOUT ce que les tests lisent : un test peut
lire un fichier que l'apprenant produit, dont le nom est justement ce qu'il doit
trouver. Exiger l'inverse reviendrait à donner la réponse dans l'énoncé.
"""

import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
LABS = REPO / "labs"

# Les chemins cités entre accents graves, sous `challenge/`. Le reste du texte
# parle de commandes et de concepts, pas d'emplacements.
CHEMIN_CITE = re.compile(r"`(challenge/[A-Za-z0-9_./-]+)`")

ENONCES = ("challenge/README.fr.md", "challenge/README.md")


def tous_les_labs() -> list[str]:
    return sorted(str(c.parent.relative_to(LABS)) for c in LABS.rglob("lab.yaml"))


def workdir_declare(rel: str) -> str:
    données = yaml.safe_load((LABS / rel / "lab.yaml").read_text(encoding="utf-8"))
    return ((données.get("runtime") or {}).get("workdir") or "").rstrip("/")


def chemins_cites(rel: str) -> set[str]:
    trouvés: set[str] = set()
    for nom in ENONCES:
        chemin = LABS / rel / nom
        if chemin.is_file():
            trouvés |= set(CHEMIN_CITE.findall(chemin.read_text(encoding="utf-8")))
    return trouvés


@pytest.mark.parametrize("rel", tous_les_labs())
def test_un_enonce_ne_cite_aucun_chemin_inexistant(rel: str) -> None:
    """Un chemin cité doit mener quelque part.

    Trois cas légitimes, et un seul fautif :

      - le répertoire de travail déclaré par le lab, qui n'existe qu'après
        `dsoxlab run` : c'est le cas le plus courant ;
      - un chemin SOUS ce répertoire, donc une fixture qui y sera copiée ;
      - un fichier ou un dossier réellement présent dans le lab, comme un
        répertoire de référence posé à côté du travail.

    Tout le reste envoie l'apprenant à un endroit où rien ne l'attend.
    """
    workdir = workdir_declare(rel)
    lab = LABS / rel

    egares = []
    for cite in sorted(chemins_cites(rel)):
        propre = cite.rstrip("/")

        if workdir and (propre == workdir or propre.startswith(workdir + "/")):
            # Sous le workdir : la cible vient des fixtures, verifiees ailleurs.
            continue
        if (lab / propre).exists():
            continue
        egares.append(cite)

    assert not egares, (
        f"{rel} cite des chemins qui n'existent pas : {egares}\n\n"
        f"Répertoire de travail déclaré : `{workdir or 'aucun'}`\n\n"
        "Un énoncé qui désigne un endroit où rien n'est lu coûte une demi-heure "
        "à qui le suit à la lettre : c'est ce que l'issue #237 de dsoxlab a "
        "mesuré, où les mêmes fichiers valaient 0/100 au mauvais endroit et "
        "100/100 au bon."
    )


def test_le_controle_porte_sur_quelque_chose() -> None:
    """Sans cela, une expression régulière cassée rendrait tout vert.

    Un contrôle qui ne trouve plus rien à contrôler est vert, et c'est la forme
    la plus discrète de faux vert.
    """
    citants = [rel for rel in tous_les_labs() if chemins_cites(rel)]
    assert len(citants) >= 50, (
        f"Seuls {len(citants)} énoncés citent un chemin, ce qui est trop peu "
        "pour un catalogue de cette taille : l'expression régulière ne trouve "
        "probablement plus rien."
    )
