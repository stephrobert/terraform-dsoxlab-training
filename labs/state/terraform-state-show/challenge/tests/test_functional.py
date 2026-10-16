"""Tests fonctionnels du lab « lire le state sans le parser a la main ».

`terraform state show` produit une fiche pour un humain, et la doc officielle
interdit d'en extraire quoi que ce soit par programme. Ces tests appliquent la
regle a eux memes : ils ne lisent JAMAIS la sortie de `state show` pour en
deduire une valeur. Ils la lancent uniquement pour prouver ce qu'elle CACHE, et
recalculent chaque verite depuis `terraform show -json`.

Faits verifies sur Terraform 1.15.4 (random + local, hors ligne) :
- `state show random_password.api` caviarde DEUX attributs, `bcrypt_hash` et
  `result`, en `(sensitive value)` ; `show -json` les rend en clair ;
- `sensitive_values` de cette ressource vaut
  `{"bcrypt_hash": true, "result": true}` ;
- `state show random_pet.env` n'affiche que `id`, `length` et `separator` : les
  attributs a `null` (`keepers`, `prefix`) sont OMIS, alors que le JSON les
  expose explicitement a `null` ;
- une adresse sans index sur une ressource en `count` echoue en code 1 sur
  « No instance found for the given address! », alors que `[1]` rend 0 ;
- `state show` et `-json` : le comportement DEPEND de la version, et le test le
  lit au lieu de le supposer. Jusqu'a Terraform 1.15 inclus, le drapeau n'existe
  pas et la commande sort en 1 sur « flag provided but not defined: -json ».
  Depuis la 1.16 il existe et rend un document JSON. Source : CHANGELOG de
  Terraform, « state show: The `state show` command can now produce
  machine-readable output when supplied with the `-json` flag », hashicorp/
  terraform#23940, livre en 1.16 ;
- `state show` ne rafraichit rien : apres une modification hors Terraform, il
  affiche toujours l'ancienne empreinte, et c'est `plan -detailed-exitcode` qui
  sort en 2.
"""

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import (
    exiger_workdir,
    message,
    output_json,
    show_json,
    terraform,
    workdir_lab,
)

WORKDIR = workdir_lab(__file__)
LAB_ID = "state-terraform-state-show"


def _ressources(cwd: Path) -> dict[str, dict]:
    """Instances du state, indexees par adresse."""
    racine = show_json(cwd)["values"]["root_module"]
    return {r["address"]: r for r in racine.get("resources", [])}


@pytest.fixture(scope="module")
def applied() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(message(
            en=f"`terraform init` failed.\n{init.stderr[-1200:]}",
            fr=f"`terraform init` a échoué.\n{init.stderr[-1200:]}",
        ))
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(
            message(
            en="`terraform apply` failed. A leftover `???` in outputs.tf, or an "
            "output exposing a sensitive value without `sensitive = true`?"
            f"\n{app.stderr[-1500:]}",
            fr="`terraform apply` a échoué. Un `???` restant dans outputs.tf, ou un "
            "output qui expose une valeur sensible sans `sensitive = true` ?"
            f"\n{app.stderr[-1500:]}",
        )
        )
    yield WORKDIR
    terraform("destroy", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)


@pytest.fixture(scope="module")
def etat(applied: Path) -> dict:
    return {
        "cwd": applied,
        "ressources": _ressources(applied),
        "sorties": output_json(applied),
    }


def _sortie(etat: dict, nom: str) -> dict:
    sorties = etat["sorties"]
    if nom not in sorties:
        pytest.fail(message(
            en=f"The output `{nom}` is missing: outputs.tf is incomplete.",
            fr=f"L'output `{nom}` est absent : outputs.tf est incomplet.",
        ))
    return sorties[nom]


# --------------------------------------------------------------------------
# 1. Le state existe, avec six ressources gerees et une data source
# --------------------------------------------------------------------------

def test_le_state_porte_six_managed_et_une_data(etat: dict) -> None:
    modes: dict[str, int] = {}
    for r in etat["ressources"].values():
        modes[r["mode"]] = modes.get(r["mode"], 0) + 1
    assert modes.get("managed") == 6, message(
        en=f"{modes.get('managed')} resources in managed mode, 6 expected.",
        fr=f"{modes.get('managed')} ressources en mode managed, attendu 6.",
    )
    assert modes.get("data") == 1, message(
        en=f"{modes.get('data')} resource in data mode, 1 expected.",
        fr=f"{modes.get('data')} ressource en mode data, attendu 1.",
    )


# --------------------------------------------------------------------------
# 2. L'adresse d'une data source porte le prefixe data.
# --------------------------------------------------------------------------

