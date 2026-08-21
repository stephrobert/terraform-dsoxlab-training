# 🎯 Challenge : corriger la faute, faire gagner le JSON

## Point de départ

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

## ✅ Objectif

1. **Corrigez la faute de frappe** dans `terraform.tfvars` : `bukcet` → `bucket`,
   pour que `bucket` vaille `prod`. Une variable non déclarée dans un `.tfvars`
   ne fait qu'un **avertissement** : elle ne casse rien, elle laisse la vraie
   variable à son défaut.
2. **Créez un `terraform.tfvars.json`** posant `replicas = 5`. Comme la variante
   **JSON l'emporte** sur `terraform.tfvars` (qui pose 2), `replicas` doit valoir
   **5**.

Après `apply`, un second `terraform plan` ne doit plus rien proposer.

## 🧭 Ce que le lab vous fait constater

- **Une faute de frappe dans un `.tfvars` ne casse pas le plan** : elle produit
  un warning et la variable reste à son défaut.
- **`terraform.tfvars.json` bat `terraform.tfvars`** : c'est un niveau de
  précédence distinct, plus fort.

## 🔍 Validation

```bash
dsoxlab check write-code-tfvars-files
```

Quatre tests lisant `terraform output -json` : `bucket` à `prod` (faute
corrigée), `replicas` à 5 (JSON gagnant), `region`, et l'idempotence. Aucun ne lit
vos `.tf`.
