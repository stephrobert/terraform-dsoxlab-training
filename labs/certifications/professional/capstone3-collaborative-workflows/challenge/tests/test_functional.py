"""Tests fonctionnels du capstone 3 : deux configurations, un state partage.

Faire collaborer deux stacks separees, en verrouillant les versions et en
s'executant sans interaction humaine, comme le ferait une CI.

## La preuve centrale : la propagation

Tout le reste pourrait etre obtenu en recopiant trois valeurs a la main. Le test
decisif rejoue la stack AMONT avec une autre plage reseau, puis exige que l'aval
suive. Une valeur recopiee reste figee, et tombe.

## Ce qui est verifie sans jamais lire un `.tf`

Le backend, par l'absence de `terraform.tfstate` local et la presence des deux
cles dans le bucket, interrogees cote Floci.

La lecture de l'etat distant, par la presence d'une entree `mode: data` de type
`terraform_remote_state` dans le state de l'aval.

Les contraintes de version, par `terraform version -json` et le verrou.

## Une mesure faite en ecrivant le lab

Un bloc `backend` n'accepte AUCUNE valeur nommee, ni variable ni local. C'est
pour cela que ses arguments arrivent par `-backend-config`, et que le bloc reste
vide dans le `.tf`.
"""

from __future__ import annotations

import json
import subprocess
import urllib.request
from pathlib import Path

import pytest

from conftest import exiger_workdir, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "certifications-professional-capstone3-collaborative-workflows"

AMONT = "reseau"
AVAL = "application"

BUCKET = "capstone3-etats"
ENDPOINT = "http://localhost:14566"

CLES_ATTENDUES = {"reseau/terraform.tfstate", "application/terraform.tfstate"}

PLAGE_ORIGINE = "10.42.0.0/16"
PLAGE_EPREUVE = "10.77.0.0/16"


def _tf(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["terraform", *args], cwd=cwd, capture_output=True, text=True, check=False
    )


def _s3(chemin: str = "") -> str:
    """Un appel S3 non signe, mais AVEC l'en-tete d'identifiants.

    Floci accepte les requetes non signees et ISOLE par identifiants : sans
    `Credential=test/...`, le bucket ecrit par Terraform serait invisible, et le
    test conclurait a tort qu'il n'existe pas.
    """
    entetes = {
        "Authorization": (
            "AWS4-HMAC-SHA256 Credential=test/00000000/eu-west-3/s3/aws4_request, "
            "SignedHeaders=host, Signature=0000"
        )
    }
    demande = urllib.request.Request(f"{ENDPOINT}/{chemin}", headers=entetes)
    with urllib.request.urlopen(demande, timeout=30) as reponse:
        return reponse.read().decode()


@pytest.fixture(scope="module")
def joue() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    return WORKDIR


def _etat(repertoire: Path) -> dict:
    proc = _tf("show", "-json", cwd=repertoire)
    assert proc.returncode == 0, (
        f"`terraform show -json` a echoue dans `{repertoire.name}/`.\n\nLa stack "
        f"n'a pas ete initialisee ou appliquee.\n{proc.stderr[-800:]}"
    )
    return json.loads(proc.stdout)


def _ressources(etat: dict) -> list[dict]:
    return etat.get("values", {}).get("root_module", {}).get("resources", [])


def _sorties(repertoire: Path) -> dict:
    proc = _tf("output", "-json", cwd=repertoire)
    assert proc.returncode == 0, (
        f"`terraform output -json` a echoue dans `{repertoire.name}/`.\n"
        f"{proc.stderr[-800:]}"
    )
    return {c: v["value"] for c, v in json.loads(proc.stdout or "{}").items()}


# --------------------------------------------------------------------------
# 1. Le state est distant, des deux cotes.
# --------------------------------------------------------------------------
def test_les_deux_states_vivent_dans_le_bucket(joue: Path) -> None:
    """Deux moities : plus de state local, et deux cles dans le bucket.

    La premiere seule serait vraie d'une stack jamais appliquee.
    """
    for stack in (AMONT, AVAL):
        local = joue / stack / "terraform.tfstate"
        assert not local.is_file(), (
            f"`{stack}/terraform.tfstate` existe encore.\n\nLe state doit partir "
            "dans le bucket : tant qu'il est local, rien n'est partage."
        )

    listing = _s3(f"{BUCKET}?list-type=2")
    presentes = {
        bloc.split("<")[0] for bloc in listing.split("<Key>")[1:]
    }
    manquantes = CLES_ATTENDUES - presentes
    assert not manquantes, (
        f"Ces cles manquent dans le bucket `{BUCKET}` : {sorted(manquantes)}.\n"
        f"Presentes : {sorted(presentes) or 'aucune'}.\n\nChaque stack range son "
        "state sous SA cle : deux configurations qui partagent la meme cle "
        "s'ecrasent."
    )


