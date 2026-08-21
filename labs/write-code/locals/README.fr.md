# Les valeurs locales, et quand elles se calculent

Un **bloc `locals`** nomme des valeurs calculées, pour ne pas répéter la même
expression à dix endroits. Simple en apparence, mais trois choses surprennent :
plusieurs blocs `locals` **fusionnent**, un ternaire **convertit ses types sans
prévenir**, et un local dérivé d'une ressource n'est **pas connu au plan**. Ce
tutoriel les montre sur un exemple **jetable** de boutique, puis le challenge
vous fera enchaîner les trois pièges sur un autre cas.

La plupart des vérifications se font dans `terraform console`, qui évalue une
expression sans rien appliquer.

## Un local, c'est un nom pour une expression

La syntaxe se réduit à `nom = expression`. Un local **n'accepte ni `type`, ni
`description`, ni `sensitive`, ni `validation`** : c'est là toute la différence
avec une variable, qui, elle, peut être typée et documentée. Un local est une
valeur interne, calculée, que rien ne surcharge depuis l'extérieur.

```hcl
variable "enseigne" {
  type    = string
  default = "Ma_Boutique"
}

locals {
  ref = replace(lower(var.enseigne), "_", "-")
}
```

Un local peut référencer **quatre** choses : une **variable**, un **attribut de
ressource**, la **sortie d'une fonction**, et **un autre local**. Les deux
premiers exemples ci-dessus le montrent : `local.ref` normalise `var.enseigne`
avec deux fonctions.

## Plusieurs blocs locals fusionnent

On peut écrire autant de blocs `locals {}` qu'on veut, dans un ou plusieurs
fichiers. Terraform les **fusionne** : un local d'un bloc peut en référencer un
autre déclaré ailleurs, tant qu'aucun cycle n'apparaît.

```hcl
locals {
  etiquette = "${local.ref}-${var.palier}"
}
```

```bash
terraform console
```

```hcl
> local.etiquette
"ma-boutique-gold"
```

`local.etiquette` (dans un second bloc) consomme `local.ref` (dans le premier),
et le résultat est bien normalisé.

## Le piège du ternaire : les types se convertissent en silence

Voici l'erreur la plus fréquente. On croit souvent qu'un ternaire dont les deux
branches n'ont pas le même type **échoue**. C'est faux : Terraform **convertit
vers un type commun sans broncher**.

```hcl
locals {
  remise = var.palier == "gold" ? 20 : 5
}
```

```hcl
> type(local.remise)
number
```

Bien. Mais glissez un guillemet autour d'un nombre, et tout bascule :

```hcl
> type(true ? 20 : "5")
string

> type(true ? 20 : 5)
number
```

`20 : "5"` ne lève **aucune erreur**, il rend une **chaîne**. Un local censé
porter un nombre se retrouve typé chaîne, et le bug se révèle bien plus loin,
là où ce nombre est utilisé. La documentation recommande d'ailleurs d'être
explicite en cas de doute, avec une fonction de conversion :

```hcl
> true ? tostring(20) : "cinq"
"20"
```

La règle simple : ne mettez pas de guillemets autour d'un nombre, et si les deux
branches diffèrent vraiment, convertissez-les explicitement.

## Un local dérivé d'une ressource est inconnu au plan

Un local se calcule pendant le **plan**, sauf s'il référence un **attribut de
ressource** qui n'existe pas encore. Dans ce cas, sa valeur est
`(known after apply)`, exactement comme l'attribut dont il dépend.

```hcl
resource "random_id" "tirage" {
  byte_length = 4
}

locals {
  empreinte = upper(random_id.tirage.hex)
}
```

Sur un plan à froid, un output exposant `local.empreinte` apparaît en inconnu :
`random_id.tirage.hex` n'est produit qu'à l'apply, et le local hérite de cette
inconnue. Le plan JSON le montre dans `output_changes[].after_unknown`. C'est
aussi ce qui crée une **dépendance implicite** dans le graphe : le local dépend
de la ressource.

## La sensibilité se propage à travers un local

Dernier piège, et il bloque l'apply. Terraform considère comme **sensible toute
expression qui utilise une valeur sensible**. Un local qui assemble une chaîne à
partir d'une variable `sensitive = true` devient donc lui-même sensible :

```hcl
variable "mot_de_passe" {
  type      = string
  sensitive = true
}

locals {
  dsn = "postgres://app:${var.mot_de_passe}@localhost/base"
}
```

Un `output` qui expose `local.dsn` **sans** `sensitive = true` fait échouer
Terraform :

```text
Error: Output refers to sensitive values
```

La correction est d'annoter la sortie `sensitive = true`. La sensibilité n'est
pas une propriété qu'on choisit, elle se propage toute seule.

## À vous de jouer

Vous savez qu'un local n'est pas une variable, que les blocs fusionnent, que le
ternaire convertit ses types, qu'un local peut être inconnu au plan, et que la
sensibilité se propage. Le challenge vous fait construire une chaîne de locals
qui traverse ces pièges, et les tests les prouvent dans le JSON.

```bash
dsoxlab run write-code-locals
dsoxlab check write-code-locals
dsoxlab hint write-code-locals
```

Sous-objectif d'examen visé : **2c** (Terraform Authoring and Operations
Professional), avec un débord sur 2f pour la sensibilité.

Référence : [Les valeurs locales en Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/locals-terraform/)
