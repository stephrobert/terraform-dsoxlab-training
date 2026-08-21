# Les expressions : références, types, conversion et null

Une **expression** calcule une valeur : une interpolation, un opérateur, un
ternaire, une référence. C'est le tissu de toute configuration. Ce qui piège,
c'est la **syntaxe de référence** d'une ressource, la **conversion de types**
(présente pour l'arithmétique, absente pour l'égalité), et la valeur **`null`**
qu'on remplace à tort par une chaîne vide. Ce tutoriel les montre dans
`terraform console` et sur un exemple **jetable** ; le challenge vous les fera
poser sur un autre cas.

`terraform console` évalue une expression sans rien appliquer. Il est
interactif, mais s'utilise aussi **en script**, en lui passant des commandes sur
l'entrée standard, ce qui en fait un outil de test.

```bash
echo 'max(3, 7, 2)' | terraform console
```

```hcl
7
```

## Référencer une ressource : sans préfixe

Les valeurs nommées ont chacune leur préfixe : `var.nom`, `local.nom`,
`data.<type>.<nom>.<attribut>`, `module.<nom>.<sortie>`, plus `each.key`,
`count.index`, `path.module` et `terraform.workspace`. Mais **une ressource
gérée fait exception : elle se référence SANS préfixe**, par
`<type>.<nom>.<attribut>` :

```hcl
resource "random_string" "jeton" {
  length = 8
}

# correct : aucun mot-cle "resource" dans l'expression
output "valeur" {
  value = random_string.jeton.result
}
```

Écrire `resource.random_string.jeton.result` est une **erreur** : le mot
`resource` n'apparaît jamais dans une expression. C'est le seul cas de la liste
sans préfixe, et la confusion la plus fréquente des débutants.

## Types et conversion automatique

Terraform a trois types primitifs (`string`, `number`, `bool`) et des types
complexes (`list`, `set`, `tuple`, `map`, `object`). Entre primitifs, il
**convertit automatiquement** quand il le peut, notamment pour l'arithmétique :

```hcl
> "5" + 3
8
```

La chaîne `"5"` est convertie en nombre. **Mais l'égalité ne convertit pas.**
C'est la règle qui surprend le plus :

```hcl
> 1 == "1"
false
```

Le nombre `1` et la chaîne `"1"` ne sont **pas** égaux, faute de conversion. La
documentation recommande de n'employer `==` et `!=` qu'entre types identiques,
ou après une conversion explicite (`tostring()`, `tonumber()`). Le même piège
guette le **ternaire**, qui, lui, convertit ses deux branches vers un type
commun : `true ? 12 : "hello"` rend une **chaîne**, pas un nombre.

## null : l'absence, pas la chaîne vide

**`null` représente l'absence d'une valeur.** Affecter `null` à un argument de
ressource revient à **ne pas l'écrire du tout** : Terraform applique alors le
défaut du provider. La documentation le dit : « If you set an argument to
`null`, Terraform behaves as though you had completely omitted it. »

```hcl
resource "local_file" "exemple" {
  filename        = "exemple.txt"
  content         = "x"
  file_permission = var.perm != "" ? var.perm : null
}
```

Ici, quand `var.perm` est vide, l'argument vaut `null` et la permission retombe
sur le défaut du provider. Écrire une **chaîne vide** `""` à la place serait une
valeur bien réelle, souvent invalide, et non une omission. C'est le mécanisme
standard pour rendre un argument optionnel.

## Opérateurs et précédence

Les opérateurs suivent une précédence classique : l'unaire (`!`, `-`), puis
`*` `/` `%`, puis `+` `-`, puis les comparaisons, puis `&&`, puis `||`. Le
multiplicatif passe **avant** l'additif :

```hcl
> 1 + 2 * 3
7
```

`1 + 2 * 3` se lit `1 + (2 * 3)`, soit `7`, jamais `9`. En cas de doute, les
parenthèses lèvent l'ambiguïté et documentent l'intention.

## Une valeur peut être inconnue au plan

Enfin, une expression qui dépend d'un attribut pas encore créé vaut
`(known after apply)`. Cette inconnue **se propage** : une valeur connue
combinée à une valeur inconnue donne une valeur inconnue. C'est pourquoi un
`count` ne peut pas dépendre d'un attribut de ressource, et pourquoi certains
outputs n'ont leur valeur qu'après l'apply.

## À vous de jouer

Vous savez qu'une ressource gérée se référence **sans préfixe**, que
l'arithmétique convertit les types mais que **`==` non**, que la précédence place
`*` avant `+`, et que **`null` omet** un argument là où `""` serait une valeur.
Le challenge vous fait poser ces expressions, et les tests en prouvent le
**type** et la valeur dans le JSON.

```bash
dsoxlab run write-code-expressions
dsoxlab check write-code-expressions
dsoxlab hint write-code-expressions
```

Sous-objectif d'examen visé : **2e** (expressions, types et valeurs).

Référence : [Les expressions en Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/expressions-terraform/)
