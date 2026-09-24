# Scénario : la faute de frappe qui ne casse rien

**Sous-objectif d'examen visé : 2e (configurer les variables d'entrée et les
sorties), la précédence des sources de valeurs en étant le coeur.**

Une variable mal orthographiée dans un `.tfvars` ne fait pas échouer le plan : elle produit un avertissement, et la vraie variable reste à son défaut. C'est un faux diagnostic classique. L'apprenant doit corriger une telle faute et prouver qu'un `terraform.tfvars.json` l'emporte sur `terraform.tfvars`.

## Capacité visée

Comprendre la précédence des fichiers de valeurs (dont `terraform.tfvars.json` au-dessus de `terraform.tfvars`) et le comportement d'une variable non déclarée : warning en fichier, erreur en `-var`, ignorée en `TF_VAR_`. Savoir qu'une faute de frappe dans un `.tfvars` laisse la variable à son défaut.

## D'où part l'apprenant

`challenge/work/` contient un projet complet et applicable. Aucune VM, aucun compte distant : seul `local` est utilisé. Le lab tourne partout où `terraform` est sur le PATH, sans réseau.

Le répertoire contient `versions.tf`, `variables.tf` (`region`, `bucket` défaut `app-defaut`, `replicas` défaut 1), `main.tf` (fourni), et un `terraform.tfvars` **dégradé** :

```hcl
region   = "eu-west-3"
bukcet   = "prod"     # FAUTE DE FRAPPE : "bukcet" au lieu de "bucket"
replicas = 2
```

`terraform apply` **réussit** en l'état (la variable non déclarée n'est qu'un warning), mais `bucket` reste à `app-defaut` : le résultat n'est pas celui attendu.

## L'état à atteindre

1. La faute de frappe est corrigée dans `terraform.tfvars` : `bucket` vaut `prod` (et non plus le défaut `app-defaut`).
2. Un `terraform.tfvars.json` est créé et pose `replicas = 5`. Comme la variante JSON l'emporte sur `terraform.tfvars` (qui pose 2), `replicas` vaut **5**.
3. `region` vaut `eu-west-3` (déjà fourni par `terraform.tfvars`).
4. Le projet converge : un second plan juste après l'apply ne propose plus rien.

## Comment on le prouve

Les tests n'ouvrent jamais les `.tf` de l'apprenant. Ils lisent `terraform output -json` et des codes retour.

1. `terraform output -json` : `bucket` vaut `prod`. Tant que la faute de frappe subsiste, il vaut `app-defaut`, et le test échoue.
2. `replicas` vaut `5`, un nombre : le `terraform.tfvars.json` a bien surchargé le `2` de `terraform.tfvars`.
3. `region` vaut `eu-west-3`.
4. `terraform plan -detailed-exitcode` retourne 0 juste après l'apply.

Référence : https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/fichiers-tfvars/
