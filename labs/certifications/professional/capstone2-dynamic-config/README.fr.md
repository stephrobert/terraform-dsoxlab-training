# Réparer d'abord, puis laisser la donnée piloter

Deuxième objectif du Professional, et le plus large : valider, interroger,
calculer, employer les méta-arguments, typer les variables, protéger les
secrets. Ce capstone les fait tenir dans une seule configuration, en deux temps.

**D'abord réparer.** La configuration livrée ne passe même pas `terraform init`.
**Ensuite construire.** Une entrée dans une variable doit produire un jeu complet
de ressources, sans une ligne dupliquée.

Le lab se joue **hors ligne**, sur `local`, `null`, `random` et `archive`.

## Les trois erreurs ne tombent pas au même moment

C'est le premier enseignement, et il surprend.

```console
$ terraform init
│ Error: Invalid combination of "count" and "for_each"
$ echo $?
1
```

**`init` parse la configuration.** Tant qu'une erreur de ce genre subsiste,
aucun provider n'est installé. Et `validate`, lancé dans cet état, répond :

```console
$ terraform validate
│ Error: Missing required provider
```

Ce message n'a rien à voir avec vos erreurs, et envoie chercher au mauvais
endroit. La méthode est donc : **init, corriger ce qu'il refuse, init de
nouveau, puis validate**.

Les deux autres erreurs apparaissent alors ensemble, avec leur numéro de ligne :

```console
$ terraform validate
│ Error: Incorrect attribute value type    on main.tf line 41
│ Error: Reference to undeclared input variable    on main.tf line 64
```

## `count` ou `for_each`, et pourquoi le choix n'est pas neutre

Terraform refuse les deux sur la même ressource. Le choix se fait sur une
question : **comment les instances sont-elles adressées dans le state ?**

| Méta-argument | Adresse | Retirer l'entrée du milieu |
| --- | --- | --- |
| `count` | par position, `[0]`, `[1]` | décale les suivantes, qui sont **détruites et recréées** |
| `for_each` | par clé, `["PROD_EU"]` | ne touche qu'elle |

Sur trois fichiers locaux, la différence ne coûte rien. Sur trois bases de
données, elle coûte les données.

## Un nom se calcule, il ne se recopie pas

```hcl
locals {
  noms = {
    for cle, _ in var.environnements :
    cle => substr("${var.prefixe}-${replace(lower(cle), "_", "-")}", 0, var.longueur_nom)
  }
}
```

`PreProd_EU` devient `lab-preprod-eu`. Trois fonctions enchaînées, et la règle
vaut pour une clé que vous n'avez jamais vue : c'est précisément ce que le
dernier test vérifie, en ajoutant un environnement.

## Filtrer se fait dans le `for_each`, jamais dans le `content`

```hcl
dynamic "source" {
  for_each = each.value.options
  content {
    filename = "${source.value}.txt"
    content  = "option ${source.value} activee\n"
  }
}
```

Un environnement sans option ne produit **aucun** bloc, sans la moindre clause
`if`. C'est l'erreur la plus fréquente sur `dynamic` : mettre un `if` dans le
`content` ne réduit pas le nombre de blocs, le bloc est déjà décidé à ce stade.

Mesuré sur la configuration cible, le compte de blocs `source` par
environnement : **2**, **3** et **1**, soit le bloc fixe plus une option par
option déclarée.

## La sensibilité n'est pas une option

```hcl
output "secrets" {
  value     = { for cle, _ in var.environnements : local.noms[cle] => random_password.secret[cle].result }
  sensitive = true
}
```

Sans `sensitive = true`, Terraform **refuse de planifier** : la valeur dérive
d'un `random_password`, donc il la considère comme sensible, et le message parle
de « sensitive values ». Ce n'est pas une politesse, c'est un refus.

## Ce qui distingue vraiment `for_each` de trois blocs copiés

Rien, tant qu'on regarde le résultat pour ces trois environnements. Tous les
tests passeraient sur une configuration écrite à la main.

C'est pourquoi le dernier **change la variable** : il copie le répertoire, ajoute
un quatrième environnement, applique, et exige que tout suive — quatre
manifestes, un nom normalisé pour une clé jamais vue, et une archive à quatre
blocs. Des blocs écrits à la main ne peuvent pas suivre.

## À vous de jouer

```bash
dsoxlab run certifications-professional-capstone2-dynamic-config
dsoxlab check certifications-professional-capstone2-dynamic-config
dsoxlab hint certifications-professional-capstone2-dynamic-config
```

Neuf tests. Ils lisent `validate -json`, `show -json` et `output -json`, jamais
vos fichiers.

Objectif d'examen visé : **2**, dans ses six sous-objectifs.

Référence : [Exercices Professional](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/certifications/professional/exercices/)
