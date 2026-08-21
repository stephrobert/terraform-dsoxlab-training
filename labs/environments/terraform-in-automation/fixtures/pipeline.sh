#!/usr/bin/env bash
# Chaine Terraform non interactive.
#
# Une CI n'a pas de clavier et ne lit pas la sortie coloree : elle decide sur
# des CODES DE RETOUR. Ce script joue les cinq etapes et consigne le code de
# chacune dans preuves/chaine.json.
#
# Regles :
#   - aucune etape ne doit pouvoir attendre une saisie ;
#   - la derniere etape applique le FICHIER de plan, pas une replanification ;
#   - le script ne s'arrete pas au premier echec : il doit relever TOUS les
#     codes, c'est tout l'interet du releve.
set -u

export TF_IN_AUTOMATION=1
mkdir -p preuves

# A completer : les cinq commandes, dans l'ordre. Chacune doit etre non
# interactive, et son code de retour doit etre capture.
#
#   1. controle du formatage, sur toute l'arborescence
#   2. initialisation
#   3. validation, en sortie machine
#   4. planification DANS UN FICHIER, avec le code detaille
#   5. application du fichier de plan

etape_1=???
code_1=???

etape_2=???
code_2=???

etape_3=???
code_3=???

etape_4=???
code_4=???

etape_5=???
code_5=???

cat > preuves/chaine.json <<JSON
{
  "fmt":      $code_1,
  "init":     $code_2,
  "validate": $code_3,
  "plan":     $code_4,
  "apply":    $code_5
}
JSON

echo "codes releves dans preuves/chaine.json"
