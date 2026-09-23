"""Tests fonctionnels du lab « un security group dont les regles se prouvent ».

Aucun test n'ouvre un `.tf` de l'apprenant : tout passe par l'etat structure et
par ce que l'API de l'emulateur rapporte.

Faits mesures sur Terraform 1.15.4, provider AWS 6.x, contre l'emulateur local :

- un nom de groupe qui commence par `sg-` est REFUSE par le provider
  (`invalid value for name (cannot begin with sg-)`) ;
- avec des ressources de regle dediees, l'attribut `ingress` du groupe est vide
  dans le state, ce qui est la signature du bon style ;
- `for_each` produit des instances dont l'`index` est une CHAINE (`"ssh"`,
  `"http"`, `"https"`) ; un `count` donnerait des entiers ;
- une regle de sortie en `ip_protocol = "-1"` sans ports rend `from_port` et
  `to_port` a `null` ;
- melanger regles inline et ressources dediees produit une difference
  PERPETUELLE : le groupe ecrase la regle qu'il ne connait pas, la ressource la
  recree, et `plan -detailed-exitcode` reste a 2 indefiniment.

ECART CONNU DE L'EMULATEUR, qui explique une absence de test : AWS documente que
Terraform RETIRE la regle de sortie « autoriser tout » posee a la naissance du
groupe. L'emulateur, lui, la conserve : l'attribut `egress` du groupe n'est donc
jamais vide ici. On verifie la DECLARATION de la regle de sortie, pas le retrait
de la regle implicite, qui n'est pas observable sur ce banc.
"""

import json
import os
import socket
import subprocess
import time

import pytest

from conftest import exiger_workdir, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "aws-sg-subnet-instance"

ENDPOINT = "http://localhost:14566"
FLUX_ATTENDUS = {"ssh", "http", "https"}

ENV = {
    **os.environ,
    "AWS_ACCESS_KEY_ID": "test",
    "AWS_SECRET_ACCESS_KEY": "test",
    "AWS_DEFAULT_REGION": "eu-west-3",
    "AWS_PAGER": "",
}


# ── Helpers ─────────────────────────────────────────────────────────────────


def _tf(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["terraform", *args], cwd=WORKDIR,
                          capture_output=True, text=True, env=ENV, check=False)


def _aws(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["aws", "--endpoint-url", ENDPOINT, *args],
                          capture_output=True, text=True, env=ENV, check=False)


def _etat() -> list[dict]:
    res = _tf("show", "-json")
    if res.returncode != 0:
        pytest.fail(f"`terraform show -json` a echoue :\n{res.stderr[-600:]}")
    etat = json.loads(res.stdout or "{}")
    return etat.get("values", {}).get("root_module", {}).get("resources", [])


def _du_type(type_: str, mode: str = "managed") -> list[dict]:
    return [r for r in _etat() if r.get("type") == type_ and r.get("mode") == mode]



# ── Disponibilite de l'emulateur ────────────────────────────────────────────
#
# Floci est publie sur le port 14566 de l'hote (cf. `runtime.services` du lab).
# Il n'est demarre QUE pendant une session `dsoxlab` : hors session, le port est
# ferme et chaque commande Terraform echoue sur un point de terminaison
# injoignable. Sans la garde ci-dessous, l'apprenant lit une pile d'erreurs
# Terraform la ou une seule phrase suffit.
FLOCI_HOST = "127.0.0.1"
FLOCI_PORT = 14566


def _floci_joignable() -> bool:
    try:
        with socket.create_connection((FLOCI_HOST, FLOCI_PORT), timeout=2):
            return True
    except OSError:
        return False


def _exiger_floci() -> None:
    """Skippe proprement si l'emulateur n'est pas la, sauf pour le formateur.

    `LAB_WORKDIR` est pose par `scripts/verify-solutions.py`, qui materialise
    lui-meme le repertoire : dans ce cas un service absent est un vrai defaut et
    doit ECHOUER, pas disparaitre dans un skip.
    """
    if _floci_joignable():
        return
    message = (
        f"Floci n'est pas joignable sur {FLOCI_HOST}:{FLOCI_PORT}. Ce lab en a "
        "besoin : Floci emule l'API AWS en local, sans compte ni carte "
        "bancaire.\n\n"
        "Lancez le lab avec `dsoxlab run aws-sg-subnet-instance`, qui le demarre tout "
        "seul, et faites votre `dsoxlab check` DEPUIS cette session : le "
        "service s'arrete quand vous la quittez."
    )
    if os.environ.get("LAB_WORKDIR"):
        pytest.fail(message)
    pytest.skip(message)

