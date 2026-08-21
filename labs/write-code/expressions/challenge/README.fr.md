# 🎯 Challenge : écrire des expressions qui calculent juste

## Point de départ

`challenge/work` contient un projet cohérent mais incomplet. `versions.tf` et
`variables.tf` sont **fournis, à ne pas modifier** : `seuil` (number) vaut 3,
`perm_forcee` (string) vaut `""` par défaut. `main.tf` déclare `random_pet.hote`
et `local_file.marqueur`, mais le `file_permission` de ce dernier est un `???`.
`outputs.tf` est troué sur quatre outputs. `terraform apply` échoue en l'état.

## ✅ Objectif

1. **`main.tf`, `file_permission`** : rendre la permission optionnelle. Quand
   `perm_forcee` vaut `""`, l'argument doit être **omis**, ce qui s'exprime par
   **`null`**, pas par une chaîne vide (qui serait une permission invalide).
2. **`ref_hote`** : exposer l'id de `random_pet.hote`. Une ressource gérée se
   référence **sans préfixe** (`random_pet.hote.id`, jamais `resource....`).
3. **`egalite_stricte`** : `var.seuil` est-il égal à la **chaîne** `"3"` ?
   L'opérateur `==` **ne convertit pas** les types.
4. **`calcul`** : `1` plus le double de `var.seuil`, en une expression. La
   **précédence** place `*` avant `+`.
5. **`perm_effective`** : la permission réellement appliquée à
   `local_file.marqueur`.

Après `apply`, un second `terraform plan` ne doit plus rien proposer.

## 🧭 Ce que le lab vous fait constater

- **Une ressource gérée se référence sans préfixe.**
- **`==` ne convertit pas** : le nombre 3 n'est pas égal à `"3"` (résultat
  `false`), alors que l'arithmétique, elle, convertit.
- **`*` passe avant `+`** : `1 + var.seuil * 2` vaut 7.
- **`null` omet un argument** : `perm_effective` retombe sur `0777`, le défaut du
  provider, là où `""` aurait échoué.

## 🔍 Validation

```bash
dsoxlab check write-code-expressions
```

Six tests lisant `terraform show -json`, `output -json` et des codes retour : la
référence sans préfixe, l'égalité non convertie, la précédence (et le type
nombre), l'omission par `null` (défaut 0777, puis une permission forcée), et
l'idempotence. Aucun ne lit vos `.tf`.