def test_adresse_de_la_data_source(etat: dict) -> None:
    attendue = next(
        adr for adr, r in etat["ressources"].items() if r["mode"] == "data"
    )
    declaree = _sortie(etat, "adresse_data")["value"]
    assert declaree == attendue, message(
        en=f"adresse_data declared {declaree!r}, expected {attendue!r}: a data "
        "source carries the `data.` prefix in the state.",
        fr=f"adresse_data déclarée {declaree!r}, attendu {attendue!r} : une data "
        "source porte le préfixe `data.` dans le state.",
    )
    # Et cette adresse fonctionne vraiment.
    proc = terraform("state", "show", "-no-color", attendue, cwd=etat["cwd"])
    assert proc.returncode == 0, message(
        en=f"`state show {attendue}` returns {proc.returncode}; the address should be "
        f"valid.\n{proc.stderr[-400:]}",
        fr=f"`state show {attendue}` rend {proc.returncode}, l'adresse devrait être "
        f"valide.\n{proc.stderr[-400:]}",
    )


# --------------------------------------------------------------------------
# 3. Sans index, une adresse ne designe aucune instance
# --------------------------------------------------------------------------

def test_adresse_de_la_deuxieme_instance(etat: dict) -> None:
    declaree = _sortie(etat, "adresse_replica")["value"]
    assert declaree in etat["ressources"], message(
        en=f"adresse_replica declared {declaree!r}, which does not exist in the state. "
        f"Available addresses: {sorted(etat['ressources'])}",
        fr=f"adresse_replica déclarée {declaree!r}, qui n'existe pas dans le state. "
        f"Adresses disponibles : {sorted(etat['ressources'])}",
    )
    assert declaree == "random_pet.replicas[1]", message(
        en=f"adresse_replica declared {declaree!r}: `count` indexes from 0, "
        "so the SECOND instance is [1].",
        fr=f"adresse_replica déclarée {declaree!r} : `count` indexe à partir de 0, "
        "la DEUXIÈME instance est donc [1].",
    )


def test_une_adresse_sans_index_est_refusee(etat: dict) -> None:
    """Le premier mur rencontre apres un state list sur une vraie config."""
    sans = terraform("state", "show", "-no-color", "random_pet.replicas",
                     cwd=etat["cwd"])
    assert sans.returncode == 1, message(
        en=f"`state show random_pet.replicas` returns {sans.returncode}, expected 1: "
        "the address does not reference a single instance.",
        fr=f"`state show random_pet.replicas` rend {sans.returncode}, attendu 1 : "
        "l'adresse ne référence pas une instance unique.",
    )
    sortie = sans.stdout + sans.stderr
    assert "No instance found for the given address!" in sortie, message(
        en=f"Expected message \"No instance found for the given address!\", got:"
        f"\n{sortie[-400:]}",
        fr=f"Message attendu « No instance found for the given address! », obtenu :"
        f"\n{sortie[-400:]}",
    )
    avec = terraform("state", "show", "-no-color", "random_pet.replicas[1]",
                     cwd=etat["cwd"])
    assert avec.returncode == 0, message(
        en=f"`state show 'random_pet.replicas[1]'` returns {avec.returncode}, expected 0.",
        fr=f"`state show 'random_pet.replicas[1]'` rend {avec.returncode}, attendu 0.",
    )


# --------------------------------------------------------------------------
# 4. Une valeur referencee, pas recopiee
# --------------------------------------------------------------------------

def test_empreinte_reprise_du_state(etat: dict) -> None:
    data = next(r for r in etat["ressources"].values() if r["mode"] == "data")
    attendue = data["values"]["content_sha256"]
    declaree = _sortie(etat, "empreinte_inventaire")["value"]
    assert declaree == attendue, message(
        en=f"empreinte_inventaire is {declaree!r}, while the state carries "
        f"{attendue!r}. Reference the attribute rather than copying the value.",
        fr=f"empreinte_inventaire vaut {declaree!r}, alors que le state porte "
        f"{attendue!r}. Référencez l'attribut plutôt que de recopier la valeur.",
    )


# --------------------------------------------------------------------------
# 5. Le secret : caviarde par state show, en clair dans le JSON
# --------------------------------------------------------------------------

def test_le_secret_est_expose_mais_marque_sensible(etat: dict) -> None:
    mot_de_passe = etat["ressources"]["random_password.api"]["values"]["result"]
    sortie = _sortie(etat, "secret_api")
    assert sortie.get("sensitive") is True, message(
        en="The secret_api output must carry `sensitive = true`. Without it, Terraform "
        "refuses to expose a sensitive value.",
        fr="L'output secret_api doit porter `sensitive = true`. Sans lui, Terraform "
        "refuse d'exposer une valeur sensible.",
    )
    assert sortie["value"] == mot_de_passe, message(
        en="secret_api is not the password from the state: reference "
        "`random_password.api.result`.",
        fr="secret_api ne vaut pas le mot de passe du state : référencez "
        "`random_password.api.result`.",
    )


