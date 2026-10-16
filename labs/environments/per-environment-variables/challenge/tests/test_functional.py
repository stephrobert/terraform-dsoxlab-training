"""Tests fonctionnels du lab « quelle valeur gagne, et comment le prouver ».

Ces tests ne lisent JAMAIS les `.tf` ni les `.tfvars` de l'apprenant. Ils
pilotent Terraform et lisent ce que Terraform ecrit : la cle `variables` de la
representation JSON du plan, qui expose la valeur REELLEMENT retenue pour
chaque variable racine. C'est la seule preuve recevable de precedence, et elle
ne demande aucun apply.

Faits verifies sur Terraform 1.15.4, hors ligne, providers `local` et `random` :

- l'echelle de precedence, du plus faible au plus fort : `default`, puis
  `TF_VAR_`, puis `terraform.tfvars`, puis `terraform.tfvars.json`, puis les
  `*.auto.tfvars` en ordre LEXICAL, puis `-var` et `-var-file` ;
- `-var` et `-var-file` sont au MEME rang : c'est l'ordre des arguments qui
  tranche, pas une hierarchie. Mesure : `-var disk_size_gb=16` place AVANT
  `-var-file=envs/prod.tfvars` retient 8, et l'inverse retient 16 ;
- une cle mal orthographiee dans un fichier de valeurs ne fait pas echouer le
  plan : elle produit `Warning: Value for undeclared variable` et laisse la
  variable a son `default`.
"""

import json
import os
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, message, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "environments-per-environment-variables"

ENVIRONNEMENTS = {
    "dev": {"disk_size_gb": 4, "retention_jours": 7},
    "staging": {"disk_size_gb": 4, "retention_jours": 14},
    "prod": {"disk_size_gb": 8, "retention_jours": 90},
}

COMMUNES = ("base_image", "tags")


# ── Helpers ─────────────────────────────────────────────────────────────────


