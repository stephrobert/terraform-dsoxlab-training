# 🎯 Challenge : itérer sans fuiter

## Point de départ

`challenge/work` contient `versions.tf`, `variables.tf` (`services`, set NON
sensible ; `db_password`, sensible), `main.tf` (le `for_each` de `local_file.conf`
est troué), et `outputs.tf` (troué). `terraform apply` échoue en l'état.

## ✅ Objectif

1. **`main.tf`, `for_each`** : itérez sur **`var.services`** (non sensible). Une
   valeur **sensible** en clé `for_each` est refusée (`Invalid for_each
   argument`). Le `content`, lui, injecte `var.db_password` (ne pas modifier) et
   contamine l'attribut.
2. **`outputs.tf`, `empreinte`** : exposez le **`sha256`** du mot de passe **sans**
   le divulguer ni rendre l'output sensible. Le `sha256` d'un secret reste
   sensible : **déclassifiez-le** avec `nonsensitive()`.

Après `apply`, un second `terraform plan` ne doit plus rien proposer.

## 🧭 Ce que le lab vous fait constater

- **Une valeur sensible ne peut pas être une clé `for_each`** : marquer
  `sensitive` peut casser un `for_each`.
- **La contamination se lit dans `sensitive_values`** (`content` à `true`).
- **`nonsensitive()`** publie un hash sans désarmer le secret.

## 🔍 Validation

```bash
dsoxlab check write-code-sensitive-data-sensitive-values
```

Quatre tests lisant `terraform show -json` et `output -json` : les clés non
sensibles du `for_each`, la contamination de `content`, l'empreinte déclassifiée,
et l'idempotence. Aucun ne lit vos `.tf`.
