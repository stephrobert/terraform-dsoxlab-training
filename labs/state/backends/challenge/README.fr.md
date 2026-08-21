# 🎯 Challenge : backend partiel et migration du state

## ✅ Objectif

Dans `challenge/work`, faites passer le projet du backend local **implicite** à un
backend `local` **paramétré**, en migrant le state. À faire :

1. **créer `backend.tf`** avec un bloc backend en **configuration partielle** :
   ```hcl
   terraform {
     backend "local" {}
   }
   ```
   (aucun `path` ici, et surtout pas `var.chemin_state` : le bloc refuse les
   valeurs nommées) ;
2. remplir le `path` de **`dev.local.tfbackend`** :
   `path = "etat/dev/terraform.tfstate"` ;
3. **créer `prod.local.tfbackend`** avec `path = "etat/prod/terraform.tfstate"`.

Le test applique d'abord sans backend, puis migre avec
`terraform init -migrate-state -backend-config=dev.local.tfbackend`.

## 🔍 Validation

`dsoxlab check state-backends` prouve, sur du JSON :

- le **`lineage`** est le même avant et après : le state a **migré**, pas été
  recréé ; deux ressources en `mode: managed` ;
- `.terraform/terraform.tfstate` porte `backend.type = local` et
  `backend.config.path = etat/dev/terraform.tfstate` ;
- la config est **partielle** : dans une copie, `init` sans `-backend-config`
  résout `path` à `null`, et `-backend-config=prod...` résout sur `etat/prod` ;
- idempotence (`plan -detailed-exitcode` = 0).

Bloqué ? `dsoxlab hint state-backends`.
