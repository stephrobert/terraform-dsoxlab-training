"""Tests fonctionnels du lab « reprendre apres un apply qui a echoue ».

Un `apply` qui echoue en cours de route laisse un state PARTIEL. Ce n'est pas un
accident a effacer : c'est le point de depart de la reparation. Le reflexe de
tout detruire pour repartir de zero est exactement ce que ce lab veut faire
perdre, parce qu'il detruit des ressources parfaitement saines.

Aucun cloud, aucune VM, aucun acces reseau : l'echec est DETERMINISTE et se
reproduit a l'identique sur n'importe quel poste.

Aucun test ne relit les `.tf` de l'apprenant, et aucun ne parse un message
d'erreur : le texte d'un message change avec les versions, l'etat structure non.

## L'empreinte de reprise, et pourquoi elle est le coeur du lab

Les identifiants des ressources creees AVANT l'echec sont releves sur l'etat de
depart, puis compares apres la reparation. Toute valeur differente signe une
destruction suivie d'une recreation : la configuration a peut-etre l'air juste,
mais le travail a ete refait au lieu d'etre repris.

C'est la seule facon de distinguer « j'ai repare » de « j'ai tout jete et
recommence », les deux donnant le meme etat final.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, message, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "first-infra-debug-apply"

IDENTIFIANT = "random_pet.identifiant"
INVENTAIRE = "local_file.inventaire"
RAPPORT = "null_resource.rapport"

# Les deux ressources que le premier apply cree AVANT d'echouer. Ce sont elles
# qui doivent survivre a la reparation.
DEJA_CREEES = (IDENTIFIANT, INVENTAIRE)

# Les identifiants du state FOURNI. Ils sont desormais deterministes pour tout
# le monde : le lab ne depend plus de ce que l'apprenant a lance avant.
#
# Releves le 2026-09-24 sur le state genere par l'apply en echec.
IDENTIFIANTS_DE_DEPART = {
    IDENTIFIANT: 'smiling-newt',
    INVENTAIRE: 'a982f4432f9af75aa7d625c6307c8d93673650e6',
}


def _tf(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["terraform", *args], cwd=cwd or WORKDIR, capture_output=True, text=True,
        check=False,
    )


def _gerees(cwd: Path | None = None) -> dict[str, dict]:
    proc = _tf("show", "-json", cwd=cwd)
    proc.check_returncode()
    racine = json.loads(proc.stdout).get("values", {}).get("root_module", {})
    return {
        r["address"]: r for r in racine.get("resources", []) if r["mode"] == "managed"
    }


def _exiger_reparation_faite() -> None:
    """Garde commune : sans reparation, les controles suivants ne disent rien.

    Mesure le 2026-09-24 : trois tests de ce fichier passaient AVANT tout
    travail, et pour une raison qui tient au dessin du lab. Le state est
    FOURNI : les trois ressources y figurent deja, et leurs identifiants ne
    bougent pas tant qu'on ne touche a rien. Constater leur presence revenait
    donc a constater la fixture.

    Ce qui distingue un lab repare d'un lab intact est que l'apply ABOUTIT. On
    l'exige donc d'abord, par ce que le provisioner produit reellement.
    """
    produits = list(WORKDIR.rglob("rapport.txt"))
    assert produits, message(
        en="The report does not exist: the apply still fails.\n\nThis check can "
        "only decide once the cause is fixed in the configuration. "
        "The state provided already carries the three resources, and observing them "
        "would prove nothing.",
        fr="Le rapport n'existe pas : l'apply échoue encore.\n\nCe contrôle ne "
        "peut se prononcer qu'une fois la cause corrigée dans la configuration. "
        "Le state fourni porte déjà les trois ressources, et les constater ne "
        "prouverait rien.",
    )

    fautive = _gerees().get(RAPPORT)
    assert fautive is not None and not fautive.get("tainted"), message(
        en=f"`{RAPPORT}` is still marked `tainted` in the state.\n\nTerraform "
        "knows it is in a doubtful state and will replace it at the next "
        "apply. As long as it is, the repair has not succeeded.",
        fr=f"`{RAPPORT}` est encore marquée `tainted` dans le state.\n\nTerraform "
        "sait qu'elle est dans un état douteux et la remplacera au prochain "
        "apply. Tant qu'elle l'est, la réparation n'a pas abouti.",
    )


@pytest.fixture(scope="module")
def repare() -> Iterator[None]:
    """Applique la configuration de l'apprenant sur le state FOURNI.

    Le state de depart n'est plus calcule : il est pose par les fixtures, donc
    identique pour tout le monde. C'est ce qui rend l'empreinte de reprise
    comparable, et le lab reproductible.

    L'apply peut echouer, et c'est meme le cas nominal tant que la
    configuration n'est pas reparee : les tests diront pourquoi, chacun a sa
    facon.
    """
    exiger_workdir(WORKDIR, LAB_ID)

    init = _tf("init", "-input=false", "-no-color")
    if init.returncode != 0:
        pytest.fail(message(
            en=f"`terraform init` failed.\n{init.stderr[-1200:]}",
            fr=f"`terraform init` a échoué.\n{init.stderr[-1200:]}",
        ))

    _tf("apply", "-auto-approve", "-input=false", "-no-color")
    yield


# --------------------------------------------------------------------------
# 1. La ressource fautive n'a pas ete supprimee ni neutralisee.
# --------------------------------------------------------------------------
def test_la_ressource_fautive_existe_toujours(repare: None) -> None:
    """Faire disparaitre une ressource n'est pas la reparer.

    Supprimer `null_resource.rapport`, ou la commenter, fait disparaitre
    l'echec ET le besoin. Le rapport devait etre produit : c'est la raison
    d'etre de cette ressource, pas un caprice.
    """
    _exiger_reparation_faite()

    gerees = _gerees()
    assert RAPPORT in gerees, message(
        en=f"`{RAPPORT}` is absent from the state. Addresses present: "
        f"{sorted(gerees)}.\n\nIf you deleted or commented it out, the failure "
        "disappeared and so did the need. The repair consists in fixing the CAUSE "
        "in the configuration, not in removing what fails.",
        fr=f"`{RAPPORT}` est absente du state. Adresses présentes : "
        f"{sorted(gerees)}.\n\nSi vous l'avez supprimée ou commentée, l'échec a "
        "disparu et le besoin aussi. La réparation consiste à corriger la CAUSE "
        "dans la configuration, pas à retirer ce qui échoue.",
    )


# --------------------------------------------------------------------------
# 2. Toutes les ressources declarees sont la.
# --------------------------------------------------------------------------
def test_toutes_les_ressources_declarees_sont_dans_le_state(
    repare: dict[str, str],
) -> None:
    _exiger_reparation_faite()

    gerees = set(_gerees())
    manquantes = {IDENTIFIANT, INVENTAIRE, RAPPORT} - gerees
    assert not manquantes, message(
        en=f"These resources are missing from the state: {sorted(manquantes)}.\nPresent: "
        f"{sorted(gerees)}.",
        fr=f"Ces ressources manquent au state : {sorted(manquantes)}.\nPrésentes : "
        f"{sorted(gerees)}.",
    )


# --------------------------------------------------------------------------
# 3. Le coeur du lab : les identifiants n'ont pas bouge.
# --------------------------------------------------------------------------
def test_les_ressources_deja_creees_n_ont_pas_ete_recreees(
    repare: dict[str, str],
) -> None:
    """La seule preuve qu'on a REPRIS plutot que TOUT REFAIT.

    Un `terraform destroy` suivi d'un nouvel apply donne exactement le meme
    etat final, et une configuration tout aussi correcte. La difference ne se
    voit que dans les identifiants : ceux que le premier apply avait attribues
    ont disparu.

    Sur un fichier local, cela ne coute rien. Sur une base de donnees ou un
    volume, cela coute les donnees.
    """
    _exiger_reparation_faite()

    gerees = _gerees()
    for adresse, avant in IDENTIFIANTS_DE_DEPART.items():
        assert adresse in gerees, message(
            en=f"`{adresse}` has disappeared from the state.",
            fr=f"`{adresse}` a disparu du state.",
        )
        apres = gerees[adresse]["values"].get("id")
        assert apres == avant, message(
            en=f"`{adresse}` carried the identifier {avant!r} before the repair, "
            f"and {apres!r} after.\n\nIt was therefore DESTROYED and then RECREATED. "
            "The final state may be correct, but the work was redone "
            "instead of being taken over: a global teardown, or a `-replace`, "
            "takes perfectly healthy resources away.",
            fr=f"`{adresse}` portait l'identifiant {avant!r} avant la réparation, "
            f"et {apres!r} après.\n\nElle a donc été DÉTRUITE puis RECRÉÉE. "
            "L'état final est peut-être correct, mais le travail a été refait "
            "au lieu d'être repris : un `destroy` global, ou un `-replace`, "
            "emporte des ressources parfaitement saines.",
        )


# --------------------------------------------------------------------------
# 4. La reparation a fait ABOUTIR l'execution.
# --------------------------------------------------------------------------
def test_le_rapport_existe_reellement_sur_le_disque(repare: None) -> None:
    """L'effet reel, et non la seule presence dans le state.

    Une `null_resource` peut figurer au state alors que son provisioner n'a
    rien produit : le state enregistre ce que Terraform a decide, pas ce qui
    s'est passe sur le disque.
    """
    attendus = list(WORKDIR.rglob("rapport.txt"))
    assert attendus, message(
        en="No `rapport.txt` on disk.\n\nThe resource may appear in the "
        "state, but its provisioner produced nothing: the state records what "
        "Terraform decided, not what actually happened.",
        fr="Aucun `rapport.txt` sur le disque.\n\nLa ressource figure peut-être au "
        "state, mais son provisioner n'a rien produit : le state enregistre ce "
        "que Terraform a décidé, pas ce qui s'est réellement passé.",
    )

    contenu = attendus[0].read_text(encoding="utf-8")
    identifiant = _gerees()[IDENTIFIANT]["values"]["id"]
    assert identifiant in contenu, message(
        en=f"The report does not carry the identifier {identifiant!r}.\nIt contains:\n"
        f"{contenu[:200]!r}\n\nIt must be a copy of the inventory, which itself "
        "derives from the identifier.",
        fr=f"Le rapport ne porte pas l'identifiant {identifiant!r}.\nIl contient :\n"
        f"{contenu[:200]!r}\n\nIl doit être la copie de l'inventaire, qui lui "
        "dérive de l'identifiant.",
    )


# --------------------------------------------------------------------------
# 5. Les deux cotes : la configuration converge, ET elle se rejoue a neuf.
# --------------------------------------------------------------------------
def test_la_configuration_converge_et_se_rejoue_sur_un_repertoire_neuf(
    repare: None, tmp_path: Path
) -> None:
    """La convergence seule ne distingue pas une vraie reparation d'un `mkdir`.

    Creer le repertoire a la main fait passer l'apply et converger le plan. La
    configuration reste pourtant fausse : sur une machine neuve, ou apres un
    `destroy`, elle echouera de la meme facon, et le collegue qui la reprendra
    ne comprendra pas pourquoi elle marche chez vous.

    Ce test rejoue donc la configuration dans un repertoire VIERGE, sans rien
    d'autre que les `.tf`. Si la reparation est dans le code, elle passe. Si
    elle etait dans un `mkdir`, elle echoue ici.
    """
    stable = _tf("plan", "-detailed-exitcode", "-input=false", "-no-color")
    assert stable.returncode == 0, message(
        en=f"`plan -detailed-exitcode` returns {stable.returncode}, expected 0.\n"
        f"{stable.stdout[-1200:]}",
        fr=f"`plan -detailed-exitcode` rend {stable.returncode}, attendu 0.\n"
        f"{stable.stdout[-1200:]}",
    )

    neuf = tmp_path / "a-neuf"
    neuf.mkdir()
    for source in WORKDIR.glob("*.tf"):
        (neuf / source.name).write_bytes(source.read_bytes())

    init = _tf("init", "-input=false", "-no-color", cwd=neuf)
    assert init.returncode == 0, message(
        en=f"`init` failed on the replay:\n{init.stderr[-800:]}",
        fr=f"`init` a échoué sur le rejeu :\n{init.stderr[-800:]}",
    )

    rejeu = _tf("apply", "-auto-approve", "-input=false", "-no-color", cwd=neuf)
    assert rejeu.returncode == 0, message(
        en="The configuration FAILS on a fresh directory, although it converges "
        "on yours.\n\nThe repair is therefore not in the code: a `mkdir` "
        "run by hand makes the apply pass here and nowhere else. The "
        "missing directory must be created by a RESOURCE.\n"
        f"{(rejeu.stderr or rejeu.stdout)[-1500:]}",
        fr="La configuration ÉCHOUE sur un répertoire neuf, alors qu'elle converge "
        "chez vous.\n\nLa réparation n'est donc pas dans le code : un `mkdir` "
        "lancé à la main fait passer l'apply ici et nulle part ailleurs. Le "
        "répertoire manquant doit être créé par une RESSOURCE.\n"
        f"{(rejeu.stderr or rejeu.stdout)[-1500:]}",
    )

    _tf("destroy", "-auto-approve", "-input=false", "-no-color", cwd=neuf)
