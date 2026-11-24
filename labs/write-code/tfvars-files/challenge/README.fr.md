# La faute de frappe qui ne casse rien

## La situation

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

Référence : https://www.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/fichiers-tfvars/

## 🎯 Challenge : corriger la faute, faire gagner le JSON

### Point de départ

`challenge/work` contient un projet **applicable en l'état** : `versions.tf`,
`variables.tf` (`region`, `bucket` défaut `app-defaut`, `replicas` défaut 1),
`main.tf` (fourni), et un `terraform.tfvars` **dégradé** :

```hcl
region   = "eu-west-3"
bukcet   = "prod"     # faute de frappe
replicas = 2
```

`terraform apply` **réussit** (la variable non déclarée n'est qu'un warning),
mais `bucket` reste à `app-defaut`.

### ✅ Objectif

1. **Corrigez la faute de frappe** dans `terraform.tfvars` : `bukcet` → `bucket`,
   pour que `bucket` vaille `prod`. Une variable non déclarée dans un `.tfvars`
   ne fait qu'un **avertissement** : elle ne casse rien, elle laisse la vraie
   variable à son défaut.
2. **Créez un `terraform.tfvars.json`** posant `replicas = 5`. Comme la variante
   **JSON l'emporte** sur `terraform.tfvars` (qui pose 2), `replicas` doit valoir
   **5**.

Après `apply`, un second `terraform plan` ne doit plus rien proposer.

### 🧭 Ce que le lab vous fait constater

- **Une faute de frappe dans un `.tfvars` ne casse pas le plan** : elle produit
  un warning et la variable reste à son défaut.
- **`terraform.tfvars.json` bat `terraform.tfvars`** : c'est un niveau de
  précédence distinct, plus fort.

### 🔍 Validation

```bash
dsoxlab check write-code-tfvars-files
```

Quatre tests lisant `terraform output -json` : `bucket` à `prod` (faute
corrigée), `replicas` à 5 (JSON gagnant), `region`, et l'idempotence. Aucun ne lit
vos `.tf`.
