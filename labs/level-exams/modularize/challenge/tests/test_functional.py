"""Épreuve de niveau C : modulariser.

Une mesure, pas un cours. Chaque test note un RÉSULTAT : tags du dépôt Git,
commit que Terraform a réellement obtenu, plans et codes de retour, UUID et
temps CPU des domaines libvirt, issue de `terraform test` quand le harnais
abîme le module. Le code n'est lu que par les vues de Terraform lui-même
(`modules.json`, `terraform providers`), jamais par sa forme.

Le nom de chaque test commence par la compétence qu'il note : `modularize`,
`reuse`. Le rapport de `dsoxlab check` donne ainsi un verdict par compétence.

Ce que la préparation (`setup.yaml`) a retenu pour le harnais vit dans
`$LAB_STATE_DIR/epreuve.json` : préfixe, dépôt, image, tailles, UUID des
machines de l'équipe web en service.

Faits mesurés avant d'écrire ces tests (cahier des charges, §15) : un module
qui embarque son bloc provider est refusé en `for_each` ; une valeur du
contrat changée dans le code, ou une validation retirée, fait échouer un
`terraform test` qui couvre le contrat ; un tag déplacé ne touche pas un
consommateur épinglé au SHA-1. Une VM qui boote dépasse 2 s de CPU.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import pytest

from conftest import exiger_workdir, workdir_lab

pytestmark = pytest.mark.no_replay

WORKDIR = workdir_lab(__file__)
LAB_ID = "level-exams-modularize"
VIRSH = ["virsh", "-c", "qemu:///system"]
SECONDES_CPU_MINIMUM = 2.0
MEMOIRE_KIB = {"petite": 512 * 1024, "moyenne": 768 * 1024}
VERSIONS = ("v1.0.0", "v1.1.0", "v2.0.0")


# ── Ce que la préparation a retenu ───────────────────────────────────────────

def _epreuve() -> dict:
    etat = os.environ.get("LAB_STATE_DIR")
    assert etat, "LAB_STATE_DIR absent : lancez l'épreuve par `dsoxlab run`, puis notez par `dsoxlab check`."
    fichier = Path(etat) / "epreuve.json"
    assert fichier.is_file(), f"{fichier} absent : la préparation n'a pas tourné (`dsoxlab run`)."
    return json.loads(fichier.read_text())


# ── Outils ───────────────────────────────────────────────────────────────────

def _run(cmd: list[str], cwd: Path | None = None, timeout: int = 600) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["TF_IN_AUTOMATION"] = "1"
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)


def _terraform(cwd: Path, *args: str, timeout: int = 600) -> subprocess.CompletedProcess[str]:
    return _run(["terraform", *args, "-no-color"], cwd=cwd, timeout=timeout)


def _git(depot: str, *args: str) -> subprocess.CompletedProcess[str]:
    return _run(["git", "-C", depot, *args])


def _commit(depot: str, ref: str) -> str | None:
    r = _git(depot, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    return r.stdout.strip() if r.returncode == 0 else None


def _virsh(*args: str) -> subprocess.CompletedProcess[str]:
    return _run([*VIRSH, *args], timeout=60)


def _boote(nom: str) -> bool:
    """Une machine `running` sans OS l'est aussi : seul le temps CPU prouve le boot."""
    debut = time.monotonic()
    while time.monotonic() - debut < 90:
        if _virsh("domstate", nom).stdout.strip() == "running":
            m = re.search(r"cpu\.time=(\d+)", _virsh("domstats", nom, "--cpu-total").stdout)
            if m and int(m.group(1)) / 1e9 >= SECONDES_CPU_MINIMUM:
                return True
        time.sleep(3)
    return False


