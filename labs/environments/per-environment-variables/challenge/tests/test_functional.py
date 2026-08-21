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

from conftest import exiger_workdir, workdir_lab

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
                f"`terraform plan {' '.join(options)}` echoue (code "
                f"{fait.returncode}). Les blocs de main.tf, outputs.tf et les "
                f"types de variables.tf sont-ils tous completes ?\n"
                f"{(fait.stderr or fait.stdout)[-1200:]}"
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
            pytest.fail(f"`terraform init` echoue.\n{init.stderr[-900:]}")
    yield WORKDIR


# ── 1. Le garde-fou ─────────────────────────────────────────────────────────


def test_le_garde_fou_est_retabli(travail: Path) -> None:
    """Sans option, le plan doit REFUSER de tourner : aucun environnement choisi."""
    fait = _plan(travail)
    sortie = fait.stdout + fait.stderr
    assert fait.returncode != 0, (
        "`terraform plan` sans aucune option REUSSIT. Une source implicite "
        "fournit donc encore une valeur aux variables qui n'ont pas de "
        "`default`, et le garde-fou de variables.tf ne protege plus rien. "
        "Quel fichier est charge sans qu'on le demande ?"
    )
    assert "No value for required variable" in sortie, (
        "Le plan echoue, mais pas pour la bonne raison. Attendu "
        "« No value for required variable ».\n" + sortie[-900:]
    )
    assert "env_name" in sortie, (
        "L'erreur ne mentionne pas `env_name`.\n" + sortie[-900:]
    )


# ── 2. Les types et les blocs completes ─────────────────────────────────────


def test_les_types_communs_sont_declares(travail: Path) -> None:
    """`base_image` et `tags` etaient laisses en `???` : le plan doit passer."""
    retenues = _variables_retenues(travail, "-var-file=envs/dev.tfvars")

    for nom in COMMUNES:
        assert nom in retenues, f"La variable `{nom}` n'est pas resolue."

    assert isinstance(retenues["base_image"], str) and retenues["base_image"], (
        f"`base_image` vaut {retenues['base_image']!r}, attendu une chaine non vide."
    )
    assert isinstance(retenues["tags"], dict) and retenues["tags"], (
        f"`tags` vaut {retenues['tags']!r}, attendu une map non vide."
    )
    for valeur in retenues["tags"].values():
        assert isinstance(valeur, str), (
            f"`tags` porte une valeur non textuelle ({valeur!r}) : le type "
            "attendu est une map de chaines."
        )


# ── 3. Les trois environnements ─────────────────────────────────────────────


def test_chaque_environnement_a_ses_valeurs(travail: Path) -> None:
    for env, attendu in ENVIRONNEMENTS.items():
        retenues = _variables_retenues(travail, f"-var-file=envs/{env}.tfvars")
        assert retenues.get("env_name") == env, (
            f"envs/{env}.tfvars donne env_name = "
            f"{retenues.get('env_name')!r}, attendu {env!r}."
        )
        for cle, valeur in attendu.items():
            assert retenues.get(cle) == valeur, (
                f"envs/{env}.tfvars donne {cle} = {retenues.get(cle)!r}, "
                f"attendu {valeur!r}."
            )


