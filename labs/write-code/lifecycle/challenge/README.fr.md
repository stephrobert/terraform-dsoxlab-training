# 🎯 Challenge : le bloc `lifecycle` décide de l'ordre, pas vous

## Point de départ imposé

`challenge/work` contient une configuration **qui s'applique telle quelle** et
qui ne contient **aucun** bloc `lifecycle`. Avant toute modification :

```bash
terraform init
terraform apply
terraform plan -var 'revision=2'
```

Ce dernier plan est votre constat de départ : Terraform **détruit avant de
créer**. Il y a donc une fenêtre pendant laquelle le fichier n'existe plus.

Ne touchez ni à `versions.tf`, ni à `variables.tf`, ni à `modele.txt`. Tout se
joue dans `main.tf`.

## ✅ Objectif

1. **Supprimer la fenêtre de trou.** `local_file.app` doit être créé avant
   d'être détruit lors d'un remplacement. N'écrivez **rien** sur
   `random_pet.version` : Terraform doit lui appliquer la règle tout seul. Si
   vous devez l'écrire à la main, c'est que vous l'avez posée au mauvais endroit.

2. **Protéger la donnée critique.** `local_file.donnees` doit faire échouer
   `terraform plan -destroy`.

3. **Faire taire la dérive du journal, sans plus.** Un changement de `content`
   venu de la configuration ne doit plus rien planifier sur `local_file.journal`.
   Un changement de `permissions`, lui, doit continuer à être planifié. Le
   raccourci qui ignore tout est donc exclu.

4. **Déclencher un remplacement depuis une valeur nue.** `local_file.marqueur`
   ne dépend d'aucun attribut mouvant. Il doit pourtant être remplacé chaque
   fois que `revision` change. Attention : `replace_triggered_by` n'accepte que
   des **ressources gérées**. Une variable ou un local sont refusés par
   Terraform, avec le message `Only resources, count.index, and each.key may be
   used in replace_triggered_by`. Il vous manque donc une ressource.

5. **Refuser une entrée invalide au plan.** `env` hors de `dev`, `staging`,
   `prod` doit faire échouer le plan. Et après création, un contenu où le jeton
   `{{env}}` n'aurait pas été substitué doit être signalé. Ces deux contrôles
   doivent vivre **dans la ressource**, pas sur la variable : un bloc
   `validation` filtrerait bien la valeur, mais ne répond pas à l'énoncé (les
   tests lisent `checks[].address.kind`).

Après votre dernier `apply`, `terraform plan` ne doit plus rien proposer.

## 🧭 Deux pièges à connaître

- **Le bloc `lifecycle` n'accepte que des valeurs littérales.** Toutes ses
  règles servent à construire le graphe de dépendances, ce qui arrive trop tôt
  pour évaluer une expression. `prevent_destroy = var.protege` répond
  `Variables not allowed`.
- **`ignore_changes` compare la configuration à l'état**, pas à ce qu'il y a sur
  le disque. Modifier le fichier à la main hors de Terraform ne sera pas absorbé.

## 🔍 Validation

```bash
dsoxlab check write-code-lifecycle
```

Douze tests. Ils pilotent Terraform et lisent le plan en JSON
(`resource_changes[].actions`, `action_reason`) ainsi que le tableau `checks`.
Aucun ne lit vos fichiers `.tf` : recopier des blocs sans les rattacher à la
bonne ressource ne passe pas.
