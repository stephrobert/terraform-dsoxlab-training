"""Tests fonctionnels du lab « policy as code, qui bloque un run et qui peut passer outre ».

L'objectif 6 est evalue en QCM : ni compte HCP Terraform, ni run distant. Ce lab
fait donc RAISONNER sur des situations decrites, et evaluer de vrais plans.

## Le piege que le lab traite

Croire qu'un `hard-mandatory` est indepassable. C'est le reglage d'override du
POLICY SET qui tranche, et la permission que detient l'utilisateur, pas le seul
niveau d'enforcement.

Verifie a la source le 2026-09-25 : « Override capability is controlled by the
policy set setting, not individual enforcement levels. »

## Comment les sept cas sont batis

Aucune reponse constante ne passe :

    "bloque" partout               echoue sur les deux cas advisory
    "bloque_surchargeable" partout echoue sur les trois cas sans droit
    "poursuit" partout             echoue sur les cinq autres

Chaque cas est assere separement, pour que le message dise LEQUEL est faux.

## Ce que les tests ne lisent pas

Aucun `.tf` de l'apprenant. Tout passe par `terraform output -json`, donc par ce
que la configuration CALCULE, jamais par ce qu'elle contient.
"""

from __future__ import annotations

import json
import subprocess

import pytest

from conftest import exiger_workdir, message, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "hcp-terraform-policy-as-code"

# Le verdict attendu pour chacun des sept runs, et POURQUOI. Le message d'echec
# reprend cette raison : c'est le seul texte que l'apprenant lira vraiment.
VERDICTS_ATTENDUS = {
    "cas1_advisory_sentinel": (
        "poursuit",
        "un advisory n'interrompt jamais un run, quel que soit le reste",
    ),
    "cas2_hard_mandatory_surchargeable": (
        "bloque_surchargeable",
        "hard-mandatory n'est PAS indepassable : le policy set autorise "
        "l'override et l'utilisateur detient la permission",
    ),
    "cas3_soft_mandatory_sans_permission": (
        "bloque",
        "le policy set autorise l'override, mais l'utilisateur n'a pas la "
        "permission : le niveau seul ne suffit pas, il faut aussi le droit",
    ),
    "cas4_opa_mandatory_policy_set_ferme": (
        "bloque",
        "l'utilisateur a la permission, mais le policy set n'autorise pas "
        "l'override : les deux conditions sont necessaires",
    ),
    "cas5_opa_advisory": (
        "poursuit",
        "un advisory ne bloque pas, meme sans aucun droit",
    ),
    "cas6_terraform_policy_mandatory_overridable": (
        "bloque_surchargeable",
        "le nom du niveau annonce l'override, mais c'est bien le policy set et "
        "la permission qui le rendent possible",
    ),
    "cas7_terraform_policy_mandatory_sans_permission": (
        "bloque",
        "le policy set autorise, l'utilisateur n'a pas la permission",
    ),
}

VERDICTS_ADMIS = {"poursuit", "bloque_surchargeable", "bloque"}

# Releve le 2026-09-25 sur la documentation officielle de HCP Terraform.
NIVEAUX_ATTENDUS = {
    "sentinel": ["advisory", "soft-mandatory", "hard-mandatory"],
    "opa": ["advisory", "mandatory"],
    "terraform": ["advisory", "mandatory overridable", "mandatory"],
}

SOURCE = (
    "https://developer.hashicorp.com/terraform/cloud-docs/policy-enforcement/"
    "manage-policy-sets"
)

ADRESSE_FAUTIVE = "local_file.config"


def _tf(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["terraform", *args], cwd=WORKDIR, capture_output=True, text=True, check=False
    )


