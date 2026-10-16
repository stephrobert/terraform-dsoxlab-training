"""Tests fonctionnels du lab « le plan dit ce que l'apply fera ».

Un ASG qui reference `version = "$Latest"` ne declenche JAMAIS d'instance
refresh, et un `create_before_destroy` pose sur le launch template ne protege
rien du tout. Ce lab fait lire ces deux verites dans le plan converti en JSON,
sans jamais appeler AWS.

Aucun `apply`, aucun emulateur. Le provider est neutralise, un state est fourni
comme socle deja en service, et tous les plans se lancent avec `-refresh=false`.
Seul le premier `terraform init` a besoin du reseau.

Formes MESUREES avant d'ecrire une assertion, sur Terraform 1.16.1 avec
hashicorp/aws 6.0.0 :
- le template rend `["update"]` : changer `image_id` cree une version, cela ne
  remplace pas le template ;
- l'ASG rend `["create", "delete"]` DANS CET ORDRE, avec
  `replace_paths = [["name"]]` ;
- `after_unknown.launch_template` vaut `[{"name": true, "version": true}]` ;
- `random_integer.suffixe` est remplace, `replace_paths = [["keepers"]]`.
"""

from __future__ import annotations

import json
import subprocess

import pytest

from conftest import exiger_workdir, message, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "aws-launch-template-autoscaling"

TEMPLATE = "aws_launch_template.socle"
GRAPPE = "aws_autoscaling_group.grappe"
SUFFIXE = "random_integer.suffixe"
NOM_INITIAL = "grappe-app-742"


def _tf(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["terraform", *args], cwd=WORKDIR, capture_output=True, text=True, check=False
    )


@pytest.fixture(scope="module")
def plan() -> dict:
    """Le plan, ecrit en binaire puis relu en JSON par l'outil.

    `-refresh=false` est indispensable : sans lui, Terraform tenterait de
    joindre AWS pour rafraichir le state fourni, et echouerait sur des
    identifiants factices.
    """
    exiger_workdir(WORKDIR, LAB_ID)

    init = _tf("init", "-input=false", "-no-color")
    if init.returncode != 0:
        pytest.fail(message(
            en=f"`terraform init` failed:\n{init.stderr[-1200:]}",
            fr=f"`terraform init` a échoué :\n{init.stderr[-1200:]}",
        ))

    produit = _tf(
        "plan", "-refresh=false", "-input=false", "-no-color", "-out=verification.tfplan"
    )
    if produit.returncode != 0:
        pytest.fail(
            message(
            en="`terraform plan` failed. Are there leftover `???`?\n"
            f"{(produit.stderr or produit.stdout)[-1800:]}",
            fr="`terraform plan` a échoué. Des `???` subsistent-ils ?\n"
            f"{(produit.stderr or produit.stdout)[-1800:]}",
        )
        )

    montre = _tf("show", "-json", "verification.tfplan")
    if montre.returncode != 0:
        pytest.fail(message(
            en=f"`show -json` of the plan failed:\n{montre.stderr[-800:]}",
            fr=f"`show -json` du plan a échoué :\n{montre.stderr[-800:]}",
        ))
    return json.loads(montre.stdout)


def _changement(plan: dict, adresse: str) -> dict:
    for c in plan.get("resource_changes", []):
        if c["address"] == adresse:
            return c
    pytest.fail(
        message(
        en=f"{adresse} does not appear in the plan. Addresses present: "
        f"{[c['address'] for c in plan.get('resource_changes', [])]}",
        fr=f"{adresse} n'apparaît pas dans le plan. Adresses présentes : "
        f"{[c['address'] for c in plan.get('resource_changes', [])]}",
    )
    )