@pytest.fixture(scope="module", autouse=True)
def applique() -> None:
    """Initialise et applique une fois pour tout le module."""
    exiger_workdir(WORKDIR, LAB_ID)
    _exiger_floci()

    # La sonde est reessayee : un emulateur conteneurise refuse parfois une
    # requete isolee alors qu'il est sain.
    sonde = None
    for _ in range(6):
        sonde = _aws("ec2", "describe-vpcs")
        if sonde.returncode == 0:
            break
        time.sleep(2)
    if sonde is None or sonde.returncode != 0:
        pytest.fail(
            f"L'emulateur EC2 ne repond pas sur {ENDPOINT}. Le lab le declare "
            "en `runtime.services` : `dsoxlab run` et `dsoxlab check` le "
            f"demarrent tout seuls.\n{sonde.stderr[-400:] if sonde else ''}"
        )

    init = _tf("init", "-input=false", "-no-color")
    if init.returncode != 0:
        pytest.fail(f"`terraform init` a echoue :\n{init.stderr[-800:]}")

    app = _tf("apply", "-auto-approve", "-input=false", "-no-color")
    if app.returncode != 0:
        pytest.fail(
            "`terraform apply` a echoue. Des blocs sont-ils encore a `???` ?\n"
            f"{(app.stderr or app.stdout)[-1500:]}"
        )


# ── 1. Le subnet est designe, pas tire au sort ──────────────────────────────


def test_le_reseau_est_gere_et_porte_deux_subnets() -> None:
    """Le VPC et les deux subnets doivent exister, et etre geres."""
    vpc = _du_type("aws_vpc")
    assert len(vpc) == 1, f"un seul VPC attendu, {len(vpc)} trouve(s)"

    subnets = _du_type("aws_subnet")
    assert len(subnets) == 2, (
        f"deux subnets attendus, {len(subnets)} trouve(s). `reseau.tf` est "
        "fourni, il ne faut pas le modifier."
    )
    tiers = {s["values"].get("tags", {}).get("Tier") for s in subnets}
    assert tiers == {"public", "private"}, f"tags Tier obtenus : {tiers}"


def test_le_subnet_est_designe_par_une_data_source_filtree() -> None:
    """Une data source, pas un index : la doc ne garantit aucun ordre.

    On exige `aws_subnet` au SINGULIER : elle echoue quand le filtre ne
    designe pas exactement une ressource, la ou `aws_subnets` rendrait une
    liste qu'il faudrait indexer, donc trier au hasard.
    """
    data = [r for r in _etat() if r.get("mode") == "data"]
    assert data, (
        "aucune data source dans l'etat : le subnet est-il designe par un "
        "index de liste plutot que par son tag ?"
    )
    types = {r.get("type") for r in data}
    assert "aws_subnet" in types, (
        f"data sources trouvees : {types}. Le lab attend `data \"aws_subnet\"`, "
        "au singulier, qui echoue si le filtre ne designe pas exactement un "
        "subnet."
    )

    retenu = next(r for r in data if r.get("type") == "aws_subnet")
    tier = (retenu["values"].get("tags") or {}).get("Tier")
    assert tier == "public", (
        f"le subnet retenu porte Tier={tier!r} au lieu de 'public' : le filtre "
        "ne vise pas le bon tag."
    )


def test_l_instance_vit_dans_le_subnet_retenu() -> None:
    instances = _du_type("aws_instance")
    assert len(instances) == 1, f"une instance attendue, {len(instances)} trouvee(s)"

    data_subnet = next(
        (r for r in _etat()
         if r.get("mode") == "data" and r.get("type") == "aws_subnet"), None
    )
    assert data_subnet is not None, "pas de data source de subnet"

    attendu = data_subnet["values"].get("id")
    obtenu = instances[0]["values"].get("subnet_id")
    assert obtenu == attendu, (
        f"l'instance est dans {obtenu}, alors que le subnet retenu est "
        f"{attendu}. Son `subnet_id` doit venir de la data source."
    )


