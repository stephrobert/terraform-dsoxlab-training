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
- `state show` n'accepte PAS `-json` : code 1, « Failed to parse command-line
  flags / flag provided but not defined: -json » ;
- `state show` ne rafraichit rien : apres une modification hors Terraform, il
  affiche toujours l'ancienne empreinte, et c'est `plan -detailed-exitcode` qui
  sort en 2.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, output_json, show_json, terraform, workdir_lab

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
        pytest.fail(f"`terraform init` a echoue.\n{init.stderr[-1200:]}")
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=WORKDIR)
    if app.returncode != 0:
        pytest.fail(
            "`terraform apply` a echoue. Un `???` restant dans outputs.tf, ou un "
            "output qui expose une valeur sensible sans `sensitive = true` ?"
            f"\n{app.stderr[-1500:]}"
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
        pytest.fail(f"L'output `{nom}` est absent : outputs.tf est incomplet.")
    return sorties[nom]


# --------------------------------------------------------------------------
# 1. Le state existe, avec six ressources gerees et une data source
# --------------------------------------------------------------------------

def test_le_state_porte_six_managed_et_une_data(etat: dict) -> None:
    modes: dict[str, int] = {}
    for r in etat["ressources"].values():
        modes[r["mode"]] = modes.get(r["mode"], 0) + 1
    assert modes.get("managed") == 6, (
        f"{modes.get('managed')} ressources en mode managed, attendu 6."
    )
    assert modes.get("data") == 1, (
        f"{modes.get('data')} ressource en mode data, attendu 1."
    )


# --------------------------------------------------------------------------
# 2. L'adresse d'une data source porte le prefixe data.
# --------------------------------------------------------------------------

def test_adresse_de_la_data_source(etat: dict) -> None:
    attendue = next(
        adr for adr, r in etat["ressources"].items() if r["mode"] == "data"
    )
    declaree = _sortie(etat, "adresse_data")["value"]
    assert declaree == attendue, (
        f"adresse_data declaree {declaree!r}, attendu {attendue!r} : une data "
        "source porte le prefixe `data.` dans le state."
    )
    # Et cette adresse fonctionne vraiment.
    proc = terraform("state", "show", "-no-color", attendue, cwd=etat["cwd"])
    assert proc.returncode == 0, (
        f"`state show {attendue}` rend {proc.returncode}, l'adresse devrait etre "
        f"valide.\n{proc.stderr[-400:]}"
    )


# --------------------------------------------------------------------------
# 3. Sans index, une adresse ne designe aucune instance
# --------------------------------------------------------------------------

def test_adresse_de_la_deuxieme_instance(etat: dict) -> None:
    declaree = _sortie(etat, "adresse_replica")["value"]
    assert declaree in etat["ressources"], (
        f"adresse_replica declaree {declaree!r}, qui n'existe pas dans le state. "
        f"Adresses disponibles : {sorted(etat['ressources'])}"
    )
    assert declaree == "random_pet.replicas[1]", (
        f"adresse_replica declaree {declaree!r} : `count` indexe a partir de 0, "
        "la DEUXIEME instance est donc [1]."
    )


def test_une_adresse_sans_index_est_refusee(etat: dict) -> None:
    """Le premier mur rencontre apres un state list sur une vraie config."""
    sans = terraform("state", "show", "-no-color", "random_pet.replicas",
                     cwd=etat["cwd"])
    assert sans.returncode == 1, (
        f"`state show random_pet.replicas` rend {sans.returncode}, attendu 1 : "
        "l'adresse ne reference pas une instance unique."
    )
    sortie = sans.stdout + sans.stderr
    assert "No instance found for the given address!" in sortie, (
        f"Message attendu « No instance found for the given address! », obtenu :"
        f"\n{sortie[-400:]}"
    )
    avec = terraform("state", "show", "-no-color", "random_pet.replicas[1]",
                     cwd=etat["cwd"])
    assert avec.returncode == 0, (
        f"`state show 'random_pet.replicas[1]'` rend {avec.returncode}, attendu 0."
    )


# --------------------------------------------------------------------------
# 4. Une valeur referencee, pas recopiee
# --------------------------------------------------------------------------

def test_empreinte_reprise_du_state(etat: dict) -> None:
    data = next(r for r in etat["ressources"].values() if r["mode"] == "data")
    attendue = data["values"]["content_sha256"]
    declaree = _sortie(etat, "empreinte_inventaire")["value"]
    assert declaree == attendue, (
        f"empreinte_inventaire vaut {declaree!r}, alors que le state porte "
        f"{attendue!r}. Referencez l'attribut plutot que de recopier la valeur."
    )


# --------------------------------------------------------------------------
# 5. Le secret : caviarde par state show, en clair dans le JSON
# --------------------------------------------------------------------------

def test_le_secret_est_expose_mais_marque_sensible(etat: dict) -> None:
    mot_de_passe = etat["ressources"]["random_password.api"]["values"]["result"]
    sortie = _sortie(etat, "secret_api")
    assert sortie.get("sensitive") is True, (
        "L'output secret_api doit porter `sensitive = true`. Sans lui, Terraform "
        "refuse d'exposer une valeur sensible."
    )
    assert sortie["value"] == mot_de_passe, (
        "secret_api ne vaut pas le mot de passe du state : referencez "
        "`random_password.api.result`."
    )


def test_state_show_caviarde_ce_que_le_json_expose(etat: dict) -> None:
    """La bascule a double tranchant : state show protege, show -json expose."""
    fiche = terraform("state", "show", "-no-color", "random_password.api",
                      cwd=etat["cwd"])
    fiche.check_returncode()
    mot_de_passe = etat["ressources"]["random_password.api"]["values"]["result"]

    assert "(sensitive value)" in fiche.stdout, (
        "La fiche de random_password.api devrait caviarder ses attributs "
        "sensibles."
    )
    assert mot_de_passe not in fiche.stdout, (
        "Le mot de passe apparait EN CLAIR dans la sortie de `state show`, ce "
        "qui contredit le caviardage attendu."
    )
    sensibles = etat["ressources"]["random_password.api"].get("sensitive_values", {})
    assert sensibles.get("result") is True, (
        f"sensitive_values devrait marquer `result`, obtenu : {sensibles}"
    )


# --------------------------------------------------------------------------
# 6. Les attributs nuls, omis de la fiche et visibles dans le JSON
# --------------------------------------------------------------------------

def test_attributs_nuls_recalcules_depuis_le_json(etat: dict) -> None:
    valeurs = etat["ressources"]["random_pet.env"]["values"]
    attendus = sorted(cle for cle, val in valeurs.items() if val is None)
    declares = _sortie(etat, "attributs_masques")["value"]
    assert declares == attendus, (
        f"attributs_masques vaut {declares!r}, attendu {attendus!r} : ce sont "
        "les attributs a null du state, que `state show` n'affiche pas."
    )
    assert attendus, "Le test n'a aucun sens si aucun attribut n'est a null."


def test_la_fiche_humaine_omet_bien_ces_attributs(etat: dict) -> None:
    fiche = terraform("state", "show", "-no-color", "random_pet.env",
                      cwd=etat["cwd"])
    fiche.check_returncode()
    declares = _sortie(etat, "attributs_masques")["value"]
    presents = [nom for nom in declares if f"{nom} " in fiche.stdout]
    assert not presents, (
        f"Ces attributs apparaissent dans la fiche de `state show` alors qu'ils "
        f"devraient en etre absents : {presents}."
    )


# --------------------------------------------------------------------------
# 7. state show n'accepte pas -json, et ne rafraichit rien
# --------------------------------------------------------------------------

def test_state_show_refuse_l_option_json(etat: dict) -> None:
    proc = terraform("state", "show", "-no-color", "-json", "random_pet.env",
                     cwd=etat["cwd"])
    assert proc.returncode == 1, (
        f"`state show -json` rend {proc.returncode}, attendu 1 : la commande "
        "n'a pas d'option -json, c'est `terraform show -json` qu'il faut."
    )
    sortie = proc.stdout + proc.stderr
    assert "flag provided but not defined: -json" in sortie, (
        f"Message attendu sur le drapeau inconnu, obtenu :\n{sortie[-400:]}"
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
    assert apres.stdout == avant.stdout, (
        "`state show` a change de sortie apres une modification hors Terraform : "
        "il ne devrait rien rafraichir."
    )

    plan = terraform("plan", "-input=false", "-detailed-exitcode", "-no-color", cwd=cwd)
    assert plan.returncode == 2, (
        f"plan -detailed-exitcode rend {plan.returncode}, attendu 2 : c'est le "
        "plan qui rafraichit et revele la derive, pas `state show`."
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
    assert plan.returncode == 0, (
        f"plan -detailed-exitcode rend {plan.returncode}, attendu 0 : renseigner "
        "des outputs ne doit rien changer a l'infrastructure."
    )
