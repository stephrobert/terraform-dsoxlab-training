# Quand la sensibilité casse for_each

## La situation

**Sous-objectif d'examen visé : 2f (gérer les données sensibles), niveau Professional.**

`sensitive` masque l'affichage, mais il a un effet de bord rarement enseigné : une valeur sensible ne peut pas servir de clé `for_each`. Marquer une variable `sensitive` peut donc casser une configuration qui marchait. L'apprenant doit itérer sur des clés non sensibles tout en injectant un secret, et exposer une empreinte sans fuiter.

## Capacité visée

Comprendre que la sensibilité se propage et a des effets de bord : une valeur sensible interdite comme clé `for_each` (`Invalid for_each argument`), un attribut contaminé marqué dans `sensitive_values`, et un `sha256` de secret qui reste sensible tant qu'il n'est pas déclassifié par `nonsensitive()`.

## D'où part l'apprenant

`challenge/work/` contient un projet incomplet. Aucune VM, aucun compte distant : seul `local` est utilisé. Le lab tourne partout où `terraform` est sur le PATH, sans réseau.

Le répertoire contient `versions.tf`, `variables.tf` (`services`, set non sensible ; `db_password`, sensible), un `main.tf` où le `for_each` de `local_file.conf` est troué, et un `outputs.tf` troué :

```hcl
resource "local_file" "conf" {
  for_each = ???        # iterer sur les services NON sensibles (pas une valeur sensible)
  filename = "${path.module}/out/${each.key}.conf"
  content  = "service=${each.key}\npassword=${var.db_password}\n"   # contamine content
}
output "empreinte" { value = ??? }   # sha256 du secret, declassifie
```

`terraform apply` échoue en l'état : les `???` ne sont pas du HCL valide, et une valeur sensible en clé `for_each` serait de toute façon refusée.

## L'état à atteindre

1. `local_file.conf` itère sur `var.services` (non sensible) : deux instances, clés `web` et `db`. Une clé `for_each` sensible lèverait `Invalid for_each argument`.
2. L'attribut `content` de chaque `conf` est marqué sensible dans `sensitive_values` du state, car il injecte `var.db_password`.
3. `empreinte` expose le `sha256` du mot de passe **déclassifié** par `nonsensitive()` : l'output n'est pas sensible, et c'est un hachage, pas le secret.
4. Le projet converge : un second plan juste après l'apply ne propose plus rien.

## Comment on le prouve

Les tests n'ouvrent jamais les `.tf` de l'apprenant. Ils lisent `terraform show -json` (dont `sensitive_values`), `output -json` et des codes retour.

1. `terraform show -json` : les instances `conf` ont pour index `web` et `db` (le `for_each` a abouti sur des clés non sensibles).
2. Toujours dans ce JSON, chaque `conf` a `sensitive_values.content` à `true` : la contamination est tracée.
3. `terraform output -json` : `empreinte` n'est pas sensible et fait 64 caractères hexadécimaux.
4. `terraform plan -detailed-exitcode` retourne 0 juste après l'apply.

Référence : https://www.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/gestion-donnees-sensibles/sensitive-terraform/

## 🎯 Challenge : itérer sans fuiter

### Point de départ

`challenge/work` contient `versions.tf`, `variables.tf` (`services`, set NON
sensible ; `db_password`, sensible), `main.tf` (le `for_each` de `local_file.conf`
est troué), et `outputs.tf` (troué). `terraform apply` échoue en l'état.

### ✅ Objectif

1. **`main.tf`, `for_each`** : itérez sur **`var.services`** (non sensible). Une
   valeur **sensible** en clé `for_each` est refusée (`Invalid for_each
   argument`). Le `content`, lui, injecte `var.db_password` (ne pas modifier) et
   contamine l'attribut.
2. **`outputs.tf`, `empreinte`** : exposez le **`sha256`** du mot de passe **sans**
   le divulguer ni rendre l'output sensible. Le `sha256` d'un secret reste
   sensible : **déclassifiez-le** avec `nonsensitive()`.

Après `apply`, un second `terraform plan` ne doit plus rien proposer.

### 🧭 Ce que le lab vous fait constater

- **Une valeur sensible ne peut pas être une clé `for_each`** : marquer
  `sensitive` peut casser un `for_each`.
- **La contamination se lit dans `sensitive_values`** (`content` à `true`).
- **`nonsensitive()`** publie un hash sans désarmer le secret.

### 🔍 Validation

```bash
dsoxlab check write-code-sensitive-data-sensitive-values
```

Quatre tests lisant `terraform show -json` et `output -json` : les clés non
sensibles du `for_each`, la contamination de `content`, l'empreinte déclassifiée,
et l'idempotence. Aucun ne lit vos `.tf`.
