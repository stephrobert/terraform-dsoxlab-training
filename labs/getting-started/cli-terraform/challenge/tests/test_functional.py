"""test_functional.py : getting-started/cli-terraform

Six preuves, aucune ne relit le `.tf` de l'apprenant et aucune ne parse une
sortie destinee a un humain. Tout passe par des codes retour et du JSON.

Le lab pose TROIS defauts volontaires : un fichier hors format canonique, une
reference orpheline qui fait echouer `validate`, et des outputs absents. Les
trois se corrigent sans changer ce que la configuration produit, et c'est le
point : `fmt` et `validate` ne jugent pas le resultat, ils jugent la forme et la
coherence.
"""

from __future__ import annotations

import json
import subprocess
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
LAB_ID = "getting-started-cli-terraform"

ADRESSES_ATTENDUES = {
    "random_pet.nom",
    "local_file.rapport",
    "null_resource.marqueur",
}
OUTPUTS_ATTENDUS = {"nom_animal", "chemin_rapport", "nom_majuscule"}


@pytest.fixture(scope="module")
def prepared() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    init = terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
    if init.returncode != 0:
        pytest.fail(message(
            en=f"`terraform init` failed.\n{init.stderr[-1200:]}",
            fr=f"`terraform init` a échoué.\n{init.stderr[-1200:]}",
        ))
    return WORKDIR


@pytest.fixture(scope="module")
def applied(prepared: Path) -> Path:
    app = terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=prepared)
    if app.returncode != 0:
        pytest.fail(
            message(
            en="`terraform apply` failed. Does an orphan reference remain?"
            f"\n{app.stderr[-1500:]}",
            fr="`terraform apply` a échoué. Une référence orpheline subsiste-t-elle ?"
            f"\n{app.stderr[-1500:]}",
        )
        )
    return prepared


# --------------------------------------------------------------------------
# 1. Le format canonique, par le code retour de `fmt -check`.
# --------------------------------------------------------------------------
def test_tous_les_fichiers_sont_au_format_canonique(prepared: Path) -> None:
    proc = terraform("fmt", "-check", "-recursive", "-no-color", cwd=prepared)
    assert proc.returncode == 0, message(
        en="`terraform fmt -check -recursive` exits with a non-zero code: a file "
        "is outside the canonical format.\nFiles concerned:\n"
        f"{proc.stdout.strip() or '(none named, see stderr)'}\n"
        f"{proc.stderr.strip()}\n\n`terraform fmt` rewrites those files.",
        fr="`terraform fmt -check -recursive` sort en code non nul : un fichier "
        "reste hors format canonique.\nFichiers concernés :\n"
        f"{proc.stdout.strip() or '(aucun nommé, voir stderr)'}\n"
        f"{proc.stderr.strip()}\n\n`terraform fmt` réécrit ces fichiers.",
    )


# --------------------------------------------------------------------------
# 2. La coherence, par le JSON de `validate`.
# --------------------------------------------------------------------------
def test_la_configuration_est_valide(prepared: Path) -> None:
    proc = terraform("validate", "-json", cwd=prepared)
    rapport = json.loads(proc.stdout or "{}")
    erreurs = [
        d for d in rapport.get("diagnostics", [])
        if d.get("severity") == "error"
    ]
    assert rapport.get("valid") is True and rapport.get("error_count") == 0, message(
        en=f"`terraform validate` returns valid={rapport.get('valid')} and "
        f"error_count={rapport.get('error_count')}.\n"
        + "\n".join(f"  - {d.get('summary')}" for d in erreurs)
        + "\n\n`validate` does not judge what the configuration produces, it judges "
        "that it holds together: a reference to a variable that is never declared is an "
        "error, not a warning.",
        fr=f"`terraform validate` rend valid={rapport.get('valid')} et "
        f"error_count={rapport.get('error_count')}.\n"
        + "\n".join(f"  - {d.get('summary')}" for d in erreurs)
        + "\n\n`validate` ne juge pas ce que la configuration produit, il juge "
        "qu'elle se tient : une référence à une variable jamais déclarée est une "
        "erreur, pas un avertissement.",
    )


# --------------------------------------------------------------------------
# 3. L'etat contient exactement les ressources attendues.
# --------------------------------------------------------------------------
def test_le_state_porte_les_trois_ressources(applied: Path) -> None:
    liste = terraform("state", "list", cwd=applied)
    assert liste.returncode == 0, message(
        en=f"`terraform state list` failed.\n{liste.stderr}",
        fr=f"`terraform state list` a échoué.\n{liste.stderr}",
    )
    adresses = {a.strip() for a in liste.stdout.splitlines() if a.strip()}
    assert adresses == ADRESSES_ATTENDUES, message(
        en=f"The state carries {sorted(adresses)}.\nExpected: "
        f"{sorted(ADRESSES_ATTENDUES)}.\n\nThe three starting resources "
        "must remain: fixing the form and the consistency does not change what "
        "the configuration produces.",
        fr=f"Le state porte {sorted(adresses)}.\nAttendu : "
        f"{sorted(ADRESSES_ATTENDUES)}.\n\nLes trois ressources de départ "
        "doivent subsister : corriger la forme et la cohérence ne change pas ce "
        "que la configuration produit.",
    )

    # `state list` lit le meme fichier, `show -json` le RESOUT : on confirme la
    # presence dans l'etat resolu, pas seulement dans l'index.
    etat = show_json(applied)
    ressources = {
        r["address"]
        for r in etat.get("values", {}).get("root_module", {}).get("resources", [])
    }
    assert ressources >= ADRESSES_ATTENDUES, message(
        en=f"`terraform show -json` does not confirm the addresses: {sorted(ressources)}",
        fr=f"`terraform show -json` ne confirme pas les adresses : {sorted(ressources)}",
    )


