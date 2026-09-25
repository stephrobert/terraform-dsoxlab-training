#!/usr/bin/env bash
# Rejoue localement ce que la CI vérifiera, y compris sur un CHECKOUT PROPRE.
#
# POURQUOI CE SCRIPT EXISTE
#
# Le 2026-09-25, la chaîne CI a échoué à son premier passage sur un défaut
# qu'aucun contrôle local ne pouvait voir : cinq fixtures déclarées dans un
# `lab.yaml` existaient sur la machine de l'auteur, mais n'étaient pas
# versionnées. Trois labs étaient donc cassés pour quiconque clone le dépôt, et
# intacts ici.
#
# La différence n'était pas dans les contrôles, elle était dans ce qu'ils
# lisaient : mon disque, et non le contenu du dépôt. Ce script comble cet écart
# en exportant le dépôt tel que git le voit, puis en y lançant les contrôles.
#
# Ce qu'il NE fait pas : CodeQL, qui demande l'infrastructure de GitHub. Tout le
# reste se joue ici.
#
#     scripts/pre-vol.sh            # tout
#     scripts/pre-vol.sh --rapide   # sans les hooks, qui sont les plus lents
set -uo pipefail

RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${RACINE}"

RAPIDE=0
[[ "${1:-}" == "--rapide" ]] && RAPIDE=1

echecs=0
titre() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()    { printf '   \033[0;32mOK\033[0m   %s\n' "$*"; }
ko()    { printf '   \033[0;31mÉCHEC\033[0m %s\n' "$*"; echecs=$((echecs + 1)); }

titre "1. Ce que git publierait : un export propre"
EXPORT="$(mktemp -d)"
trap 'rm -rf "${EXPORT}"' EXIT
# L'INDEX, et non HEAD : ce qu'on s'apprête à livrer, pas le dernier commit.
# Sans cela, un fichier ajouté mais pas encore commité manque à l'export, et
# le pré-vol accuse à tort un lab qu'on vient d'écrire.
ARBRE="$(git write-tree)"
if git archive "${ARBRE}" | tar -x -C "${EXPORT}"; then
    ok "index exporté dans un répertoire neuf"
else
    ko "git archive a échoué"
fi

# Le contrat, lu sur l'export et non sur le disque de travail. C'est CE
# contrôle qui aurait vu les fixtures manquantes.
if (cd "${EXPORT}" && LAB_HOME="${EXPORT}" dsoxlab validate-structure > /tmp/pre-vol-structure.log 2>&1); then
    ok "dsoxlab validate-structure sur l'export"
else
    ko "dsoxlab validate-structure sur l'export"
    grep -E '✘' /tmp/pre-vol-structure.log | head -10
fi

# Les fixtures déclarées sont-elles toutes versionnées ?
if python3 - "${EXPORT}" <<'PY'
import pathlib, sys
racine = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(racine / "scripts"))
from lecture_yaml import lire_yaml

manquantes = []
for contrat in sorted((racine / "labs").rglob("lab.yaml")):
    donnees = lire_yaml(contrat)
    for fixture in (donnees.get("runtime") or {}).get("fixtures") or []:
        if not (contrat.parent / "fixtures" / fixture).is_file():
            manquantes.append(f"{contrat.parent.name}/{fixture}")
if manquantes:
    print("  fixtures déclarées absentes de l'export :")
    for m in manquantes:
        print(f"    - {m}")
    raise SystemExit(1)
PY
then
    ok "toutes les fixtures déclarées sont versionnées"
else
    ko "des fixtures déclarées manquent à l'export"
fi

titre "2. Les méta-tests et le catalogue"
if python3 -m pytest tests/ -q > /tmp/pre-vol-tests.log 2>&1; then
    ok "$(tail -1 /tmp/pre-vol-tests.log)"
else
    ko "méta-tests"
    tail -12 /tmp/pre-vol-tests.log
fi

if python3 scripts/gen_catalog.py --check > /dev/null 2>&1; then
    ok "catalogue des README à jour"
else
    ko "catalogue périmé : lancez scripts/gen_catalog.py"
fi

titre "3. Le lint, avec les règles du dépôt"
if uvx ruff check > /tmp/pre-vol-ruff.log 2>&1; then
    ok "ruff"
else
    ko "ruff"
    tail -8 /tmp/pre-vol-ruff.log
fi

titre "4. Les workflows"
if command -v docker > /dev/null && docker run --rm -v "${RACINE}":/repo -w /repo rhysd/actionlint:latest > /tmp/pre-vol-actionlint.log 2>&1; then
    ok "actionlint"
elif ! command -v docker > /dev/null; then
    echo "   (ignoré : docker absent)"
else
    ko "actionlint"
    tail -8 /tmp/pre-vol-actionlint.log
fi

if [[ "${RAPIDE}" -eq 0 ]]; then
    titre "5. Les hooks, dans les deux étapes que la CI rejoue"
    if uvx pre-commit@4.6.0 run --all-files > /tmp/pre-vol-hooks.log 2>&1; then
        ok "hooks, étape commit"
    else
        ko "hooks, étape commit"
        grep -E 'Failed' /tmp/pre-vol-hooks.log | head -6
    fi
    if uvx pre-commit@4.6.0 run --all-files --hook-stage pre-push > /tmp/pre-vol-push.log 2>&1; then
        ok "hooks, étape pre-push"
    else
        ko "hooks, étape pre-push"
        grep -E 'Failed' /tmp/pre-vol-push.log | head -6
    fi
fi

printf '\n'
if [[ "${echecs}" -eq 0 ]]; then
    printf '\033[0;32mPré-vol vert.\033[0m La CI ne devrait rien trouver de plus, hors CodeQL.\n'
else
    printf '\033[0;31m%s contrôle(s) en échec.\033[0m Corrigez avant de pousser.\n' "${echecs}"
fi
exit "${echecs}"
