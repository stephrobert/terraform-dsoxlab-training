# Scénario : la valeur qui ne touche jamais le state

**Sous-objectif d'examen visé : 2f (gérer les données sensibles), niveau Professional.**

`sensitive` masque l'affichage mais laisse le secret en clair dans le state. Une valeur **éphémère**, elle, n'y est **jamais écrite**. L'apprenant doit générer un jeton éphémère, le garder hors du state, et l'exposer proprement, mesures à l'appui.

## Capacité visée

Déclarer une valeur éphémère avec un bloc `ephemeral`, comprendre qu'elle ne peut aller que dans un contexte éphémère (sinon `Invalid use of ephemeral value`), qu'un output racine la refuse (`Ephemeral value not allowed`), et l'exposer sans la divulguer avec `ephemeralasnull()`. Distinguer une valeur éphémère d'un `random_password` ordinaire, persisté en clair dans le state.

## D'où part l'apprenant

`challenge/work/` contient un projet incomplet. Aucune VM, aucun compte distant : seuls `hashicorp/local` et `hashicorp/random` (>= 3.7 pour la ressource éphémère) sont utilisés, `terraform init` est déjà passé. Le lab tourne partout où `terraform` 1.15 est sur le PATH, sans réseau.

Le répertoire contient `versions.tf`, `variables.tf` (`longueur`, number, défaut 20), un `main.tf` où le bloc du jeton est troué et un `outputs.tf` troué :

```hcl
??? "random_password" "jeton" {        # quel mot-cle produit une valeur ephemere ?
  length = var.longueur
}
resource "random_password" "persistant" { length = var.longueur }   # contraste, persiste
resource "local_file" "marqueur" { ... }                            # non secret, ne pas y fuiter le jeton
```

```hcl
output "jeton_masque" { value = ??? }  # exposer le jeton ephemere SANS le divulguer
```

`terraform apply` échoue en l'état : les `???` ne sont pas du HCL valide, et exposer un éphémère au root sans précaution serait de toute façon refusé.

## L'état à atteindre

1. Le bloc du jeton est déclaré **`ephemeral`** : sa valeur est générée pendant l'opération mais **jamais écrite** dans le state.
2. `random_password.persistant` reste une ressource ordinaire : son `result` est présent **en clair** dans le state. C'est le contraste qui donne son sens à l'éphémère.
3. `jeton_masque` expose le résultat du jeton éphémère via **`ephemeralasnull()`**, et vaut donc `null`. Exposer directement `ephemeral.random_password.jeton.result` lèverait `Ephemeral value not allowed`.
4. Le jeton éphémère n'apparaît **nulle part** dans le state : aucune adresse éphémère, aucune valeur.
5. Le projet converge : un second plan juste après l'apply ne propose plus rien, bien que la valeur éphémère soit regénérée à chaque run.

## Comment on le prouve

Les tests n'ouvrent jamais les `.tf` de l'apprenant et ne parsent aucune sortie humaine. Ils lancent Terraform dans `challenge/work` et ne lisent que du JSON ou des codes retour.

1. `terraform show -json` : il y a **exactement un** `random_password` dans le state, nommé `persistant`, et son `result` fait 20 caractères en clair. Deux `random_password` trahiraient un jeton déclaré `resource` au lieu de `ephemeral`.
2. Toujours dans `show -json` : aucune adresse ne contient `ephemeral`, et toutes les ressources sont en `mode: managed`. La valeur éphémère est absente du state.
3. `terraform output -json` : `jeton_masque` vaut `null`. `ephemeralasnull()` neutralise l'éphémère ; une valeur non éphémère serait ressortie telle quelle, donc ce `null` prouve le caractère éphémère.
4. `terraform plan -detailed-exitcode` retourne 0 juste après l'apply.

Référence : https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/gestion-donnees-sensibles/ephemeral-values/
