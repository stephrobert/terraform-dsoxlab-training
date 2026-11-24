# Ce que les expressions calculent vraiment

## La situation

**Sous-objectif d'examen visé : 2e (déclarer et consommer des expressions, types et valeurs).**

Écrire une interpolation ne fait échouer personne. Ce qui fait échouer, ce sont les règles fines : la référence d'une ressource gérée s'écrit sans préfixe, l'opérateur `==` ne convertit pas les types là où l'arithmétique le fait, la précédence place `*` avant `+`, et `null` omet un argument là où une chaîne vide serait une valeur invalide. L'apprenant doit poser ces expressions et le prouver, mesures à l'appui.

## Capacité visée

Lire et écrire des expressions Terraform correctes : référencer une ressource gérée sans préfixe, anticiper le résultat d'une égalité entre types différents, appliquer la précédence des opérateurs, et employer `null` pour rendre un argument optionnel. Savoir vérifier le **type** d'un résultat, pas seulement sa valeur.

## D'où part l'apprenant

`challenge/work/` contient un projet incomplet. Aucune VM, aucun compte distant : seuls `hashicorp/random` et `hashicorp/local` sont utilisés, `terraform init` est déjà passé. Le lab tourne partout où `terraform` est sur le PATH, sans réseau.

Le répertoire contient `versions.tf`, `variables.tf` (`seuil`, number, défaut 3 ; `perm_forcee`, string, défaut `""`), un `main.tf` où `random_pet.hote` est déclarée, `local_file.marqueur` référence son id dans son nom de fichier, et son `file_permission` est un `???`, et un `outputs.tf` troué :

```hcl
output "ref_hote"        { value = ??? }   # id de la ressource, SANS prefixe
output "egalite_stricte" { value = ??? }   # var.seuil == "3" (== ne convertit pas)
output "calcul"          { value = ??? }   # 1 + le double de var.seuil (precedence)
output "perm_effective"  { value = ??? }   # la permission reellement appliquee
```

`terraform apply` échoue en l'état : les `???` ne sont pas du HCL valide, et un `file_permission` mis à `""` serait de toute façon rejeté.

## L'état à atteindre

1. `file_permission` vaut `null` quand `perm_forcee` est vide (donc l'argument est omis), et la valeur fournie sinon. Écrire `""` directement échoue : une chaîne vide n'est pas une omission.
2. `ref_hote` expose l'id de `random_pet.hote`, référencée **sans préfixe**.
3. `egalite_stricte` vaut **false** : `var.seuil` (nombre 3) n'est pas égal à la chaîne `"3"`, car `==` ne convertit pas.
4. `calcul` vaut **7** : `1 + var.seuil * 2`, la multiplication d'abord.
5. `perm_effective` vaut `0777` sur un apply par défaut : la permission omise retombe sur le défaut du provider.
6. Le projet converge : un second plan juste après l'apply ne propose plus rien.

## Comment on le prouve

Les tests n'ouvrent jamais les `.tf` de l'apprenant et ne parsent aucune sortie humaine. Ils lancent Terraform dans `challenge/work` et ne lisent que du JSON ou des codes retour.

1. `terraform show -json` donne l'id du `random_pet`, et `terraform output -json` donne `ref_hote` : les deux sont égaux.
2. `egalite_stricte` vaut `false` dans `output -json`.
3. `calcul` vaut `7` et est de type nombre.
4. `perm_effective` vaut `0777` par défaut ; un rejeu avec `-var perm_forcee=0600` le fait passer à `0600`, puis l'état est restauré.
5. `terraform plan -detailed-exitcode` retourne 0 juste après l'apply.

Référence : https://www.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/expressions-terraform/

## 🎯 Challenge : écrire des expressions qui calculent juste

### Point de départ

`challenge/work` contient un projet cohérent mais incomplet. `versions.tf` et
`variables.tf` sont **fournis, à ne pas modifier** : `seuil` (number) vaut 3,
`perm_forcee` (string) vaut `""` par défaut. `main.tf` déclare `random_pet.hote`
et `local_file.marqueur`, mais le `file_permission` de ce dernier est un `???`.
`outputs.tf` est troué sur quatre outputs. `terraform apply` échoue en l'état.

### ✅ Objectif

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

### 🧭 Ce que le lab vous fait constater

- **Une ressource gérée se référence sans préfixe.**
- **`==` ne convertit pas** : le nombre 3 n'est pas égal à `"3"` (résultat
  `false`), alors que l'arithmétique, elle, convertit.
- **`*` passe avant `+`** : `1 + var.seuil * 2` vaut 7.
- **`null` omet un argument** : `perm_effective` retombe sur `0777`, le défaut du
  provider, là où `""` aurait échoué.

### 🔍 Validation

```bash
dsoxlab check write-code-expressions
```

Six tests lisant `terraform show -json`, `output -json` et des codes retour : la
référence sans préfixe, l'égalité non convertie, la précédence (et le type
nombre), l'omission par `null` (défaut 0777, puis une permission forcée), et
l'idempotence. Aucun ne lit vos `.tf`.
