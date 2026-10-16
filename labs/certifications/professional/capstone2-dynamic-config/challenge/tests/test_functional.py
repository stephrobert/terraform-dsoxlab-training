"""Tests fonctionnels du capstone 2 : configuration dynamique et troubleshooting.

Deux moities, et la premiere conditionne la seconde : reparer une configuration
qui ne valide pas, puis la rendre reellement pilotee par la donnee.

## Ce que « pilote par la donnee » veut dire ici

Trois entrees dans une variable doivent produire trois jeux de ressources, sans
une ligne dupliquee, et le lab le PROUVE en changeant la variable : les tests
rejouent la configuration avec une entree de plus, dans une copie, et exigent
que tout suive. Des blocs ecrits a la main ne peuvent pas suivre.

## Ce qui empeche d'etre vert sans travail

La configuration de depart ne passe meme pas `terraform init`, qui parse la
configuration et refuse la combinaison `count` + `for_each`. Et une fois les
erreurs corrigees, les valeurs « a completer » restent syntaxiquement correctes
et fonctionnellement fausses : les noms ne sont pas normalises, le manifeste
n'est pas du JSON, le `dynamic` n'existe pas.

## Une mesure faite en ecrivant le lab

Les trois erreurs ne tombent pas au meme moment. `init` echoue sur la premiere,
parce qu'il PARSE la configuration ; tant qu'elle est la, aucun provider n'est
installe et `validate` repond « Missing required provider », ce qui envoie
chercher au mauvais endroit. Les deux autres n'apparaissent qu'ensuite.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from conftest import exiger_workdir, message, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "certifications-professional-capstone2-dynamic-config"

# Les trois environnements de la variable fournie, et le nom normalise attendu
# pour chacun : minuscules, soulignes en tirets, prefixe devant.
NOMS_ATTENDUS = {
    "Dev_Local": "lab-dev-local",
    "PreProd_EU": "lab-preprod-eu",
    "PROD_EU": "lab-prod-eu",
}

# Le nombre de blocs `source` que chaque archive doit porter : le bloc fixe,
# plus un par option. Mesure sur la configuration cible.
SOURCES_ATTENDUES = {"Dev_Local": 2, "PreProd_EU": 3, "PROD_EU": 1}

TYPES_PAR_ENVIRONNEMENT = ("random_password", "random_pet", "local_file", "null_resource")


def _tf(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["terraform", *args], cwd=cwd or WORKDIR, capture_output=True, text=True, check=False
    )


@pytest.fixture(scope="module")
def joue() -> Path:
    """Initialise et applique la configuration de l'apprenant.

    Ce sont les tests qui appliquent, comme partout dans ce catalogue : le lab
    livre des fichiers, pas un etat. Consequence utile ici, `init` est le
    premier a parler, et c'est lui qui refuse la combinaison `count` +
    `for_each`.
    """
    exiger_workdir(WORKDIR, LAB_ID)

    init = _tf("init", "-input=false", "-no-color")
    assert init.returncode == 0, message(
        en="`terraform init` failed.\n\n`init` PARSES the configuration: it "
        "refuses in particular that a resource carries both `count` and "
        "`for_each`. As long as it fails, no provider is installed, and "
        "`validate` will answer \"Missing required provider\", which sends you "
        f"looking in the wrong place.\n\n{init.stderr[-1200:]}",
        fr="`terraform init` a échoué.\n\n`init` PARSE la configuration : il "
        "refuse notamment qu'une ressource porte à la fois `count` et "
        "`for_each`. Tant qu'il échoue, aucun provider n'est installé, et "
        "`validate` répondra « Missing required provider », ce qui envoie "
        f"chercher au mauvais endroit.\n\n{init.stderr[-1200:]}",
    )

    applique = _tf("apply", "-auto-approve", "-input=false", "-no-color")
    assert applique.returncode == 0, message(
        en="`terraform apply` failed.\n\nTwo frequent causes: an error "
        "that `validate` still reports, or an output exposing a sensitive "
        "value without declaring it, which Terraform refuses to plan.\n\n"
        f"{applique.stderr[-1200:]}",
        fr="`terraform apply` a échoué.\n\nDeux causes fréquentes : une erreur "
        "que `validate` signale encore, ou une sortie qui expose une valeur "
        "sensible sans le déclarer, ce que Terraform refuse de planifier.\n\n"
        f"{applique.stderr[-1200:]}",
    )
    return WORKDIR


@pytest.fixture(scope="module")
def etat(joue: Path) -> dict:
    proc = _tf("show", "-json")
    assert proc.returncode == 0, message(
        en=f"`terraform show -json` failed.\n\nThe configuration was not "
        f"applied, or it does not validate.\n{proc.stderr[-800:]}",
        fr=f"`terraform show -json` a échoué.\n\nLa configuration n'a pas été "
        f"appliquée, ou elle ne valide pas.\n{proc.stderr[-800:]}",
    )
    return json.loads(proc.stdout)


@pytest.fixture(scope="module")
def sorties(joue: Path) -> dict:
    proc = _tf("output", "-json")
    assert proc.returncode == 0, message(
        en=f"`terraform output -json` failed.\n{proc.stderr[-800:]}",
        fr=f"`terraform output -json` a échoué.\n{proc.stderr[-800:]}",
    )
    return json.loads(proc.stdout or "{}")


def _ressources(etat: dict) -> list[dict]:
    return etat.get("values", {}).get("root_module", {}).get("resources", [])


# --------------------------------------------------------------------------
# 1. La configuration valide, donc les trois erreurs sont corrigees.
# --------------------------------------------------------------------------
def test_la_configuration_valide(joue: Path) -> None:
    """`validate -json` plutot que le texte : `valid` est un booleen.

    Un message change avec les versions, pas un booleen. Et `error_count` dit
    combien il en reste, ce qu'aucune lecture du texte ne donne aussi bien.
    """
    proc = _tf("validate", "-json")
    rapport = json.loads(proc.stdout or "{}")

    assert rapport.get("valid") is True, message(
        en=f"`terraform validate` counts {rapport.get('error_count')} error(s).\n\n"
        + "\n".join(
            f"  {d.get('summary')} - {d.get('range', {}).get('filename')} "
            f"line {d.get('range', {}).get('start', {}).get('line')}"
            for d in rapport.get("diagnostics", [])
            if d.get("severity") == "error"
        )
        + "\n\nReminder: `init` fails on the `count` + `for_each` combination, "
        "and as long as it fails, `validate` answers \"Missing required provider\", "
        "which is unrelated. Fix what `init` refuses first.",
        fr=f"`terraform validate` compte {rapport.get('error_count')} erreur(s).\n\n"
        + "\n".join(
            f"  {d.get('summary')} — {d.get('range', {}).get('filename')} "
            f"ligne {d.get('range', {}).get('start', {}).get('line')}"
            for d in rapport.get("diagnostics", [])
            if d.get("severity") == "error"
        )
        + "\n\nRappel : `init` échoue sur la combinaison `count` + `for_each`, "
        "et tant qu'il échoue, `validate` répond « Missing required provider », "
        "ce qui n'a rien à voir. Corrigez d'abord ce que `init` refuse.",
    )


# --------------------------------------------------------------------------
# 2. Une entree produit un jeu complet de ressources, nommees par fonction.
# --------------------------------------------------------------------------
def test_chaque_environnement_produit_son_jeu_de_ressources(etat: dict) -> None:
    ressources = _ressources(etat)
    assert ressources, message(
        en="The state is empty: nothing was applied.",
        fr="Le state est vide : rien n'a été appliqué.",
    )

    for type_ in TYPES_PAR_ENVIRONNEMENT:
        instances = [r for r in ressources if r["type"] == type_ and r["mode"] == "managed"]
        cles = sorted(str(r.get("index")) for r in instances)
        assert cles == sorted(NOMS_ATTENDUS), message(
            en=f"`{type_}` counts {len(instances)} instance(s), indexed by "
            f"{cles}.\nOne per environment expected: {sorted(NOMS_ATTENDUS)}.\n\n"
            "The indexes must be the map's KEYS, not integers: a "
            "`count` would give 0, 1, 2, and removing an entry in the middle "
            "would shift all the following ones.",
            fr=f"`{type_}` compte {len(instances)} instance(s), indexées par "
            f"{cles}.\nAttendu une par environnement : {sorted(NOMS_ATTENDUS)}.\n\n"
            "Les index doivent être les CLÉS de la map, pas des entiers : un "
            "`count` donnerait 0, 1, 2, et une entrée retirée au milieu "
            "décalerait toutes les suivantes.",
        )


def test_les_noms_sont_normalises_par_une_fonction(etat: dict) -> None:
    """Le nom attendu ne peut pas sortir de la cle sans transformation.

    `PreProd_EU` doit devenir `lab-preprod-eu` : minuscules, souligne en tiret,
    prefixe devant. Une valeur recopiee a la main passerait ce test mais
    tomberait sur celui qui change la variable.
    """
    fichiers = {
        str(r.get("index")): r["values"]["filename"]
        for r in _ressources(etat)
        if r["type"] == "local_file" and r["mode"] == "managed"
    }

    for cle, attendu in NOMS_ATTENDUS.items():
        chemin = fichiers.get(cle, "")
        assert chemin.endswith(f"/{attendu}.json"), message(
            en=f"The manifest of `{cle}` is named {Path(chemin).name!r}, expected "
            f"{attendu + '.json'!r}.\n\nThe name is computed: lower case, "
            "underscores turned into hyphens, prefix in front, truncated to "
            "`var.longueur_nom`.",
            fr=f"Le manifeste de `{cle}` s'appelle {Path(chemin).name!r}, attendu "
            f"{attendu + '.json'!r}.\n\nLe nom se calcule : minuscules, "
            "soulignés changés en tirets, préfixe devant, tronqué à "
            "`var.longueur_nom`.",
        )


def test_le_manifeste_est_du_json_serialise_par_une_fonction(etat: dict) -> None:
    """Une chaine construite a la main produit du JSON *presque* valide.

    Une virgule en trop, un guillemet oublie dans un nom, et le document ne se
    relit plus. `jsonencode` echappe ce qu'il faut et ferme ce qu'il ouvre.
    """
    manifestes = {
        str(r.get("index")): r["values"]["content"]
        for r in _ressources(etat)
        if r["type"] == "local_file" and r["mode"] == "managed"
    }
    etiquettes = {
        str(r.get("index")): r["values"]["id"]
        for r in _ressources(etat)
        if r["type"] == "random_pet" and r["mode"] == "managed"
    }

    for cle, attendu in NOMS_ATTENDUS.items():
        brut = manifestes.get(cle, "")
        try:
            document = json.loads(brut)
        except json.JSONDecodeError as erreur:
            pytest.fail(
                message(
                en=f"The manifest of `{cle}` is not valid JSON: {erreur}\n\n"
                f"Contents: {brut[:200]!r}\n\nUse `jsonencode`, never a "
                "concatenation.",
                fr=f"Le manifeste de `{cle}` n'est pas du JSON valide : {erreur}\n\n"
                f"Contenu : {brut[:200]!r}\n\nUtilisez `jsonencode`, jamais une "
                "concaténation.",
            )
            )

        assert document.get("nom") == attendu, message(
            en=f"The manifest of `{cle}` carries the name {document.get('nom')!r}, "
            f"expected {attendu!r}.",
            fr=f"Le manifeste de `{cle}` porte le nom {document.get('nom')!r}, "
            f"attendu {attendu!r}.",
        )
        assert document.get("etiquette") == etiquettes.get(cle), message(
            en=f"The label of the manifest of `{cle}` does not match "
            f"the identifier of that environment's `random_pet`.\n\nIt must "
            "be REFERENCED, not copied: otherwise it does not follow.",
            fr=f"L'étiquette du manifeste de `{cle}` ne correspond pas à "
            f"l'identifiant du `random_pet` de cet environnement.\n\nElle doit "
            "être RÉFÉRENCÉE, pas recopiée : sinon elle ne suit pas.",
        )


# --------------------------------------------------------------------------
# 3. Le bloc dynamic, prouve par le NOMBRE de blocs produits.
# --------------------------------------------------------------------------
def test_le_dynamic_genere_un_bloc_par_option(etat: dict) -> None:
    """Le filtrage se fait dans le `for_each`, jamais dans le `content`.

    `PROD_EU` n'a aucune option : son archive ne doit porter que le bloc fixe.
    Un `if` place dans le `content` ne reduirait pas le nombre de blocs, il
    n'en changerait que le contenu.
    """
    archives = {
        str(r.get("index")): r["values"].get("source") or []
        for r in _ressources(etat)
        if r["type"] == "archive_file" and r["mode"] == "data"
    }
    assert archives, message(
        en="No `archive_file` in `mode: data` in the state. That data source "
        "is the one carrying the `dynamic` block.",
        fr="Aucune `archive_file` en `mode: data` dans le state. Cette data source "
        "est celle qui porte le bloc `dynamic`.",
    )

    for cle, attendu in SOURCES_ATTENDUES.items():
        blocs = archives.get(cle, [])
        noms = [b.get("filename") for b in blocs]
        assert len(blocs) == attendu, message(
            en=f"The archive of `{cle}` carries {len(blocs)} `source` block(s), "
            f"{attendu} expected.\nPresent: {noms}\n\nThe count is the fixed "
            "block, plus one per option of that environment.",
            fr=f"L'archive de `{cle}` porte {len(blocs)} bloc(s) `source`, "
            f"{attendu} attendu(s).\nPrésents : {noms}\n\nLe compte est le bloc "
            "fixe, plus un par option de cet environnement.",
        )


# --------------------------------------------------------------------------
# 4. Les sorties : une structure agregee, et une valeur sensible declaree.
# --------------------------------------------------------------------------
def test_les_sorties_exposent_une_structure_agregee(sorties: dict) -> None:
    environnements = sorties.get("environnements", {}).get("value")
    assert isinstance(environnements, dict), message(
        en=f"`environnements` returns {type(environnements).__name__}, a map "
        "was expected.\n\nA list of raw values cannot be queried by key.",
        fr=f"`environnements` rend {type(environnements).__name__}, une map "
        "attendue.\n\nUne liste de valeurs brutes ne s'interroge pas par clé.",
    )
    assert set(environnements) == set(NOMS_ATTENDUS.values()), message(
        en=f"`environnements` is indexed by {sorted(environnements)}.\nThe "
        f"normalised names were expected: {sorted(NOMS_ATTENDUS.values())}.",
        fr=f"`environnements` est indexé par {sorted(environnements)}.\nAttendu les "
        f"noms normalisés : {sorted(NOMS_ATTENDUS.values())}.",
    )

    attendu_options = {
        NOMS_ATTENDUS[cle]: nombre - 1 for cle, nombre in SOURCES_ATTENDUES.items()
    }
    for nom, valeur in environnements.items():
        assert valeur.get("nombre_d_options") == attendu_options[nom], message(
            en=f"`{nom}` announces {valeur.get('nombre_d_options')} option(s), "
            f"{attendu_options[nom]} expected.",
            fr=f"`{nom}` annonce {valeur.get('nombre_d_options')} option(s), "
            f"{attendu_options[nom]} attendue(s).",
        )

    assert sorties.get("nombre_archives", {}).get("value") == len(NOMS_ATTENDUS), message(
        en=f"`nombre_archives` is {sorties.get('nombre_archives', {}).get('value')}, "
        f"{len(NOMS_ATTENDUS)} expected.",
        fr=f"`nombre_archives` vaut {sorties.get('nombre_archives', {}).get('value')}, "
        f"{len(NOMS_ATTENDUS)} attendu.",
    )


def test_la_sortie_des_secrets_est_declaree_sensible(sorties: dict, joue: Path) -> None:
    """Terraform REFUSE de planifier une valeur sensible exposee sans le dire.

    Si la configuration a ete appliquee, la sortie est donc forcement marquee.
    Ce test le constate, et verifie surtout que l'affichage humain la masque :
    c'est la moitie que l'on oublie.
    """
    secrets = sorties.get("secrets")
    assert secrets is not None, message(
        en="The `secrets` output is missing.",
        fr="La sortie `secrets` est absente.",
    )
    assert secrets.get("sensitive") is True, message(
        en="`secrets` is not marked sensitive. Terraform would have refused to "
        "plan: the configuration applied is therefore not this one.",
        fr="`secrets` n'est pas marquée sensible. Terraform aurait refusé de "
        "planifier : la configuration appliquée n'est donc pas celle-là.",
    )
    assert set(secrets["value"]) == set(NOMS_ATTENDUS.values()), message(
        en=f"`secrets` is indexed by {sorted(secrets['value'])}, the normalised "
        f"names were expected.",
        fr=f"`secrets` est indexé par {sorted(secrets['value'])}, attendu les noms "
        f"normalisés.",
    )

    humaine = _tf("output", "-no-color")
    ligne = next(
        (sortie for sortie in humaine.stdout.splitlines() if sortie.startswith("secrets")),
        "",
    )
    assert "<sensitive>" in ligne, message(
        en=f"The display returns {ligne!r}: nothing is hidden on screen.",
        fr=f"L'affichage rend {ligne!r} : rien n'est masqué à l'écran.",
    )


# --------------------------------------------------------------------------
# 5. La preuve qu'aucun bloc n'est ecrit a la main : on change la variable.
# --------------------------------------------------------------------------
def test_une_entree_de_plus_produit_un_jeu_de_plus(joue: Path, tmp_path: Path) -> None:
    """Le seul test qui distingue vraiment `for_each` de trois blocs copies.

    Tout ce qui precede passerait sur une configuration ecrite a la main pour
    ces trois environnements precis. Ici la variable gagne une entree, dans une
    COPIE du repertoire, et la configuration doit suivre sans etre touchee.
    """
    copie = tmp_path / "variante"
    shutil.copytree(
        joue, copie, ignore=shutil.ignore_patterns("out", "*.tfstate*", "*.tfplan")
    )

    ajout = (
        'environnements = {\n'
        '  "Dev_Local"  = { taille = 1, options = ["trace"] }\n'
        '  "PreProd_EU" = { taille = 2, options = ["trace", "metriques"] }\n'
        '  "PROD_EU"    = { taille = 4, options = [] }\n'
        '  "Bac_A_Sable" = { taille = 8, options = ["trace", "metriques", "audit"] }\n'
        '}\n'
    )
    (copie / "variante.auto.tfvars").write_text(ajout, encoding="utf-8")

    applique = _tf("apply", "-auto-approve", "-input=false", "-no-color", cwd=copie)
    assert applique.returncode == 0, message(
        en=f"The configuration does not apply with one more entry.\n"
        f"{applique.stderr[-1000:]}",
        fr=f"La configuration ne s'applique pas avec une entrée de plus.\n"
        f"{applique.stderr[-1000:]}",
    )

    montre = _tf("show", "-json", cwd=copie)
    montre.check_returncode()
    ressources = _ressources(json.loads(montre.stdout))

    manifestes = [
        r for r in ressources if r["type"] == "local_file" and r["mode"] == "managed"
    ]
    assert len(manifestes) == 4, message(
        en=f"With four environments, the configuration produces {len(manifestes)} "
        "manifest(s).\n\nIt therefore does not follow the variable: some blocks are "
        "written by hand.",
        fr=f"Avec quatre environnements, la configuration produit {len(manifestes)} "
        "manifeste(s).\n\nElle ne suit donc pas la variable : des blocs sont "
        "écrits à la main.",
    )

    nouveau = next(
        (r for r in manifestes if str(r.get("index")) == "Bac_A_Sable"), None
    )
    assert nouveau is not None, message(
        en="The new environment produced no manifest.",
        fr="Le nouvel environnement n'a produit aucun manifeste.",
    )
    assert nouveau["values"]["filename"].endswith("/lab-bac-a-sable.json"), message(
        en=f"The new environment's manifest is named "
        f"{Path(nouveau['values']['filename']).name!r}, expected "
        "'lab-bac-a-sable.json'.\n\nThe normalisation must hold for a key "
        "you have never seen.",
        fr=f"Le manifeste du nouvel environnement s'appelle "
        f"{Path(nouveau['values']['filename']).name!r}, attendu "
        "'lab-bac-a-sable.json'.\n\nLa normalisation doit valoir pour une clé "
        "que vous n'avez jamais vue.",
    )

    archives = {
        str(r.get("index")): r["values"].get("source") or []
        for r in ressources
        if r["type"] == "archive_file" and r["mode"] == "data"
    }
    assert len(archives.get("Bac_A_Sable", [])) == 4, message(
        en=f"The new environment's archive carries "
        f"{len(archives.get('Bac_A_Sable', []))} block(s), 4 expected: the fixed "
        "block and its three options.",
        fr=f"L'archive du nouvel environnement porte "
        f"{len(archives.get('Bac_A_Sable', []))} bloc(s), 4 attendus : le bloc "
        "fixe et ses trois options.",
    )


def test_la_configuration_converge(joue: Path) -> None:
    plan = _tf("plan", "-detailed-exitcode", "-input=false", "-no-color")
    assert plan.returncode == 0, message(
        en=f"`plan -detailed-exitcode` returns {plan.returncode}, expected 0.\n"
        + plan.stdout[-800:],
        fr=f"`plan -detailed-exitcode` rend {plan.returncode}, attendu 0.\n"
        + plan.stdout[-800:],
    )
