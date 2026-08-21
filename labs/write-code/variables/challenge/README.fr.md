# 🎯 Challenge : typer, valider, et maîtriser la précédence

## Point de départ

`challenge/work` contient une configuration cohérente mais incomplète.
`versions.tf` et `main.tf` sont **fournis, à ne pas modifier** : `main.tf`
consomme les variables (un `local_file` rendu, un `random_password`, les
`output`), et sa forme **dicte les types attendus**.

Deux fichiers de valeurs sont fournis, **à ne pas modifier** :

- `terraform.tfvars` : pose `env = "dev"` et, volontairement, `retention_days = null`.
- `zz-override.auto.tfvars` : repose `env = "staging"`.

`variables.tf` est **troué** (`???`) sur quatre variables : `env`, `nodes`,
`retention_days` et `db_password`. `terraform validate` échoue en l'état.

## ✅ Objectif

Complétez les quatre variables :

1. **`env`** (string) : ajoutez une **`validation`** qui refuse toute valeur hors
   de `dev`, `staging`, `prod`, et échoue au plan avant tout provider.
2. **`nodes`** : contraignez le **type** en `map(object(...))` avec `size`
   (string), `replicas` (number, **optionnel**, défaut 1) et `public` (bool,
   **optionnel**, défaut false). L'entrée incomplète du fichier de valeurs doit
   être complétée par Terraform.
3. **`retention_days`** (number, défaut 7) : garantissez qu'un `null` explicite
   **retombe sur le défaut** avec **`nullable = false`**.
4. **`db_password`** (string) : marquez-la **`sensitive`**.

Après `apply`, un second `terraform plan` ne doit plus rien proposer.

## 🧭 Ce que le lab vous fait constater

- **`env` vaut `staging`**, pas `dev` : un `*.auto.tfvars` l'emporte sur
  `terraform.tfvars`. Un `TF_VAR_env` exporté ne le déloge pas ; seul un `-var`
  y parvient.
- **`retention_days` vaut 7** malgré le `null` du fichier : c'est
  `nullable = false` qui le garantit.
- **`db_password` reste en clair dans le state.** `sensitive` masque
  l'affichage, mais `terraform show -json` rend la valeur. Ce n'est pas une
  protection du secret.

## 🔍 Validation

```bash
dsoxlab check write-code-variables
```

Huit tests lisant `terraform validate -json`, `show -json`, `output -json` et
des codes retour : la validité, les `optional()` complétés, le `nullable`, le
masque `sensitive` face au clair du state, la précédence des sources, le rejet
de validation, et l'idempotence. Aucun ne lit vos `.tf`.
