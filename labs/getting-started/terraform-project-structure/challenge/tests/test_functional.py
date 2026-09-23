"""test_functional.py : getting-started/terraform-project-structure

Huit preuves qu'un découpage n'a rien changé, et que la précédence des valeurs
est bien celle qu'on croit.

Aucun test ne fait un `ls` pour constater qu'un fichier porte le bon nom, et
aucun ne lit les `.tf` de l'apprenant.

Le découpage se prouve autrement, et c'est le point technique du lab. Mesuré le
2026-09-23 : le JSON d'un plan ne porte AUCUN nom de fichier, contrairement à ce
qu'on pourrait croire du bloc `configuration`. En revanche, `terraform validate
-json` nomme le fichier de la déclaration en conflit. On dépose donc une sonde
qui redéclare un bloc, et le diagnostic nomme le fichier d'origine.

Le nom de la sonde compte : les `.tf` sont lus dans l'ordre alphabétique, et
c'est la SECONDE déclaration rencontrée qui est signalée. Une sonde nommée
`aaa-sonde.tf` est lue en premier, donc le diagnostic désigne l'original. Une
sonde nommée `zzz-sonde.tf` se désignerait elle-même, et ne prouverait rien.
Les deux cas ont été mesurés.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from conftest import exiger_workdir, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "getting-started-terraform-project-structure"

PLAN_REFERENCE = "plan-reference.json"
PLAN_APRES = "plan-apres.json"
MONOLITHE = "tout.tf"
SONDE = "aaa-sonde.tf"

OPERATEUR = "formateur"

# famille de bloc -> (fichier attendu, contenu de la sonde qui la redéclare)
DECOUPAGE = {
    "terraform": (
        "terraform.tf",
        'terraform {\n  required_providers {\n    random = {\n'
        '      source  = "hashicorp/random"\n      version = "~> 3.6"\n'
        "    }\n  }\n}\n",
    ),
    "provider": ("providers.tf", 'provider "random" {\n}\n'),
    "variable": (
        "variables.tf",
        'variable "projet" {\n  type    = string\n  default = "sonde"\n}\n',
    ),
    "locals": ("locals.tf", 'locals {\n  etiquette = "sonde"\n}\n'),
    "resource": (
        "main.tf",
        'resource "random_pet" "nom" {\n  length = 3\n}\n',
    ),
    "output": ("outputs.tf", 'output "projet_effectif" {\n  value = "sonde"\n}\n'),
}

# Champs qui changent d'un plan à l'autre sans que la configuration bouge.
VOLATILS = ("timestamp", "terraform_version", "format_version")


@pytest.fixture(scope="module")
def joue() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    return WORKDIR


def tf_avec_env(cwd: Path, *args: str, env: dict[str, str] | None = None):
    """Comme `terraform()`, mais en maîtrisant l'environnement.

    Nécessaire pour éprouver `TF_VAR_`, dont tout le lab consiste à situer le
    rang exact.
    """
    return subprocess.run(
        ["terraform", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, **(env or {})},
    )


def charger(cwd: Path, nom: str) -> dict:
    fichier = cwd / nom
    assert fichier.is_file(), (
        f"`{nom}` est absent. Il s'obtient avec `terraform plan -out=<fichier>` "
        f"puis `terraform show -json <fichier> > {nom}`."
    )
    try:
        return json.loads(fichier.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erreur:
        pytest.fail(f"`{nom}` n'est pas du JSON valide : {erreur}")


def changements_comparables(plan: dict) -> dict:
    """Les changements du plan, débarrassés de ce qui varie sans raison."""
    comparables = {}
    for changement in plan.get("resource_changes", []):
        variation = changement["change"]
        comparables[changement["address"]] = {
            "actions": variation["actions"],
            "after": variation.get("after"),
            "after_unknown": variation.get("after_unknown"),
        }
    return comparables


def diagnostics_avec_sonde(cwd: Path, contenu: str) -> list[dict]:
    """Dépose une sonde, relève les erreurs, et la retire quoi qu'il arrive."""
    sonde = cwd / SONDE
    sonde.write_text(contenu, encoding="utf-8")
    try:
        brut = terraform("validate", "-json", cwd=cwd).stdout
        rapport = json.loads(brut) if brut.strip() else {}
        return [d for d in rapport.get("diagnostics", []) if d.get("severity") == "error"]
    finally:
        sonde.unlink(missing_ok=True)


