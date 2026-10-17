"""Tests fonctionnels du lab « produire un inventaire Ansible depuis le state ».

Terraform sait ce qu'il a cree ; Ansible doit le savoir aussi. Le lab produit le
pont entre les deux, et il porte sur ce qui rend ce pont FIABLE plutot que
seulement fonctionnel.

Aucun cloud, aucun hyperviseur : le parc est simule par des ressources dont
certains attributs ne sont connus qu'apres creation. C'est deliberé : une valeur
devinable ne prouverait rien. Un inventaire recopie a la main donnerait le meme
fichier aujourd'hui, et mentirait demain.

Aucun test ne relit les `.tf` de l'apprenant. Tout se lit dans l'etat structure
et dans l'artefact produit.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, message, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "first-infra-ansible"

INVENTAIRE = "inventaire.json"
CIDR_DE_BASE = "10.20.0.0/16"

# Le parc par defaut, tel que les fixtures le declarent.
PARC = {
    "web1": {"role": "web", "index": 11},
    "web2": {"role": "web", "index": 12},
    "bdd1": {"role": "bdd", "index": 21},
}


def _tf(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["terraform", *args], cwd=cwd or WORKDIR, capture_output=True, text=True,
        check=False,
    )


@pytest.fixture(scope="module")
def applique() -> Iterator[None]:
    exiger_workdir(WORKDIR, LAB_ID)

    init = _tf("init", "-input=false", "-no-color")
    if init.returncode != 0:
        pytest.fail(message(
            en=f"`terraform init` failed.\n{init.stderr[-1200:]}",
            fr=f"`terraform init` a échoué.\n{init.stderr[-1200:]}",
        ))

    app = _tf("apply", "-auto-approve", "-input=false", "-no-color")
    if app.returncode != 0:
        pytest.fail(
            message(
            en="`terraform apply` failed. Are there leftover `???`?\n"
            f"{(app.stderr or app.stdout)[-1800:]}",
            fr="`terraform apply` a échoué. Des `???` subsistent-ils ?\n"
            f"{(app.stderr or app.stdout)[-1800:]}",
        )
        )
    try:
        yield
    finally:
        _tf("destroy", "-auto-approve", "-input=false", "-no-color")


def _etat() -> dict:
    proc = _tf("show", "-json")
    proc.check_returncode()
    return json.loads(proc.stdout)


def _gerees() -> dict[str, dict]:
    racine = _etat().get("values", {}).get("root_module", {})
    return {
        r["address"]: r for r in racine.get("resources", []) if r["mode"] == "managed"
    }


def _sorties() -> dict:
    proc = _tf("output", "-json")
    proc.check_returncode()
    return json.loads(proc.stdout or "{}")


def _fichier() -> dict:
    chemin = WORKDIR / INVENTAIRE
    assert chemin.is_file(), message(
        en=f"`{INVENTAIRE}` is missing. A resource of the `local` provider must "
        "write it in the module's directory.",
        fr=f"`{INVENTAIRE}` est absent. Une ressource du provider `local` doit "
        "l'écrire dans le répertoire du module.",
    )
    brut = chemin.read_text(encoding="utf-8")
    try:
        return json.loads(brut)
    except json.JSONDecodeError as erreur:
        pytest.fail(
            message(
            en=f"`{INVENTAIRE}` is not valid JSON: {erreur}\n\nThat is the "
            "signature of a string concatenation: it produces ALMOST valid "
            "JSON, and the almost costs an hour. `jsonencode` escapes "
            f"what it must and never gets a comma wrong.\n{brut[:300]}",
            fr=f"`{INVENTAIRE}` n'est pas du JSON valide : {erreur}\n\nC'est la "
            "signature d'une concaténation de chaînes : elle produit du JSON "
            "PRESQUE valide, et le presque coûte une heure. `jsonencode` échappe "
            f"ce qu'il faut et ne se trompe jamais de virgule.\n{brut[:300]}",
        )
        )


def _identifiants_du_state() -> dict[str, str]:
    """Les identifiants attribues a la creation, introuvables autrement."""
    return {
        adresse.split('"')[1]: ressource["values"]["hex"]
        for adresse, ressource in _gerees().items()
        if adresse.startswith("random_id.machine[")
    }


# --------------------------------------------------------------------------
# 1. Le type du parc refuse ce qui n'a pas la bonne forme.
# --------------------------------------------------------------------------
def test_le_parc_est_type_et_refuse_une_entree_mal_formee(applique: None) -> None:
    """`any` accepterait tout, et ne prouverait rien.

    La difference se voit AU PLAN : une entree a laquelle il manque `index`, ou
    dont le role serait un nombre, doit etre refusee avant tout appel de
    provider. Avec `any`, la meme faute passe le plan et casse plus loin, sur un
    message qui ne nomme ni la variable ni l'entree fautive.
    """
    refus = _tf(
        "plan", "-input=false", "-no-color",
        "-var", 'parc={"casse":{"role":"web"}}',
    )
    assert refus.returncode != 0, message(
        en="A fleet one of whose entries has NO `index` is accepted at plan time.\n\nThe "
        "type is too broad: `any` or `map(any)` let any shape "
        "through. A `map(object({…}))` refuses this one before any provider "
        "call.",
        fr="Un parc dont une entrée n'a PAS d'`index` est accepté au plan.\n\nLe "
        "type est trop large : `any` ou `map(any)` laissent passer n'importe "
        "quelle forme. Un `map(object({...}))` refuse celle-ci avant tout appel "
        "de provider.",
    )

    accepte = _tf(
        "plan", "-input=false", "-no-color",
        "-var", 'parc={"valide":{"role":"web","index":5}}',
    )
    assert accepte.returncode in (0, 2), message(
        en="A WELL-formed fleet is refused at plan time: the type is too strict.\n"
        f"{(accepte.stderr or accepte.stdout)[-1000:]}",
        fr="Un parc BIEN formé est refusé au plan : le type est trop strict.\n"
        f"{(accepte.stderr or accepte.stdout)[-1000:]}",
    )


# --------------------------------------------------------------------------
# 2. Les adresses sont CALCULEES depuis le CIDR.
# --------------------------------------------------------------------------
def test_les_adresses_derivent_du_cidr_de_base(applique: None) -> None:
    """Une adresse recopiee serait juste aujourd'hui et fausse demain.

    On ne compare pas a une liste ecrite dans le test : on recalcule depuis le
    CIDR et l'index, exactement comme la configuration aurait du le faire. Deux
    calculs independants qui tombent d'accord valent mieux qu'une constante.
    """
    import ipaddress

    reseau = ipaddress.ip_network(CIDR_DE_BASE)
    inventaire = _fichier()

    for nom, serveur in PARC.items():
        attendue = str(reseau[serveur["index"]])
        groupe = inventaire.get(serveur["role"], {}).get("hosts", {})
        assert nom in groupe, message(
            en=f"`{nom}` does not appear in the group `{serveur['role']}`. "
            f"Groups found: {sorted(inventaire)}.",
            fr=f"`{nom}` n'apparaît pas dans le groupe `{serveur['role']}`. "
            f"Groupes trouvés : {sorted(inventaire)}.",
        )
        obtenue = groupe[nom].get("ansible_host")
        assert obtenue == attendue, message(
            en=f"`{nom}` carries the address {obtenue!r}, expected {attendue!r}.\n\n"
            f"It is computed from `{CIDR_DE_BASE}` and the index "
            f"{serveur['index']}, through an HCL function. Copied by hand, it "
            "would be wrong at the first network change, with nothing reporting "
            "it.",
            fr=f"`{nom}` porte l'adresse {obtenue!r}, attendu {attendue!r}.\n\n"
            f"Elle se calcule depuis `{CIDR_DE_BASE}` et l'index "
            f"{serveur['index']}, par une fonction HCL. Recopiée à la main, elle "
            "serait fausse au premier changement de réseau, sans que rien ne le "
            "signale.",
        )


# --------------------------------------------------------------------------
# 3. Le fichier porte une valeur IMPOSSIBLE a ecrire de tete.
# --------------------------------------------------------------------------
def test_le_fichier_porte_les_identifiants_attribues_a_la_creation(
    applique: None,
) -> None:
    """La preuve que l'inventaire vient du STATE et non d'une saisie.

    Les adresses, on pourrait les deviner : elles suivent une regle. Les
    identifiants, non : ils sont tires a la creation. S'ils sont justes, le
    fichier a ete genere depuis ce que Terraform a reellement cree.
    """
    identifiants = _identifiants_du_state()
    assert identifiants, message(
        en="No `random_id.machine[…]` in the state: the simulated fleet was not "
        "created.",
        fr="Aucun `random_id.machine[...]` dans le state : le parc simulé n'a pas "
        "été créé.",
    )

    inventaire = _fichier()
    for nom, attendu in identifiants.items():
        role = PARC[nom]["role"]
        hote = inventaire.get(role, {}).get("hosts", {}).get(nom, {})
        assert hote.get("machine_id") == attendu, message(
            en=f"`{nom}` carries the identifier {hote.get('machine_id')!r} in "
            f"the inventory, and {attendu!r} in the state.\n\nThat value is "
            "drawn at creation: it cannot be guessed, and that is "
            "why it proves the file comes from the state.",
            fr=f"`{nom}` porte l'identifiant {hote.get('machine_id')!r} dans "
            f"l'inventaire, et {attendu!r} dans le state.\n\nCette valeur est "
            "tirée à la création : elle ne peut pas être devinée, et c'est "
            "pourquoi elle prouve que le fichier vient du state.",
        )


# --------------------------------------------------------------------------
# 4. L'output expose la STRUCTURE, pas la chaine.
# --------------------------------------------------------------------------
def test_l_output_expose_la_structure_et_non_le_texte(applique: None) -> None:
    sorties = _sorties()
    assert "inventaire" in sorties, message(
        en=f"The `inventaire` output is not declared. Present: {sorted(sorties)}.",
        fr=f"L'output `inventaire` n'est pas déclaré. Présents : {sorted(sorties)}.",
    )
    valeur = sorties["inventaire"]["value"]
    assert isinstance(valeur, dict), message(
        en=f"The output is of type {type(valeur).__name__}.\n\nA string would force "
        "every consumer to decode it again, whereas `terraform output -json` "
        "can already return a structure. Expose `local.inventaire`, not the "
        "file's content.",
        fr=f"L'output est de type {type(valeur).__name__}.\n\nUne chaîne obligerait "
        "tout consommateur à la redécoder, alors que `terraform output -json` "
        "sait déjà rendre une structure. Exposez `local.inventaire`, pas le "
        "contenu du fichier.",
    )
    assert valeur == _fichier(), message(
        en="The output and the file do not describe the same inventory.\n\nThey "
        "must come from the same source: two expressions written separately "
        "will diverge the day one of them is modified.",
        fr="L'output et le fichier ne décrivent pas le même inventaire.\n\nIls "
        "doivent venir de la même source : deux expressions écrites séparément "
        "divergeront le jour où l'une des deux sera modifiée.",
    )


# --------------------------------------------------------------------------
# 5. Juste apres l'apply, rien n'est en attente.
# --------------------------------------------------------------------------
def test_aucun_changement_juste_apres_l_apply(applique: None) -> None:
    plan = _tf("plan", "-detailed-exitcode", "-input=false", "-no-color")
    assert plan.returncode == 0, message(
        en=f"`plan -detailed-exitcode` returns {plan.returncode}, expected 0.\n"
        f"{plan.stdout[-1200:]}",
        fr=f"`plan -detailed-exitcode` rend {plan.returncode}, attendu 0.\n"
        f"{plan.stdout[-1200:]}",
    )


# --------------------------------------------------------------------------
# 6. Le fichier est GERE : il se recree, et il suit le parc.
# --------------------------------------------------------------------------
def test_le_fichier_est_gere_et_suit_les_changements_du_parc(
    applique: None,
) -> None:
    """Deux moities, et la seconde est celle qui compte.

    Qu'un fichier supprime soit recree prouve qu'il est gere. Mais un fichier
    ECRIT UNE FOIS et jamais relie au parc passerait aussi ce controle : il
    serait recree a l'identique, perime, et personne ne le saurait.

    La seconde moitie ferme cela : changer une valeur du parc doit faire bouger
    le plan. Si rien ne bouge, l'inventaire ne depend pas de ce qu'il decrit.
    """
    chemin = WORKDIR / INVENTAIRE
    chemin.unlink()
    manquant = _tf("plan", "-detailed-exitcode", "-input=false", "-no-color")
    assert manquant.returncode == 2, message(
        en=f"With the file deleted, `plan -detailed-exitcode` returns "
        f"{manquant.returncode}, expected 2.\n\nA file written outside "
        "Terraform, by a provisioner for instance, would not be managed: its "
        "disappearance would go unnoticed.",
        fr=f"Le fichier supprimé, `plan -detailed-exitcode` rend "
        f"{manquant.returncode}, attendu 2.\n\nUn fichier écrit hors de "
        "Terraform, par un provisioner par exemple, ne serait pas géré : sa "
        "disparition passerait inaperçue.",
    )
    remise = _tf("apply", "-auto-approve", "-input=false", "-no-color")
    assert remise.returncode == 0, message(
        en=f"Recreating it failed.\n{remise.stderr[-1000:]}",
        fr=f"La recréation a échoué.\n{remise.stderr[-1000:]}",
    )
    assert chemin.is_file(), message(
        en="The file was not recreated.",
        fr="Le fichier n'a pas été recréé.",
    )

    modifie = _tf(
        "plan", "-detailed-exitcode", "-input=false", "-no-color",
        "-var", 'parc={"web1":{"role":"web","index":99}}',
    )
    assert modifie.returncode == 2, message(
        en=f"With the fleet modified, `plan -detailed-exitcode` returns {modifie.returncode}, "
        "expected 2.\n\nThe inventory therefore does not depend on what it describes: it was "
        "written once, and it will go stale without anyone seeing it.",
        fr=f"Le parc modifié, `plan -detailed-exitcode` rend {modifie.returncode}, "
        "attendu 2.\n\nL'inventaire ne dépend donc pas de ce qu'il décrit : il a "
        "été écrit une fois, et il périmera sans que personne ne le voie.",
    )


# --------------------------------------------------------------------------
# 7. Les deux cotes : ce que le destroy emporte.
# --------------------------------------------------------------------------
def test_le_destroy_emporte_le_fichier_d_inventaire(applique: None) -> None:
    """Un artefact GERE disparait avec ce qui le decrivait.

    C'est la contrepartie du test precedent, et elle a un sens pratique : un
    inventaire qui survit a la destruction du parc pointe vers des machines qui
    n'existent plus. Ansible s'y connectera, echouera, et le message parlera de
    reseau.
    """
    chemin = WORKDIR / INVENTAIRE
    assert chemin.is_file(), message(
        en="The file should exist before the `destroy`.",
        fr="Le fichier devrait exister avant le `destroy`.",
    )

    detruit = _tf("destroy", "-auto-approve", "-input=false", "-no-color")
    assert detruit.returncode == 0, message(
        en=f"`terraform destroy` failed.\n{(detruit.stderr or detruit.stdout)[-1200:]}",
        fr=f"`terraform destroy` a échoué.\n{(detruit.stderr or detruit.stdout)[-1200:]}",
    )
    assert not chemin.exists(), message(
        en=f"`{INVENTAIRE}` survived the `destroy`.\n\nAn inventory outliving the "
        "fleet it describes points at machines that no longer exist. Ansible "
        "will connect to it, fail, and the message will talk about the network.",
        fr=f"`{INVENTAIRE}` a survécu au `destroy`.\n\nUn inventaire qui survit au "
        "parc qu'il décrit pointe vers des machines qui n'existent plus. Ansible "
        "s'y connectera, échouera, et le message parlera de réseau.",
    )
    assert not _gerees(), message(
        en=f"The state still carries {sorted(_gerees())} after the `destroy`.",
        fr=f"Le state porte encore {sorted(_gerees())} après le `destroy`.",
    )
