#!/usr/bin/env bash
# Rejoue les tests de TOUS les labs contre leur solution de référence.
#
# Même mécanisme que le dépôt ansible-training : la fixture autouse
# `_apply_lab_state` du conftest pose l'état de départ de chaque lab (fixtures +
# solution déchiffrée) dans `challenge/work` AVANT ses tests. C'est le contrôle
# formateur « mes solutions passent mes propres tests ».
#
# Pour UN lab, préférer la CLI, qui pose l'état de départ et désactive le rejeu
# de la solution (LAB_NO_REPLAY) :
#     dsoxlab check <id-du-lab>
#
# Prérequis :
#   - terraform (ou tofu) sur le PATH ;
#   - .vault-pass présent (les solutions sont chiffrées) ;
#   - pour les labs qui déclarent un `runtime.services` (section aws, Floci),
#     le service doit être joignable, sinon ces labs-là SKIPPENT proprement.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_DIR}"

log()  { echo -e "\033[0;34m[test-all]\033[0m $*"; }
ok()   { echo -e "\033[0;32m[OK]\033[0m $*"; }
fail() { echo -e "\033[0;31m[FAIL]\033[0m $*" >&2; }

if [[ ! -d labs ]]; then
    fail "labs/ introuvable — à lancer depuis la racine du dépôt."
    exit 1
fi

# Un catalogue vide doit ÉCHOUER, pas passer en silence : sinon la suite sort
# verte dès qu'elle ne trouve aucun lab.
lab_count="$(find labs -name lab.yaml | wc -l)"
if [[ "${lab_count}" -eq 0 ]]; then
    fail "aucun lab trouvé sous labs/ : catalogue vide ?"
    exit 1
fi
log "${lab_count} labs — tests joués avec la solution de référence"

if [[ ! -f .vault-pass ]]; then
    fail ".vault-pass absent : les solutions chiffrées ne peuvent pas être rejouées."
    exit 1
fi

if python3 -m pytest labs/ "$@"; then
    ok "tous les labs passent"
else
    fail "au moins un lab échoue (voir ci-dessus)"
    exit 1
fi