# --------------------------------------------------------------------------
# 4. Les outputs existent et portent les bonnes valeurs.
# --------------------------------------------------------------------------
def test_les_outputs_exposent_les_valeurs_calculees(applied: Path) -> None:
    outputs = output_json(applied)
    manquants = OUTPUTS_ATTENDUS - set(outputs)
    assert not manquants, message(
        en=f"Missing outputs: {sorted(manquants)}. They are the ONLY channel through "
        "which the configuration exposes its values to a script: without them, "
        "one would have to read the state, which is not a contract.",
        fr=f"Outputs manquants : {sorted(manquants)}. Ils sont le SEUL canal par "
        "lequel la configuration expose ses valeurs à un script : sans eux, il "
        "faudrait lire le state, qui n'est pas un contrat.",
    )

    nom = outputs["nom_animal"]["value"]
    assert nom and "-" in nom, message(
        en=f"`nom_animal` is \"{nom}\": the name drawn by random_pet is expected.",
        fr=f"`nom_animal` vaut « {nom} » : on attend le nom tiré par random_pet.",
    )
    assert outputs["nom_majuscule"]["value"] == nom.upper(), message(
        en=f"`nom_majuscule` is \"{outputs['nom_majuscule']['value']}\" while "
        f"`nom_animal` is \"{nom}\". One must be the other in upper case.",
        fr=f"`nom_majuscule` vaut « {outputs['nom_majuscule']['value']} » alors que "
        f"`nom_animal` vaut « {nom} ». L'un doit être l'autre en majuscules.",
    )
    assert outputs["chemin_rapport"]["value"].endswith("rapport.txt"), message(
        en=f"`chemin_rapport` is \"{outputs['chemin_rapport']['value']}\": the "
        "path of the report written by local_file is expected.",
        fr=f"`chemin_rapport` vaut « {outputs['chemin_rapport']['value']} » : on "
        "attend le chemin du rapport écrit par local_file.",
    )


# --------------------------------------------------------------------------
# 5. LE test : l'expression se recalcule hors du state, et rien ne derive.
# --------------------------------------------------------------------------
def test_l_expression_se_recalcule_et_la_configuration_ne_derive_plus(
    applied: Path,
) -> None:
    """Les deux moitiees sont dans le MEME test, deliberement.

    « Le plan ne propose plus rien » est vrai de tout apply reussi, et isolee
    cette assertion ne dirait pas si les outputs disent la verite. Accolee au
    recalcul par `terraform console`, elle distingue une configuration qui
    expose ses valeurs d'une configuration qui a simplement converge.

    `terraform console` est pilote par l'entree standard : c'est le seul moyen
    de l'employer sans interaction, et le helper `terraform()` du conftest ne
    prend pas de stdin.
    """
    nom = output_json(applied)["nom_animal"]["value"]

    console = subprocess.run(
        ["terraform", "console", "-no-color"],
        cwd=applied,
        input="upper(random_pet.nom.id)\n",
        capture_output=True,
        text=True,
        check=False,
    )
    assert console.returncode == 0, message(
        en=f"`terraform console` failed.\n{console.stderr[-800:]}",
        fr=f"`terraform console` a échoué.\n{console.stderr[-800:]}",
    )
    evalue = console.stdout.strip().strip('"')
    assert evalue == nom.upper(), message(
        en=f"`terraform console` evaluates upper(random_pet.nom.id) to \"{evalue}\", "
        f"while the `nom_animal` output is \"{nom}\". Both must "
        "agree: otherwise the output does not say what the configuration computes.",
        fr=f"`terraform console` évalue upper(random_pet.nom.id) à « {evalue} », "
        f"alors que l'output `nom_animal` vaut « {nom} ». Les deux doivent "
        "concorder : sinon l'output ne dit pas ce que la configuration calcule.",
    )

    plan = terraform(
        "plan", "-no-color", "-input=false", "-detailed-exitcode", cwd=applied
    )
    assert plan.returncode != 1, message(
        en=f"`terraform plan` failed.\n{plan.stderr[-800:]}",
        fr=f"`terraform plan` a échoué.\n{plan.stderr[-800:]}",
    )
    assert plan.returncode == 0, message(
        en="`terraform plan -detailed-exitcode` returns 2: changes remain "
        "planned after the apply, so the configuration has not converged.",
        fr="`terraform plan -detailed-exitcode` rend 2 : des changements restent "
        "planifiés après l'apply, donc la configuration n'a pas convergé.",
    )
