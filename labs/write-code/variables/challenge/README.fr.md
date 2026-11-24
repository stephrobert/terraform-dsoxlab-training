# Variables Terraform, typage, validation et précédence

## La situation

**Sous-objectif d'examen visé : 2e (variables et outputs, types complexes).**

Déclarer une variable et poser un `default` ne fait échouer personne. Ce lab
traite les trois pièges qui font échouer : l'ordre réel de précédence des
sources de valeurs, le `null` explicite qui écrase un `default` tant que
`nullable = false` n'est pas posé, et la confusion entre `sensitive` (un
masquage d'affichage) et une valeur qui reste en clair dans le fichier d'état.

## Capacité visée

Paramétrer une configuration pour qu'elle produise le bon résultat quelle que
soit la source de valeurs employée : contraindre un type complexe, rejeter une
valeur invalide avant tout appel de provider, garantir qu'un `null` retombe sur
le défaut, savoir quelle source gagne quand plusieurs se contredisent.

## D'où part l'apprenant

`challenge/work` contient une configuration incomplète mais cohérente :

- `versions.tf` et `main.tf` : fournis, non modifiables. `main.tf` construit un
  `local_file` rendu à partir des variables, un `random_password`, et les blocs
  `output` qui exposent le tout. Sa forme dicte les types attendus.
- `variables.tf` : troué. Les blocs existent, mais `type`, `validation`,
  `nullable` et `sensitive` sont remplacés par `???`, sur `env`, `nodes`
  (une map d'objets à attributs optionnels), `retention_days` et `db_password`.
- `terraform.tfvars` : fourni, non modifiable, pose `env = "dev"` et,
  volontairement, `retention_days = null`.
- `zz-override.auto.tfvars` : fourni, non modifiable, repose `env`.

`terraform init` est déjà joué. En l'état, `terraform validate` échoue.

## L'état à atteindre

1. `terraform validate` réussit et `terraform apply` aboutit sans intervention.
2. `nodes` est contrainte en `map(object(...))` avec au moins un attribut
   `optional()` porteur d'un défaut : l'entrée incomplète du fichier de valeurs
   est complétée par Terraform lui-même.
3. Une valeur hors ensemble autorisé pour `env` fait échouer le `plan` sur le
   message du bloc `validation`, sans solliciter aucun provider.
4. `retention_days` vaut son défaut dans l'état final alors que le fichier de
   valeurs lui affecte `null` : c'est `nullable = false` qui le garantit.
5. `env` vaut ce que pose `zz-override.auto.tfvars`, y compris lorsqu'un
   `TF_VAR_env` contradictoire est exporté, et cède devant un `-var`.
6. `db_password` est sensible : l'output correspondant est signalé comme tel.

## Comment on le prouve

Les tests n'ouvrent jamais les fichiers `.tf` de l'apprenant.

- `terraform validate -json` doit renvoyer `valid: true`.
- `terraform output -json` couvre les états 2, 4 et 6 : structure complète de
  `nodes` après application des `optional()`, valeur de `retention_days`
  comparée au défaut attendu, drapeau `sensitive: true` sur le mot de passe.
- `terraform show -json` relit le contenu écrit par la ressource `local_file`
  en `mode: managed` : les valeurs ont traversé la configuration, pas seulement
  les outputs.
- L'état 3 se prouve par le code de sortie : `plan` avec une valeur interdite
  en `-var` doit échouer, le même plan avec une valeur autorisée doit passer.
- L'état 5 se prouve par trois lectures de `terraform output -json` sur `env` :
  sans variable d'environnement, avec `TF_VAR_env` exporté à une autre valeur,
  puis avec un `-var`. Seule la troisième doit changer le résultat.
- `terraform plan -detailed-exitcode` doit renvoyer 0 après l'apply final.

## 🎯 Challenge : typer, valider, et maîtriser la précédence

### Point de départ

`challenge/work` contient une configuration cohérente mais incomplète.
`versions.tf` et `main.tf` sont **fournis, à ne pas modifier** : `main.tf`
consomme les variables (un `local_file` rendu, un `random_password`, les
`output`), et sa forme **dicte les types attendus**.

Deux fichiers de valeurs sont fournis, **à ne pas modifier** :

- `terraform.tfvars` : pose `env = "dev"` et, volontairement, `retention_days = null`.
- `zz-override.auto.tfvars` : repose `env = "staging"`.

`variables.tf` est **troué** (`???`) sur quatre variables : `env`, `nodes`,
`retention_days` et `db_password`. `terraform validate` échoue en l'état.

### ✅ Objectif

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

### 🧭 Ce que le lab vous fait constater

- **`env` vaut `staging`**, pas `dev` : un `*.auto.tfvars` l'emporte sur
  `terraform.tfvars`. Un `TF_VAR_env` exporté ne le déloge pas ; seul un `-var`
  y parvient.
- **`retention_days` vaut 7** malgré le `null` du fichier : c'est
  `nullable = false` qui le garantit.
- **`db_password` reste en clair dans le state.** `sensitive` masque
  l'affichage, mais `terraform show -json` rend la valeur. Ce n'est pas une
  protection du secret.

### 🔍 Validation

```bash
dsoxlab check write-code-variables
```

Huit tests lisant `terraform validate -json`, `show -json`, `output -json` et
des codes retour : la validité, les `optional()` complétés, le `nullable`, le
masque `sensitive` face au clair du state, la précédence des sources, le rejet
de validation, et l'idempotence. Aucun ne lit vos `.tf`.
