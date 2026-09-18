#!/usr/bin/env python3
"""Rejoue les solutions de référence et prouve qu'elles marchent encore.

Raison d'être : une montée de version de Terraform (ou d'un provider) peut
casser une solution sans que personne ne s'en aperçoive, parce que les tests
d'un lab ne tournent que si un apprenant le joue. Ce script rejoue **toutes**
les solutions de référence avec le binaire actuellement installé et enregistre
le résultat dans ``solution/verified-with.json``.

Pour chaque lab disposant d'une solution :

1. un répertoire temporaire est créé,
2. les ``fixtures/`` du lab y sont copiées (l'état de départ de l'apprenant),
3. les fichiers de ``solution/<section>/<lab>/`` y sont **déchiffrés** par-dessus,
   via ``ansible-vault`` et le mot de passe local ``.vault-pass`` (jamais commité),
4. la suite ``challenge/tests/test_functional.py`` du lab est jouée contre ce
   répertoire, via la variable d'environnement ``LAB_WORKDIR``.

Le workdir de l'apprenant n'est jamais touché.

Usage :

    python3 scripts/verify-solutions.py            # rejoue tout
    python3 scripts/verify-solutions.py --lab write-code/functions
    python3 scripts/verify-solutions.py --check    # échoue si une solution casse
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SOLUTIONS = REPO / "solution"
LABS = REPO / "labs"
RECORD = SOLUTIONS / "verified-with.json"
VAULT_PASS = REPO / ".vault-pass"


def outil_version(binaire: str, *args: str) -> str | None:
    """Version d'un outil, ou None s'il est absent du PATH."""
    if shutil.which(binaire) is None:
        return None
    try:
        proc = subprocess.run(
            [binaire, *args], capture_output=True, text=True, timeout=30, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    premiere = proc.stdout.strip().splitlines()
    if not premiere:
        return None
    match = re.search(r"v?(\d+\.\d+\.\d+)", premiere[0])
    return match.group(1) if match else premiere[0].strip()


def solutions_disponibles() -> list[str]:
    """Chemins relatifs des labs ayant une solution, triés.

    Le répertoire du lab est reconnu par la présence de ``labs/<rel>/lab.yaml``,
    et non par le parent immédiat du fichier : depuis que les solutions peuvent
    porter des sous-répertoires (un module local, par exemple), un
    ``solution/<lab>/modules/stockage/main.tf`` aurait sinon été pris pour un
    lab nommé ``<lab>/modules/stockage``.
    """
    if not SOLUTIONS.is_dir():
        return []
    trouves = set()
    for fichier in SOLUTIONS.rglob("*"):
        if not fichier.is_file():
            continue
        if fichier.name == RECORD.name or fichier.suffix == ".md":
            continue
        candidat = fichier.parent
        while candidat != SOLUTIONS:
            if (LABS / candidat.relative_to(SOLUTIONS) / "lab.yaml").is_file():
                trouves.add(str(candidat.relative_to(SOLUTIONS)))
                break
            candidat = candidat.parent
    return sorted(trouves)


def dechiffrer(fichier: Path) -> bytes:
    """Contenu en clair d'un fichier de solution chiffré par ansible-vault."""
    proc = subprocess.run(
        ["ansible-vault", "view", "--vault-password-file", str(VAULT_PASS), str(fichier)],
        capture_output=True, check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Déchiffrement impossible pour {fichier.name} : "
            f"{proc.stderr.decode(errors='replace').strip()}"
        )
    return proc.stdout


def materialiser(lab_rel: str, cible: Path) -> None:
    """Copie les fixtures puis déchiffre la solution par-dessus."""
    fixtures = LABS / lab_rel / "fixtures"
    if fixtures.is_dir():
        for fichier in sorted(fixtures.rglob("*")):
            if fichier.is_file():
                # Le runtime shell de dsoxlab (>= 0.1.37) PRESERVE le chemin
                # declare dans runtime.fixtures : on reproduit ce comportement a
                # l'identique, sans quoi un lab a module local ne pourrait pas
                # etre rejoue (deux main.tf s'ecraseraient).
                dst = cible / fichier.relative_to(fixtures)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(fichier, dst)

    for chiffre in sorted((SOLUTIONS / lab_rel).rglob("*")):
        if chiffre.is_file():
            dst = cible / chiffre.relative_to(SOLUTIONS / lab_rel)
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(dechiffrer(chiffre))


def rejouer(lab_rel: str, garder: bool = False) -> tuple[bool, str]:
    """Joue la suite de tests du lab contre la solution. Rend (succes, detail)."""
    suite = LABS / lab_rel / "challenge" / "tests" / "test_functional.py"
    if not suite.is_file():
        return False, "suite de tests introuvable"

    tmp = Path(tempfile.mkdtemp(prefix="verif-solution-"))
    try:
        materialiser(lab_rel, tmp)
        env = dict(os.environ, LAB_WORKDIR=str(tmp))
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", str(suite), "-q", "--no-header"],
            cwd=REPO, env=env, capture_output=True, text=True, check=False,
        )
        resume = proc.stdout.strip().splitlines()
        detail = resume[-1] if resume else "aucune sortie"
        return proc.returncode == 0, detail
    finally:
        if garder:
            print(f"    (répertoire conservé : {tmp})")
        else:
            shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lab", help="ne rejouer qu'un lab (ex: write-code/functions)")
    parser.add_argument("--check", action="store_true",
                        help="code retour non nul si une solution casse (mode CI)")
    parser.add_argument("--keep", action="store_true",
                        help="conserver les répertoires temporaires pour inspection")
    args = parser.parse_args()

    if not VAULT_PASS.is_file():
        print("Fichier .vault-pass absent : les solutions sont chiffrées et ne "
              "peuvent pas être rejouées.\nDemandez le mot de passe au formateur, "
              "puis placez-le dans .vault-pass (jamais commité).")
        return 1

    tf = outil_version("terraform", "version")
    if tf is None:
        print("terraform absent du PATH : impossible de vérifier les solutions.")
        return 1

    labs = [args.lab] if args.lab else solutions_disponibles()
    if not labs:
        print("Aucune solution de référence trouvée sous solution/.")
        return 0

    print(f"Terraform {tf}, {len(labs)} solution(s) à rejouer.\n")

    resultats: dict[str, dict[str, str]] = {}
    echecs = 0
    for lab_rel in labs:
        print(f"  {lab_rel} ... ", end="", flush=True)
        ok, detail = rejouer(lab_rel, garder=args.keep)
        print("OK" if ok else "ÉCHEC")
        if not ok:
            print(f"    {detail}")
            echecs += 1
        resultats[lab_rel] = {"statut": "ok" if ok else "echec", "detail": detail}

    RECORD.parent.mkdir(parents=True, exist_ok=True)
    RECORD.write_text(json.dumps({
        "terraform": tf,
        "verifie_le": datetime.now(UTC).strftime("%Y-%m-%d"),
        "solutions": resultats,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"\n{len(labs) - echecs}/{len(labs)} solution(s) valide(s) avec Terraform {tf}.")
    print(f"Résultat enregistré dans {RECORD.relative_to(REPO)}.")

    if echecs and args.check:
        print("\nUne solution ne passe plus : Terraform ou un provider a changé "
              "de comportement. Corrigez la solution ET le guide correspondant.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