# --------------------------------------------------------------------------
# 1. Changer l'AMI MET A JOUR le template, cela ne le remplace pas.
# --------------------------------------------------------------------------
def test_le_template_est_mis_a_jour_et_non_remplace(plan: dict) -> None:
    actions = _changement(plan, TEMPLATE)["change"]["actions"]
    assert actions == ["update"], message(
        en=f"{TEMPLATE} announces {actions}, expected `['update']`.\n\nA launch "
        "template is VERSIONED: changing its `image_id` creates a new "
        "version and leaves the previous ones in place. Replacing it would destroy "
        "the history, and everything referencing an older version.",
        fr=f"{TEMPLATE} annonce {actions}, attendu `['update']`.\n\nUn launch "
        "template est VERSIONNÉ : changer son `image_id` crée une nouvelle "
        "version et laisse les précédentes en place. Le remplacer détruirait "
        "l'historique, et tout ce qui référence une ancienne version.",
    )


# --------------------------------------------------------------------------
# 2. La version referencee est INCONNUE au plan. C'est tout le sujet.
# --------------------------------------------------------------------------
def test_la_version_referencee_est_calculee_a_l_apply(plan: dict) -> None:
    inconnus = _changement(plan, GRAPPE)["change"].get("after_unknown") or {}
    blocs = inconnus.get("launch_template") or []
    assert blocs, message(
        en="The ASG's `launch_template` block carries no unknown field.\n\n"
        "That is the signature of a `version = \"$Latest\"`: that string is "
        "KNOWN at plan time, so nothing moves and the ASG stays "
        "`no-op`. The group will never be refreshed, and nobody will "
        "notice for a long time. Omitting the argument is no better: it "
        "falls back on `\"$Default\"`, with the same effect.",
        fr="Le bloc `launch_template` de l'ASG ne porte aucun champ inconnu.\n\n"
        "C'est la signature d'un `version = \"$Latest\"` : cette chaîne est "
        "CONNUE au moment du plan, donc rien ne bouge et l'ASG reste en "
        "`no-op`. Le groupe ne sera jamais rafraîchi, et personne ne s'en "
        "apercevra avant longtemps. Omettre l'argument ne vaut pas mieux : il "
        "retombe sur `\"$Default\"`, avec le même effet.",
    )
    assert blocs[0].get("version") is True, message(
        en=f"The `version` field of the `launch_template` block is {blocs[0].get('version')!r} "
        "in `after_unknown`, expected `true`.\n\nIt must be COMPUTED at "
        "apply time: the version targeted does not exist yet at plan time, "
        "since it is the template's update that will create it.",
        fr=f"Le champ `version` du bloc `launch_template` vaut {blocs[0].get('version')!r} "
        "dans `after_unknown`, attendu `true`.\n\nIl doit être CALCULÉ à "
        "l'apply : la version visée n'existe pas encore au moment du plan, "
        "puisque c'est la mise à jour du template qui la créera.",
    )


# --------------------------------------------------------------------------
# 3. Le groupe est cree AVANT d'etre detruit. L'ordre est le test.
# --------------------------------------------------------------------------
def test_le_groupe_est_cree_avant_d_etre_detruit(plan: dict) -> None:
    actions = _changement(plan, GRAPPE)["change"]["actions"]
    assert actions == ["create", "delete"], message(
        en=f"{GRAPPE} announces {actions}, expected `['create', 'delete']`.\n\n"
        "The ORDER of the two values is exactly what distinguishes "
        "`create_before_destroy` from the default behaviour. `['delete', "
        "'create']` opens a window with ZERO instances on a group in service, "
        "and the instruction forbids it.",
        fr=f"{GRAPPE} annonce {actions}, attendu `['create', 'delete']`.\n\n"
        "L'ORDRE des deux valeurs est exactement ce qui distingue "
        "`create_before_destroy` du comportement par défaut. `['delete', "
        "'create']` ouvre une fenêtre à ZÉRO instance sur un groupe en service, "
        "et la consigne l'interdit.",
    )