def test_les_versions_sont_contraintes_des_deux_cotes(joue: Path) -> None:
    """Une configuration collaborative qui laisse flotter ses versions ne se
    comporte pas pareil chez deux personnes.

    Le verrou est lu plutot que le `.tf` : il dit ce qui est REELLEMENT epingle.
    """
    for stack in (AMONT, AVAL):
        verrou = joue / stack / ".terraform.lock.hcl"
        assert verrou.is_file(), (
            f"`{stack}/.terraform.lock.hcl` est absent : `init` n'a pas abouti."
        )
        contenu = verrou.read_text(encoding="utf-8")
        assert "constraints" in contenu, (
            f"Le verrou de `{stack}/` ne porte aucune contrainte de version.\n\n"
            "Le provider a ete installe sans contrainte : rien ne garantit que "
            "le collegue obtiendra la meme version."
        )

        proc = _tf("version", "-json", cwd=joue / stack)
        proc.check_returncode()
        version = json.loads(proc.stdout)
        assert version.get("provider_selections"), (
            f"Aucun provider installe pour `{stack}/`."
        )


# --------------------------------------------------------------------------
# 2. L'aval LIT l'amont, il ne le recopie pas.
# --------------------------------------------------------------------------
def test_l_aval_lit_l_etat_distant_de_l_amont(joue: Path) -> None:
    """La seule passerelle entre deux configurations est l'etat distant.

    Une entree `mode: data` de type `terraform_remote_state` le prouve : des
    valeurs recopiees n'en produiraient aucune.
    """
    lues = [
        r for r in _ressources(_etat(joue / AVAL))
        if r["mode"] == "data" and r["type"] == "terraform_remote_state"
    ]
    assert lues, (
        "La stack aval ne lit aucun etat distant.\n\nAdresses presentes : "
        f"{[r['address'] for r in _ressources(_etat(joue / AVAL))]}\n\n"
        "Aucune expression ne traverse la frontiere entre deux configurations : "
        "il faut lire l'etat de l'amont par `terraform_remote_state`."
    )


def test_les_valeurs_de_l_aval_sont_celles_publiees_par_l_amont(joue: Path) -> None:
    amont = _sorties(joue / AMONT)
    aval = _sorties(joue / AVAL)

    for nom in ("identifiant_reseau", "plage_reseau", "passerelle"):
        assert nom in amont, (
            f"La stack amont ne publie pas `{nom}`. Publie : {sorted(amont)}.\n\n"
            "Ce qui n'est pas expose en output est invisible d'en face, meme si "
            "la valeur figure dans le state."
        )

    raccordement = aval.get("raccordement")
    assert isinstance(raccordement, dict), (
        f"`raccordement` rend {type(raccordement).__name__}, un objet attendu."
    )
    attendu = {
        "identifiant": amont["identifiant_reseau"],
        "plage": amont["plage_reseau"],
        "passerelle": amont["passerelle"],
    }
    assert raccordement == attendu, (
        f"L'aval annonce {raccordement}.\nL'amont publie {attendu}."
    )


