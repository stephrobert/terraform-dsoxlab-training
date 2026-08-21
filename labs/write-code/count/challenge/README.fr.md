# 🎯 Challenge : choisir count ou for_each, et le prouver

## Point de départ

`challenge/work` déclare un petit projet. `versions.tf` et `variables.tf` sont
**complets, à ne pas modifier**. Trois variables pilotent le tout : `services`
(un `list(string)`, `["web", "api", "cache"]`), `workers` (un nombre, `3`) et
`rapport` (un booléen, `false`).

`main.tf` livre la **version count applicable** de `local_file.service`,
volontairement. `workers.tf`, `rapport.tf` et `outputs.tf` arrivent troués
(`???`).

## ✅ Objectif

**Lancez d'abord `init` puis `apply`** sur la version count : vous avez alors
`service[0]`, `[1]`, `[2]` dans l'état. Un `plan -var 'services=["web","cache"]'`
montre le piège : retirer un service en recrée un autre.

Ensuite :

1. **Migrez `local_file.service`** vers `for_each` keyé par nom, et ajoutez les
   blocs `moved` pour que la migration ne détruise rien.
2. **`random_pet.worker`** : des copies interchangeables, donc
   `count = var.workers`.
3. **`local_file.rapport`** : optionnel, donc `count = var.rapport ? 1 : 0`.
4. **Sorties** : `noms_workers` (splat sur les workers), `chemins_services` (une
   expression `for` sur la map des services, car le splat ne s'applique pas à
   `for_each`), `rapport` (`one()` sur le rapport 0-ou-1).

Après votre apply final, un second `terraform plan` ne doit plus rien proposer.

## 🧭 Le piège à éviter

- **`count` indexe par entier, `for_each` par clé.** Retirer un élément du milieu
  d'une liste `count` décale tous les suivants.
- **Un bloc ne porte jamais les deux** : `count` et `for_each` ensemble lèvent
  `Invalid combination of "count" and "for_each"`.
- **Migrer sans `moved`** détruit et recrée toutes les instances.

## 🔍 Validation

```bash
dsoxlab check write-code-count
```

Huit tests lisant `terraform show -json` et `output -json` : le type d'index des
instances `service`, les actions du plan au retrait, la migration non
destructrice (une preuve `moved` reconstruite depuis `challenge/reference/`), la
réduction de count, le rapport conditionnel, et l'idempotence. Aucun ne lit vos
`.tf`.