# ── 2. Le groupe ne porte aucune regle inline ───────────────────────────────


def test_le_groupe_appartient_au_vpc_et_n_a_aucune_regle_entrante_inline() -> None:
    """`ingress` vide dans le state est la signature des ressources dediees.

    Melanger les deux styles produit une difference perpetuelle, mesuree : le
    groupe ecrase la regle qu'il ne connait pas, la ressource dediee la recree,
    et le plan ne se stabilise jamais.
    """
    groupes = _du_type("aws_security_group")
    assert len(groupes) == 1, f"un groupe attendu, {len(groupes)} trouve(s)"
    valeurs = groupes[0]["values"]

    vpc = _du_type("aws_vpc")[0]["values"]["id"]
    assert valeurs.get("vpc_id") == vpc, (
        f"le groupe est rattache a {valeurs.get('vpc_id')}, pas au VPC du lab "
        f"({vpc})."
    )

    inline = valeurs.get("ingress") or []
    assert inline == [], (
        f"le groupe porte {len(inline)} regle(s) d'entree INLINE. Elles doivent "
        "toutes etre des ressources `aws_vpc_security_group_ingress_rule` : "
        "melanger les deux styles produit une difference perpetuelle."
    )


def test_le_nom_du_groupe_est_accepte_par_le_provider() -> None:
    """Un nom qui commence par `sg-` est refuse. S'il est applique, il est bon."""
    nom = _du_type("aws_security_group")[0]["values"].get("name") or ""
    assert nom, "le groupe n'a pas de nom"
    assert not nom.startswith("sg-"), (
        f"nom {nom!r} : le provider refuse tout nom commencant par `sg-`."
    )


# ── 3. Les regles d'entree viennent d'un seul bloc ──────────────────────────


def test_les_trois_flux_viennent_d_un_seul_bloc_for_each() -> None:
    """`for_each` se prouve par l'`index`, qui est une CHAINE.

    Un `count` donnerait des entiers, et trois blocs copies-colles donneraient
    trois `name` de ressource differents, donc un seul element par adresse.
    """
    regles = _du_type("aws_vpc_security_group_ingress_rule")
    assert len(regles) == 3, (
        f"trois regles d'entree attendues, {len(regles)} trouvee(s). Elles "
        "doivent venir de `for_each` sur `var.flux_entrants`."
    )

    noms = {r.get("name") for r in regles}
    assert len(noms) == 1, (
        f"les regles proviennent de {len(noms)} blocs differents ({noms}). Le "
        "lab en attend UN SEUL, porte par `for_each`."
    )

    index = [r.get("index") for r in regles]
    assert all(isinstance(i, str) for i in index), (
        f"index obtenus : {index}. Des entiers signent un `count` ; `for_each` "
        "sur une map donne des chaines."
    )
    assert set(index) == FLUX_ATTENDUS, (
        f"cles obtenues : {sorted(i for i in index if i)}, attendues : "
        f"{sorted(FLUX_ATTENDUS)}"
    )


def test_chaque_regle_ouvre_son_port_et_une_seule_cidr() -> None:
    ports = {22, 80, 443}
    obtenus = set()
    for regle in _du_type("aws_vpc_security_group_ingress_rule"):
        v = regle["values"]
        assert v.get("ip_protocol") == "tcp", (
            f"regle {regle.get('index')!r} : ip_protocol="
            f"{v.get('ip_protocol')!r}, 'tcp' attendu"
        )
        assert v.get("from_port") == v.get("to_port"), (
            f"regle {regle.get('index')!r} : la plage doit viser un seul port, "
            f"obtenu {v.get('from_port')}-{v.get('to_port')}"
        )
        assert v.get("cidr_ipv4"), (
            f"regle {regle.get('index')!r} : aucune `cidr_ipv4`"
        )
        assert v.get("cidr_ipv4") != "0.0.0.0/0", (
            f"regle {regle.get('index')!r} ouvre a 0.0.0.0/0 : le lab demande "
            "la seule CIDR de `var.cidr_autorise`."
        )
        obtenus.add(v.get("from_port"))
    assert obtenus == ports, f"ports ouverts : {sorted(obtenus)}, attendus {sorted(ports)}"


