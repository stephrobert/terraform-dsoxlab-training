"""Tests fonctionnels du lab « une chaine non interactive ».

Les tests n'ouvrent ni `main.tf` ni `pipeline.sh`, et ne lisent aucune sortie
destinee a un humain. Chaque affirmation de l'apprenant est REJOUEE : les tests
relancent eux-memes les commandes et comparent au releve de `preuves/`.

Faits verifies sur Terraform 1.15.4, hors ligne (`local`, `random`, et le
provider `terraform` integre) :

- `plan -detailed-exitcode` rend 2 avant l'apply, 0 apres, 1 sur configuration
  cassee ; `fmt -check` rend 3 sur un fichier mal indente, jamais 1 ;
- `plan -input=false` sans valeur de variable ECHOUE aussitot, il n'attend pas ;
- a l'apply d'un plan SAUVEGARDE, seule une tentative de changer une variable
  leve une erreur : `-destroy`, `-refresh=false` et `-target` sont acceptes et
  ignores, si bien qu'un apply `-destroy` sur un plan de creation CREE ;
- un verrou concurrent fait echouer immediatement avec le defaut, et patienter
  avec `-lock-timeout` ;
- le secret d'une variable `sensitive` sort en clair de `show -json <plan>`.
"""

import json
import os
import shutil
import subprocess
import threading
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from conftest import exiger_workdir, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "environments-terraform-in-automation"

PREUVES = (
    "chaine.json", "codes.json", "prompt.json",
    "plan_fige.json", "verrou.json", "fuite.json",
)
# Sentinelle : le test vérifie que cette chaîne n'apparaît NULLE PART dans les
# traces du pipeline. C'est un leurre posé par le lab, pas un secret.
SECRET = "SECRET-EN-CLAIR-12345"  # noqa: S105
DUREE_MINIMALE_APPLY = 10.0


# ── Helpers ─────────────────────────────────────────────────────────────────


def _tf(*args: str, cwd: Path) -> tuple[subprocess.CompletedProcess[str], float]:
    debut = time.monotonic()
    fait = subprocess.run(
        ["terraform", *args], cwd=cwd, capture_output=True, text=True,
        env=os.environ.copy(),
        check=False,
    )
    return fait, time.monotonic() - debut


def _preuve(travail: Path, nom: str) -> dict:
    chemin = travail / "preuves" / nom
    if not chemin.is_file():
        pytest.fail(
            f"preuves/{nom} est absent. Ce lab demande de CONSIGNER ce que "
            "Terraform repond, pas seulement de le lire."
        )
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erreur:
        pytest.fail(f"preuves/{nom} n'est pas du JSON valide : {erreur}")


def _copie(source: Path, cible: Path) -> Path:
    shutil.copytree(source, cible, symlinks=True)
    return cible


@pytest.fixture(scope="module")
def travail() -> Iterator[Path]:
    exiger_workdir(WORKDIR, LAB_ID)
    if not (WORKDIR / ".terraform" / "providers").is_dir():
        init, _ = _tf("init", "-input=false", "-no-color", cwd=WORKDIR)
        if init.returncode != 0:
            pytest.fail(f"`terraform init` echoue.\n{init.stderr[-800:]}")
    yield WORKDIR


# ── 1. La chaine a tourne, et l'etat est celui attendu ──────────────────────


def test_les_six_preuves_existent(travail: Path) -> None:
    manquantes = [n for n in PREUVES if not (travail / "preuves" / n).is_file()]
    assert not manquantes, f"Preuves absentes : {manquantes}"


def test_l_etat_final_porte_les_trois_ressources(travail: Path) -> None:
    montre, _ = _tf("show", "-json", cwd=travail)
    if montre.returncode != 0:
        pytest.fail(f"`terraform show -json` echoue.\n{montre.stderr[-600:]}")
    etat = json.loads(montre.stdout or "{}")
    gerees = [
        r for r in etat.get("values", {}).get("root_module", {}).get("resources", [])
        if r.get("mode") == "managed"
    ]
    adresses = sorted(r["address"] for r in gerees)
    assert len(gerees) == 3, (
        f"L'etat porte {len(gerees)} ressource(s) : {adresses}. Attendu 3, "
        "c'est-a-dire une configuration reellement appliquee."
    )