def test_state_show_caviarde_ce_que_le_json_expose(etat: dict) -> None:
    """La bascule a double tranchant : state show protege, show -json expose."""
    fiche = terraform("state", "show", "-no-color", "random_password.api",
                      cwd=etat["cwd"])
    fiche.check_returncode()
    mot_de_passe = etat["ressources"]["random_password.api"]["values"]["result"]

    assert "(sensitive value)" in fiche.stdout, message(
        en="The record of random_password.api should redact its sensitive "
        "attributes.",
        fr="La fiche de random_password.api devrait caviarder ses attributs "
        "sensibles.",
    )
    assert mot_de_passe not in fiche.stdout, message(
        en="The password appears IN CLEAR in the output of `state show`, which "
        "contradicts the expected redaction.",
        fr="Le mot de passe apparaît EN CLAIR dans la sortie de `state show`, ce "
        "qui contredit le caviardage attendu.",
    )
    sensibles = etat["ressources"]["random_password.api"].get("sensitive_values", {})
    assert sensibles.get("result") is True, message(
        en=f"sensitive_values should mark `result`, got: {sensibles}",
        fr=f"sensitive_values devrait marquer `result`, obtenu : {sensibles}",
    )


# --------------------------------------------------------------------------
# 6. Les attributs nuls, omis de la fiche et visibles dans le JSON
# --------------------------------------------------------------------------

def test_attributs_nuls_recalcules_depuis_le_json(etat: dict) -> None:
    valeurs = etat["ressources"]["random_pet.env"]["values"]
    attendus = sorted(cle for cle, val in valeurs.items() if val is None)
    declares = _sortie(etat, "attributs_masques")["value"]
    assert declares == attendus, message(
        en=f"attributs_masques is {declares!r}, expected {attendus!r}: those are "
        "the state's null attributes, which `state show` does not display.",
        fr=f"attributs_masques vaut {declares!r}, attendu {attendus!r} : ce sont "
        "les attributs à null du state, que `state show` n'affiche pas.",
    )
    assert attendus, message(
        en="The test means nothing if no attribute is null.",
        fr="Le test n'a aucun sens si aucun attribut n'est à null.",
    )


def test_la_fiche_humaine_omet_bien_ces_attributs(etat: dict) -> None:
    fiche = terraform("state", "show", "-no-color", "random_pet.env",
                      cwd=etat["cwd"])
    fiche.check_returncode()
    declares = _sortie(etat, "attributs_masques")["value"]
    presents = [nom for nom in declares if f"{nom} " in fiche.stdout]
    assert not presents, message(
        en=f"These attributes appear in the `state show` record although they "
        f"should be absent from it: {presents}.",
        fr=f"Ces attributs apparaissent dans la fiche de `state show` alors qu'ils "
        f"devraient en être absents : {presents}.",
    )


# --------------------------------------------------------------------------
# 7. state show et -json : un comportement qui a change de version
# --------------------------------------------------------------------------

def _version_terraform() -> tuple[int, ...]:
    """La version du binaire, lue et non supposee."""
    brut = terraform("version", "-json", cwd=Path.cwd()).stdout
    numero = json.loads(brut)["terraform_version"]
    return tuple(int(n) for n in numero.split("-")[0].split("."))


