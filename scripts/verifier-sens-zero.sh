#!/usr/bin/env bash
# Chaque lab rend-il 0 AVANT que l'apprenant ait travaillé ?
#
# `scripts/test-all.sh` ne prouve qu'un sens : la solution de référence passe
# ses propres tests. C'est nécessaire, et cela ne suffit pas. Un test toujours
# vert passe ce contrôle exactement comme un bon test : les deux y sont
# indiscernables.
#
# Ce script mesure l'autre moitié. Pour chaque lab : `clean`, `run`, puis
# `check` SANS avoir rien fait. Tout score au-dessus de 0 désigne un test qui
# mesure le setup et non le travail.
#
# Mesuré le 2026-09-23, avant que ce script n'existe : six labs sur soixante et
# un rendaient des points à vide, dont un à 50/100. Le motif était presque
# toujours le même, et il ne se voit pas à la lecture :
#
#   - un CONTRÔLE NÉGATIF isolé (« cette adresse n'est pas reportée », « ce
#     plan ne détruit pas ceci ») : sur une configuration que l'apprenant n'a
#     pas écrite, le symptôme est absent parce que le SUJET est absent ;
#   - une CONVERGENCE isolée (« le plan est vide ») : une configuration nue
#     converge parfaitement, et même nécessairement ;
#   - une PRÉMISSE du lab prise pour un résultat (« le fichier est là », « les
#     artefacts sont intacts ») : c'est le setup qui l'a posée.
#
# La correction n'est jamais de supprimer ces moitiés, qui restent utiles :
# c'est de les FUSIONNER dans un test qui n'est atteignable qu'après le travail,
# où elles distinguent une correction réussie d'une panne.
#
# Prérequis : terraform sur le PATH, .vault-pass présent, dsoxlab installé.
#
# Usage :
#     scripts/verifier-sens-zero.sh              # tous les labs
#     scripts/verifier-sens-zero.sh <id> [<id>]  # quelques-uns
#     scripts/verifier-sens-zero.sh --check      # code retour non nul si défaut

set -uo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_DIR}"

log()  { echo -e "\033[0;34m[sens-zero]\033[0m $*"; }
ok()   { echo -e "\033[0;32m[OK]\033[0m $*"; }
fail() { echo -e "\033[0;31m[DEFAUT]\033[0m $*" >&2; }

mode_check=0
demandes=()
for argument in "$@"; do
    case "${argument}" in
        --check) mode_check=1 ;;
        *)       demandes+=("${argument}") ;;
    esac
done

if [[ ! -f .vault-pass ]]; then
    fail ".vault-pass absent : impossible de poser l'état de départ des labs."
    exit 1
fi

export LAB_HOME="${REPO_DIR}"

# Les labs qui ont un test écrit, donc quelque chose à mesurer. Les squelettes
# sont ignorés : leur test échoue exprès, ils rendent 0 par construction et
# n'apprendraient rien ici.
if [[ ${#demandes[@]} -gt 0 ]]; then
    ids="$(printf '%s\n' "${demandes[@]}")"
else
    ids="$(python3 - <<'PY'
import pathlib

import yaml

MARQUEUR = "tests non implémentés"

for contrat in sorted(pathlib.Path("labs").rglob("lab.yaml")):
    suite = contrat.parent / "challenge" / "tests" / "test_functional.py"
    if not suite.is_file():
        continue
    if MARQUEUR in suite.read_text(encoding="utf-8"):
        continue
    contenu = yaml.safe_load(contrat.read_text(encoding="utf-8")) or {}
    if contenu.get("id"):
        print(contenu["id"])
PY
)"
fi

total="$(printf '%s\n' "${ids}" | grep -c . || true)"
if [[ "${total}" -eq 0 ]]; then
    fail "aucun lab à mesurer : catalogue vide ?"
    exit 1
fi

log "${total} lab(s) à éprouver sans travail"

defauts=0
rang=0
while read -r id; do
    [[ -n "${id}" ]] || continue
    rang=$((rang + 1))
    printf '  [%d/%d] %-52s ' "${rang}" "${total}" "${id}"

    printf 'y\n' | dsoxlab clean "${id}" >/dev/null 2>&1
    dsoxlab run "${id}" </dev/null >/dev/null 2>&1

    sortie="$(dsoxlab check "${id}" </dev/null 2>&1)"
    score="$(printf '%s' "${sortie}" \
        | grep -oE 'Score :[[:space:]]+[0-9]+' | grep -oE '[0-9]+$' | head -1)"

    printf 'y\n' | dsoxlab clean "${id}" >/dev/null 2>&1

    if [[ -z "${score}" ]]; then
        echo -e "\033[0;33mILLISIBLE\033[0m"
        defauts=$((defauts + 1))
        continue
    fi
    if [[ "${score}" -eq 0 ]]; then
        echo -e "\033[0;32m0 / 100\033[0m"
        continue
    fi

    echo -e "\033[0;31m${score} / 100\033[0m"
    defauts=$((defauts + 1))

    # On nomme les tests fautifs : le score seul ne permet pas de corriger.
    rel="$(python3 - "${id}" <<'PY'
import pathlib
import sys

import yaml

cible = sys.argv[1]
for contrat in sorted(pathlib.Path("labs").rglob("lab.yaml")):
    contenu = yaml.safe_load(contrat.read_text(encoding="utf-8")) or {}
    if contenu.get("id") == cible:
        print(contrat.parent)
        break
PY
)"
    if [[ -n "${rel}" ]]; then
        dsoxlab run "${id}" </dev/null >/dev/null 2>&1
        LAB_NO_REPLAY=1 python3 -m pytest "${rel}" -v --no-header \
            -p no:cacheprovider 2>/dev/null \
            | grep -E 'PASSED' \
            | sed -E 's/.*::([^ ]+) PASSED.*/        vert à vide : \1/'
        printf 'y\n' | dsoxlab clean "${id}" >/dev/null 2>&1
    fi
done <<< "${ids}"

echo
if [[ "${defauts}" -eq 0 ]]; then
    ok "les ${total} labs rendent 0 sans travail."
    exit 0
fi

fail "${defauts} lab(s) sur ${total} rendent des points sans travail."
cat >&2 <<'AIDE'

Un test vert avant le travail ne mesure pas une compétence, il mesure le setup.
Pour chaque test nommé ci-dessus, se demander : « serait-il vert si le candidat
ne faisait rien ? » Si oui, ce n'est pas un test, c'est une hypothèse.

Ne le supprimez pas : fusionnez-le dans un test qu'on ne peut atteindre
qu'après le travail. Un contrôle négatif doit d'abord établir que son sujet
existe ; une convergence ne vaut qu'accolée à ce qui devait converger.
AIDE

[[ "${mode_check}" -eq 1 ]] && exit 1
exit 0