def test_la_chaine_a_releve_cinq_codes(travail: Path) -> None:
    chaine = _preuve(travail, "chaine.json")
    attendues = {"fmt", "init", "validate", "plan", "apply"}
    assert set(chaine) == attendues, (
        f"chaine.json porte {sorted(chaine)}, attendu {sorted(attendues)}."
    )
    # `plan -detailed-exitcode` rend 2 quand il reste des changements : c'est un
    # succes, pas une erreur. Les quatre autres etapes doivent rendre 0.
    for etape in ("fmt", "init", "validate", "apply"):
        assert chaine[etape] == 0, (
            f"chaine.json donne {etape} = {chaine[etape]}, attendu 0."
        )
    assert chaine["plan"] in (0, 2), (
        f"chaine.json donne plan = {chaine['plan']}, attendu 0 ou 2. Un 1 "
        "signale une erreur de planification, pas des changements."
    )


# ── 2. Les codes de retour, rejoues ─────────────────────────────────────────


def test_les_trois_codes_du_plan_sont_exacts(travail: Path, tmp_path: Path) -> None:
    releve = _preuve(travail, "codes.json")

    apres, _ = _tf("plan", "-input=false", "-detailed-exitcode", "-no-color",
                   cwd=travail)
    assert apres.returncode == 0, (
        f"Apres apply, `plan -detailed-exitcode` rend {apres.returncode}, "
        "attendu 0 : la configuration n'a pas converge."
    )
    assert releve.get("plan_apres_apply") == 0, (
        f"codes.json annonce plan_apres_apply = {releve.get('plan_apres_apply')}, "
        "mesure 0."
    )

    # Avant apply : on rejoue sur une copie vierge de tout etat.
    vierge = _copie(travail, tmp_path / "vierge")
    (vierge / "terraform.tfstate").unlink(missing_ok=True)
    shutil.rmtree(vierge / "produits", ignore_errors=True)
    avant, _ = _tf("plan", "-input=false", "-detailed-exitcode", "-no-color",
                   cwd=vierge)
    assert avant.returncode == 2, (
        f"Sans etat, `plan -detailed-exitcode` rend {avant.returncode}, "
        "attendu 2."
    )
    assert releve.get("plan_avant_apply") == 2, (
        f"codes.json annonce plan_avant_apply = "
        f"{releve.get('plan_avant_apply')}, mesure 2."
    )

    # Configuration cassee : code 1.
    cassee = _copie(travail, tmp_path / "cassee")
    (cassee / "casse.tf").write_text(
        'resource "local_file" {\n  broken\n}\n', encoding="utf-8"
    )
    fait, _ = _tf("plan", "-input=false", "-detailed-exitcode", "-no-color",
                  cwd=cassee)
    assert fait.returncode == 1, (
        f"Sur configuration cassee, le plan rend {fait.returncode}, attendu 1."
    )
    assert releve.get("plan_config_cassee") == 1, (
        f"codes.json annonce plan_config_cassee = "
        f"{releve.get('plan_config_cassee')}, mesure 1."
    )


def test_le_code_de_fmt_check_est_trois(travail: Path, tmp_path: Path) -> None:
    releve = _preuve(travail, "codes.json")
    copie = _copie(travail, tmp_path / "fmt")
    (copie / "mal_indente.tf").write_text(
        'variable "vilain" {\n        type = string\n  default="x"\n}\n',
        encoding="utf-8",
    )
    fait, _ = _tf("fmt", "-check", "-recursive", "-no-color", cwd=copie)
    assert fait.returncode == 3, (
        f"`fmt -check` rend {fait.returncode} sur un fichier mal indente, "
        "attendu 3."
    )
    assert releve.get("fmt_check_mal_indente") == 3, (
        f"codes.json annonce fmt_check_mal_indente = "
        f"{releve.get('fmt_check_mal_indente')}, mesure 3. Ce n'est pas 1 : un "
        "pipeline qui teste `-eq 1` ne detecte donc jamais rien."
    )


# ── 3. L'invite : echec immediat, pas attente ───────────────────────────────


