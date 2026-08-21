# 🎯 Challenge : une chaîne de locals qui traverse trois pièges

## Point de départ

`challenge/work` déclare un projet dont **seul `locals.tf` est troué**.
`versions.tf`, `variables.tf`, `main.tf` et `outputs.tf` sont **complets, à ne
pas modifier**. Les variables fournies sont `project` (`Atelier_Locaux`),
`environment` (`prod`), `node_count`, `memory_mb` et `db_password` (sensible).

`locals.tf` arrive avec **trois blocs `locals` distincts**, volontairement :
Terraform les fusionne, un local d'un bloc peut donc en référencer un autre.
Chaque valeur est un `???`, et `terraform init` échoue en l'état.

## ✅ Objectif

Écrire les neuf locals, répartis en trois blocs :

**Nommage**
1. `slug` : `project` en minuscules, underscores changés en tirets.
2. `base_name` : `slug` et `environment` joints par un tiret. Attendu :
   `atelier-locaux-prod`.

**Calcul**
3. `is_production` : vrai seulement si `environment` vaut `prod`.
4. `effective_ram` : la mémoire **doublée** en prod, sinon sa valeur. **Ce doit
   rester un nombre** : un mélange nombre/chaîne dans le ternaire le
   convertirait silencieusement en chaîne.
5. `node_names` : une liste de `node_count` chaînes `base_name-001`,
   `base_name-002`, ... Une expression `for` et `format("%s-%03d", ...)`.

**Dérivé d'une ressource** (donc inconnu au plan)
6. `build_digest` : les 8 premiers caractères de `random_id.build.hex`.
7. `manifest_name` : `base_name`, un tiret, `build_digest`, extension `.json`.
8. `db_dsn` : `postgres://app:<db_password>@localhost/<base_name>`. Il hérite de
   la sensibilité de `db_password`.

Après votre `apply`, `terraform plan` ne doit plus rien proposer.

## 🧭 Les trois pièges

- **Le ternaire convertit les types.** `4096 : "2048"` est valide mais rend une
  chaîne. `effective_ram` doit sortir en **nombre**.
- **Un local dérivé d'une ressource est inconnu au plan.** `manifest_name`
  apparaît en `(known after apply)`, contrairement à `base_name`.
- **La sensibilité se propage.** `db_dsn` dérive de `db_password` sensible :
  l'output correspondant est déjà marqué `sensitive`, ne le retirez pas.

## 🔍 Validation

```bash
dsoxlab check write-code-locals
```

Neuf tests. Ils lisent `terraform show -json` (plan et state) et `output -json` :
`after_unknown` pour la frontière plan/apply, le **type JSON** de `effective_ram`,
le `sensitive` de `db_dsn`, et le hex réel de la ressource. Aucun ne lit vos `.tf`.
