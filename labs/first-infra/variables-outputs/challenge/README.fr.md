# 🎯 Challenge : variables, locals et la précédence réelle

## Point de départ

`challenge/work` contient un projet incomplet. **Aucun provider distant, aucune
VM** : le lab tourne partout où `terraform` est sur le `PATH`, sans réseau.

`versions.tf` est déjà correct. `variables.tf`, `locals.tf`, `main.tf` et
`outputs.tf` sont **troués**. `terraform.tfvars` est fourni : il fixe `env` et
reste **muet sur `region`**.

`terraform plan` échoue en l'état : les `???` ne sont pas du HCL valide.

## ✅ Objectif

1. **Quatre variables typées** : `env` (string, défaut `dev`), `replicas`
   (number, défaut 2), `sizing` (un `object({ cpu, memory_mb })` avec défaut),
   et `region` — **sans défaut**.
2. **Deux validations** : `env` n'accepte que `dev`, `staging`, `prod` ;
   `replicas` reste entre 1 et 9. Chaque bloc porte son `error_message`, qui est
   **obligatoire**.
3. **Un fichier `env.auto.tfvars`** fixant `env = "prod"`.
4. **`local.stack_name`** valant `app-<env>-<region>`, calculé en interne.
5. **Un `local_file`** écrivant `manifest-<stack_name>.json`.
6. **Cinq sorties** : `env_effectif`, `region_effective`, `stack_name`,
   `sizing_total_mb` et `manifest_path`.

## 🧭 Les quatre marches, dans l'ordre

```
default  <  TF_VAR_  <  terraform.tfvars  <  *.auto.tfvars  <  -var
```

La marche **décisive** est la deuxième : un fichier de valeurs **bat** la
variable d'environnement. `TF_VAR_` se situe juste au-dessus du `default`, et en
dessous de **tout** fichier. C'est le rang que presque tout le monde place trop
haut, et s'en apercevoir en production coûte une soirée.

La plus **discrète** est la troisième : un `*.auto.tfvars` est chargé
automatiquement, après `terraform.tfvars`. Son nom ne le dit pas, aucune
commande ne le mentionne, et un collègue qui en dépose un dans le dépôt change
le comportement de tout le monde.

## 🔍 Validation

```bash
dsoxlab check first-infra-variables-outputs
```

Huit tests. Les quatre marches sont vérifiées **dans l'ordre**, en manipulant
réellement l'environnement et les fichiers. Les validations sont jugées sur le
**code retour seulement** : un message est une chaîne que son auteur choisit, en
faire un critère reviendrait à noter la rédaction. Un contre-contrôle vérifie
qu'une valeur admise **passe**, sans quoi une condition qui refuse tout ferait
passer le test pour la mauvaise raison.