def test_le_plan_sans_variable_echoue_aussitot(travail: Path, tmp_path: Path) -> None:
    releve = _preuve(travail, "prompt.json")
    copie = _copie(travail, tmp_path / "prompt")
    for parasite in ("terraform.tfvars", "terraform.tfvars.json"):
        (copie / parasite).unlink(missing_ok=True)
    for auto in copie.glob("*.auto.tfvars"):
        auto.unlink()

    fait, duree = _tf("plan", "-input=false", "-no-color", cwd=copie)
    assert fait.returncode == 1, (
        f"Sans valeur pour `environnement`, le plan rend {fait.returncode}, "
        "attendu 1."
    )
    assert "No value for required variable" in (fait.stdout + fait.stderr), (
        "Le plan echoue, mais pas sur l'absence de valeur de variable."
    )
    assert duree < 5.0, (
        f"Le plan a mis {duree:.1f}s : il ne devrait PAS attendre."
    )
    assert releve.get("code") == 1, (
        f"prompt.json annonce code = {releve.get('code')}, mesure 1."
    )
    attente = releve.get("attente_secondes")
    assert isinstance(attente, (int, float)) and attente < 5.0, (
        f"prompt.json annonce attente_secondes = {attente}. La commande "
        "n'attend pas : elle echoue tout de suite."
    )


# ── 4. Ce qu'un plan sauvegarde fige VRAIMENT ───────────────────────────────


def test_le_sort_des_quatre_options_est_exact(travail: Path, tmp_path: Path) -> None:
    releve = _preuve(travail, "plan_fige.json")
    attendu = {
        "var": "erreur",
        "destroy": "ignore",
        "refresh_false": "ignore",
        "target": "ignore",
    }
    assert set(releve) == set(attendu), (
        f"plan_fige.json porte {sorted(releve)}, attendu {sorted(attendu)}."
    )

    options = {
        "var": ["-var", "environnement=autre"],
        "destroy": ["-destroy"],
        "refresh_false": ["-refresh=false"],
        "target": ["-target=random_pet.nom"],
    }
    for cle, args in options.items():
        # CHAQUE option est essayee sur un plan FRAIS, dans une copie vierge :
        # enchainer les essais rendrait le plan perime et Terraform repondrait
        # « Saved plan is stale » sans jamais juger l'option elle-meme.
        copie = _copie(travail, tmp_path / f"fige-{cle}")
        (copie / "terraform.tfstate").unlink(missing_ok=True)
        shutil.rmtree(copie / "produits", ignore_errors=True)
        planifie, _ = _tf("plan", "-out=essai.tfplan", "-input=false", "-no-color",
                          cwd=copie)
        assert planifie.returncode == 0, (
            f"Impossible d'enregistrer un plan pour l'essai {cle}.\n"
            f"{planifie.stderr[-500:]}"
        )
        fait, _ = _tf("apply", "-input=false", "-no-color", *args, "essai.tfplan",
                      cwd=copie)
        mesure = "erreur" if fait.returncode != 0 else "ignore"
        assert mesure == attendu[cle], (
            f"L'option {args} sur un plan sauvegarde donne {mesure!r}, "
            f"mesure attendue {attendu[cle]!r}."
        )
        assert releve[cle] == attendu[cle], (
            f"plan_fige.json annonce {cle} = {releve[cle]!r}, mesure "
            f"{attendu[cle]!r}. Rappel : seule une tentative de changer une "
            "VARIABLE leve une erreur ; les modes de planification sont "
            "acceptes et ignores."
        )


# ── 5. Le verrou ────────────────────────────────────────────────────────────