# --------------------------------------------------------------------------
# 4. Le remplacement est declenche par le NOM.
# --------------------------------------------------------------------------
def test_le_chemin_de_remplacement_designe_le_nom(plan: dict) -> None:
    chemins = _changement(plan, GRAPPE)["change"].get("replace_paths") or []
    assert ["name"] in chemins, message(
        en=f"The plan declares the replacement paths {chemins}, expected "
        "`[['name']]`.\n\nIt is the name change that forces the group's "
        "replacement. If the replacement came from elsewhere, the switch would "
        "not be the one we think.",
        fr=f"Le plan déclare les chemins de remplacement {chemins}, attendu "
        "`[['name']]`.\n\nC'est le changement de nom qui force le remplacement "
        "du groupe. Si le remplacement venait d'ailleurs, la bascule ne serait "
        "pas celle qu'on croit.",
    )


# --------------------------------------------------------------------------
# 5. Le nouveau nom est inconnu, donc necessairement different.
# --------------------------------------------------------------------------
def test_le_nom_du_nouveau_groupe_est_inconnu_au_plan(plan: dict) -> None:
    changement = _changement(plan, GRAPPE)["change"]
    inconnus = changement.get("after_unknown") or {}
    assert inconnus.get("name") is True, message(
        en=f"The `name` field is {inconnus.get('name')!r} in `after_unknown`, "
        "expected `true`.\n\nA fixed name would be KNOWN at plan time, and Terraform "
        "would then see two groups bearing the same name during the switch. AWS "
        "refuses that.",
        fr=f"Le champ `name` vaut {inconnus.get('name')!r} dans `after_unknown`, "
        "attendu `true`.\n\nUn nom figé serait CONNU au plan, et Terraform "
        "verrait alors deux groupes portant le même nom pendant la bascule. AWS "
        "le refuse.",
    )
    apres = (changement.get("after") or {}).get("name")
    assert apres != NOM_INITIAL, message(
        en=f"The new group would still carry {NOM_INITIAL!r}. The two "
        "generations would collide.",
        fr=f"Le nouveau groupe porterait encore {NOM_INITIAL!r}. Les deux "
        "générations entreraient en collision.",
    )


# --------------------------------------------------------------------------
# 6. Le suffixe est retire quand le template change, et pas autrement.
# --------------------------------------------------------------------------
def test_le_suffixe_est_regenere_avec_le_template(plan: dict) -> None:
    changement = _changement(plan, SUFFIXE)["change"]
    assert "create" in changement["actions"] and "delete" in changement["actions"], message(
        en=f"{SUFFIXE} announces {changement['actions']}, a replacement was expected.\n\n"
        "Without `keepers`, that number NEVER changes: the group's name stays "
        "fixed, and the naming convention is of no use.",
        fr=f"{SUFFIXE} annonce {changement['actions']}, attendu un remplacement.\n\n"
        "Sans `keepers`, ce nombre ne change JAMAIS : le nom du groupe reste "
        "figé, et la convention de nommage ne sert à rien.",
    )
    chemins = changement.get("replace_paths") or []
    assert ["keepers"] in chemins, message(
        en=f"The suffix's replacement comes from {chemins}, expected `[['keepers']]`."
        "\n\nThe suffix must depend on the TEMPLATE, to change exactly when "
        "the template changes, and never otherwise.",
        fr=f"Le remplacement du suffixe vient de {chemins}, attendu `[['keepers']]`."
        "\n\nLe suffixe doit dépendre du TEMPLATE, pour changer exactement quand "
        "le template change, et jamais autrement.",
    )


