# Variables : typage, validation, nullable, sensitive et précédence

Déclarer une variable et poser un `default` ne fait échouer personne. Ce qui
fait échouer, ce sont quatre pièges rarement enseignés : le **type par défaut**
qui laisse tout passer, le `null` explicite qui **écrase** un `default`, le
`sensitive` qu'on prend pour une protection alors qu'il ne masque que
l'affichage, et l'**ordre de précédence** des sources de valeurs. Ce tutoriel
les montre sur un exemple **jetable** de catalogue ; le challenge vous les fera
enchaîner sur un autre cas.

## Une variable, c'est plus qu'un default

Le bloc `variable` accepte bien plus que `description`, `type` et `default`. Les
arguments qui comptent vraiment sont `validation`, `sensitive`, `nullable`
(défaut `true`) et, depuis Terraform 1.10, `ephemeral`. Sans contrainte de
`type`, une variable vaut **`any`** : elle accepte n'importe quoi, et le bug
n'apparaît qu'à l'usage.

```hcl
variable "region" {
  type    = string
  default = "eu-west-3"
}
```

Quelques noms sont **réservés** et ne peuvent pas nommer une variable : `source`,
`version`, `providers`, `count`, `for_each`, `lifecycle`, `depends_on`,
`locals`.

## Les types complexes, et optional()

Le sujet ne s'arrête pas à `list(string)`. Le type le plus utile en pratique est
**`object({...})`**, souvent dans une `map`, avec des attributs **`optional()`**
porteurs d'un défaut :

```hcl
variable "serveurs" {
  type = map(object({
    cpu     = number
    memoire = optional(number, 512)
    expose  = optional(bool, false)
  }))
}
```

Fournissez une entrée incomplète, et Terraform la **complète** avec les défauts
des `optional()` :

```hcl
serveurs = {
  api = { cpu = 2 }   # memoire = 512, expose = false ajoutes par Terraform
}
```

`set(...)`, `tuple([...])` et les objets imbriqués suivent la même logique. Un
`optional(x)` sans second argument vaut `null` par défaut ; avec un second
argument, il vaut ce défaut.

## La validation rejette avant tout provider

Un bloc **`validation`** vérifie une condition sur la variable et **échoue au
plan**, avant le moindre appel de provider. C'est la barrière la moins chère
contre une valeur absurde :

```hcl
variable "taille" {
  type = string

  validation {
    condition     = contains(["S", "M", "L"], var.taille)
    error_message = "taille doit valoir S, M ou L."
  }
}
```

```bash
terraform plan -var taille=XXL
```

```text
Error: Invalid value for variable
```

La configuration ne consomme aucune ressource : l'erreur tombe à la validation.

## Le piège du null : nullable

Voici le piège le plus rentable du sujet. Une variable a un `default`, on croit
donc être protégé. Mais passer **explicitement `null`** (souvent depuis un
fichier de valeurs généré) **écrase** le default et propage `null` :

```hcl
variable "essais" {
  type    = number
  default = 3
}
```

Avec `essais = null` dans un `terraform.tfvars`, la variable vaut **`null`**, pas
`3`. Pour forcer le retour au défaut, on pose **`nullable = false`** :

```hcl
variable "essais" {
  type     = number
  default  = 3
  nullable = false
}
```

Désormais, un `null` explicite **retombe sur `3`**. C'est exactement le
comportement attendu d'une variable qui ne doit jamais valoir `null`.

## sensitive masque l'affichage, pas le state

Dernier malentendu, et il est dangereux. **`sensitive = true` ne protège pas le
secret.** Il masque la valeur dans la sortie humaine de `plan`, `apply` et
`terraform output`, rien de plus. La documentation est explicite : « Terraform
still records sensitive values in the state, so anyone who can access your state
data can access your sensitive values. »

```hcl
variable "cle_api" {
  type      = string
  sensitive = true
}
```

Concrètement, `terraform show -json` et `terraform output -json` rendent la
valeur **en clair**, et le fichier d'état la stocke telle quelle.

<Aside type="caution" title="sensitive n'est pas du chiffrement">
Pour exclure réellement une valeur du plan et du state, c'est **`ephemeral =
true`** (Terraform 1.10+), pas `sensitive`. `sensitive` reste utile contre les
fuites dans les logs, mais ne remplace jamais un state chiffré et à accès
restreint.
</Aside>

## L'ordre de précédence des sources

Quand plusieurs sources donnent une valeur à la même variable, Terraform les
applique dans un **ordre fixe**, du plus faible au plus fort :

1. le `default` du bloc `variable` ;
2. la variable d'environnement **`TF_VAR_<nom>`** ;
3. le fichier **`terraform.tfvars`** ;
4. le fichier **`terraform.tfvars.json`** ;
5. les fichiers **`*.auto.tfvars`** (et `.json`), chargés en **ordre
   lexical** : le dernier nom dans l'alphabet gagne ;
6. les options **`-var`** et **`-var-file`** de la ligne de commande, appliquées
   dans l'ordre où elles sont fournies.

Deux surprises fréquentes : un `*.auto.tfvars` l'emporte sur un `TF_VAR_`
exporté, et entre deux `*.auto.tfvars`, c'est l'ordre alphabétique qui tranche,
pas l'ordre d'écriture. La ligne de commande, elle, gagne toujours.

## À vous de jouer

Vous savez qu'une variable sans `type` vaut `any`, qu'un `object` porte des
`optional()` à défaut, qu'une `validation` rejette au plan, qu'un `null`
explicite écrase un `default` sauf `nullable = false`, que `sensitive` ne masque
que l'affichage, et dans quel ordre les sources s'appliquent. Le challenge vous
fait poser ces contraintes sur une configuration troée, et les tests les
prouvent dans le JSON.

```bash
dsoxlab run write-code-variables
dsoxlab check write-code-variables
dsoxlab hint write-code-variables
```

Sous-objectifs d'examen visés : **2e** (variables et types complexes) et **2f**
(données sensibles).

Référence : [Les variables en Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/variables-terraform/)