# --------------------------------------------------------------------------
# 1. Le plan de référence a bien été figé AVANT le découpage.
# --------------------------------------------------------------------------
def test_le_plan_de_reference_existe_et_annonce_les_creations(joue: Path) -> None:
    plan = charger(joue, PLAN_REFERENCE)
    changements = changements_comparables(plan)
    assert changements, (
        f"`{PLAN_REFERENCE}` n'annonce aucun changement de ressource. Il a été "
        "produit après l'application, et ne peut plus servir de référence."
    )
    creations = {a for a, c in changements.items() if c["actions"] == ["create"]}
    assert creations == set(changements), (
        f"Le plan de référence annonce autre chose que des créations : "
        f"{ {a: c['actions'] for a, c in changements.items()} }.\n\nIl doit être "
        "figé avant tout `apply`, sur un répertoire sans state."
    )


# --------------------------------------------------------------------------
# 2. Chaque famille de blocs vit bien dans son fichier.
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("famille", "fichier", "contenu"),
    [(f, *v) for f, v in DECOUPAGE.items()],
    ids=list(DECOUPAGE),
)
def test_chaque_famille_de_blocs_vit_dans_son_fichier(
    joue: Path, famille: str, fichier: str, contenu: str
) -> None:
    erreurs = diagnostics_avec_sonde(joue, contenu)
    assert erreurs, (
        f"Redéclarer un bloc `{famille}` ne provoque aucune erreur. La "
        "déclaration d'origine est donc absente : le découpage a perdu quelque "
        "chose en route."
    )
    nomme = {(d.get("range") or {}).get("filename") for d in erreurs}
    assert fichier in nomme, (
        f"La déclaration `{famille}` d'origine se trouve dans {sorted(nomme)}, "
        f"attendu `{fichier}`.\n\nTerraform lit tous les `.tf` comme un seul "
        "document : le découpage n'a aucun effet fonctionnel, mais c'est ce qui "
        "rend un projet lisible."
    )


# --------------------------------------------------------------------------
# 3. Le monolithe a disparu, et la configuration reste valide.
# --------------------------------------------------------------------------
def test_le_monolithe_a_disparu_et_la_configuration_est_valide(joue: Path) -> None:
    assert not (joue / MONOLITHE).exists(), (
        f"`{MONOLITHE}` est toujours là. Comme Terraform lit TOUS les `.tf`, il "
        "redéclare en double chacun des blocs que vous venez de déplacer."
    )

    rapport = json.loads(terraform("validate", "-json", cwd=joue).stdout)
    assert rapport.get("valid") is True, (
        "`terraform validate` échoue :\n"
        + "\n".join(
            f"  - {d.get('summary')} ({(d.get('range') or {}).get('filename')})"
            for d in rapport.get("diagnostics", [])
        )
    )


# --------------------------------------------------------------------------
# 4. Le plan n'a pas bougé d'un iota.
# --------------------------------------------------------------------------
def test_le_plan_est_strictement_identique_apres_decoupage(joue: Path) -> None:
    avant = charger(joue, PLAN_REFERENCE)
    apres = charger(joue, PLAN_APRES)

    for champ in VOLATILS:
        avant.pop(champ, None)
        apres.pop(champ, None)

    changements_avant = changements_comparables(avant)
    changements_apres = changements_comparables(apres)

    adresses_avant, adresses_apres = set(changements_avant), set(changements_apres)
    assert adresses_avant == adresses_apres, (
        f"Le découpage a changé l'ensemble des adresses.\n"
        f"Disparues : {sorted(adresses_avant - adresses_apres)}\n"
        f"Apparues : {sorted(adresses_apres - adresses_avant)}\n\n"
        "Un bloc a été perdu ou dupliqué pendant le déplacement."
    )
    for adresse in sorted(adresses_avant):
        assert changements_avant[adresse] == changements_apres[adresse], (
            f"{adresse} ne planifie plus la même chose après découpage.\n"
            f"Avant : {changements_avant[adresse]}\n"
            f"Après : {changements_apres[adresse]}\n\n"
            "Déplacer un bloc ne doit RIEN changer. Une valeur a été retouchée "
            "au passage."
        )


# --------------------------------------------------------------------------
# 5. Un `*.auto.tfvars` l'emporte sur `terraform.tfvars`.
# --------------------------------------------------------------------------
def test_le_fichier_auto_l_emporte_sur_terraform_tfvars(joue: Path) -> None:
    sorties = json.loads(
        tf_avec_env(joue, "output", "-json").stdout
    )
    assert "environnement_effectif" in sorties, (
        f"La sortie `environnement_effectif` est absente : {sorted(sorties)}."
    )
    assert sorties["environnement_effectif"]["value"] == "production", (
        f"`environnement` vaut {sorties['environnement_effectif']['value']!r}.\n\n"
        "`terraform.tfvars` la pose à `recette`, `env.auto.tfvars` à "
        "`production`. Les fichiers `*.auto.tfvars` sont chargés APRÈS, et "
        "l'emportent donc."
    )