def _module(equipe: str) -> dict:
    """Le module de l'équipe, tel que Terraform l'a installé : source, ref, sous-dossier, clone."""
    fichier = WORKDIR / equipe / ".terraform" / "modules" / "modules.json"
    assert fichier.is_file(), f"{equipe} : aucun module installé (terraform init n'a pas tourné, ou pas de module)."
    modules = [m for m in json.loads(fichier.read_text())["Modules"] if m["Key"] and "depot-modules.git" in m["Source"]]
    assert modules, f"{equipe} : aucun module tiré du dépôt depot-modules.git."
    m = modules[0]
    source = m["Source"]
    ref = re.search(r"[?&]ref=([^&]+)", source)
    sous = re.search(r"\.git//([^?]+)", source)
    clone = WORKDIR / equipe / ".terraform" / "modules" / m["Key"].split(".")[0]
    return {"source": source, "ref": ref.group(1) if ref else None, "sous": sous.group(1) if sous else "",
            "clone": clone, "cle": m["Key"]}


def _sous_dossier() -> str:
    """Le dossier du module dans le dépôt, lu sur la source de l'équipe web."""
    return _module("equipe-web")["sous"]


def _source(ref: str) -> str:
    """L'adresse du module à `ref`, sous-dossier compris s'il y en a un."""
    sous = _sous_dossier()
    return f"git::file://{_epreuve()['depot']}" + (f"//{sous}" if sous else "") + f"?ref={ref}"


def _extraire(depot: str, ref: str) -> Path:
    """Le module tel qu'il est à `ref`, dans un clone jetable."""
    t = Path(tempfile.mkdtemp(prefix="epreuve-c-"))
    r = _run(["git", "clone", "-q", depot, str(t / "depot")])
    assert r.returncode == 0, f"Clone du dépôt impossible : {r.stderr}"
    r = _git(str(t / "depot"), "checkout", "-q", ref)
    assert r.returncode == 0, f"{ref} introuvable dans le dépôt."
    return t / "depot" / _sous_dossier() if _sous_dossier() else t / "depot"


def _appelant(source: str, entrees: str, for_each: bool = True) -> Path:
    """Un appelant jetable du module, avec son provider."""
    t = Path(tempfile.mkdtemp(prefix="epreuve-c-appelant-"))
    e = _epreuve()
    boucle = '  for_each = toset(["x", "y"])\n  nom      = "essai-${each.key}"\n' if for_each else '  nom = "essai"\n'
    (t / "main.tf").write_text(f'''terraform {{
  required_providers {{
    libvirt = {{
      source  = "dmacvicar/libvirt"
      version = "0.9.9"
    }}
  }}
}}

provider "libvirt" {{
  uri = "qemu:///system"
}}

module "m" {{
  source        = "{source}"
{boucle}  image_de_base = "{e['image_de_base']}"
  reseau        = "default"
{entrees}
}}
''')
    return t


def _sans_validation(texte: str) -> str:
    """Retire chaque bloc `validation { … }`, accolades imbriquées comprises."""
    sortie, i = [], 0
    while True:
        m = re.search(r"\n[ \t]*validation\s*\{", texte[i:])
        if not m:
            sortie.append(texte[i:])
            return "".join(sortie)
        debut = i + m.start()
        sortie.append(texte[i:debut])
        j, profondeur = i + m.end(), 1
        while profondeur:
            profondeur += {"{": 1, "}": -1}.get(texte[j], 0)
            j += 1
        i = j


@pytest.fixture(autouse=True)
def _workdir() -> None:
    exiger_workdir(WORKDIR, LAB_ID)


# ── modularize ───────────────────────────────────────────────────────────────

def test_modularize_le_depot_publie_les_trois_versions() -> None:
    e = _epreuve()
    sous = _sous_dossier()
    for v in VERSIONS:
        assert _commit(e["depot"], v), f"Le dépôt n'a pas de tag {v}."
        r = _git(e["depot"], "ls-tree", "--name-only", v, *([f"{sous}/"] if sous else []))
        assert any(n.endswith(".tf") for n in r.stdout.split()), f"{v} : aucun fichier .tf dans « {sous or '/'} »."