def _terraform(
    *args: str, cwd: Path, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Comme le helper du conftest, mais capable d'injecter des `TF_VAR_`."""
    return subprocess.run(
        ["terraform", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def _plan(
    rep: Path, *options: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return _terraform(
        "plan", "-input=false", "-no-color", *options, cwd=rep, env=env
    )


def _variables_retenues(
    rep: Path, *options: str, env: dict[str, str] | None = None
) -> dict:
    """Valeurs REELLEMENT retenues, lues dans le JSON du plan."""
    with tempfile.TemporaryDirectory() as tmp:
        plan = Path(tmp) / "tfplan"
        fait = _terraform(
            "plan", f"-out={plan}", "-input=false", "-no-color", *options,
            cwd=rep, env=env,
        )
        if fait.returncode != 0:
            pytest.fail(
                message(
                en=f"`terraform plan {' '.join(options)}` fails (code "
                f"{fait.returncode}). Are the blocks of main.tf, outputs.tf and the "
                f"types in variables.tf all completed?\n"
                f"{(fait.stderr or fait.stdout)[-1200:]}",
                fr=f"`terraform plan {' '.join(options)}` échoue (code "
                f"{fait.returncode}). Les blocs de main.tf, outputs.tf et les "
                f"types de variables.tf sont-ils tous complétés ?\n"
                f"{(fait.stderr or fait.stdout)[-1200:]}",
            )
            )
        montre = _terraform("show", "-json", str(plan), cwd=rep, env=env)
        montre.check_returncode()
        brut = json.loads(montre.stdout)
    return {
        nom: valeur.get("value")
        for nom, valeur in (brut.get("variables") or {}).items()
    }


def _avec_tf_var(**valeurs: str) -> dict[str, str]:
    """Environnement courant PLUS les `TF_VAR_` demandees.

    On herite de l'environnement au lieu d'en fabriquer un minimal : sans le
    PATH reel, `terraform` lui-meme devient introuvable.
    """
    env = os.environ.copy()
    env.update({f"TF_VAR_{nom}": valeur for nom, valeur in valeurs.items()})
    return env


def _nombre(valeur: object) -> object:
    """Normalise un nombre rendu par le JSON du plan.

    Mesure sur 1.15.4 : une valeur passee par `-var` sur la ligne de commande
    reste une CHAINE dans `.variables` du JSON du plan (`'16'`), alors que la
    meme valeur venue d'un `.tfvars` typé y figure en nombre (`8`). Terraform
    la convertit bien selon le `type` declare pour l'utiliser, mais la
    representation du plan expose l'entree brute.
    """
    if isinstance(valeur, str):
        try:
            return int(valeur)
        except ValueError:
            return valeur
    return valeur


def _copie(source: Path, cible: Path) -> Path:
    """Copie du travail, `.terraform` compris, pour ne rien abimer."""
    shutil.copytree(source, cible, symlinks=True)
    return cible


@pytest.fixture(scope="module")
def travail() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    # Les plugins ne sont pas le travail de l'apprenant : on les remet si
    # besoin, sans rien changer d'autre.
    if not (WORKDIR / ".terraform" / "providers").is_dir():
        init = _terraform("init", "-input=false", "-no-color", cwd=WORKDIR)
        if init.returncode != 0:
            pytest.fail(message(
                en=f"`terraform init` fails.\n{init.stderr[-900:]}",
                fr=f"`terraform init` échoue.\n{init.stderr[-900:]}",
            ))
    yield WORKDIR


# ── 1. Le garde-fou ─────────────────────────────────────────────────────────


def test_le_garde_fou_est_retabli(travail: Path) -> None:
    """Sans option, le plan doit REFUSER de tourner : aucun environnement choisi."""
    fait = _plan(travail)
    sortie = fait.stdout + fait.stderr
    assert fait.returncode != 0, message(
        en="`terraform plan` with no option at all SUCCEEDS. An implicit source "
        "therefore still provides a value to the variables that have no "
        "`default`, and the guard in variables.tf no longer protects anything. "
        "Which file is loaded without being asked for?",
        fr="`terraform plan` sans aucune option RÉUSSIT. Une source implicite "
        "fournit donc encore une valeur aux variables qui n'ont pas de "
        "`default`, et le garde-fou de variables.tf ne protège plus rien. "
        "Quel fichier est chargé sans qu'on le demande ?",
    )
    assert "No value for required variable" in sortie, message(
        en="The plan fails, but not for the right reason. Expected "
        "\"No value for required variable\".\n" + sortie[-900:],
        fr="Le plan échoue, mais pas pour la bonne raison. Attendu "
        "« No value for required variable ».\n" + sortie[-900:],
    )
    assert "env_name" in sortie, message(
        en="The error does not mention `env_name`.\n" + sortie[-900:],
        fr="L'erreur ne mentionne pas `env_name`.\n" + sortie[-900:],
    )


# ── 2. Les types et les blocs completes ─────────────────────────────────────


def test_les_types_communs_sont_declares(travail: Path) -> None:
    """`base_image` et `tags` etaient laisses en `???` : le plan doit passer."""
    retenues = _variables_retenues(travail, "-var-file=envs/dev.tfvars")

    for nom in COMMUNES:
        assert nom in retenues, message(
            en=f"The variable `{nom}` is not resolved.",
            fr=f"La variable `{nom}` n'est pas résolue.",
        )

    assert isinstance(retenues["base_image"], str) and retenues["base_image"], message(
        en=f"`base_image` is {retenues['base_image']!r}, a non-empty string was expected.",
        fr=f"`base_image` vaut {retenues['base_image']!r}, attendu une chaîne non vide.",
    )
    assert isinstance(retenues["tags"], dict) and retenues["tags"], message(
        en=f"`tags` is {retenues['tags']!r}, a non-empty map was expected.",
        fr=f"`tags` vaut {retenues['tags']!r}, attendu une map non vide.",
    )
    for valeur in retenues["tags"].values():
        assert isinstance(valeur, str), message(
            en=f"`tags` carries a non-textual value ({valeur!r}): the expected "
            "type is a map of strings.",
            fr=f"`tags` porte une valeur non textuelle ({valeur!r}) : le type "
            "attendu est une map de chaînes.",
        )


# ── 3. Les trois environnements ─────────────────────────────────────────────


def test_chaque_environnement_a_ses_valeurs(travail: Path) -> None:
    for env, attendu in ENVIRONNEMENTS.items():
        retenues = _variables_retenues(travail, f"-var-file=envs/{env}.tfvars")
        assert retenues.get("env_name") == env, message(
            en=f"envs/{env}.tfvars gives env_name = "
            f"{retenues.get('env_name')!r}, expected {env!r}.",
            fr=f"envs/{env}.tfvars donne env_name = "
            f"{retenues.get('env_name')!r}, attendu {env!r}.",
        )
        for cle, valeur in attendu.items():
            assert retenues.get(cle) == valeur, message(
                en=f"envs/{env}.tfvars gives {cle} = {retenues.get(cle)!r}, "
                f"expected {valeur!r}.",
                fr=f"envs/{env}.tfvars donne {cle} = {retenues.get(cle)!r}, "
                f"attendu {valeur!r}.",
            )


def test_staging_ne_declenche_plus_d_avertissement(travail: Path) -> None:
    """Une cle mal orthographiee ne casse rien : elle se signale, sans plus."""
    fait = _plan(travail, "-var-file=envs/staging.tfvars")
    sortie = fait.stdout + fait.stderr
    assert "Value for undeclared variable" not in sortie, message(
        en="envs/staging.tfvars still triggers \"Value for undeclared "
        "variable\". One of its keys matches no `variable` block, "
        "and Terraform ignores it WITHOUT failing: the variable keeps its "
        "`default`. The key is to be fixed, not worked around.\n"
        + sortie[-700:],
        fr="envs/staging.tfvars déclenche encore « Value for undeclared "
        "variable ». Une de ses clés ne correspond à aucun bloc `variable`, "
        "et Terraform l'ignore SANS échouer : la variable reste à son "
        "`default`. La clé se corrige, elle ne se contourne pas.\n"
        + sortie[-700:],
    )


# ── 4. Les valeurs communes ne sont pas recopiees ───────────────────────────


def test_les_valeurs_communes_viennent_du_fichier_auto_charge(
    travail: Path, tmp_path: Path
) -> None:
    """Preuve par la privation : sans le fichier commun, les valeurs disparaissent.

    Si l'apprenant avait recopie `base_image` et `tags` dans chaque fichier
    d'environnement, les retirer du fichier auto charge ne changerait rien.
    """
    copie = _copie(travail, tmp_path / "sans-commun")
    commun = copie / "commun.auto.tfvars"
    assert commun.is_file(), message(
        en="commun.auto.tfvars has disappeared: it is the file carrying the values "
        "shared by every environment.",
        fr="commun.auto.tfvars a disparu : c'est lui qui porte les valeurs "
        "partagées par tous les environnements.",
    )
    commun.unlink()

    fait = _plan(copie, "-var-file=envs/prod.tfvars")
    sortie = fait.stdout + fait.stderr
    if fait.returncode != 0:
        assert "No value for required variable" in sortie, sortie[-700:]
        return  # les valeurs communes venaient bien du seul fichier auto charge

    retenues = _variables_retenues(copie, "-var-file=envs/prod.tfvars")
    for nom in COMMUNES:
        reference = _variables_retenues(travail, "-var-file=envs/prod.tfvars")[nom]
        assert retenues.get(nom) != reference, message(
            en=f"`{nom}` keeps its value although commun.auto.tfvars was "
            "removed: it is therefore copied into the environment "
            "files. Shared values are declared once, "
            "in the auto-loaded file.",
            fr=f"`{nom}` garde sa valeur alors que commun.auto.tfvars a été "
            "retiré : elle est donc recopiée dans les fichiers "
            "d'environnement. Les valeurs partagées se déclarent une seule "
            "fois, dans le fichier auto chargé.",
        )


# ── 5. La precedence, mesuree ───────────────────────────────────────────────


def test_une_variable_d_environnement_bat_le_default(travail: Path) -> None:
    env = _avec_tf_var(
        env_name="depuis-l-environnement",
        disk_size_gb="3",
        retention_jours="42",
    )
    retenues = _variables_retenues(travail, env=env)
    assert _nombre(retenues.get("retention_jours")) == 42, message(
        en="TF_VAR_retention_jours=42 does not win over the `default` of the "
        f"`variable` block: the value kept is {retenues.get('retention_jours')!r}.",
        fr="TF_VAR_retention_jours=42 ne l'emporte pas sur le `default` du bloc "
        f"`variable` : la valeur retenue est {retenues.get('retention_jours')!r}.",
    )
    assert retenues.get("env_name") == "depuis-l-environnement", message(
        en="TF_VAR_env_name is not taken into account although no values "
        "file is loaded.",
        fr="TF_VAR_env_name n'est pas pris en compte alors qu'aucun fichier de "
        "valeurs n'est chargé.",
    )


def test_une_variable_d_environnement_perd_contre_un_fichier(travail: Path) -> None:
    env = _avec_tf_var(env_name="depuis-l-environnement")
    retenues = _variables_retenues(travail, "-var-file=envs/prod.tfvars", env=env)
    assert retenues.get("env_name") == "prod", message(
        en="With TF_VAR_env_name exported AND -var-file=envs/prod.tfvars, the "
        f"value kept is {retenues.get('env_name')!r}. An environment "
        "variable loses against the slightest values file.",
        fr="Avec TF_VAR_env_name exporté ET -var-file=envs/prod.tfvars, la "
        f"valeur retenue est {retenues.get('env_name')!r}. Une variable "
        "d'environnement perd contre le moindre fichier de valeurs.",
    )


def test_l_ordre_des_options_tranche(travail: Path) -> None:
    """`-var` et `-var-file` sont au meme rang : l'ordre decide."""
    avant = _variables_retenues(
        travail, "-var", "disk_size_gb=16", "-var-file=envs/prod.tfvars"
    )
    assert _nombre(avant.get("disk_size_gb")) == 8, message(
        en="`-var disk_size_gb=16` placed BEFORE `-var-file=envs/prod.tfvars` "
        f"gives {avant.get('disk_size_gb')!r}, expected 8: the file is "
        "applied afterwards, so it wins.",
        fr="`-var disk_size_gb=16` placé AVANT `-var-file=envs/prod.tfvars` "
        f"donne {avant.get('disk_size_gb')!r}, attendu 8 : le fichier est "
        "appliqué après, donc il gagne.",
    )

    apres = _variables_retenues(
        travail, "-var-file=envs/prod.tfvars", "-var", "disk_size_gb=16"
    )
    assert _nombre(apres.get("disk_size_gb")) == 16, message(
        en="`-var disk_size_gb=16` placed AFTER the file gives "
        f"{apres.get('disk_size_gb')!r}, expected 16.",
        fr="`-var disk_size_gb=16` placé APRÈS le fichier donne "
        f"{apres.get('disk_size_gb')!r}, attendu 16.",
    )


def test_un_auto_tfvars_lexicalement_posterieur_gagne(
    travail: Path, tmp_path: Path
) -> None:
    copie = _copie(travail, tmp_path / "lexical")
    (copie / "zz-surcharge.auto.tfvars").write_text(
        'base_image = "image-de-surcharge.qcow2"\n', encoding="utf-8"
    )
    retenues = _variables_retenues(copie, "-var-file=envs/prod.tfvars")
    assert retenues.get("base_image") == "image-de-surcharge.qcow2", message(
        en="An auto-loaded file lexically later than commun.auto.tfvars "
        f"does not win: base_image is {retenues.get('base_image')!r}. "
        "The *.auto.tfvars apply in lexical order, and the last one wins.",
        fr="Un fichier auto chargé lexicalement postérieur à commun.auto.tfvars "
        f"ne l'emporte pas : base_image vaut {retenues.get('base_image')!r}. "
        "Les *.auto.tfvars s'appliquent en ordre lexical, le dernier gagne.",
    )


def test_un_type_complexe_se_passe_en_ligne_de_commande(travail: Path) -> None:
    retenues = _variables_retenues(
        travail,
        "-var-file=envs/prod.tfvars",
        "-var",
        'tags={"equipe":"astreinte","criticite":"haute"}',
    )
    assert retenues.get("tags") == {
        "equipe": "astreinte",
        "criticite": "haute",
    }, message(
        en=f"`tags` is {retenues.get('tags')!r} after an override by `-var` "
        "in JSON syntax. A complex type passes fine on the command line.",
        fr=f"`tags` vaut {retenues.get('tags')!r} après une surcharge par `-var` "
        "en syntaxe JSON. Un type complexe se passe bien en ligne de commande.",
    )


# ── 6. L'etat applique ──────────────────────────────────────────────────────


def test_l_etat_applique_est_celui_de_prod(travail: Path) -> None:
    montre = _terraform("show", "-json", cwd=travail)
    montre.check_returncode()
    etat = json.loads(montre.stdout)
    racine = etat.get("values", {}).get("root_module", {})
    ressources = {r["address"]: r for r in racine.get("resources", [])}

    assert "local_file.profil" in ressources, message(
        en="`local_file.profil` is absent from the state: the prod environment "
        "was not applied (`terraform apply -var-file=envs/prod.tfvars`).",
        fr="`local_file.profil` est absent de l'état : l'environnement prod "
        "n'a pas été appliqué (`terraform apply -var-file=envs/prod.tfvars`).",
    )
    profil = ressources["local_file.profil"]["values"]
    assert profil["filename"].endswith("profils/prod.json"), message(
        en=f"The profile produced is {profil['filename']!r}, a path "
        "ending in profils/prod.json was expected.",
        fr=f"Le profil produit est {profil['filename']!r}, attendu un chemin "
        "finissant par profils/prod.json.",
    )

    contenu = json.loads(profil["content"])
    assert contenu.get("disque_go") == 8, message(
        en=f"The profile records disque_go = {contenu.get('disque_go')!r}, "
        "expected 8.",
        fr=f"Le profil consigne disque_go = {contenu.get('disque_go')!r}, "
        "attendu 8.",
    )
    assert contenu.get("retention") == 90, message(
        en=f"The profile records retention = {contenu.get('retention')!r}, "
        "expected 90.",
        fr=f"Le profil consigne retention = {contenu.get('retention')!r}, "
        "attendu 90.",
    )
    assert contenu.get("environnement") == "prod", message(
        en=f"The profile records environnement = {contenu.get('environnement')!r}.",
        fr=f"Le profil consigne environnement = {contenu.get('environnement')!r}.",
    )

    sorties = etat["values"]["outputs"]
    assert sorties["taille_octets"]["value"] == 8 * 1024 * 1024 * 1024, message(
        en=f"`taille_octets` is {sorties['taille_octets']['value']!r}, expected "
        f"{8 * 1024 * 1024 * 1024} (8 GB converted to bytes).",
        fr=f"`taille_octets` vaut {sorties['taille_octets']['value']!r}, attendu "
        f"{8 * 1024 * 1024 * 1024} (8 Go convertis en octets).",
    )
    assert str(sorties["profil"]["value"]).endswith("profils/prod.json"), message(
        en=f"`profil` is {sorties['profil']['value']!r}.",
        fr=f"`profil` vaut {sorties['profil']['value']!r}.",
    )


def test_le_plan_de_prod_ne_propose_plus_rien(travail: Path) -> None:
    fait = _plan(travail, "-detailed-exitcode", "-var-file=envs/prod.tfvars")
    assert fait.returncode == 0, message(
        en=f"`plan -detailed-exitcode -var-file=envs/prod.tfvars` returns "
        f"{fait.returncode}, expected 0. The prod environment has not converged."
        f"\n{(fait.stdout + fait.stderr)[-700:]}",
        fr=f"`plan -detailed-exitcode -var-file=envs/prod.tfvars` rend "
        f"{fait.returncode}, attendu 0. L'environnement prod n'a pas convergé."
        f"\n{(fait.stdout + fait.stderr)[-700:]}",
    )