# --------------------------------------------------------------------------
# 3. LA preuve : on change l'amont, l'aval doit suivre.
# --------------------------------------------------------------------------
def test_une_valeur_changee_en_amont_se_propage(joue: Path) -> None:
    """Le seul test que des valeurs recopiees ne passent pas.

    L'amont est rejoue avec une autre plage, l'aval doit annoncer un changement
    puis porter la nouvelle valeur. Tout est remis en etat a la fin, quoi qu'il
    arrive : sans cela, le lab resterait sur une plage qui n'est pas la sienne.
    """
    avant = _sorties(joue / AVAL)["raccordement"]
    assert avant["plage"] == PLAGE_ORIGINE, (
        f"L'aval part de la plage {avant['plage']!r}, {PLAGE_ORIGINE!r} attendue."
    )

    try:
        change = _tf("apply", "-auto-approve", "-input=false", "-no-color",
                     "-var", f"plage_reseau={PLAGE_EPREUVE}", cwd=joue / AMONT)
        assert change.returncode == 0, (
            f"Impossible de rejouer l'amont.\n{change.stderr[-800:]}"
        )

        attente = _tf("plan", "-detailed-exitcode", "-input=false", "-no-color",
                      cwd=joue / AVAL)
        assert attente.returncode == 2, (
            f"Apres changement de la plage en amont, le plan de l'aval rend "
            f"{attente.returncode}, attendu 2.\n\n"
            + (
                "Un 0 signifie que l'aval ne suit PAS : ses valeurs sont "
                "recopiees, pas lues. C'est exactement ce que ce test existe "
                "pour attraper."
                if attente.returncode == 0
                else "Un 1 signale une erreur."
            )
        )

        suivi = _tf("apply", "-auto-approve", "-input=false", "-no-color", cwd=joue / AVAL)
        assert suivi.returncode == 0, f"L'aval n'a pas pu suivre.\n{suivi.stderr[-800:]}"

        apres = _sorties(joue / AVAL)["raccordement"]
        assert apres["plage"] == PLAGE_EPREUVE, (
            f"L'aval annonce toujours la plage {apres['plage']!r} apres le "
            f"changement en amont, {PLAGE_EPREUVE!r} attendue."
        )
    finally:
        _tf("apply", "-auto-approve", "-input=false", "-no-color",
            "-var", f"plage_reseau={PLAGE_ORIGINE}", cwd=joue / AMONT)
        _tf("apply", "-auto-approve", "-input=false", "-no-color", cwd=joue / AVAL)


# --------------------------------------------------------------------------
# 4. L'automation : tout passe sans interaction, et converge.
# --------------------------------------------------------------------------
def test_le_cycle_en_deux_temps_fonctionne_sans_interaction(joue: Path) -> None:
    """`plan -out` puis `apply` du FICHIER de plan, ce que fait une CI.

    Un apply direct relit la configuration au moment d'appliquer : ce qui a ete
    revu n'est donc pas forcement ce qui part. Appliquer un plan enregistre
    ferme cet ecart.
    """
    for stack in (AMONT, AVAL):
        plan = _tf("plan", "-out=automation.tfplan", "-input=false", "-no-color",
                   cwd=joue / stack)
        assert plan.returncode == 0, (
            f"`plan -out` a echoue dans `{stack}/` sans interaction.\n"
            f"{plan.stderr[-800:]}"
        )

        applique = _tf("apply", "-input=false", "-no-color", "automation.tfplan",
                       cwd=joue / stack)
        assert applique.returncode == 0, (
            f"`apply` du fichier de plan a echoue dans `{stack}/`.\n"
            f"{applique.stderr[-800:]}"
        )


def test_les_deux_stacks_convergent(joue: Path) -> None:
    for stack in (AMONT, AVAL):
        plan = _tf("plan", "-detailed-exitcode", "-input=false", "-no-color",
                   cwd=joue / stack)
        assert plan.returncode == 0, (
            f"`plan -detailed-exitcode` rend {plan.returncode} dans `{stack}/`, "
            f"attendu 0.\n{plan.stdout[-800:]}"
        )


# --------------------------------------------------------------------------
# 5. Le nettoyage, inconditionnel et dans le bon ordre.
# --------------------------------------------------------------------------
def test_le_destroy_vide_les_deux_stacks_et_leurs_etats(joue: Path) -> None:
    """L'aval D'ABORD, l'amont ensuite.

    L'inverse echouerait : `application/` lit l'etat de `reseau/`, et detruire
    l'amont en premier ferait disparaitre ce que l'aval doit relire pour se
    planifier. C'est le meme ordre qu'a l'aller, a l'envers.

    Ce test s'execute meme si les precedents ont echoue : un lab rate qui laisse
    deux states dans le bucket fait payer sa propre reprise.
    """
    for stack in (AVAL, AMONT):
        detruit = _tf("destroy", "-auto-approve", "-input=false", "-no-color",
                      cwd=joue / stack)
        assert detruit.returncode == 0, (
            f"`destroy` a echoue dans `{stack}/`.\n{detruit.stderr[-1000:]}"
        )

        restantes = [
            r["address"] for r in _ressources(_etat(joue / stack)) if r["mode"] == "managed"
        ]
        assert not restantes, (
            f"`{stack}/` porte encore {restantes} apres le destroy."
        )

    assert not (joue / AVAL / "raccordement.json").exists(), (
        "`raccordement.json` a survecu au destroy : Terraform le gerait, il "
        "devait disparaitre avec le reste."
    )
