# 🎯 Challenge : contraindre et verrouiller les versions

## Point de départ

`challenge/work` contient `versions.tf` (troué) et `main.tf` (fourni, deux
ressources triviales pour tirer les providers `local` et `random`).
`terraform init` échoue en l'état.

## ✅ Objectif

Complétez les trois contraintes de `versions.tf` :

1. **`required_version`** : un **littéral** contraignant Terraform à au moins
   `1.15.0` (par exemple `>= 1.15.0`). Le bloc `terraform` n'accepte **aucune**
   variable (`Variables not allowed`).
2. **`local`** : **épinglez exactement** la version `2.5.1` (opérateur `=`).
3. **`random`** : bornez en **pessimiste** pour autoriser toute la série `3.x`
   compatible (à partir de `3.6`) mais **jamais** `4.0` (`~> 3.6`).

Après `apply`, un second `terraform plan` ne doit plus rien proposer.

## 🧭 Ce que le lab vous fait constater

- **Le pin exact `=`** fait résoudre `local` pile à `2.5.1`.
- **Le pessimiste `~>`** garde `random` dans la série `3.x`.
- **Le lock file** enregistre des empreintes `h1:` et se committe.

## 🔍 Validation

```bash
dsoxlab check write-code-version-constraints
```

Quatre tests lisant `terraform version -json`, le lock file et des codes retour :
le pin exact de `local`, le pessimiste de `random`, les empreintes `h1:` du lock,
et l'idempotence. Aucun ne lit vos `.tf`.