def test_staging_ne_declenche_plus_d_avertissement(travail: Path) -> None:
    """Une cle mal orthographiee ne casse rien : elle se signale, sans plus."""
    fait = _plan(travail, "-var-file=envs/staging.tfvars")
    sortie = fait.stdout + fait.stderr
    assert "Value for undeclared variable" not in sortie, (
        "envs/staging.tfvars declenche encore « Value for undeclared "
        "variable ». Une de ses cles ne correspond a aucun bloc `variable`, "
        "et Terraform l'ignore SANS echouer : la variable reste a son "
        "`default`. La cle se corrige, elle ne se contourne pas.\n"
        + sortie[-700:]
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
    assert commun.is_file(), (
        "commun.auto.tfvars a disparu : c'est lui qui porte les valeurs "
        "partagees par tous les environnements."
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
        assert retenues.get(nom) != reference, (
            f"`{nom}` garde sa valeur alors que commun.auto.tfvars a ete "
            "retire : elle est donc recopiee dans les fichiers "
            "d'environnement. Les valeurs partagees se declarent une seule "
            "fois, dans le fichier auto charge."
        )


# ── 5. La precedence, mesuree ───────────────────────────────────────────────


def test_une_variable_d_environnement_bat_le_default(travail: Path) -> None:
    env = _avec_tf_var(
        env_name="depuis-l-environnement",
        disk_size_gb="3",
        retention_jours="42",
    )
    retenues = _variables_retenues(travail, env=env)
    assert _nombre(retenues.get("retention_jours")) == 42, (
        "TF_VAR_retention_jours=42 ne l'emporte pas sur le `default` du bloc "
        f"`variable` : la valeur retenue est {retenues.get('retention_jours')!r}."
    )
    assert retenues.get("env_name") == "depuis-l-environnement", (
        "TF_VAR_env_name n'est pas pris en compte alors qu'aucun fichier de "
        "valeurs n'est charge."
    )


def test_une_variable_d_environnement_perd_contre_un_fichier(travail: Path) -> None:
    env = _avec_tf_var(env_name="depuis-l-environnement")
    retenues = _variables_retenues(travail, "-var-file=envs/prod.tfvars", env=env)
    assert retenues.get("env_name") == "prod", (
        "Avec TF_VAR_env_name exporte ET -var-file=envs/prod.tfvars, la "
        f"valeur retenue est {retenues.get('env_name')!r}. Une variable "
        "d'environnement perd contre le moindre fichier de valeurs."
    )


def test_l_ordre_des_options_tranche(travail: Path) -> None:
    """`-var` et `-var-file` sont au meme rang : l'ordre decide."""
    avant = _variables_retenues(
        travail, "-var", "disk_size_gb=16", "-var-file=envs/prod.tfvars"
    )
    assert _nombre(avant.get("disk_size_gb")) == 8, (
        "`-var disk_size_gb=16` place AVANT `-var-file=envs/prod.tfvars` "
        f"donne {avant.get('disk_size_gb')!r}, attendu 8 : le fichier est "
        "applique apres, donc il gagne."
    )

    apres = _variables_retenues(
        travail, "-var-file=envs/prod.tfvars", "-var", "disk_size_gb=16"
    )
    assert _nombre(apres.get("disk_size_gb")) == 16, (
        "`-var disk_size_gb=16` place APRES le fichier donne "
        f"{apres.get('disk_size_gb')!r}, attendu 16."
    )


def test_un_auto_tfvars_lexicalement_posterieur_gagne(
    travail: Path, tmp_path: Path
) -> None:
    copie = _copie(travail, tmp_path / "lexical")
    (copie / "zz-surcharge.auto.tfvars").write_text(
        'base_image = "image-de-surcharge.qcow2"\n', encoding="utf-8"
    )
    retenues = _variables_retenues(copie, "-var-file=envs/prod.tfvars")
    assert retenues.get("base_image") == "image-de-surcharge.qcow2", (
        "Un fichier auto charge lexicalement posterieur a commun.auto.tfvars "
        f"ne l'emporte pas : base_image vaut {retenues.get('base_image')!r}. "
        "Les *.auto.tfvars s'appliquent en ordre lexical, le dernier gagne."
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
    }, (
        f"`tags` vaut {retenues.get('tags')!r} apres une surcharge par `-var` "
        "en syntaxe JSON. Un type complexe se passe bien en ligne de commande."
    )


# ── 6. L'etat applique ──────────────────────────────────────────────────────


def test_l_etat_applique_est_celui_de_prod(travail: Path) -> None:
    montre = _terraform("show", "-json", cwd=travail)
    montre.check_returncode()
    etat = json.loads(montre.stdout)
    racine = etat.get("values", {}).get("root_module", {})
    ressources = {r["address"]: r for r in racine.get("resources", [])}

    assert "local_file.profil" in ressources, (
        "`local_file.profil` est absent de l'etat : l'environnement prod "
        "n'a pas ete applique (`terraform apply -var-file=envs/prod.tfvars`)."
    )
    profil = ressources["local_file.profil"]["values"]
    assert profil["filename"].endswith("profils/prod.json"), (
        f"Le profil produit est {profil['filename']!r}, attendu un chemin "
        "finissant par profils/prod.json."
    )

    contenu = json.loads(profil["content"])
    assert contenu.get("disque_go") == 8, (
        f"Le profil consigne disque_go = {contenu.get('disque_go')!r}, "
        "attendu 8."
    )
    assert contenu.get("retention") == 90, (
        f"Le profil consigne retention = {contenu.get('retention')!r}, "
        "attendu 90."
    )
    assert contenu.get("environnement") == "prod", (
        f"Le profil consigne environnement = {contenu.get('environnement')!r}."
    )

    sorties = etat["values"]["outputs"]
    assert sorties["taille_octets"]["value"] == 8 * 1024 * 1024 * 1024, (
        f"`taille_octets` vaut {sorties['taille_octets']['value']!r}, attendu "
        f"{8 * 1024 * 1024 * 1024} (8 Go convertis en octets)."
    )
    assert str(sorties["profil"]["value"]).endswith("profils/prod.json"), (
        f"`profil` vaut {sorties['profil']['value']!r}."
    )


def test_le_plan_de_prod_ne_propose_plus_rien(travail: Path) -> None:
    fait = _plan(travail, "-detailed-exitcode", "-var-file=envs/prod.tfvars")
    assert fait.returncode == 0, (
        f"`plan -detailed-exitcode -var-file=envs/prod.tfvars` rend "
        f"{fait.returncode}, attendu 0. L'environnement prod n'a pas converge."
        f"\n{(fait.stdout + fait.stderr)[-700:]}"
    )
