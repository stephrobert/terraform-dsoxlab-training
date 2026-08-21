# 🎯 Challenge : composer des valeurs avec les fonctions HCL

## ✅ Objectif

La configuration livrée dans `challenge/work` **ne se valide pas**. Sept `locals`
et deux attributs de ressource sont remplacés par des `???`, et une déclaration
manque dans `versions.tf`.

Complétez-la **uniquement avec des expressions de fonctions**. Aucune valeur ne
doit être écrite en dur : tout se dérive des variables de `variables.tf`.

## 📋 Ce qui est fourni

| Fichier | État |
|---|---|
| `variables.tf` | **complet, à ne pas modifier** |
| `outputs.tf` | **complet, à ne pas modifier** |
| `node.yaml.tftpl` | **complet, à ne pas modifier** |
| `versions.tf` | une déclaration de provider manque |
| `locals.tf` | sept `???` à remplacer |
| `main.tf` | deux `???` à remplacer |

Les variables valent `environments_csv = "prod,dev,prod,staging"`,
`tags = { projet = "demo", equipe = "devops" }`, `environment = "qa"` et
`memory_mib = 1536`.

## 🎯 Les valeurs exactes à produire

| Output | Valeur attendue | Le piège |
|---|---|---|
| `env_uniques` | `["dev", "prod", "staging"]` | le CSV contient un doublon, et `for_each` refuse une liste |
| `env_recycle` | `"staging"` | accès à l'**index 5** sur la liste triée de 3 éléments |
| `taille` | `"small"` | `"qa"` est **absent** de la table, le plan ne doit pas s'interrompre |
| `tags_effectifs` | contient `projet`, `equipe`, et `env = "qa"` | l'ordre de fusion décide du gagnant |
| `memory_gib` | `2` | 1536 Mio font 1,5 Gio, et l'arrondi ne va pas vers le bas |
| `tfvars_rendu` | `env = "qa"` puis `gib = 2`, une paire par ligne | produit par une fonction **de provider** |

## 🧩 Les trois pièges

1. **`element()` hors bornes reboucle en modulo.** L'index 5 sur trois éléments
   donne `5 % 3 = 2`. Elle ne retombe pas sur le premier élément.
2. **`lookup()` sans valeur de repli lève une erreur.** Elle ne rend pas `null`.
3. **Dans un template, seul `${` s'échappe en `$${`.** Les fichiers rendus doivent
   contenir `$HOME` et `$(date)` **intacts**, ainsi que le texte littéral
   `${AUTRE}`.

## 🏗️ Ce que la ressource doit produire

`local_file.node` crée **un fichier par environnement distinct**, adressé dans le
state par la valeur (`["dev"]`, `["prod"]`, `["staging"]`) et non par un index
numérique. Chaque fichier reçoit `hostname = "node-<environnement>"`.

## ⚠️ Le provider intégré

L'output `tfvars_rendu` exige une fonction du provider **intégré** `terraform`.
Déclarez-le dans `required_providers` avec la source
`terraform.io/builtin/terraform`, puis **relancez `terraform init`**. Sans cela,
l'appel échoue sur `Unknown provider`.

## 🔍 Validation

```bash
dsoxlab check write-code-functions
```

Les tests interrogent l'état structuré (`terraform output -json`,
`terraform show -json`), jamais vos fichiers `.tf`. Ils vérifient en plus que
`terraform plan -detailed-exitcode` retourne **0** après l'`apply` : une
expression instable, un horodatage par exemple, ferait échouer ce contrôle.