# ── 4. La sortie est declaree explicitement ─────────────────────────────────


def test_la_sortie_est_declaree_sans_ports() -> None:
    """`ip_protocol = "-1"` couvre tous les protocoles : les ports n'ont pas de sens.

    La documentation du provider est explicite : avec `-1`, `from_port` et
    `to_port` « should not be defined ».
    """
    sorties = _du_type("aws_vpc_security_group_egress_rule")
    assert len(sorties) == 1, (
        f"une regle de sortie attendue, {len(sorties)} trouvee(s). Sans elle, "
        "l'instance ne peut joindre personne."
    )
    v = sorties[0]["values"]
    assert v.get("ip_protocol") == "-1", (
        f"ip_protocol={v.get('ip_protocol')!r} : '-1' attendu pour couvrir tous "
        "les protocoles."
    )
    for champ in ("from_port", "to_port"):
        assert v.get(champ) is None, (
            f"{champ}={v.get(champ)!r} : avec `-1`, aucun port ne doit etre "
            "defini."
        )


def test_l_instance_reference_le_groupe_par_identifiant() -> None:
    """`vpc_security_group_ids` attend des IDs, `security_groups` des NOMS.

    Les deux sont des listes : la difference n'est pas la cardinalite mais la
    nature de la valeur, et le fait que `security_groups` ne vaut que dans le
    VPC par defaut.
    """
    instance = _du_type("aws_instance")[0]["values"]
    groupe = _du_type("aws_security_group")[0]["values"]["id"]

    ids = instance.get("vpc_security_group_ids") or []
    assert groupe in ids, (
        f"le groupe {groupe} n'est pas dans `vpc_security_group_ids` "
        f"({ids}). Attention : `security_groups` attend des noms et ne vaut "
        "que dans le VPC par defaut."
    )


# ── 5. Ce que l'emulateur confirme, et la stabilite ─────────────────────────


def test_l_emulateur_rapporte_les_quatre_regles() -> None:
    """Le state dit ce que Terraform croit ; l'API dit ce qui existe."""
    groupe = _du_type("aws_security_group")[0]["values"]["id"]
    res = _aws("ec2", "describe-security-group-rules", "--filters",
               f"Name=group-id,Values={groupe}", "--output", "json")
    assert res.returncode == 0, (
        f"`describe-security-group-rules` a echoue :\n{res.stderr[-400:]}"
    )
    regles = json.loads(res.stdout or "{}").get("SecurityGroupRules", [])
    entrantes = [r for r in regles if not r.get("IsEgress")]
    sortantes = [r for r in regles if r.get("IsEgress")]

    assert len(entrantes) == 3, (
        f"l'API rapporte {len(entrantes)} regle(s) entrante(s) sur ce groupe, "
        "3 attendues"
    )
    assert sortantes, "l'API ne rapporte aucune regle sortante sur ce groupe"


def test_un_plan_relance_n_annonce_aucun_changement() -> None:
    """Idempotence. Un melange des deux styles ferait rendre 2 indefiniment."""
    res = _tf("plan", "-input=false", "-detailed-exitcode", "-no-color")
    assert res.returncode == 0, (
        f"`plan -detailed-exitcode` a rendu {res.returncode}. La valeur 2 "
        "signale une derive : des regles inline cohabitent-elles avec les "
        f"ressources dediees ?\n{(res.stdout or res.stderr)[-900:]}"
    )


def test_les_trois_outputs_sont_renseignes() -> None:
    res = _tf("output", "-json")
    assert res.returncode == 0, f"`terraform output` a echoue :\n{res.stderr[-400:]}"
    sorties = json.loads(res.stdout or "{}")

    for nom in ("subnet_id", "security_group_id", "instance_subnet_id"):
        assert nom in sorties, f"output `{nom}` absent"
        assert sorties[nom].get("value"), (
            f"output `{nom}` vide : sa `value` est-elle encore a `???` ?"
        )

    assert sorties["subnet_id"]["value"] == sorties["instance_subnet_id"]["value"], (
        "le subnet expose et celui de l'instance different : l'instance n'a pas "
        "ete posee dans le subnet retenu."
    )
