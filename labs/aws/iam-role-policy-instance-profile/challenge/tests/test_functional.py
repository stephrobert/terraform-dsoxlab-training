"""Tests fonctionnels du lab « la chaine IAM, et les deux mots qu'on confond ».

`aws_iam_policy_document` est une data source LOCALE : elle n'interroge rien,
elle fabrique du JSON. Ce lab rend cette evidence demontrable, et dissipe
l'inversion de vocabulaire sur les deux policies d'un role.

Aucun test ne relit les `.tf` de l'apprenant, et aucun ne parse une sortie
humaine. Le JSON produit arrive par `terraform output -json`, l'inventaire par
`terraform show -json`, et ce que l'emulateur a REELLEMENT recu par l'API.

Formes mesurees sur Floci 1.6.0 avant d'ecrire une seule assertion :
- `get-instance-profile` rend un tableau `Roles` d'UN seul element : le tableau
  est un artefact de l'API, pas une possibilite ;
- `describe-iam-instance-profile-associations` rend un etat `associated` ;
- `list-attached-role-policies` rend la policy rattachee par son ARN.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "aws-iam-role-policy-instance-profile"

ENDPOINT = "http://localhost:14566"
ENV = {
    **os.environ,
    "AWS_ACCESS_KEY_ID": "test",
    "AWS_SECRET_ACCESS_KEY": "test",
    "AWS_DEFAULT_REGION": "eu-west-3",
}

BUCKET = "donnees-applicatives"
ARN_BUCKET = f"arn:aws:s3:::{BUCKET}"
ARN_OBJETS = f"arn:aws:s3:::{BUCKET}/*"

LUES_ATTENDUES = {
    "data.aws_iam_policy_document.confiance",
    "data.aws_iam_policy_document.permissions",
}
GEREES_ATTENDUES = {
    "aws_iam_role.application",
    "aws_iam_policy.lecture_s3",
    "aws_iam_role_policy_attachment.lecture",
    "aws_iam_instance_profile.application",
    "aws_instance.application",
}


# ── Disponibilite de l'emulateur ────────────────────────────────────────────
FLOCI_HOST = "127.0.0.1"
FLOCI_PORT = 14566


def _floci_joignable() -> bool:
    try:
        with socket.create_connection((FLOCI_HOST, FLOCI_PORT), timeout=2):
            return True
    except OSError:
        return False


def _exiger_floci() -> None:
    if _floci_joignable():
        return
    message = (
        f"Floci n'est pas joignable sur {FLOCI_HOST}:{FLOCI_PORT}. Ce lab en a "
        "besoin : Floci emule l'API AWS en local, sans compte ni carte "
        f"bancaire.\n\nLancez le lab avec `dsoxlab run {LAB_ID}`, qui le "
        "demarre tout seul, et faites votre `dsoxlab check` DEPUIS cette "
        "session."
    )
    if os.environ.get("LAB_WORKDIR"):
        pytest.fail(message)
    pytest.skip(message)


def _tf(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["terraform", *args], cwd=WORKDIR, capture_output=True, text=True,
        env=ENV, check=False,
    )


def _aws(*args: str) -> dict:
    proc = subprocess.run(
        ["aws", "--endpoint-url", ENDPOINT, *args],
        capture_output=True, text=True, env=ENV, check=False,
    )
    if proc.returncode != 0:
        pytest.fail(
            f"`aws {' '.join(args)}` a echoue :\n{(proc.stderr or proc.stdout)[-800:]}"
        )
    return json.loads(proc.stdout or "{}")


@pytest.fixture(scope="module", autouse=True)
def applique() -> Iterator[None]:
    exiger_workdir(WORKDIR, LAB_ID)
    _exiger_floci()

    init = _tf("init", "-input=false", "-no-color")
    if init.returncode != 0:
        pytest.fail(f"`terraform init` a echoue :\n{init.stderr[-1000:]}")

    app = _tf("apply", "-auto-approve", "-input=false", "-no-color")
    if app.returncode != 0:
        pytest.fail(
            "`terraform apply` a echoue. Des blocs sont-ils encore a `???` ?\n"
            f"{(app.stderr or app.stdout)[-1800:]}"
        )

    yield

    # Teardown : detruire PENDANT que l'emulateur repond encore. Floci lance un
    # conteneur Docker par instance EC2, et ils survivent a son propre arret.
    _tf("destroy", "-auto-approve", "-input=false", "-no-color")


def _etat() -> dict:
    proc = _tf("show", "-json")
    proc.check_returncode()
    return json.loads(proc.stdout)


def _sorties() -> dict:
    proc = _tf("output", "-json")
    proc.check_returncode()
    return json.loads(proc.stdout)


def _document(nom: str) -> dict:
    """Le JSON fabrique par une data source, deserialise."""
    brut = _sorties()[nom]["value"]
    try:
        return json.loads(brut)
    except json.JSONDecodeError as erreur:
        pytest.fail(f"`{nom}` n'est pas du JSON valide : {erreur}")


def _statements(document: dict) -> list[dict]:
    statements = document.get("Statement", [])
    return statements if isinstance(statements, list) else [statements]


def _en_liste(valeur) -> list:
    """IAM rend tantot une chaine, tantot une liste, pour le meme champ."""
    if valeur is None:
        return []
    return valeur if isinstance(valeur, list) else [valeur]


# --------------------------------------------------------------------------
# 1. Deux documents LUS, cinq objets GERES.
# --------------------------------------------------------------------------
def test_les_documents_sont_des_data_sources_et_les_objets_sont_geres() -> None:
    ressources = _etat()["values"]["root_module"]["resources"]
    lues = {r["address"] for r in ressources if r["mode"] == "data"}
    gerees = {r["address"] for r in ressources if r["mode"] == "managed"}

    assert lues == LUES_ATTENDUES, (
        f"Le state lit {sorted(lues)}.\nAttendu : {sorted(LUES_ATTENDUES)}.\n\n"
        "`aws_iam_policy_document` est une data source LOCALE : elle n'appelle "
        "aucune API, et apparait pourtant en `mode: data`. C'est le point du "
        "lab : « data » ne veut pas dire « distant », cela veut dire « lu »."
    )
    assert gerees == GEREES_ATTENDUES, (
        f"Le state gere {sorted(gerees)}.\nAttendu : {sorted(GEREES_ATTENDUES)}."
    )


# --------------------------------------------------------------------------
# 2. La trust policy dit QUI, et rien d'autre.
# --------------------------------------------------------------------------
def test_la_trust_policy_autorise_le_service_ec2_a_endosser_le_role() -> None:
    statements = _statements(_document("trust_policy_json"))
    assert len(statements) == 1, (
        f"La trust policy porte {len(statements)} statements, un seul est "
        "attendu."
    )
    statement = statements[0]

    assert "sts:AssumeRole" in _en_liste(statement.get("Action")), (
        f"L'action vaut {statement.get('Action')!r}, attendu `sts:AssumeRole`. "
        "Une trust policy n'autorise pas des permissions : elle autorise "
        "l'ENDOSSEMENT du role."
    )

    principal = statement.get("Principal") or {}
    services = _en_liste(principal.get("Service"))
    assert "ec2.amazonaws.com" in services, (
        f"Le `Principal` vaut {principal!r}, attendu un `Service` valant "
        "`ec2.amazonaws.com`.\n\nUn `type = \"AWS\"` designerait un compte ou un "
        "role, un `type = \"Federated\"` un fournisseur d'identite : le document "
        "serait valide, et personne ne pourrait endosser le role."
    )


# --------------------------------------------------------------------------
# 3. Les permissions, et les DEUX ARN qu'elles exigent.
# --------------------------------------------------------------------------
def test_les_permissions_portent_deux_arn_distincts() -> None:
    statements = _statements(_document("permissions_json"))
    par_action: dict[str, list] = {}
    for statement in statements:
        for action in _en_liste(statement.get("Action")):
            par_action[action] = _en_liste(statement.get("Resource"))

    assert "s3:ListBucket" in par_action, (
        f"Aucun statement ne porte `s3:ListBucket`. Actions trouvees : "
        f"{sorted(par_action)}."
    )
    assert "s3:GetObject" in par_action, (
        f"Aucun statement ne porte `s3:GetObject`. Actions trouvees : "
        f"{sorted(par_action)}."
    )

    assert par_action["s3:ListBucket"] == [ARN_BUCKET], (
        f"`s3:ListBucket` vise {par_action['s3:ListBucket']}, attendu "
        f"[{ARN_BUCKET!r}].\n\nLister s'exerce sur le BUCKET."
    )
    assert par_action["s3:GetObject"] == [ARN_OBJETS], (
        f"`s3:GetObject` vise {par_action['s3:GetObject']}, attendu "
        f"[{ARN_OBJETS!r}].\n\nLire s'exerce sur les OBJETS, d'ou le suffixe "
        "`/*`. C'est l'erreur la plus frequente d'IAM sur S3 : une policy qui ne "
        "porte que l'ARN du bucket laisse lister et refuse de lire, et le "
        "message d'AWS ne dit pas pourquoi."
    )
    assert par_action["s3:ListBucket"] != par_action["s3:GetObject"], (
        "Les deux actions visent le meme ARN : l'une des deux ne fonctionnera "
        "pas."
    )


# --------------------------------------------------------------------------
# 4. Le role ne detient aucune permission par lui-meme.
# --------------------------------------------------------------------------
def test_le_role_ne_porte_que_la_confiance_et_la_policy_est_rattachee() -> None:
    sorties = _sorties()
    role = sorties["role_name"]["value"]

    inline = _aws("iam", "list-role-policies", "--role-name", role)
    assert not inline.get("PolicyNames"), (
        f"Le role porte des policies INLINE : {inline.get('PolicyNames')}.\n\n"
        "Le lab demande une policy geree, rattachee : une policy inline vit "
        "dans le role et ne peut etre reutilisee par personne."
    )

    rattachees = _aws("iam", "list-attached-role-policies", "--role-name", role)
    arns = [p["PolicyArn"] for p in rattachees.get("AttachedPolicies", [])]
    assert arns == [sorties["policy_arn"]["value"]], (
        f"Le role porte {arns}, attendu exactement "
        f"[{sorties['policy_arn']['value']!r}]."
    )


# --------------------------------------------------------------------------
# 5. Un profil, UN role. Le tableau est un artefact de l'API.
# --------------------------------------------------------------------------
def test_le_profil_ne_porte_qu_un_seul_role() -> None:
    sorties = _sorties()
    profil = _aws(
        "iam", "get-instance-profile",
        "--instance-profile-name", sorties["instance_profile_name"]["value"],
    )["InstanceProfile"]

    roles = profil.get("Roles", [])
    assert len(roles) == 1, (
        f"Le profil porte {len(roles)} roles : {[r.get('RoleName') for r in roles]}."
        "\n\nAWS en autorise EXACTEMENT un, quoi qu'en dise le guide. Le champ "
        "`Roles` est un tableau parce que l'API l'a toujours ete, pas parce "
        "qu'on peut en mettre plusieurs : l'argument Terraform s'appelle `role`, "
        "au singulier."
    )
    assert roles[0]["RoleName"] == sorties["role_name"]["value"], (
        f"Le profil porte le role {roles[0]['RoleName']!r}, attendu "
        f"{sorties['role_name']['value']!r}."
    )


# --------------------------------------------------------------------------
# 6. L'instance a bien recu le profil.
# --------------------------------------------------------------------------
def test_l_instance_est_associee_au_profil() -> None:
    sorties = _sorties()
    attendu = sorties["instance_profile_name"]["value"]

    instances = {
        r["values"]["id"]
        for r in _etat()["values"]["root_module"]["resources"]
        if r["address"] == "aws_instance.application"
    }
    assert instances, "`aws_instance.application` est absente du state."

    associations = _aws(
        "ec2", "describe-iam-instance-profile-associations"
    ).get("IamInstanceProfileAssociations", [])
    nôtres = [a for a in associations if a.get("InstanceId") in instances]
    assert nôtres, (
        f"Aucune association pour l'instance {instances}. L'argument "
        "`iam_instance_profile` a-t-il ete renseigne ?"
    )
    for association in nôtres:
        assert association.get("State") == "associated", (
            f"L'association est en etat {association.get('State')!r}, attendu "
            "`associated`."
        )
        arn = association["IamInstanceProfile"]["Arn"]
        assert arn.endswith(f"/{attendu}"), (
            f"L'instance porte le profil {arn!r}, attendu un ARN se terminant "
            f"par `/{attendu}`."
        )


# --------------------------------------------------------------------------
# 7. Les deux cotes : retirer l'attachement ne detruit QUE lui.
# --------------------------------------------------------------------------
def test_retirer_l_attachement_laisse_le_role_et_la_policy_debout(
    tmp_path: Path,
) -> None:
    """Le test qui distingue un rattachement d'une appartenance.

    Un plan vide, seul, serait vrai avant le travail : une configuration nue
    converge. Ici on demande d'abord la convergence, PUIS on retire le
    rattachement sur une COPIE et on exige une seule suppression.

    C'est ce qui prouve que la policy est un objet a part, reutilisable par
    d'autres roles, et non une propriete du role. Si le plan annonçait aussi la
    destruction du role ou de la policy, ils auraient ete ecrits comme
    dependants l'un de l'autre.
    """
    stable = _tf("plan", "-detailed-exitcode", "-input=false", "-no-color")
    assert stable.returncode == 0, (
        f"`plan -detailed-exitcode` rend {stable.returncode} avant toute "
        f"modification, attendu 0.\n{stable.stdout[-1000:]}"
    )

    import shutil

    copie = tmp_path / "sans-attachement"
    shutil.copytree(WORKDIR, copie)

    source = (copie / "main.tf").read_text(encoding="utf-8")
    debut = source.find('resource "aws_iam_role_policy_attachment"')
    assert debut != -1, (
        "`aws_iam_role_policy_attachment` est introuvable dans main.tf : il n'y "
        "a rien a retirer, et ce test ne mesurerait rien."
    )
    fin = source.find('\nresource "', debut + 10)
    ampute = source[:debut] + (source[fin + 1:] if fin != -1 else "")
    (copie / "main.tf").write_text(ampute, encoding="utf-8")

    plan = subprocess.run(
        ["terraform", "plan", "-input=false", "-no-color", "-out=sans.tfplan"],
        cwd=copie, capture_output=True, text=True, env=ENV, check=False,
    )
    assert plan.returncode == 0, f"Le plan a echoue :\n{plan.stderr[-1000:]}"

    montre = subprocess.run(
        ["terraform", "show", "-json", "sans.tfplan"],
        cwd=copie, capture_output=True, text=True, env=ENV, check=False,
    )
    actions = {
        c["address"]: c["change"]["actions"]
        for c in json.loads(montre.stdout).get("resource_changes", [])
        if c["change"]["actions"] != ["no-op"]
    }
    assert actions == {"aws_iam_role_policy_attachment.lecture": ["delete"]}, (
        f"Le plan annonce {actions}, attendu une seule suppression, celle du "
        "rattachement.\n\nLe role et la policy doivent SURVIVRE : ce sont des "
        "objets a part entiere. Une policy rattachee a plusieurs roles ne "
        "disparait pas parce que l'un d'eux s'en detache."
    )
