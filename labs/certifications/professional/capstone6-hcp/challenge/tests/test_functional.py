"""Tests fonctionnels du capstone de l'objectif 6.

L'objectif 6 du Professional est le seul évalué **en QCM** : HashiCorp ne
demande aucune manipulation dans HCP Terraform. Ce capstone n'exige donc **aucun
compte**, comme les sept labs de la section.

## Ce qu'un capstone doit faire de plus qu'un lab

Les sept labs traitent un sous-objectif chacun. Ici, chaque situation en croise
DEUX, et c'est tout l'exercice : pris séparément, chaque champ se traite par un
réflexe acquis ; ensemble, ils se renforcent ou s'annulent, et l'ordre dans
lequel on les regarde décide du résultat.

Les six situations produisent **six verdicts différents**. Aucune réponse
constante ne passe, et il n'y a pas non plus de majorité à jouer.

## Les trois croisements qui coûtent

1. **Une policy `mandatory` en échec sur une pull request ne bloque rien**, parce
   qu'il n'y a rien à bloquer : un plan spéculatif ne peut pas appliquer. Le
   réflexe « mandatory donc bloqué » se trompe de question.
2. **Un `advisory` en échec n'empêche pas un auto-apply.** Le niveau décide
   d'une seule chose, et ce n'est pas celle-là.
3. **Un mode d'exécution `local` rend la question des policies sans objet** :
   rien ne s'exécute chez HCP Terraform, donc aucune policy ne s'y évalue.

## Ce que les tests lisent

`terraform output -json` pour l'audit, l'initialisation pour le rattachement, et
le state pour le secret. Aucun `.tf` d'apprenant n'est relu, sauf là où c'est
inévitable et dit.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from conftest import exiger_workdir, output_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "certifications-professional-capstone6-hcp"

AUDIT = "audit"
RATTACHEMENT = "rattachement"
# Le nom du RÉPERTOIRE, pas un mot de passe : ruff se déclenche sur le mot
# « secret » dans le nom de la constante, quelle que soit sa valeur.
REP_SECRET = "secret"  # noqa: S105

ORGANISATION = "atelier-dsoxlab"
WORKSPACE = "audit-conformite"
# Le jeton factice que la fixture pose. Le test vérifie qu'il ne sort ni
# dans la fiche ni dans le state.
JETON = "tfr-9d21c8fa47e3-prod"

# Relevés le 2026-09-25 sur Terraform 1.16.1, chacun sur un cas minimal.
FRONTIERE = "Required token could not be found"
FAUTES = {
    "Conflicting 'cloud' and 'backend'": "un bloc `backend` cohabite avec le bloc `cloud`",
    "Invalid workspaces configuration": "`name` et `tags` figurent ensemble",
    "Variables not allowed": "le bloc `cloud` référence une valeur nommée",
    "Duplicate HCP Terraform configurations": "deux blocs `cloud` sont déclarés",
    "problems during initialisation": "la configuration porte une faute que l'init refuse",
}

VERDICTS_ATTENDUS = {
    "cas1_pr_avec_policy_bloquante": (
        "plan_speculatif",
        "une pull request ne produit qu'un plan spéculatif, qui ne peut RIEN "
        "appliquer. La policy `mandatory` en échec n'y change rien : il n'y a "
        "rien à bloquer. Le réflexe « mandatory donc bloqué » se trompe de "
        "question",
    ),
    "cas2_commit_auto_apply_policy_advisory": (
        "apply_automatique",
        "un `advisory` en échec n'interrompt jamais un run. L'auto-apply "
        "s'applique donc, le déclencheur y donnant droit et l'auteur ayant la "
        "permission",
    ),
    "cas3_commit_auto_apply_policy_mandatory_surchargeable": (
        "bloque_surchargeable",
        "la policy `mandatory` échoue et bloque, mais le policy set autorise "
        "l'override ET l'auteur détient la permission. Les deux sont "
        "nécessaires, et ici les deux sont là",
    ),
    "cas4_commit_sans_changement": (
        "planned_and_finished",
        "« If a plan contains no changes, HCP Terraform does not attempt to "
        "apply it. » L'auto-apply ne s'applique pas à un plan vide",
    ),
    "cas5_run_trigger_tout_permis": (
        "attend_confirmation",
        "« Some plans can't be auto-applied, like plans queued by run triggers "
        "or by users without permission to apply runs. » Le réglage est actif, "
        "le déclencheur n'y donne pas droit",
    ),
    "cas7_mandatory_sans_permission": (
        "bloque",
        "le policy set autorise l'override, mais l'auteur n'a pas la "
        "permission. Les deux sont nécessaires, et une seule ne suffit pas. "
        "Ce cas existe parce qu'une falsification l'a exigé : sans lui, une "
        "règle qui oubliait la permission rendait quand même 15/15",
    ),
    "cas6_mode_local_avec_policy": (
        "aucun_run_distant",
        "un workspace en mode `local` ne sert plus que de backend d'état : "
        "l'exécution a lieu sur le poste, et la question des policies devient "
        "sans objet, puisque rien ne s'exécute chez HCP Terraform",
    ),
}

VERDICTS_ADMIS = {
    "aucun_run_distant",
    "plan_speculatif",
    "planned_and_finished",
    "bloque",
    "bloque_surchargeable",
    "apply_automatique",
    "attend_confirmation",
}

GOUVERNANCE_ATTENDUE = {
    "ce_qui_autorise_un_override": (
        "le_reglage_du_policy_set_et_la_permission",
        "« Override capability is controlled by the policy set setting, not "
        "individual enforcement levels. » Le niveau ne décide que d'une chose : "
        "un advisory ne bloque jamais",
    ),
    "policies_en_mode_local": (
        "elles_ne_s_executent_pas",
        "en mode `local`, le workspace « acts only as a remote backend for "
        "Terraform state ». Sentinel, l'estimation de coût et les notifications "
        "reposent toutes sur l'exécution distante",
    ),
    "ou_vivent_les_identifiants": (
        "des_variables_d_environnement_du_workspace",
        "« You must add specific environment variables to that workspace to "
        "tell HCP Terraform how to authenticate. » Jamais dans le dépôt",
    ),
}

TFRC_VIDE = Path(tempfile.gettempdir()) / "dsoxlab-capstone6-vide.tfrc"
TFRC_VIDE.touch()


@pytest.fixture(scope="module")
def joue() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    return WORKDIR


def _applique(repertoire: Path, ou: str) -> dict:
    init = terraform("init", "-input=false", "-no-color", cwd=repertoire)
    assert init.returncode == 0, f"`init` a échoué dans `{ou}/`.\n{init.stderr[-800:]}"

    applique = terraform(
        "apply", "-auto-approve", "-input=false", "-no-color", cwd=repertoire
    )
    assert applique.returncode == 0, (
        f"`apply` a échoué dans `{ou}/`.\n\nUn `???` subsiste, ou une expression "
        f"ne tient pas.\n{applique.stderr[-1200:]}"
    )
    return {c: v["value"] for c, v in output_json(repertoire).items()}


@pytest.fixture(scope="module")
def sorties(joue: Path) -> dict:
    return _applique(joue / AUDIT, AUDIT)


# --------------------------------------------------------------------------
# 1. L'audit : six situations, six verdicts.
# --------------------------------------------------------------------------
def test_les_sept_situations_sont_qualifiees(sorties: dict) -> None:
    verdicts = sorties.get("verdicts")
    assert isinstance(verdicts, dict), (
        f"`verdicts` rend {type(verdicts).__name__}, une map attendue."
    )
    assert set(verdicts) == set(VERDICTS_ATTENDUS), (
        f"Situations qualifiées : {sorted(verdicts)}.\nAttendu les sept : "
        f"{sorted(VERDICTS_ATTENDUS)}."
    )

    hors = {n: v for n, v in verdicts.items() if v not in VERDICTS_ADMIS}
    assert not hors, f"Verdicts hors vocabulaire : {hors}."


def test_les_sept_verdicts_sont_tous_differents(sorties: dict) -> None:
    """Le capstone est bâti ainsi, et cela vaut d'être vérifié.

    Sept situations, sept issues distinctes : le vocabulaire entier est employé,
    chaque mot une seule fois. Aucune réponse constante ne passe, et il n'y a
    pas de majorité à jouer. Si deux verdicts coïncident, c'est que la règle
    écrite confond deux cas que la plateforme distingue.
    """
    verdicts = sorties["verdicts"]
    doublons = {
        v for v in verdicts.values() if list(verdicts.values()).count(v) > 1
    }
    assert not doublons, (
        f"Ces verdicts sont rendus plusieurs fois : {sorted(doublons)}.\n\n"
        "Les sept situations ont sept issues différentes. Deux cas qui reçoivent "
        "le même verdict signalent une règle qui les confond."
    )


@pytest.mark.parametrize("cas", sorted(VERDICTS_ATTENDUS))
def test_chaque_situation_recoit_le_bon_verdict(sorties: dict, cas: str) -> None:
    attendu, pourquoi = VERDICTS_ATTENDUS[cas]
    obtenu = sorties["verdicts"].get(cas)
    assert obtenu == attendu, (
        f"`{cas}` vaut {obtenu!r}, attendu {attendu!r}.\n\n{pourquoi.capitalize()}."
    )


@pytest.mark.parametrize("fait", sorted(GOUVERNANCE_ATTENDUE))
def test_chaque_fait_de_gouvernance(sorties: dict, fait: str) -> None:
    gouvernance = sorties.get("gouvernance")
    assert isinstance(gouvernance, dict), (
        f"`gouvernance` rend {type(gouvernance).__name__}, une map attendue."
    )
    attendu, pourquoi = GOUVERNANCE_ATTENDUE[fait]
    obtenu = gouvernance.get(fait)
    assert obtenu == attendu, (
        f"`{fait}` vaut {obtenu!r}, {attendu!r} attendu.\n\n{pourquoi.capitalize()}."
    )


# --------------------------------------------------------------------------
# 2. Le rattachement : jusqu'au jeton, et pas plus loin.
# --------------------------------------------------------------------------
def test_le_rattachement_va_jusqu_a_l_authentification(joue: Path) -> None:
    """La frontière du capstone, et les deux moitiés sont nécessaires.

    Mesuré le 2026-09-25 : une configuration portant `backend` et `cloud`
    affiche « Required token could not be found » À CÔTÉ de sa faute. La marque
    de frontière, seule, déclarerait donc juste une configuration cassée.

    L'environnement est expurgé de tout jeton pour que la mesure soit la même
    sur n'importe quel poste, y compris un poste authentifié.
    """
    repertoire = joue / RATTACHEMENT
    env = {c: v for c, v in os.environ.items() if not c.startswith("TF_TOKEN_")}
    env["TF_CLI_CONFIG_FILE"] = str(TFRC_VIDE)

    proc = subprocess.run(
        ["terraform", "init", "-input=false", "-no-color"],
        cwd=repertoire,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    sortie = proc.stdout + proc.stderr

    restantes = {m: r for m, r in FAUTES.items() if m in sortie}
    assert not restantes, (
        "Le rattachement porte encore des fautes :\n"
        + "\n".join(f"  - {r}" for r in restantes.values())
    )

    assert FRONTIERE in sortie, (
        "Le rattachement ne va pas jusqu'à l'authentification.\n\nUne "
        "configuration `cloud` correcte s'arrête sur « Required token could not "
        f"be found ». Sortie obtenue :\n\n{sortie[-1000:]}"
    )


def test_le_rattachement_designe_le_bon_workspace(joue: Path) -> None:
    """Le seul test qui ouvre un fichier, et c'est assumé.

    Sans compte, ni state ni plan n'existent : aucune sortie structurée ne dit
    par quelle stratégie ni vers quoi le répertoire se rattache.
    """
    texte = (joue / RATTACHEMENT / "versions.tf").read_text(encoding="utf-8")
    nu = "\n".join(ligne.split("#")[0] for ligne in texte.splitlines())

    assert f'"{ORGANISATION}"' in nu, (
        f"L'organisation `{ORGANISATION}` n'est pas écrite en chaîne littérale.\n\n"
        "Un bloc `cloud` est résolu avant toute évaluation d'expression."
    )
    assert f'"{WORKSPACE}"' in nu, (
        f"Le workspace `{WORKSPACE}` n'est pas désigné."
    )
    assert "tags" not in nu, (
        "Le rattachement porte des `tags`. Il vise UN workspace, par son nom : "
        "les deux stratégies s'excluent."
    )


# --------------------------------------------------------------------------
# 3. Le secret : ce qui sort, et ce qui ne sort pas.
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def secret(joue: Path) -> dict:
    return _applique(joue / REP_SECRET, REP_SECRET)


def test_le_jeton_n_entre_pas_dans_le_state(joue: Path, secret: dict) -> None:
    """On balaie le state entier, pas seulement l'attribut attendu.

    Un secret déplacé ailleurs serait tout aussi exposé, et une vérification
    ciblée ne le verrait pas.
    """
    etat = joue / REP_SECRET / "terraform.tfstate"
    assert etat.is_file(), "Aucun state : la configuration n'a pas été appliquée."

    contenu = etat.read_text(encoding="utf-8")
    assert JETON not in contenu, (
        f"Le state porte le jeton en clair, {contenu.count(JETON)} fois.\n\n"
        "`sensitive` empêche Terraform de l'AFFICHER, pas de l'enregistrer. Un "
        "state se lit, se sauvegarde et se partage."
    )


def test_la_fiche_permet_de_verifier_sans_divulguer(joue: Path, secret: dict) -> None:
    """Le test qui exerce les deux côtés.

    Ce qui est interdit : que le jeton sorte. Ce qui reste exigé : qu'un
    auditeur puisse vérifier. Une fiche vidée de tout satisferait la première
    moitié et ne servirait plus à rien.
    """
    fiche = joue / REP_SECRET / "fiche-service.txt"
    assert fiche.is_file(), (
        "`fiche-service.txt` n'a pas été créée : la ressource n'a pas été "
        "appliquée."
    )

    texte = fiche.read_text(encoding="utf-8")
    empreinte = hashlib.sha256(JETON.encode()).hexdigest()

    assert JETON not in texte, "La fiche porte le jeton en clair."
    assert empreinte in texte, (
        "La fiche ne porte pas l'empreinte SHA-256 du jeton.\n\nSans elle, un "
        "auditeur ne peut rien vérifier : la fiche est certes sans secret, mais "
        "elle est aussi sans usage."
    )

    publiee = secret.get("empreinte_publiee")
    assert publiee == empreinte, (
        f"`empreinte_publiee` vaut {publiee!r}, l'empreinte du jeton attendue.\n\n"
        "Terraform propage la sensibilité à travers les fonctions sans regarder "
        "ce qu'elles font : l'output doit donc être annoté `sensitive`, faute de "
        "quoi l'apply échoue sur « Output refers to sensitive values »."
    )