@pytest.fixture(scope="module")
def sorties() -> dict:
    exiger_workdir(WORKDIR, LAB_ID)

    init = _tf("init", "-input=false", "-no-color")
    assert init.returncode == 0, message(
        en=f"`terraform init` failed.\n{init.stderr[-1000:]}",
        fr=f"`terraform init` a échoué.\n{init.stderr[-1000:]}",
    )

    applique = _tf("apply", "-auto-approve", "-input=false", "-no-color")
    assert applique.returncode == 0, message(
        en=f"`terraform apply` failed.\n\nThe configuration does not compute: a "
        f"`???` remains, or an expression does not hold.\n{applique.stderr[-1200:]}",
        fr=f"`terraform apply` a échoué.\n\nLa configuration ne calcule pas : un "
        f"`???` subsiste, ou une expression ne tient pas.\n{applique.stderr[-1200:]}",
    )

    proc = _tf("output", "-json")
    proc.check_returncode()
    return {c: v["value"] for c, v in json.loads(proc.stdout or "{}").items()}


# --------------------------------------------------------------------------
# 1. Les sept verdicts, un par un.
# --------------------------------------------------------------------------
def test_les_sept_runs_sont_tous_qualifies(sorties: dict) -> None:
    verdicts = sorties.get("verdicts")
    assert isinstance(verdicts, dict), message(
        en=f"The `verdicts` output returns {type(verdicts).__name__}, a map was expected.",
        fr=f"La sortie `verdicts` rend {type(verdicts).__name__}, une map attendue.",
    )
    assert set(verdicts) == set(VERDICTS_ATTENDUS), message(
        en=f"Runs classified: {sorted(verdicts)}.\nAll seven were expected: "
        f"{sorted(VERDICTS_ATTENDUS)}.",
        fr=f"Runs qualifiés : {sorted(verdicts)}.\nAttendu les sept : "
        f"{sorted(VERDICTS_ATTENDUS)}.",
    )

    hors_vocabulaire = {
        nom: valeur for nom, valeur in verdicts.items() if valeur not in VERDICTS_ADMIS
    }
    assert not hors_vocabulaire, message(
        en=f"These verdicts are not in the accepted vocabulary: "
        f"{hors_vocabulaire}.\nAccepted: {sorted(VERDICTS_ADMIS)}.",
        fr=f"Ces verdicts ne sont pas dans le vocabulaire admis : "
        f"{hors_vocabulaire}.\nAdmis : {sorted(VERDICTS_ADMIS)}.",
    )


@pytest.mark.parametrize("cas", sorted(VERDICTS_ATTENDUS))
def test_chaque_run_recoit_le_bon_verdict(sorties: dict, cas: str) -> None:
    """Un test par cas, pour que le message dise LEQUEL est faux.

    Une assertion unique sur les sept dirait seulement que quelque chose cloche,
    ce qui oblige a tout relire.
    """
    attendu, pourquoi = VERDICTS_ATTENDUS[cas]
    obtenu = sorties["verdicts"].get(cas)

    assert obtenu == attendu, message(
        en=f"`{cas}` is {obtenu!r}, expected {attendu!r}.\n\n{pourquoi.capitalize()}.\n\n"
        "A reminder of the rule, checked at the source: it is not the enforcement "
        "level that decides the override, it is the POLICY SET'S SETTING, "
        "crossed with the user's Manage Policy Overrides permission. The "
        "level decides one thing only: an advisory never blocks.\n\n"
        f"Source: {SOURCE}",
        fr=f"`{cas}` vaut {obtenu!r}, attendu {attendu!r}.\n\n{pourquoi.capitalize()}.\n\n"
        "Rappel de la règle, vérifiée à la source : ce n'est pas le niveau "
        "d'enforcement qui décide de l'override, c'est le RÉGLAGE DU POLICY SET, "
        "croisé avec la permission Manage Policy Overrides de l'utilisateur. Le "
        "niveau ne décide que d'une chose : un advisory ne bloque jamais.\n\n"
        f"Source : {SOURCE}",
    )


