# Transformer une collection avec les expressions for

Une **expression `for`** transforme une collection en une autre : filtrer,
renommer, regrouper, croiser deux niveaux. C'est l'outil qui remplace le
copier-coller quand une même donnée doit ressortir sous plusieurs formes. Ce
tutoriel l'enseigne sur un exemple **jetable**, une poignée d'équipes, puis vous
laisse l'appliquer à un autre catalogue dans le challenge.

Tout se teste dans `terraform console`, sans écrire une seule ressource. C'est le
réflexe à prendre : on éprouve l'expression, puis on l'écrit. Montez d'abord la
donnée de travail dans un répertoire à part :

```hcl
locals {
  equipes = {
    alpha = { pole = "produit", effectif = 4, competences = ["go", "k8s"] }
    bravo = { pole = "produit", effectif = 6, competences = ["go"] }
    delta = { pole = "data", effectif = 3, competences = [] }
  }
}
```

```bash
terraform console
```

## Crochets ou accolades : tuple ou object

C'est la distinction la plus importante du sujet, et elle décide de tout le
reste. **Des crochets `[ ]` produisent un tuple, des accolades `{ }` produisent
un object.** Terraform ne confond jamais les deux, et la fonction `type()` le
montre :

```hcl
> type([for k, v in local.equipes : k])
tuple([string, string, string])

> type({for k, v in local.equipes : k => v.effectif})
object({alpha: number, bravo: number, delta: number})
```

Retenez-le : la forme des délimiteurs dicte la forme du résultat. Un tuple est
une suite ordonnée ; un object associe des clés à des valeurs. La syntaxe object
porte une flèche `k => v` que le tuple n'a pas.

## Filtrer une liste

La forme la plus courante extrait une sous-liste. Entre crochets, on itère la
map et on ne garde que les clés voulues :

```hcl
> [for k, v in local.equipes : k]
[
  "alpha",
  "bravo",
  "delta",
]
```

L'ordre n'est pas un hasard : une expression `for` sur une map **itère les clés
triées lexicalement**. Inutile de réordonner à la main. Une clause `if`, placée
après l'expression, filtre l'itération :

```hcl
> [for k, v in local.equipes : k if v.pole == "produit"]
[
  "alpha",
  "bravo",
]
```

La condition voit les deux variables d'itération, la clé comme la valeur. On
peut donc tout aussi bien filtrer sur la clé :

```hcl
> [for k, v in local.equipes : k if k != "delta"]
[
  "alpha",
  "bravo",
]
```

## Construire une map

Avec des accolades et une flèche, la même itération produit un object. Ici, le
nom de l'équipe devient la clé, l'effectif la valeur :

```hcl
> {for k, v in local.equipes : k => v.effectif}
{
  "alpha" = 4
  "bravo" = 6
  "delta" = 3
}
```

## Regrouper avec l'ellipsis

Que se passe-t-il quand deux entrées produisent la **même clé** ? Par défaut,
Terraform refuse. `alpha` et `bravo` sont toutes deux du pôle `produit` :

```hcl
> {for k, v in local.equipes : v.pole => k}

Error: Duplicate object key

Two different items produced the key "produit" in this 'for' expression. If
duplicates are expected, use the ellipsis (...) after the value expression to
enable grouping by key.
```

Le message donne lui-même la parade : **l'ellipsis `...`** après l'expression de
valeur active le mode groupement. Chaque clé porte alors la **liste** des
valeurs, au lieu de les écraser :

```hcl
> {for k, v in local.equipes : v.pole => k...}
{
  "data" = [
    "delta",
  ]
  "produit" = [
    "alpha",
    "bravo",
  ]
}
```

L'ellipsis n'existe qu'avec des accolades. L'appliquer à un tuple
(`[for ... : k...]`) échoue avec « Grouping ellipsis (...) cannot be used when
building a tuple » : grouper n'a de sens que par clé.

## Le splat, et son piège sur une map

Terraform propose une forme courte, le **splat `[*]`**, qui remplace un `for`
simple sur une liste : `var.liste[*].id` équivaut à `[for o in var.liste : o.id]`.
Pratique, tant qu'on l'applique à une liste.

Sur une **map**, le splat devient un piège, parce qu'il **ne lève aucune
erreur**. Il enveloppe la map entière dans un tuple d'un seul élément :

```hcl
> length(local.equipes[*])
1
```

`1`, pas `3`. La configuration continue de valider, et casse plus loin, là où on
attendait trois entrées. Une ressource pilotée par `for_each` étant elle-même
une map, le splat lui est tout aussi inadapté. **Sur une map, écrivez toujours
une expression `for` explicite**, jamais un splat.

## Croiser deux niveaux : flatten

Dès qu'il faut combiner deux dimensions, chaque équipe et chacune de ses
compétences, on imbrique deux `for`. Le résultat est une liste de listes, qu'on
aplatit avec `flatten` :

```hcl
> flatten([for k, v in local.equipes : [for comp in v.competences : "${k}:${comp}"]])
[
  "alpha:go",
  "alpha:k8s",
  "bravo:go",
]
```

Remarquez `delta` : sa liste de compétences est vide, la boucle interne ne
produit rien, et `flatten` l'absorbe naturellement. Aucune entrée `delta:` dans
le résultat, sans une seule clause `if` pour l'exclure.

## Valider une collection entière

Combinée à `alltrue`, une expression `for` vérifie une propriété sur **chaque**
élément d'une collection, ce qu'un test simple ne sait pas faire :

```hcl
> alltrue([for k, v in local.equipes : v.effectif > 0])
true
```

C'est le motif pour valider une variable de type complexe : la fonction rend
`true` seulement si la condition tient pour toutes les entrées.

## Ce qu'une expression for ne sait pas faire

Une expression `for` ne génère que des **valeurs de collection**. Elle **ne peut
pas** produire des blocs de configuration imbriqués : pour répéter un bloc
`ingress` ou `setting` à l'intérieur d'une ressource, c'est un bloc `dynamic`
qu'il faut, pas un `for`. Confondre les deux est une impasse fréquente.

## À vous de jouer

Vous savez filtrer, construire une map, regrouper, aplatir, et éviter le splat
sur une map. Le challenge applique tout cela à un autre catalogue, et vérifie
chaque forme dans `terraform output -json` :

```bash
dsoxlab run write-code-for-loops
dsoxlab check write-code-for-loops
dsoxlab hint write-code-for-loops
```

Gardez le réflexe de la console : une expression `for` se valide en trois
secondes avant d'entrer dans un `local`.

Sous-objectif d'examen visé : **2c** (Terraform Authoring and Operations
Professional).

Référence : [Les expressions for en Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/boucles-for-terraform/)