def test_modularize_le_module_n_embarque_pas_son_provider() -> None:
    e = _epreuve()
    appelant = _appelant(_source("v1.1.0"), '  taille        = "petite"')
    init = _terraform(appelant, "init", "-input=false")
    assert init.returncode == 0, (
        f"Le module en v1.1.0 ne s'appelle pas en for_each : il embarque sans doute son bloc provider.\n"
        f"{(init.stdout + init.stderr)[-500:]}")
    valide = _terraform(appelant, "validate")
    assert valide.returncode == 0, f"Le module en v1.1.0 ne se valide pas : {(valide.stdout + valide.stderr)[-400:]}"
    providers = _terraform(appelant, "providers").stdout
    contrainte = re.search(r"module\.m.*?\n\s*└── provider\[registry\.terraform\.io/dmacvicar/libvirt\]\s*(.*)", providers, re.S)
    assert contrainte and contrainte.group(1).strip().startswith(">="), (
        f"Le module doit contraindre seulement le plancher du provider libvirt (« >= … ») :\n{providers}")


def test_modularize_les_tests_du_module_passent() -> None:
    module = _extraire(_epreuve()["depot"], "v1.1.0")
    assert list(module.rglob("*.tftest.hcl")), "Le module en v1.1.0 n'a aucun fichier .tftest.hcl."
    assert _terraform(module, "init", "-input=false").returncode == 0, "init du module en v1.1.0 impossible."
    r = _terraform(module, "test", timeout=900)
    assert r.returncode == 0, f"terraform test échoue sur le module en v1.1.0 :\n{(r.stdout + r.stderr)[-600:]}"


@pytest.mark.parametrize("regression", ["tailles-changees", "validation-retiree"])
def test_modularize_les_tests_voient_une_regression(regression: str) -> None:
    module = _extraire(_epreuve()["depot"], "v1.1.0")
    sources = [f for f in module.glob("*.tf")]
    touche = False
    for f in sources:
        t = f.read_text()
        n = re.sub(r"\b768\b", "1024", re.sub(r"\b512\b", "640", t)) if regression == "tailles-changees" else _sans_validation(t)
        if n != t:
            f.write_text(n)
            touche = True
    assert touche, f"Régression « {regression} » : rien à abîmer, le module ne porte pas le contrat (tailles 512 et 768, validation de taille)."
    assert _terraform(module, "init", "-input=false").returncode == 0, "init du module abîmé impossible."
    r = _terraform(module, "test", timeout=900)
    assert r.returncode != 0, f"Régression « {regression} » injectée dans le module : terraform test passe encore, il ne la voit pas."


def test_modularize_le_projet_en_service_garde_ses_machines() -> None:
    e = _epreuve()
    for cote, uuid in e["uuid_web"].items():
        nom = f"{e['prefixe']}-web-{cote}"
        actuel = _virsh("domuuid", nom).stdout.strip()
        assert actuel == uuid, f"{nom} a été RECRÉÉE (UUID {uuid} devenu {actuel or 'absent'})."
        assert _boote(nom), f"{nom} ne tourne plus."
    etat = _terraform(WORKDIR / "equipe-web", "state", "list").stdout
    assert re.search(r"^module\..*libvirt_domain\.", etat, re.M), "equipe-web ne gère pas ses machines par un module."
    plan = _terraform(WORKDIR / "equipe-web", "plan", "-input=false", "-detailed-exitcode")
    assert plan.returncode == 0, f"Plan de equipe-web : {plan.returncode} (0 attendu).\n{(plan.stdout + plan.stderr)[-400:]}"


# ── reuse ────────────────────────────────────────────────────────────────────

