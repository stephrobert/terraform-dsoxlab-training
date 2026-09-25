"""Méta-tests du dépôt : ce qu'un lab Floci doit porter pour ne rien laisser.

## Le défaut que ces tests ferment

Floci démarre un vrai conteneur Docker derrière chaque instance EC2, et lui
publie un port SSH (2200, 2201, ...). Ces conteneurs **survivent** à l'arrêt de
Floci comme à `dsoxlab clean`.

Mesuré le 2026-09-24 : après une session interrompue, la création d'instance
suivante échoue sur

    Bind for 0.0.0.0:2201 failed: port is already allocated

message qui ne parle ni d'instance, ni de lab, ni de port SSH. L'instance reste
dans un état non démarré, les filtres `instance-state-name=running` ne la
retournent plus, et le lab paraît cassé sans raison. Deux cycles ont été perdus
là-dessus, sur deux labs différents.

## Les deux moitiés, et pourquoi il en faut deux

**Un `destroy` en fin de tests** couvre le cas nominal : le lab range ce qu'il a
sorti. Il ne couvre pas l'interruption, Ctrl-C ou échec avant le dernier test.

**La déclaration `spawns`** couvre l'interruption : dsoxlab retire les
conteneurs engendrés quand il (re)crée le conteneur de service et au `clean`.

Aucune des deux ne suffit seule, et c'est pourquoi les deux sont exigées ici.

## Ce que ces tests ne peuvent pas faire

Ils lisent la déclaration, pas l'exécution : ils vérifient qu'un lab Floci
DÉCLARE ce qu'il engendre et qu'il détruit, pas que dsoxlab nettoie. Cela se
mesure en jouant le lab, et cela a été fait sur dsoxlab 0.1.89, dans les trois
cas du contrat :

- un orphelin retenant le port 2200, posé à la main, disparaît quand dsoxlab
  crée le conteneur de service ;
- une instance créée par l'apprenant SURVIT à un `run` qui réutilise un service
  déjà debout ;
- elle disparaît au `clean`.

C'est la deuxième qui distingue la déclaration du contournement qu'elle
remplace : celui-ci supprimait le travail en cours.
"""

from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
LABS = REPO / "labs"

FRAGMENT_ENGENDRE = "floci-ec2"
PORT_CANONIQUE = "14566:4566"
NOM_CANONIQUE = "floci"


def labs_floci() -> list[str]:
    """Les labs qui déclarent Floci comme service."""
    trouves = []
    for lab in sorted(LABS.rglob("lab.yaml")):
        données = yaml.safe_load(lab.read_text(encoding="utf-8"))
        services = (données.get("runtime") or {}).get("services") or []
        if any("floci" in (s.get("image") or "") for s in services):
            trouves.append(str(lab.parent.relative_to(LABS)))
    return trouves


def service_floci(rel: str) -> dict:
    données = yaml.safe_load((LABS / rel / "lab.yaml").read_text(encoding="utf-8"))
    for service in données["runtime"]["services"]:
        if "floci" in (service.get("image") or ""):
            return service
    raise AssertionError(f"{rel} : service floci introuvable")


LABS_FLOCI = labs_floci()


def test_au_moins_un_lab_utilise_floci() -> None:
    """Sans cela, les tests ci-dessous passeraient sur une liste vide.

    Un fichier de tests paramétré sur une liste vide est vert, et ne mesure
    rien. C'est la forme la plus discrète de faux vert.
    """
    assert LABS_FLOCI, (
        "Aucun lab ne déclare Floci. Soit la détection est cassée, soit les "
        "labs AWS ont perdu leur service."
    )


