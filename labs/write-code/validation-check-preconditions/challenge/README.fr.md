# 🎯 Challenge : quatre niveaux de validation

## ✅ Objectif

Dans `challenge/work`, remplissez les **quatre niveaux** de validation. Quatre
fichiers sont troués (`condition` et `error_message` à écrire) :

1. **`variables.tf`** : la `validation` de `nom_projet` (1 à 20 caractères) et
   celle de `taille_lot` (validation **croisée** : `taille_lot <= taille_max`).
2. **`main.tf`** : dans `lifecycle`, la `precondition` (garde-fou :
   `taille_max <= 10`) et la `postcondition` (le nom généré n'est pas vide ;
   c'est la seule à disposer de `self`).
3. **`outputs.tf`** : la `precondition` de l'output `noms` (autant de noms que
   `taille_lot`).
4. **`checks.tf`** : l'`assert` du bloc `check`. Il doit **échouer** sur l'état
   final (le manifeste compte `taille_lot` lignes, pas `taille_max`) : c'est
   ainsi qu'on montre qu'un `check` **avertit sans bloquer**.

## 🔍 Validation

`dsoxlab check write-code-validation-check-preconditions` prouve, sur du JSON :

- le tableau `checks` de `show -json` porte les **quatre** `kind` (`var`,
  `resource`, `output_value`, `check`) ; les trois premiers en `pass`, le
  `check` en `fail` avec votre message ;
- l'apply réussit **malgré** ce `check` en échec ;
- `plan -var taille_max=20` échoue (precondition) ;
- `validate -json` rend `valid: true` là où `plan -var taille_lot=10` échoue ;
- `plan -detailed-exitcode` rend `2` (data source du `check` relu à chaque plan).

Bloqué ? `dsoxlab hint write-code-validation-check-preconditions`.