def test_le_verrou_est_mesure(travail: Path, tmp_path: Path) -> None:
    releve = _preuve(travail, "verrou.json")
    assert releve.get("defaut_secondes") == 0, (
        f"verrou.json annonce defaut_secondes = {releve.get('defaut_secondes')}. "
        "Le defaut de `-lock-timeout` est 0s : la commande n'attend pas."
    )

    copie = _copie(travail, tmp_path / "verrou")
    (copie / "terraform.tfstate").unlink(missing_ok=True)
    shutil.rmtree(copie / "produits", ignore_errors=True)

    resultat: dict = {}

    def apply_lent() -> None:
        fait, duree = _tf("apply", "-auto-approve", "-input=false", "-no-color",
                          cwd=copie)
        resultat["code"] = fait.returncode
        resultat["duree"] = duree

    fil = threading.Thread(target=apply_lent)
    fil.start()
    time.sleep(4.0)  # on laisse l'apply prendre le verrou

    concurrent, _ = _tf("plan", "-input=false", "-no-color", cwd=copie)
    avec_delai, _ = _tf("plan", "-input=false", "-no-color", "-lock-timeout=90s",
                        cwd=copie)
    fil.join()

    assert resultat.get("duree", 0) >= DUREE_MINIMALE_APPLY, (
        f"L'apply n'a dure que {resultat.get('duree', 0):.1f}s. Il doit durer "
        f"au moins {DUREE_MINIMALE_APPLY:.0f}s pour qu'un verrou soit "
        "observable : la commande de `local-exec` est-elle assez lente ?"
    )
    assert concurrent.returncode == 1, (
        f"Le plan concurrent rend {concurrent.returncode}, attendu 1 : avec le "
        "defaut, il doit echouer immediatement sur le verrou."
    )
    assert "state lock" in (concurrent.stdout + concurrent.stderr).lower(), (
        "Le plan concurrent echoue, mais pas sur le verrou d'etat."
    )
    assert avec_delai.returncode == 0, (
        f"Avec `-lock-timeout`, le plan rend {avec_delai.returncode}, attendu "
        "0 : il doit patienter puis aboutir."
    )
    assert releve.get("code_avec_defaut") == 1, (
        f"verrou.json annonce code_avec_defaut = "
        f"{releve.get('code_avec_defaut')}, mesure 1."
    )
    assert releve.get("code_avec_delai") == 0, (
        f"verrou.json annonce code_avec_delai = "
        f"{releve.get('code_avec_delai')}, mesure 0."
    )


# ── 6. La fuite, et le .gitignore ───────────────────────────────────────────


def test_le_chemin_de_la_fuite_est_exact(travail: Path, tmp_path: Path) -> None:
    releve = _preuve(travail, "fuite.json")
    chemin = str(releve.get("chemin", "")).strip()
    assert chemin, "fuite.json ne designe aucun chemin."

    copie = _copie(travail, tmp_path / "fuite")
    (copie / "terraform.tfstate").unlink(missing_ok=True)
    shutil.rmtree(copie / "produits", ignore_errors=True)
    planifie, _ = _tf("plan", "-out=fuite.tfplan", "-input=false", "-no-color",
                      cwd=copie)
    assert planifie.returncode == 0, "Impossible d'enregistrer le plan d'essai."

    montre, _ = _tf("show", "-json", "fuite.tfplan", cwd=copie)
    assert montre.returncode == 0, "Impossible de relire le plan en JSON."
    assert SECRET in montre.stdout, (
        "Le secret n'apparait pas dans la relecture JSON du plan : la variable "
        "porte-t-elle bien sa valeur par defaut ?"
    )

    # Le chemin annonce est evalue par jq contre le JSON du plan.
    jq = subprocess.run(
        ["jq", "-r", chemin], input=montre.stdout,
        capture_output=True, text=True,
        check=False,
    )
    assert jq.returncode == 0, (
        f"Le chemin {chemin!r} n'est pas une expression jq valide : "
        f"{jq.stderr.strip()[:200]}"
    )
    assert SECRET in jq.stdout, (
        f"Le chemin {chemin!r} ne designe pas le secret. Il rend "
        f"{jq.stdout.strip()[:80]!r}. Cherchez ou la valeur sort en clair, par "
        "exemple sous `.variables`."
    )


def test_le_gitignore_attrape_le_plan_sans_extension(
    travail: Path, tmp_path: Path
) -> None:
    """Un `.gitignore` se verifie en le faisant TRAVAILLER, pas en le lisant."""
    depot = tmp_path / "depot"
    depot.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=depot, capture_output=True, check=False)
    shutil.copy2(travail / ".gitignore", depot / ".gitignore")

    for nom in ("tfplan", "essai.tfplan"):
        (depot / nom).write_text("x", encoding="utf-8")
        verdict = subprocess.run(
            ["git", "check-ignore", "-q", nom], cwd=depot, capture_output=True,
            check=False,
        )
        assert verdict.returncode == 0, (
            f"`git check-ignore` ne considere pas {nom} comme ignore. Le nom "
            "produit par `plan -out=tfplan` n'a AUCUNE extension : un motif "
            "`*.tfplan` seul ne l'attrape pas."
        )