# --------------------------------------------------------------------------
# 6. `terraform.tfvars` l'emporte sur `TF_VAR_`.
# --------------------------------------------------------------------------
def test_le_fichier_l_emporte_sur_la_variable_d_environnement(joue: Path) -> None:
    proc = tf_avec_env(
        joue,
        "apply", "-auto-approve", "-input=false", "-no-color",
        "-var", f"operateur={OPERATEUR}",
        env={"TF_VAR_projet": "depuis-l-environnement"},
    )
    assert proc.returncode == 0, f"L'application a échoué.\n{proc.stderr[-1500:]}"

    sorties = json.loads(tf_avec_env(joue, "output", "-json").stdout)
    assert sorties["projet_effectif"]["value"] == "catalogue", (
        f"`projet` vaut {sorties['projet_effectif']['value']!r} alors que "
        "`TF_VAR_projet` était posée dans l'environnement.\n\n"
        "`terraform.tfvars` la pose à `catalogue` et doit l'emporter : "
        "`TF_VAR_` se situe juste au-dessus du `default`, et en dessous de tout "
        "fichier de valeurs. C'est le rang le plus souvent mal placé."
    )


# --------------------------------------------------------------------------
# 7. `-var` l'emporte sur tout le reste.
# --------------------------------------------------------------------------
def test_la_ligne_de_commande_l_emporte_sur_toutes_les_autres_sources(
    joue: Path,
) -> None:
    proc = tf_avec_env(
        joue,
        "apply", "-auto-approve", "-input=false", "-no-color",
        "-var", f"operateur={OPERATEUR}",
        "-var", "projet=depuis-la-ligne-de-commande",
        "-var", "environnement=depuis-la-ligne-de-commande",
        env={"TF_VAR_projet": "depuis-l-environnement"},
    )
    assert proc.returncode == 0, f"L'application a échoué.\n{proc.stderr[-1500:]}"

    sorties = json.loads(tf_avec_env(joue, "output", "-json").stdout)
    for nom in ("projet_effectif", "environnement_effectif"):
        assert sorties[nom]["value"] == "depuis-la-ligne-de-commande", (
            f"`{nom}` vaut {sorties[nom]['value']!r} alors que `-var` a été "
            "fourni. La ligne de commande gagne toujours, y compris contre un "
            "`*.auto.tfvars`."
        )

    # On remet la configuration dans l'état que les fichiers décrivent, pour
    # que le test suivant mesure la convergence et non les restes de celui-ci.
    remise = tf_avec_env(
        joue,
        "apply", "-auto-approve", "-input=false", "-no-color",
        "-var", f"operateur={OPERATEUR}",
    )
    assert remise.returncode == 0, f"La remise en état a échoué.\n{remise.stderr[-1200:]}"


# --------------------------------------------------------------------------
# 8. Les deux côtés : la convergence, et ce que le disque porte vraiment.
# --------------------------------------------------------------------------
def test_la_configuration_converge_et_le_disque_porte_les_valeurs_effectives(
    joue: Path,
) -> None:
    plan = tf_avec_env(
        joue,
        "plan", "-detailed-exitcode", "-input=false", "-no-color",
        "-var", f"operateur={OPERATEUR}",
    )
    assert plan.returncode == 0, (
        f"`plan -detailed-exitcode` rend {plan.returncode}, attendu 0.\n"
        "0 = diff vide, 1 = erreur, 2 = un changement reste en attente.\n"
        f"{plan.stdout[-1200:]}"
    )

    # L'autre moitié, et elle n'est vraie qu'après le travail : le fichier
    # écrit porte les valeurs EFFECTIVES, celles qui ont gagné la précédence,
    # et non les `default` déclarés dans les variables.
    rapport = joue / "rapport.txt"
    assert rapport.is_file(), (
        "`rapport.txt` est absent : la configuration n'a jamais été appliquée."
    )
    contenu = rapport.read_text(encoding="utf-8")
    for attendu in ("projet : catalogue", "environnement : production",
                    f"operateur : {OPERATEUR}", "etiquette : catalogue-production"):
        assert attendu in contenu, (
            f"Le rapport ne contient pas {attendu!r}.\nIl contient :\n{contenu}\n\n"
            "Le fichier sur le disque doit porter les valeurs qui ont "
            "réellement gagné, pas les `default` déclarés."
        )
    for interdit in ("projet : atelier", "environnement : dev",
                     "environnement : recette"):
        assert interdit not in contenu, (
            f"Le rapport contient {interdit!r} : une valeur perdante s'est "
            "propagée jusqu'au disque."
        )
