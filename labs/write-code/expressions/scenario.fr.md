# Scénario : ce que les expressions calculent vraiment

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

Référence : https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/expressions-terraform/
