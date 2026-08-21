# 🎯 Challenge : une chaîne jugée sur ses codes de retour

## 📦 Le point de départ

| Fichier | Ce que c'est |
| --- | --- |
| `main.tf` | **incomplet** : un marquage et une commande à écrire |
| `pipeline.sh` | squelette : cinq étapes en `???`, et le relevé des codes |
| `.gitignore` | **incomplet** : il laisse passer le fichier de plan |
| `CIBLE.md` | le format attendu des six fichiers de preuves |

Rien n'est initialisé, aucun état, aucun `preuves/`.

## ✅ Ce qu'il faut obtenir

1. La configuration est formatée, valide, initialisée sans prompt, appliquée
   **depuis un fichier de plan**, et convergée. L'apply dure **au moins dix
   secondes**.
2. `preuves/chaine.json` : le code de chacune des **cinq** étapes.
3. `preuves/codes.json` : les **trois** valeurs de `plan -detailed-exitcode`, et
   le code de `fmt -check` sur un fichier mal indenté.
4. `preuves/prompt.json` : le code **et le temps d'attente** d'un
   `plan -input=false` sans valeur de variable.
5. `preuves/plan_fige.json` : le sort de **quatre** options passées à l'apply
   d'un plan sauvegardé, chacune valant `erreur` ou `ignore`.
6. `preuves/verrou.json` : le défaut de `-lock-timeout`, et le code d'un plan
   lancé **pendant** un apply, avec ce défaut puis avec une durée suffisante.
7. `preuves/fuite.json` : le chemin `jq` exact où le secret sort en clair du plan
   sauvegardé. Et le `.gitignore` exclut réellement ce fichier.

## ⚠️ Trois choses à ne pas supposer

Le code de `fmt -check` sur un fichier mal indenté **n'est pas 1**.

Un `plan -input=false` sans valeur de variable **n'attend pas** : mesurez son
temps plutôt que de le supposer.

À l'apply d'un plan sauvegardé, **une seule** des quatre options fait échouer la
commande. Les autres sont acceptées, et **ignorées**.

## 🔍 Validation

`dsoxlab check environments-terraform-in-automation` **rejoue** chacune de vos
affirmations : il relance `fmt -check`, les trois plans, l'apply concurrent sous
verrou et les quatre options du plan sauvegardé, puis compare à vos relevés. Un
chiffre recopié depuis un cours au lieu d'être mesuré tombe.

Le `.gitignore`, lui, est mis à l'épreuve par `git check-ignore` dans un dépôt
jetable.

Bloqué ? `dsoxlab hint environments-terraform-in-automation`.