def test_state_show_et_l_option_json_selon_la_version(etat: dict) -> None:
    """Ce test a ete ECRIT FAUX, et l'a reste jusqu'au 2026-09-23.

    Il affirmait que `state show` n'accepte pas `-json`. C'etait vrai sur la
    1.15.4, sur laquelle il avait ete eprouve. La 1.16 a livre ce drapeau, et le
    test est devenu rouge sur un poste a jour. Le probleme depassait le test :
    le lab ENSEIGNAIT une chose fausse a l'apprenant.

    La lecon juste n'est pas « ce drapeau n'existe pas », qui est date. C'est
    que les deux commandes ne rendent pas la meme chose : `state show -json`
    decrit UNE ressource, `show -json` decrit le state ENTIER, avec ses outputs
    et ses valeurs sensibles. C'est cette distinction qui ne vieillira pas.

    Source du changement : CHANGELOG de Terraform, hashicorp/terraform#23940,
    livre en 1.16.
    """
    proc = terraform("state", "show", "-no-color", "-json", "random_pet.env",
                     cwd=etat["cwd"])
    version = _version_terraform()

    if version < (1, 16):
        assert proc.returncode == 1, message(
            en=f"On Terraform {'.'.join(map(str, version))}, `state show -json` "
            f"returns {proc.returncode}, expected 1: the flag does not exist "
            "yet, `terraform show -json` is the one to use.",
            fr=f"Sur Terraform {'.'.join(map(str, version))}, `state show -json` "
            f"rend {proc.returncode}, attendu 1 : le drapeau n'existe pas "
            "encore, c'est `terraform show -json` qu'il faut.",
        )
        sortie = proc.stdout + proc.stderr
        assert "flag provided but not defined: -json" in sortie, message(
            en=f"Expected message about the unknown flag, got:\n{sortie[-400:]}",
            fr=f"Message attendu sur le drapeau inconnu, obtenu :\n{sortie[-400:]}",
        )
        return

    assert proc.returncode == 0, message(
        en=f"On Terraform {'.'.join(map(str, version))}, `state show -json` "
        f"should succeed: the flag exists since 1.16.\n"
        f"{(proc.stdout + proc.stderr)[-400:]}",
        fr=f"Sur Terraform {'.'.join(map(str, version))}, `state show -json` "
        f"devrait réussir : le drapeau existe depuis la 1.16.\n"
        f"{(proc.stdout + proc.stderr)[-400:]}",
    )
    fiche = json.loads(proc.stdout)
    assert "resource" in fiche, message(
        en=f"`state show -json` should describe ONE resource. Keys obtained: "
        f"{sorted(fiche)}.",
        fr=f"`state show -json` devrait décrire UNE ressource. Clés obtenues : "
        f"{sorted(fiche)}.",
    )

    # La distinction qui compte, et qui ne depend d'aucune version : l'une
    # decrit une ressource, l'autre le state entier.
    complet = json.loads(
        terraform("show", "-json", cwd=etat["cwd"]).stdout
    )
    assert "values" in complet and "outputs" in complet.get("values", {}), message(
        en="`show -json` should return the whole state, outputs included. That is what "
        "distinguishes it from `state show -json`, limited to one resource.",
        fr="`show -json` devrait rendre le state entier, outputs compris. C'est ce "
        "qui le distingue de `state show -json`, limité à une ressource.",
    )
    assert "outputs" not in fiche.get("resource", {}), message(
        en="`state show -json` must not return the outputs: it describes "
        "a single resource only.",
        fr="`state show -json` ne doit pas rendre les outputs : il ne décrit "
        "qu'une ressource.",
    )


def test_state_show_ne_rafraichit_pas(etat: dict) -> None:
    """Il montre le state enregistre, jamais l'infrastructure reelle."""
    cwd = etat["cwd"]
    fichier = Path(etat["ressources"]["local_file.inventaire"]["values"]["filename"])
    if not fichier.is_absolute():
        fichier = cwd / fichier
    avant = terraform("state", "show", "-no-color", "local_file.inventaire", cwd=cwd)
    avant.check_returncode()

    with fichier.open("a", encoding="utf-8") as fh:
        fh.write("derive introduite hors terraform\n")

    apres = terraform("state", "show", "-no-color", "local_file.inventaire", cwd=cwd)
    apres.check_returncode()
    assert apres.stdout == avant.stdout, message(
        en="`state show` changed its output after a modification made outside Terraform: "
        "it should refresh nothing.",
        fr="`state show` a changé de sortie après une modification hors Terraform : "
        "il ne devrait rien rafraîchir.",
    )

    plan = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=cwd)
    assert plan.returncode == 2, message(
        en=f"plan -detailed-exitcode returns {plan.returncode}, expected 2: it is the "
        "plan that refreshes and reveals the drift, not `state show`.",
        fr=f"plan -detailed-exitcode rend {plan.returncode}, attendu 2 : c'est le "
        "plan qui rafraîchit et révèle la dérive, pas `state show`.",
    )
    # On remet l'etat en place pour ne pas fausser le test d'idempotence.
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=cwd)
    app.check_returncode()


# --------------------------------------------------------------------------
# 8. Converge une fois les reponses posees
# --------------------------------------------------------------------------

def test_idempotence(etat: dict) -> None:
    plan = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color",
                     cwd=etat["cwd"])
    assert plan.returncode == 0, message(
        en=f"plan -detailed-exitcode returns {plan.returncode}, expected 0: filling in "
        "outputs must change nothing in the infrastructure.",
        fr=f"plan -detailed-exitcode rend {plan.returncode}, attendu 0 : renseigner "
        "des outputs ne doit rien changer à l'infrastructure.",
    )
