#!/usr/bin/env bash
# FOURNI. Ce script se lit, il ne se corrige pas.
#
# Il decrit une SUITE D'ETAPES : cree un repertoire, tire un identifiant,
# ajoute une ligne au rapport. Chaque etape est raisonnable prise seule. Le
# defaut n'est dans aucune d'elles : il est dans le fait que le resultat depend
# du NOMBRE d'executions.
#
# Rejouez-le deux fois, puis comparez `sortie-imperative/dernier-id.txt` et le
# nombre de lignes de `sortie-imperative/rapport.txt`. C'est ce comportement que
# votre configuration Terraform doit remplacer.
set -eu

SORTIE="sortie-imperative"
mkdir -p "$SORTIE"

# Un identifiant tire a chaque appel : rien ne le rattache a l'appel precedent.
IDENTIFIANT="$(tr -dc 'a-z0-9' < /dev/urandom | head -c 8)"

# `>>` empile. Le rapport grossit a chaque passage.
printf 'rapport genere, identifiant : %s\n' "$IDENTIFIANT" >> "$SORTIE/rapport.txt"
printf '%s\n' "$IDENTIFIANT" > "$SORTIE/dernier-id.txt"

printf 'identifiant du jour : %s\n' "$IDENTIFIANT"