# --------------------------------------------------------------------------
# 2. Les connaissances, qui se lisent et ne se devinent pas.
# --------------------------------------------------------------------------
def test_les_niveaux_de_chaque_framework(sorties: dict) -> None:
    """Trois frameworks, trois vocabulaires, et c'est ce qui se confond."""
    obtenus = sorties.get("niveaux_par_framework")
    assert isinstance(obtenus, dict), message(
        en=f"`niveaux_par_framework` returns {type(obtenus).__name__}, a map was expected.",
        fr=f"`niveaux_par_framework` rend {type(obtenus).__name__}, une map attendue.",
    )

    assert set(obtenus) == set(NIVEAUX_ATTENDUS), message(
        en=f"Frameworks described: {sorted(obtenus)}.\nExpected: "
        f"{sorted(NIVEAUX_ATTENDUS)}.",
        fr=f"Frameworks décrits : {sorted(obtenus)}.\nAttendu : "
        f"{sorted(NIVEAUX_ATTENDUS)}.",
    )

    for framework, attendus in NIVEAUX_ATTENDUS.items():
        assert obtenus[framework] == attendus, message(
            en=f"`{framework}`: {obtenus[framework]}\nExpected: {attendus}\n\n"
            "The three frameworks have neither the same number of levels nor the "
            "same names. Sentinel has three, OPA two, and Terraform policy "
            "three, one of which names the override in its title.\n\n"
            f"Source: {SOURCE}",
            fr=f"`{framework}` : {obtenus[framework]}\nAttendu : {attendus}\n\n"
            "Les trois frameworks n'ont ni le même nombre de niveaux ni les "
            "mêmes noms. Sentinel en a trois, OPA deux, et Terraform policy "
            "trois dont un qui nomme l'override dans son intitulé.\n\n"
            f"Source : {SOURCE}",
        )


def test_ce_qui_distingue_les_policy_checks_des_evaluations(sorties: dict) -> None:
    """La distinction tient a l'ORDRE d'execution, et elle decide de ce qu'on voit.

    Les policy checks passent APRES l'estimation de cout, donc ils la lisent.
    Les policy evaluations passent juste AVANT, donc elles ne la voient pas.
    """
    checks = sorties.get("policy_checks")
    assert isinstance(checks, dict), message(
        en=f"`policy_checks` returns {type(checks).__name__}, a map was expected.",
        fr=f"`policy_checks` rend {type(checks).__name__}, une map attendue.",
    )

    assert checks.get("framework_unique") == "sentinel", message(
        en=f"`framework_unique` is {checks.get('framework_unique')!r}.\n\nPolicy "
        "checks are the historical mode: a single framework runs in them.",
        fr=f"`framework_unique` vaut {checks.get('framework_unique')!r}.\n\nLes "
        "policy checks sont le mode historique : un seul framework s'y exécute.",
    )
    assert checks.get("version_maximale") == "0.40.x", message(
        en=f"`version_maximale` is {checks.get('version_maximale')!r}, `0.40.x` "
        "expected.\n\nPolicy checks do not follow the more "
        "recent versions of the framework.",
        fr=f"`version_maximale` vaut {checks.get('version_maximale')!r}, `0.40.x` "
        "attendu.\n\nLes policy checks ne suivent pas les versions plus "
        "récentes du framework.",
    )
    assert checks.get("voit_le_cout") is True, message(
        en=f"`voit_le_cout` is {checks.get('voit_le_cout')!r}.\n\nChecks "
        "run AFTER the cost estimate, and that is precisely their "
        "interest: they can write a rule about cost. Evaluations, "
        "on the other hand, come just before and do not see it.",
        fr=f"`voit_le_cout` vaut {checks.get('voit_le_cout')!r}.\n\nLes checks "
        "s'exécutent APRÈS l'estimation de coût, et c'est justement leur "
        "intérêt : ils peuvent écrire une règle sur le coût. Les évaluations, "
        "elles, passent juste avant et ne la voient pas.",
    )


