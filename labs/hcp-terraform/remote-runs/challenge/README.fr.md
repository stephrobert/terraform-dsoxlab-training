# 🎯 Challenge : lire le flux d'un run qui a échoué en cours de route

## 📦 Point de départ

`challenge/work` contient trois répertoires. **Aucun compte nécessaire.**

| Fichier | État |
| --- | --- |
| `flux/main.tf` | **fourni**, à ne pas modifier : sa troisième ressource échoue volontairement |
| `analyse/analyse.tf` | cinq `???` : lire le flux et en tirer les conclusions |
| `questionnaire/questionnaire.tf` | **fourni**, à ne pas modifier |
| `questionnaire/reponses.auto.tfvars` | cinq `???` à renseigner |

## ✅ Objectif

1. **Jouer le run en enregistrant son flux**, dans `flux/` :

   ```bash
   terraform apply -auto-approve -json > run.jsonl
   ```

   Il se terminera sur un code non nul. **C'est le résultat attendu** : la
   troisième ressource écrit sous un chemin dont le parent est un fichier.

2. **Analyser le flux** : les messages par type, le résumé qu'il porte, les
   adresses qui ont abouti, celle qui a échoué, et l'écart entre ce qui était
   annoncé et ce qui a eu lieu.

3. **Répondre aux cinq questions** sur les trois workflows.

## 🧭 Le piège, et il se referme sur une habitude raisonnable

Le flux d'un run qui **aboutit** porte deux messages `change_summary`, celui du
plan et celui de l'apply. Filtrer sur l'apply est alors la bonne chose à faire.

Le flux d'un run qui **échoue en cours** n'en porte qu'un, celui du plan. Filtrer
sur l'apply ne rend rien, et le résumé qui reste annonce davantage que ce qui
s'est produit.

Cet écart est tout l'intérêt de l'exercice. Comptez, ne vous fiez pas.

## ⚠️ Le flux ne peut pas s'écrire à la main

Les tests exigent que l'état du système concorde avec lui : deux fichiers
présents, l'impossible absent, et exactement deux ressources dans le state.

## 🔍 Validation

```bash
dsoxlab check hcp-terraform-remote-runs
```

Douze tests. Ils relisent `flux/run.jsonl` et recalculent ce que votre analyse
aurait dû rendre : rien n'est comparé à un chiffre gelé, un flux différent donne
des attendus différents.

Bloqué ? `dsoxlab hint hcp-terraform-remote-runs`.