def test_reuse_l_equipe_data_est_figee_au_contenu() -> None:
    e = _epreuve()
    m = _module("equipe-data")
    assert m["ref"] and re.fullmatch(r"[0-9a-f]{40}", m["ref"]), (
        f"equipe-data doit épingler le module par un SHA-1 complet (ref=…), source : {m['source']}")
    assert m["ref"] == _commit(e["depot"], "v1.0.0"), "equipe-data doit être figée sur le contenu de v1.0.0."
    for cote, taille in e["tailles_data"].items():
        nom = f"{e['prefixe']}-data-{cote}"
        assert _boote(nom), f"{nom} n'existe pas ou ne démarre pas."
        memoire = int(re.search(r"Max memory:\s+(\d+)", _virsh("dominfo", nom).stdout).group(1))
        assert memoire == MEMOIRE_KIB[taille], f"{nom} : {memoire} KiB, {MEMOIRE_KIB[taille]} attendus ({taille})."
    plan = _terraform(WORKDIR / "equipe-data", "plan", "-input=false", "-detailed-exitcode")
    assert plan.returncode == 0, f"Plan de equipe-data : {plan.returncode} (0 attendu)."


def test_reuse_l_equipe_web_suit_les_versions_publiees() -> None:
    e = _epreuve()
    m = _module("equipe-web")
    assert m["ref"], f"equipe-web tire le module sans ref : elle suivrait la branche, pas les versions publiées."
    assert m["ref"] not in VERSIONS and not re.fullmatch(r"[0-9a-f]{7,40}", m["ref"]), (
        f"equipe-web pointe « {m['ref']} » : figée, elle ne suit pas les versions publiées.")
    assert _commit(e["depot"], f"refs/tags/{m['ref']}"), f"« {m['ref']} » n'est pas un tag du dépôt."
    obtenu = _git(str(m["clone"]), "rev-parse", "HEAD").stdout.strip()
    assert obtenu == _commit(e["depot"], "v1.1.0"), "equipe-web n'a pas obtenu la version mineure v1.1.0."


def test_reuse_la_majeure_exige_d_adapter_le_consommateur() -> None:
    e = _epreuve()
    source = _source("v2.0.0")
    ancien = _appelant(source, '  taille        = "petite"', for_each=False)
    _terraform(ancien, "init", "-input=false")
    r = _terraform(ancien, "validate")
    assert r.returncode != 0, "Un consommateur de la v1 passe tel quel en v2.0.0 : ce n'est pas une version majeure."
    adapte = _appelant(source, "  memoire_mib   = 512", for_each=False)
    _terraform(adapte, "init", "-input=false")
    r = _terraform(adapte, "validate")
    assert r.returncode == 0, f"En v2.0.0, memoire_mib doit remplacer taille :\n{(r.stdout + r.stderr)[-400:]}"


def test_reuse_un_tag_deplace_ne_touche_pas_l_equipe_figee() -> None:
    e = _epreuve()
    depot = e["depot"]
    tags = {t: _commit(depot, t) for t in _git(depot, "tag").stdout.split()}
    t = Path(tempfile.mkdtemp(prefix="epreuve-c-tag-"))
    copie = t / "equipe-data"
    shutil.copytree(WORKDIR / "equipe-data", copie, symlinks=True)
    try:
        # Un commit qui change le contrat, sur lequel on déplace tous les tags.
        _run(["git", "clone", "-q", depot, str(t / "depot")])
        travail = str(t / "depot")
        for f in (t / "depot").rglob("*.tf"):
            f.write_text(re.sub(r"\b512\b", "1024", f.read_text()))
        _git(travail, "-c", "user.email=harnais@exemple.test", "-c", "user.name=harnais", "commit", "-qam", "tag deplace")
        for tag in tags:
            _git(travail, "tag", "-f", tag)
        _git(travail, "push", "-q", "--force", "origin", "--tags")
        _terraform(copie, "init", "-input=false", "-upgrade")
        plan = _terraform(copie, "plan", "-input=false", "-detailed-exitcode")
        assert plan.returncode == 0, (
            f"Tags déplacés : le plan de equipe-data rend {plan.returncode} (0 attendu), elle n'est pas figée au contenu.")
    finally:
        for tag, commit in tags.items():
            if commit:
                _git(depot, "tag", "-f", tag, commit)
        shutil.rmtree(t, ignore_errors=True)
