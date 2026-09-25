"""Tests fonctionnels du lab « les commandes que l'examen attend ».

Huit preuves couvrant ce qu'un candidat doit savoir FAIRE, et non reciter :
`validate`, `fmt`, la cascade de precedence, `moved`, `import`, `removed`,
`-replace`, et ce que `sensitive` protege vraiment.

Aucun cloud, aucune VM. Aucun test ne relit les `.tf` de l'apprenant, et aucun
ne parse un message : seuls des codes de retour, du JSON et l'etat du disque.

Codes MESURES sur Terraform 1.16.1, avant d'ecrire une assertion :

    validate avant init ......... 1   (les schemas manquent, rien n'est validable)
    validate sur config valide ... 0
    validate attribut inexistant . 1
    fmt -check mal indente ....... 3   (et non 1 : un test `-eq 1` laisserait tout passer)
    fmt -check apres fmt ......... 0
    plan -detailed avant apply ... 2

Une contrainte du lab a ete decouverte en l'ecrivant : `terraform init` PARSE la
configuration, donc il echoue sur un `???`. Son message parle d'operateur
ternaire, ce qui envoie chercher au mauvais endroit.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from conftest import exiger_workdir, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "certifications-associate-essential-commands"

CODES = "preuves/codes.json"
PLAN_REPLACE = "preuves/plan-replace.json"
PREEXISTANT = "etat/preexistant.txt"

ANCIENNE_ADRESSE = "random_pet.ancien_nom"
ADOPTEE = "local_file.adopte"
IMPORTEE = "terraform_data.provisionne_ailleurs"
A_REMPLACER = "null_resource.a_remplacer"

CODES_ATTENDUS = {
    "validate_avant_init": 1,
    "validate_configuration_valide": 0,
    "validate_attribut_absent": 1,
    "fmt_check_avant": 3,
    "fmt_check_apres": 0,
    "plan_avant_convergence": 2,
}

CASCADE = {
    "gagnant_default": "gagnant-default",
    "gagnant_environnement": "gagnant-environnement",
    "gagnant_fichier": "gagnant-fichier",
    "gagnant_ligne_de_commande": "gagnant-ligne-de-commande",
}


# L'environnement du lab. Il n'est pas decoratif : `par_environnement` ne
# recoit sa valeur que de la, et un `plan` lance sans lui verrait la variable
# retomber sur son `default`.
#
# Mesure le 2026-09-24, apres avoir ecrit un test qui l'oubliait : le plan
# annoncait alors un changement d'output et rendait 2 au lieu de 0. Le defaut
# n'etait pas dans la configuration de l'apprenant, mais dans mon harnais.
#
# C'est un enseignement du lab a part entiere : une configuration qui depend de
# l'environnement n'est reproductible que si cet environnement l'est aussi.
ENVIRONNEMENT_DU_LAB = {
    "TF_VAR_par_environnement": "gagnant-environnement",
    "TF_VAR_par_fichier": "perdant-environnement",
    "TF_VAR_par_ligne_de_commande": "perdant-environnement",
}


def _tf(*args: str) -> subprocess.CompletedProcess[str]:
    return _tf_dans(WORKDIR, *args)


def _tf_dans(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["terraform", *args], cwd=cwd, capture_output=True, text=True,
        check=False, env={**os.environ, **ENVIRONNEMENT_DU_LAB},
    )


def _copie_jetable(racine: Path, nom: str, avec_init: bool = True) -> Path:
    """Une copie du repertoire de travail, ou l'on peut casser sans rien perdre.

    Les binaires de providers pesent une cinquantaine de megaoctets : on ne les
    recopie pas, on les emprunte par lien symbolique. Terraform suit ce lien,
    ce qui evite un `init` reseau par geste rejoue.

    `avec_init=False` rend le repertoire tel qu'il etait AVANT tout `init` :
    c'est le seul etat ou `validate` peut montrer qu'il lui manque les schemas.
    """
    dest = racine / nom
    shutil.copytree(
        WORKDIR, dest,
        ignore=shutil.ignore_patterns(".terraform", "preuves", "*.tfplan"),
    )
    if avec_init:
        (dest / ".terraform").symlink_to(WORKDIR / ".terraform", target_is_directory=True)
    return dest


@pytest.fixture(scope="module")
def joue() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    return WORKDIR


def _charger(nom: str) -> dict:
    chemin = WORKDIR / nom
    assert chemin.is_file(), (
        f"`{nom}` est absent. Le lab demande de le produire : c'est la trace de "
        "ce que vous avez observe, et elle ne se reconstitue pas apres coup."
    )
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erreur:
        pytest.fail(f"`{nom}` n'est pas du JSON valide : {erreur}")


def _gerees() -> dict[str, dict]:
    proc = _tf("show", "-json")
    proc.check_returncode()
    racine = json.loads(proc.stdout).get("values", {}).get("root_module", {})
    return {
        r["address"]: r for r in racine.get("resources", []) if r["mode"] == "managed"
    }


def _sorties() -> dict:
    proc = _tf("output", "-json")
    proc.check_returncode()
    return json.loads(proc.stdout or "{}")


# --------------------------------------------------------------------------
# 1. Les six codes de retour, releves en cours de route.
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def codes_rejoues(joue: Path, tmp_path_factory: pytest.TempPathFactory) -> dict[str, int]:
    """Les six gestes, rejoues par le test lui-meme dans des copies jetables.

    Comparer `codes.json` a une table de constantes ne mesurerait rien du
    systeme : cela dirait seulement que l'apprenant a ecrit les bons chiffres.
    Le test les releve donc lui-meme, sur le repertoire de l'apprenant, et
    compare les deux releves.

    Ce n'est pas un dispositif anti-triche : les tests sont publics, et qui les
    lit y verra les chiffres. C'est une garantie de JUSTESSE. Le jour ou une
    version de Terraform change un de ces codes, ce lab recalerait des
    candidats irreprochables ; ici, c'est le rejeu qui parle, et le message
    nomme l'ecart au lieu de le mettre sur le dos de l'apprenant.
    """
    racine = tmp_path_factory.mktemp("rejeu")
    releves: dict[str, int] = {}

    # 1. `validate` sans schemas. Le repertoire est copie SANS `.terraform`.
    avant_init = _copie_jetable(racine, "avant-init", avec_init=False)
    (avant_init / ".terraform.lock.hcl").unlink(missing_ok=True)
    releves["validate_avant_init"] = _tf_dans(avant_init, "validate", "-no-color").returncode

    # 2. `validate` sur la configuration reparee, schemas en place.
    valide = _copie_jetable(racine, "valide")
    releves["validate_configuration_valide"] = _tf_dans(valide, "validate", "-no-color").returncode

    # 5. Le format canonique se mesure sur la meme copie, intacte.
    releves["fmt_check_apres"] = _tf_dans(valide, "fmt", "-check", "-recursive", "-no-color").returncode

    # 3. Un attribut qui n'existe dans aucun schema. C'est precisement ce que
    #    « validate ne fait que la syntaxe » pretend impossible.
    attribut = _copie_jetable(racine, "attribut-absent")
    (attribut / "zz_sonde.tf").write_text(
        'resource "null_resource" "sonde_du_test" {\n'
        '  attribut_qui_n_existe_dans_aucun_schema = true\n'
        "}\n",
        encoding="utf-8",
    )
    releves["validate_attribut_absent"] = _tf_dans(attribut, "validate", "-no-color").returncode

    # 4. Un fichier hors format canonique.
    mal_indente = _copie_jetable(racine, "mal-indente")
    cible = mal_indente / "versions.tf"
    cible.write_text(
        "".join(
            "    " + ligne if ligne.strip() else ligne
            for ligne in cible.read_text(encoding="utf-8").splitlines(True)
        ),
        encoding="utf-8",
    )
    releves["fmt_check_avant"] = _tf_dans(mal_indente, "fmt", "-check", "-recursive", "-no-color").returncode

    # 6. Un plan sur un repertoire dont l'etat a ete retire : tout reste a faire.
    a_converger = _copie_jetable(racine, "avant-convergence")
    for trace in a_converger.glob("terraform.tfstate*"):
        trace.unlink()
    releves["plan_avant_convergence"] = _tf_dans(
        a_converger, "plan", "-detailed-exitcode", "-input=false", "-no-color",
        "-var", "par_ligne_de_commande=gagnant-ligne-de-commande",
    ).returncode

    return releves


def test_les_six_codes_de_retour_sont_ceux_observes(
    joue: Path, codes_rejoues: dict[str, int]
) -> None:
    """Ces codes ne se reconstituent PAS apres coup.

    Une fois la configuration reparee, `validate` ne peut plus rendre 1 et
    `fmt -check` ne peut plus rendre 3. C'est pourquoi le lab demande de les
    consigner au moment ou ils sont observes.
    """
    # D'abord le harnais. Si le rejeu ne retrouve pas ce qui a ete mesure le
    # 2026-09-24 sur Terraform 1.16.1, le lab a vieilli et ce n'est pas au
    # candidat de le payer.
    derive = {
        geste: (obtenu, CODES_ATTENDUS[geste])
        for geste, obtenu in codes_rejoues.items()
        if obtenu != CODES_ATTENDUS[geste]
    }
    assert not derive, (
        "Le rejeu ne retrouve plus les codes mesures en ecrivant ce lab :\n"
        + "\n".join(f"  {g} : rejoue {o}, attendu {a}" for g, (o, a) in sorted(derive.items()))
        + "\n\nCE N'EST PAS VOTRE TRAVAIL QUI EST EN CAUSE. Une version de "
        "Terraform a change un de ces comportements ; le lab doit etre remesure. "
        f"Version en place : {_tf('version').stdout.splitlines()[0] if _tf('version').returncode == 0 else 'inconnue'}."
    )

    releves = _charger(CODES)
    manquants = set(CODES_ATTENDUS) - set(releves)
    assert not manquants, (
        f"Ces codes manquent a `{CODES}` : {sorted(manquants)}.\nRelevés : "
        f"{sorted(releves)}."
    )

    for geste, attendu in sorted(codes_rejoues.items()):
        obtenu = releves[geste]
        assert obtenu == attendu, (
            f"`{geste}` vaut {obtenu!r}, le rejeu donne {attendu}.\n\n"
            + (
                "`fmt -check` rend 3, et non 1. Un script qui testerait `-eq 1` "
                "laisserait passer tous les fichiers mal indentes."
                if geste.startswith("fmt")
                else "`validate` a besoin des SCHEMAS des providers : avant "
                "`init`, il ne peut rien valider, et echoue pour cette raison "
                "et non pour une faute de syntaxe."
                if geste == "validate_avant_init"
                else "Relevez le code au moment ou vous lancez la commande."
            )
        )


# --------------------------------------------------------------------------
# 2. La cascade de precedence, quatre gagnants distincts.
# --------------------------------------------------------------------------
def test_chaque_marche_de_la_cascade_designe_son_gagnant(joue: Path) -> None:
    sorties = _sorties()
    for nom, attendu in CASCADE.items():
        assert nom in sorties, (
            f"L'output `{nom}` n'est pas declare. Presents : {sorted(sorties)}."
        )
        obtenu = sorties[nom]["value"]
        assert obtenu == attendu, (
            f"`{nom}` vaut {obtenu!r}, attendu {attendu!r}.\n\nChaque variable "
            "est posee par PLUSIEURS sources a la fois : une seule gagne, et le "
            "nom de la valeur dit laquelle."
        )


# --------------------------------------------------------------------------
# 3. Le renommage par `moved` a ete APPLIQUE.
# --------------------------------------------------------------------------
def test_le_renommage_est_passe_par_un_moved_applique(joue: Path) -> None:
    gerees = _gerees()
    assert ANCIENNE_ADRESSE not in gerees, (
        f"`{ANCIENNE_ADRESSE}` figure encore dans le state.\n\nUn `plan` seul "
        "n'ecrit rien : le bloc `moved` doit avoir ete APPLIQUE."
    )
    nouvelles = [a for a in gerees if a.startswith("random_pet.")]
    assert nouvelles, f"Aucun `random_pet` dans le state : {sorted(gerees)}."


# --------------------------------------------------------------------------
# 4. L'adoption par `import`.
# --------------------------------------------------------------------------
def test_la_ressource_preexistante_a_ete_importee(joue: Path) -> None:
    """`terraform_data` est la seule ressource importable des providers locaux.

    Mesure : `local_file`, `null_resource` et `random_pet` repondent tous
    « Resource Import Not Implemented ». Le geste enseigne est le meme, seul le
    type de ressource change.
    """
    gerees = _gerees()
    assert IMPORTEE in gerees, (
        f"`{IMPORTEE}` n'est pas dans le state. Adresses : {sorted(gerees)}."
    )
    identifiant = gerees[IMPORTEE]["values"].get("id")
    assert identifiant == "identifiant-connu", (
        f"`{IMPORTEE}` porte l'identifiant {identifiant!r}, attendu "
        "`identifiant-connu`.\n\nElle a ete CREEE et non importee : un import "
        "reprend l'objet existant avec son identifiant."
    )


# --------------------------------------------------------------------------
# 5. Le retrait par `removed`, l'objet survivant.
# --------------------------------------------------------------------------
def test_la_ressource_retiree_du_state_a_laisse_son_fichier(joue: Path) -> None:
    """L'inverse exact d'un `destroy`, et la seule facon de rendre un objet.

    `removed` avec `lifecycle { destroy = false }` retire la ressource du state
    et laisse l'objet en place. Sans ce `lifecycle`, le meme bloc le
    DETRUIRAIT : un mot d'ecart, et le fichier disparait.
    """
    gerees = _gerees()
    assert ADOPTEE not in gerees, (
        f"`{ADOPTEE}` figure encore dans le state : elle n'a pas ete retiree."
    )
    fichier = joue / PREEXISTANT
    assert fichier.is_file(), (
        f"`{PREEXISTANT}` a DISPARU du disque.\n\nLe bloc `removed` l'a detruit "
        "au lieu de simplement le retirer du state. Il lui manque "
        "`lifecycle { destroy = false }` : un mot d'ecart, et l'objet est perdu."
    )
    assert fichier.read_text(encoding="utf-8").strip(), (
        f"`{PREEXISTANT}` est vide : son contenu a ete reecrit."
    )


# --------------------------------------------------------------------------
# 6. Le plan de remplacement, enregistre sans etre applique.
# --------------------------------------------------------------------------
def test_le_plan_de_remplacement_vise_la_bonne_ressource(joue: Path) -> None:
    plan = _charger(PLAN_REPLACE)
    actions = {
        c["address"]: c["change"]["actions"]
        for c in plan.get("resource_changes", [])
        if c["change"]["actions"] != ["no-op"]
    }
    assert A_REMPLACER in actions, (
        f"Le plan ne vise pas `{A_REMPLACER}`. Il annonce {actions}.\n\n"
        "`-replace=<adresse>` demande explicitement le remplacement d'une "
        "ressource que rien n'obligeait a bouger."
    )
    assert set(actions[A_REMPLACER]) == {"delete", "create"}, (
        f"`{A_REMPLACER}` porte {actions[A_REMPLACER]}, attendu une destruction "
        "suivie d'une creation."
    )
    assert set(actions) == {A_REMPLACER}, (
        f"Le plan touche aussi {sorted(set(actions) - {A_REMPLACER})}.\n\n"
        "`-replace` ne vise QU'UNE ressource : si d'autres bougent, la "
        "configuration n'avait pas converge avant."
    )


# --------------------------------------------------------------------------
# 7. `sensitive` masque l'ecran, et RIEN d'autre.
# --------------------------------------------------------------------------
def test_la_sortie_sensible_est_masquee_mais_en_clair_dans_le_state(
    joue: Path,
) -> None:
    sorties = _sorties()
    assert "identifiant_sensible" in sorties, (
        f"L'output `identifiant_sensible` est absent : {sorted(sorties)}."
    )
    assert sorties["identifiant_sensible"]["sensitive"] is True, (
        "`identifiant_sensible` n'est pas marque sensible."
    )

    humaine = _tf("output", "-no-color")
    assert humaine.returncode == 0, f"`terraform output` a echoue.\n{humaine.stderr}"
    ligne = next(
        (
            ligne
            for ligne in humaine.stdout.splitlines()
            if ligne.startswith("identifiant_sensible")
        ),
        "",
    )
    assert "<sensitive>" in ligne, f"L'affichage rend {ligne!r} : rien n'est masque."

    # L'autre moitie, et c'est elle qui enseigne : le masquage s'arrete a
    # l'ecran. Le state porte la valeur en clair.
    etat = json.loads((joue / "terraform.tfstate").read_text(encoding="utf-8"))
    assert etat["outputs"]["identifiant_sensible"]["value"] == (
        sorties["identifiant_sensible"]["value"]
    ), (
        "La valeur sensible ne figure pas en clair dans `terraform.tfstate`. "
        "Elle devrait : `sensitive` ne chiffre rien, il cache un affichage."
    )


# --------------------------------------------------------------------------
# 8. Les deux cotes : tout converge, et le formatage tient.
# --------------------------------------------------------------------------
def test_la_configuration_converge_et_reste_au_format_canonique(
    joue: Path,
) -> None:
    """La convergence seule serait vraie d'une configuration a peine ecrite.

    Accolee au formatage, elle dit autre chose : la configuration a ete
    reprise, reformatee par l'outil, et elle tient toujours. Les deux codes de
    retour sont lus, jamais la sortie.
    """
    plan = _tf("plan", "-detailed-exitcode", "-input=false", "-no-color",
               "-var", "par_ligne_de_commande=gagnant-ligne-de-commande")
    assert plan.returncode == 0, (
        f"`plan -detailed-exitcode` rend {plan.returncode}, attendu 0.\n"
        f"{plan.stdout[-1200:]}"
    )

    format_ = _tf("fmt", "-check", "-recursive", "-no-color")
    assert format_.returncode == 0, (
        f"`fmt -check -recursive` rend {format_.returncode}, attendu 0.\n\n"
        "Des fichiers sont hors format canonique :\n"
        f"{format_.stdout[-500:]}\n\nLancez `terraform fmt -recursive` plutot "
        "que de reindenter a la main."
    )