def test_ce_que_l_edition_free_autorise(sorties: dict) -> None:
    free = sorties.get("free_tier")
    assert isinstance(free, dict), message(
        en=f"`free_tier` returns {type(free).__name__}, a map was expected.",
        fr=f"`free_tier` rend {type(free).__name__}, une map attendue.",
    )

    attendu = {"policy_sets": 1, "policies_par_set": 5, "connexion_vcs": False}
    for cle, valeur in attendu.items():
        assert free.get(cle) == valeur, message(
            en=f"`free_tier.{cle}` is {free.get(cle)!r}, {valeur!r} expected.\n\n"
            "\"HCP Terraform Free edition includes one policy set of up to five "
            "policies.\" Connecting to a repository is reserved for higher "
            f"editions.\n\nSource: {SOURCE}",
            fr=f"`free_tier.{cle}` vaut {free.get(cle)!r}, {valeur!r} attendu.\n\n"
            "« HCP Terraform Free edition includes one policy set of up to five "
            "policies. » La connexion à un dépôt est réservée aux éditions "
            f"supérieures.\n\nSource : {SOURCE}",
        )


# --------------------------------------------------------------------------
# 3. La regle de conformite, eprouvee dans les DEUX sens.
# --------------------------------------------------------------------------
def test_la_regle_accepte_le_plan_conforme_et_refuse_l_autre(sorties: dict) -> None:
    """Une regle qui refuse tout passerait la moitie de ce test.

    C'est pourquoi les deux sens sont exiges : le plan conforme doit sortir
    SANS violation, et le non conforme doit nommer l'adresse fautive.
    """
    violations = sorties.get("violations")
    assert isinstance(violations, dict), message(
        en=f"`violations` returns {type(violations).__name__}, a map was expected.",
        fr=f"`violations` rend {type(violations).__name__}, une map attendue.",
    )
    assert set(violations) == {"conforme", "non_conforme"}, message(
        en=f"Plans evaluated: {sorted(violations)}.\nExpected `conforme` and "
        "`non_conforme`.",
        fr=f"Plans évalués : {sorted(violations)}.\nAttendu `conforme` et "
        "`non_conforme`.",
    )

    assert violations["conforme"] == [], message(
        en=f"The COMPLIANT plan is declared at fault: {violations['conforme']}.\n\n"
        "It creates a file in 0640, which grants no right to the rest of the "
        "world. A rule that refuses it refuses everything, and is useless.",
        fr=f"Le plan CONFORME est déclaré fautif : {violations['conforme']}.\n\n"
        "Il crée un fichier en 0640, qui n'accorde aucun droit au reste du "
        "monde. Une règle qui le refuse refuse tout, et ne sert à rien.",
    )

    assert violations["non_conforme"] == [ADRESSE_FAUTIVE], message(
        en=f"The NON-COMPLIANT plan returns {violations['non_conforme']}, expected "
        f"`[{ADRESSE_FAUTIVE!r}]`.\n\nIt creates a file in 0777, which grants "
        "a right to the rest of the world. The rule must return the offending "
        "ADDRESSES: a rule that only says \"no\" without saying \"where\" forces "
        "whoever receives it to go looking.",
        fr=f"Le plan NON CONFORME rend {violations['non_conforme']}, attendu "
        f"`[{ADRESSE_FAUTIVE!r}]`.\n\nIl crée un fichier en 0777, qui accorde "
        "un droit au reste du monde. La règle doit rendre les ADRESSES "
        "fautives : une règle qui dit seulement « non » sans dire « où » oblige "
        "celui qui la subit à chercher.",
    )


def test_la_configuration_converge() -> None:
    plan = _tf("plan", "-detailed-exitcode", "-input=false", "-no-color")
    assert plan.returncode == 0, message(
        en=f"`plan -detailed-exitcode` returns {plan.returncode}, expected 0.\n"
        + plan.stdout[-800:],
        fr=f"`plan -detailed-exitcode` rend {plan.returncode}, attendu 0.\n"
        + plan.stdout[-800:],
    )