@pytest.mark.parametrize("rel", LABS_FLOCI)
def test_un_lab_floci_declare_les_conteneurs_qu_il_engendre(rel: str) -> None:
    """Le champ `spawns`, apparu en dsoxlab 0.1.89 sur l'issue #239.

    Il remplace le contournement que ce dépôt portait : un script curl vers
    l'API Docker, posé en première commande de chaque `post_start`. Celui-ci
    marchait et avait trois défauts que la déclaration supprime.

    Il nettoyait à CHAQUE démarrage, y compris quand dsoxlab réutilisait un
    conteneur debout : ce que le service avait engendré depuis était alors le
    travail en cours de l'apprenant, et le contournement ne savait pas faire la
    différence. `spawns` ne nettoie qu'à la (re)création et au `clean`, ce qui a
    été vérifié dans les trois cas.

    Il ne protégeait pas non plus les conteneurs de dsoxlab lui-même, et il
    fallait le recopier dans chaque lab.
    """
    spawns = service_floci(rel).get("spawns") or []

    assert spawns, (
        f"{rel} ne déclare aucun `spawns`.\n\nFloci lance un vrai conteneur "
        "Docker derrière chaque instance EC2, et lui publie un port SSH. dsoxlab "
        "ne les connaît pas tant que le lab ne les déclare pas : ils survivent "
        "alors au `clean`, et la prochaine instance échoue sur `port is already "
        "allocated`, un message qui ne parle ni d'instance ni de lab."
    )
    assert FRAGMENT_ENGENDRE in spawns, (
        f"{rel} déclare `spawns: {spawns}`, sans le fragment "
        f"`{FRAGMENT_ENGENDRE}`.\n\nC'est ainsi que Floci nomme les conteneurs "
        "qu'il lance."
    )


@pytest.mark.parametrize("rel", LABS_FLOCI)
def test_un_lab_floci_detruit_ce_qu_il_a_cree(rel: str) -> None:
    """Le nettoyage au démarrage ne dispense pas de ranger en sortant.

    Sans destroy, le lab laisse une instance vivante entre deux sessions, et
    c'est le lab suivant qui la trouve et s'en étonne.
    """
    suite = LABS / rel / "challenge/tests/test_functional.py"
    assert suite.is_file(), f"{rel} n'a pas de test fonctionnel."

    texte = suite.read_text(encoding="utf-8")
    assert "destroy" in texte, (
        f"{rel} ne détruit rien dans ses tests.\n\nUn lab qui crée des "
        "ressources chez un fournisseur, fût-il émulé, doit les rendre."
    )


@pytest.mark.parametrize("rel", LABS_FLOCI)
def test_les_labs_floci_publient_tous_le_meme_port(rel: str) -> None:
    """Deux conventions valaient deux façons de se tromper.

    Mesuré le 2026-09-24 : six labs publiaient Floci sur 14566 et un sur 4566.
    Trois scénarios annonçaient le mauvais port à l'apprenant, dont deux que
    j'avais écrits en recopiant le voisin.

    14566 plutôt que 4566, parce que 4566 est le port par défaut de LocalStack :
    un poste qui en fait tourner un verrait le conflit sans comprendre pourquoi.
    """
    ports = service_floci(rel).get("ports") or []
    assert ports == [PORT_CANONIQUE], (
        f"{rel} publie Floci sur {ports}, attendu ['{PORT_CANONIQUE}'].\n\n"
        "Une seule convention dans le dépôt : sinon un scénario recopié d'un "
        "lab voisin annonce un port faux, et l'apprenant cherche longtemps."
    )


@pytest.mark.parametrize("rel", LABS_FLOCI)
def test_les_labs_floci_nomment_tous_leur_service_pareil(rel: str) -> None:
    """Un nom different vaut un conteneur different, sur le meme port.

    dsoxlab nomme le conteneur d'apres le service : `dsoxlab-<projet>-<service>`.
    Deux noms valent donc deux conteneurs, que rien n'empeche de coexister, sauf
    le port qu'ils se disputent.

    Mesure du 2026-09-24 : un lab nommait son service `cloud` la ou les six
    autres disaient `floci`. Son conteneur tournait encore dix heures apres,
    et le lab suivant echouait sur

        Bind for 0.0.0.0:14566 failed: port is already allocated

    Le message nomme le port, jamais le lab qui le retient, et le `clean` de
    l'un ne touche pas le service de l'autre.
    """
    nom = service_floci(rel).get("name")
    assert nom == NOM_CANONIQUE, (
        f"{rel} nomme son service Floci `{nom}`, attendu `{NOM_CANONIQUE}`.\n\n"
        "dsoxlab derive le nom du conteneur de celui du service : deux noms "
        "valent deux conteneurs qui se disputent le meme port, et le `clean` de "
        "l'un ne stoppe pas l'autre."
    )
