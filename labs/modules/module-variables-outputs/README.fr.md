# L'interface d'un module : quatre mécanismes au-delà de `type` et `default`

Un module se juge à ce qu'il **accepte** en entrée et à ce qu'il **garantit** en
sortie. Déclarer un `type` et un `default` couvre le cas simple, et laisse passer
quatre situations qui cassent en pratique : un **attribut d'objet** facultatif,
un **`null` passé explicitement**, une sortie qui devrait **refuser** de se
publier, et un **secret** qui traverse la frontière du module.

Ce tutoriel montre les quatre, mesurés sur une configuration jetable.

## Le terrain d'essai

Un module qui produit un jeton pour un canal de diffusion :

```hcl
# modules/bulletin/main.tf
resource "random_password" "jeton" {
  length = var.taille_jeton
}
```

Appelé au plus court, avec un seul attribut :

```hcl
module "bulletin" {
  source = "./modules/bulletin"

  canal = { nom = "interne" }
}
```

## `optional()` : rendre facultatif un attribut d'objet

`default` porte sur la **variable entière**, jamais sur les **champs** d'un
objet. Déclarez `object({ nom = string, frequence = string })` et l'appel
ci-dessus échoue : il manque un attribut.

Le mécanisme officiel est **`optional(type, defaut)`**, disponible depuis la
**1.3** :

```hcl
variable "canal" {
  type = object({
    nom       = string
    frequence = optional(string, "hebdomadaire")
    actif     = optional(bool, true)
  })
}
```

Le second argument est la valeur substituée quand l'attribut est **absent**. Le
module comble donc lui-même ce que l'appelant n'a pas fourni :

```json
{
  "actif": true,
  "frequence": "hebdomadaire",
  "nom": "interne"
}
```

Sans le second argument, `optional(string)` rendrait `null` : la variable serait
facultative, mais sans valeur de repli.

## `nullable` : un `null` explicite n'est pas une absence

Voici le piège que l'on ne voit pas venir. Un appelant écrit
`libelle = null` en croyant « ne rien passer ». Avec une variable qui a pourtant
un `default` :

```hcl
variable "libelle" {
  type    = string
  default = "bulletin"
}
```

La valeur reçue est **`null`**, pas `"bulletin"` :

```text
libelle = null
```

Parce que **`nullable` vaut `true` par défaut** : un `null` explicite est une
valeur comme une autre, et il écrase le défaut. La correction tient en une
ligne :

```hcl
variable "libelle" {
  type     = string
  default  = "bulletin"
  nullable = false
}
```

Le même appel rend alors `"bulletin"`. Un module réutilisable pose donc
`nullable = false` sur toute variable dont le défaut doit **toujours** valoir.

## `validation` : refuser une valeur, et dire où corriger

Un bloc `validation` rejette une valeur avec un message que vous écrivez :

```hcl
variable "taille_jeton" {
  type    = number
  default = 16

  validation {
    condition     = var.taille_jeton >= 12 && var.taille_jeton <= 64
    error_message = "taille_jeton doit etre comprise entre 12 et 64."
  }
}
```

Le refus est explicite, et la dernière ligne compte quand plusieurs modules
déclarent la même variable :

```text
Error: Invalid value for variable

  on main.tf line 6, in module "bulletin":
   6:   taille_jeton = 8
    ├────────────────
    │ var.taille_jeton is 8

taille_jeton doit etre comprise entre 12 et 64.

This was checked by the validation rule at
modules/bulletin/variables.tf:19,3-13.
```

Terraform nomme **deux** endroits : où la valeur fautive a été passée, et où la
règle qui l'a refusée est écrite.

## Les sorties portent plus que `value`

Un bloc `output` accepte notamment **`description`**, **`sensitive`**,
**`precondition`**, **`type`** et **`depends_on`**. Deux d'entre eux changent le
comportement observable.

**`sensitive`** empêche l'affichage de la valeur, et sa nécessité **remonte** :

```hcl
output "jeton" {
  description = "Jeton d'acces du canal."
  sensitive   = true
  value       = random_password.jeton.result
}
```

Republiez cette valeur à la racine sans la marquer, et le plan **échoue** :

```text
Error: Output refers to sensitive values

To reduce the risk of accidentally exporting sensitive data that was intended
to be only internal, Terraform requires that any root module output
containing sensitive data be explicitly marked as sensitive, to confirm your
intent.
```

Le module enfant n'a même pas besoin d'avoir marqué sa propre sortie : la
**contamination** vient de la valeur elle-même. Chaîner des modules sans le
savoir mène droit à ce refus.

**`precondition`** permet à une sortie de **refuser de se publier** :

```hcl
output "emplacement" {
  value = local_file.this.filename

  precondition {
    condition     = var.canal.actif
    error_message = "L'emplacement n'est publie que pour un canal actif."
  }
}
```

La condition est évaluée **au plan**, et son échec l'arrête net :

```text
Error: Module output value precondition failed
```

C'est la façon d'exprimer une **garantie** : le module ne publie pas une valeur
qui n'aurait pas de sens dans l'état où on l'appelle.

## À vous de jouer

Vous savez rendre facultatif un attribut d'objet avec `optional()`, protéger un
défaut d'un `null` explicite avec `nullable = false`, refuser une valeur hors
bornes avec un message qui dit où corriger, garder une sortie derrière une
`precondition`, et faire traverser un secret sans casser le plan. Le challenge
vous remet un module appelé **deux fois**, dont toute l'interface est à écrire :
c'est l'appel minimal qui la mettra à l'épreuve.

```bash
dsoxlab run modules-module-variables-outputs
dsoxlab check modules-module-variables-outputs
dsoxlab hint modules-module-variables-outputs
```

Sous-objectif d'examen visé : **2e** (variables et outputs, types complexes), en
appui sur **4a** et **2f**.

Référence : [variables et outputs d'un module](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/variables-outputs-module/)
