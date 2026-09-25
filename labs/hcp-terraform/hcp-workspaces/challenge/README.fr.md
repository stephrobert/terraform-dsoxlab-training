# 🎯 Challenge : un mot, deux sens, deux stratégies de rattachement

## 📦 Point de départ

`challenge/work` contient trois répertoires. **Aucun compte, aucun
`terraform login`** : ce lab ne crée rien dans HCP Terraform.

| Répertoire | État |
| --- | --- |
| `nomme/` | **trois fautes**, doit se rattacher par nom à `app-prod` |
| `etiquete/` | **deux fautes**, doit se rattacher par étiquettes |
| `questionnaire/questionnaire.tf` | **fourni**, à ne pas modifier |
| `questionnaire/reponses.auto.tfvars` | cinq `???` à renseigner |

## ✅ Objectif

1. **Réparer `nomme/`** pour qu'il se rattache au workspace `app-prod` de
   l'organisation `atelier-dsoxlab`, **par son nom**.
2. **Réparer `etiquete/`** pour qu'il se rattache **par étiquettes**, avec un
   `project` et aucun `name`.
3. **Répondre aux cinq questions**, avec les mots que l'énuméré autorise.

## 🧭 Lancez `validate`, puis `init`, et comparez

Cette comparaison est tout l'intérêt du lab. `terraform validate` répond
« Success! The configuration is valid. » sur deux des trois fautes de `nomme/`.
Seul l'`init` les voit, parce qu'un bloc `cloud` est résolu au moment où
Terraform établit où vit le state, avant toute évaluation d'expression.

Il en découle une conséquence, et c'est l'une des cinq questions.

## ⚠️ Où vous vous arrêtez, et c'est normal

Une configuration **correcte** aboutit ici :

```
Initializing HCP Terraform...

Error: Required token could not be found
```

Cette erreur est le but, pas un échec : elle signifie que votre rattachement a
été accepté et que Terraform demande maintenant à s'authentifier. Une
configuration fautive n'arrive jamais jusque-là.

Attention toutefois : deux des fautes affichent cette même ligne **à côté** de
leur propre erreur. Lisez tout ce qu'`init` affiche, pas seulement la dernière
ligne.

## 🔍 Validation

```bash
dsoxlab check hcp-terraform-hcp-workspaces
```

Huit tests. Les deux répertoires sont initialisés dans un environnement expurgé
de tout jeton, pour que la mesure soit la même sur n'importe quel poste, y
compris un poste ayant déjà fait `terraform login`.

Une réponse hors de l'énuméré est refusée **au plan**, avec un message qui dit
quoi écrire.

Bloqué ? `dsoxlab hint hcp-terraform-hcp-workspaces`.