# --------------------------------------------------------------------------
# 7. Les deux garde-fous de la bascule, et ils vont par paire.
# --------------------------------------------------------------------------
def test_les_preferences_interdisent_de_descendre_et_autorisent_a_depasser(
    plan: dict,
) -> None:
    apres = _changement(plan, GRAPPE)["change"].get("after") or {}
    rafraichissements = apres.get("instance_refresh") or []
    assert rafraichissements, message(
        en="The ASG declares no `instance_refresh`: nothing will replace the "
        "existing instances when the template changes.",
        fr="L'ASG ne déclare aucun `instance_refresh` : rien ne remplacera les "
        "instances existantes quand le template changera.",
    )
    preferences = (rafraichissements[0].get("preferences") or [{}])[0]

    minimum = preferences.get("min_healthy_percentage")
    assert minimum == 100, message(
        en=f"`min_healthy_percentage` is {minimum!r}, expected 100.\n\nAny "
        "lower value allows the fleet to drop below its target "
        "capacity during the switch, which the instruction forbids.",
        fr=f"`min_healthy_percentage` vaut {minimum!r}, attendu 100.\n\nToute "
        "valeur inférieure autorise la grappe à descendre sous sa capacité "
        "cible pendant la bascule, ce que la consigne interdit.",
    )

    maximum = preferences.get("max_healthy_percentage")
    assert maximum is not None and maximum > 100, message(
        en=f"`max_healthy_percentage` is {maximum!r}, a value above 100 was "
        "expected.\n\nIt is the guard one forgets, and without it the "
        "first is untenable: its default value is 100, which forbids "
        "precisely the margin needed to start an instance BEFORE stopping "
        "one. The two go in pairs.",
        fr=f"`max_healthy_percentage` vaut {maximum!r}, attendu une valeur "
        "supérieure à 100.\n\nC'est le garde-fou qu'on oublie, et sans lui le "
        "premier est intenable : sa valeur par défaut vaut 100, ce qui interdit "
        "précisément la marge nécessaire pour démarrer une instance AVANT d'en "
        "arrêter une. Les deux vont par paire.",
    )


# --------------------------------------------------------------------------
# 8. Les deux cotes : le plan annonce vraiment quelque chose.
# --------------------------------------------------------------------------
def test_le_plan_annonce_des_changements_et_rien_n_a_ete_neutralise(
    plan: dict,
) -> None:
    """Le test qui empeche de faire passer les autres en ne faisant rien.

    Chacun des sept controles precedents porte sur la FORME d'un changement.
    Une configuration videe de sa substance, ou un state trafique, pourrait
    theoriquement les contourner en ne produisant aucun changement du tout.

    Ce dernier exige donc que le plan ne soit pas vide, par le code de sortie de
    `plan -detailed-exitcode`, dont la valeur 2 est ici l'ATTENDU et non un
    defaut. Et il verifie que les trois ressources du socle sont toujours la.
    """
    detaille = _tf("plan", "-refresh=false", "-detailed-exitcode", "-input=false",
                   "-no-color")
    assert detaille.returncode == 2, message(
        en=f"`plan -refresh=false -detailed-exitcode` returns {detaille.returncode}, "
        "expected 2.\n\nHere, 2 is SUCCESS: it signals pending "
        "changes. A 0 would mean that the new AMI triggers nothing, hence "
        f"that the lab no longer measures anything.\n{detaille.stdout[-1000:]}",
        fr=f"`plan -refresh=false -detailed-exitcode` rend {detaille.returncode}, "
        "attendu 2.\n\nIci, 2 est le SUCCÈS : il signale des changements en "
        "attente. Un 0 signifierait que la nouvelle AMI ne déclenche rien, donc "
        f"que le lab ne mesure plus rien.\n{detaille.stdout[-1000:]}",
    )

    adresses = {c["address"] for c in plan.get("resource_changes", [])}
    assert adresses == {TEMPLATE, GRAPPE, SUFFIXE}, message(
        en=f"The plan carries {sorted(adresses)}, exactly "
        f"{sorted({TEMPLATE, GRAPPE, SUFFIXE})} expected.\n\nA resource was added "
        "to or removed from the configuration: the base provided is no longer the one "
        "the other checks describe.",
        fr=f"Le plan porte {sorted(adresses)}, attendu exactement "
        f"{sorted({TEMPLATE, GRAPPE, SUFFIXE})}.\n\nUne ressource a été ajoutée "
        "ou retirée de la configuration : le socle fourni n'est plus celui que "
        "les autres contrôles décrivent.",
    )
