# Générer des blocs, et savoir ne pas le faire

Un bloc **`dynamic`** fabrique des blocs imbriqués à partir d'une collection, là
où le schéma du provider expose un bloc répétable. C'est l'outil quand le
**nombre** de blocs vient d'une variable, pas d'une écriture à la main. Mais il a
un mur : il ne peut pas générer un bloc de **méta-arguments** comme `lifecycle`.
Ce tutoriel enseigne les deux faces sur un exemple **jetable**, un bundle de
fichiers, puis le challenge vous fera l'appliquer à un document cloud-init.

L'exemple s'appuie sur `archive_file`, dont le bloc `source` est répétable et
tourne en local, sans cloud :

```hcl
terraform {
  required_providers {
    archive = { source = "hashicorp/archive", version = "~> 2.4" }
  }
}
```

## Un bloc dynamic répète un bloc du provider

Le principe : on remplace plusieurs blocs identiques par un seul bloc `dynamic`
qui les génère. Sa **`for_each`** fournit la collection, son bloc **`content`**
décrit le bloc à produire, et une variable d'itération, nommée par défaut comme
le bloc, donne accès à l'élément courant.

```hcl
locals {
  entrees = {
    "config.yaml" = "cle: valeur\n"
    "notes.txt"   = "rien a signaler\n"
  }
}

data "archive_file" "bundle" {
  type        = "zip"
  output_path = "${path.module}/bundle.zip"

  dynamic "source" {
    for_each = local.entrees
    content {
      filename = source.key
      content  = source.value
    }
  }
}
```

Le bloc `dynamic "source"` génère autant de blocs `source` que la map compte
d'entrées. La variable d'itération porte le nom du bloc, `source`, et donne
`source.key` (la clé) et `source.value` (la valeur). Après un `apply` :

```bash
terraform output nb_fichiers   # length(...source)
```

```text
2
```

Deux entrées dans la map, deux blocs `source` générés.

## Filtrer se fait dans le for_each, jamais dans le content

C'est l'erreur la plus fréquente. Pour n'inclure qu'une partie des éléments, on
filtre **la collection** avec une expression `for`, dans le `for_each` :

```hcl
dynamic "source" {
  for_each = { for k, v in local.entrees : k => v if length(v) > 0 }
  content {
    filename = source.key
    content  = source.value
  }
}
```

Mettre un `if` dans le `content` ne sert à rien : le bloc est déjà décidé à ce
stade. Le nombre de blocs se règle en amont, sur la collection.

## Renommer la variable d'itération avec iterator

Par défaut, la variable porte le nom du bloc. Quand un bloc imbriqué porte le
**même nom que son parent**, ou pour la lisibilité, l'argument **`iterator`**
la renomme :

```hcl
dynamic "source" {
  for_each = local.entrees
  iterator = fichier
  content {
    filename = fichier.key
    content  = fichier.value
  }
}
```

`terraform validate` accepte, et le `content` accède désormais à `fichier.key` et
`fichier.value`. C'est la seule façon de distinguer deux niveaux quand un
`dynamic` en contient un autre du même nom.

## Le piège de .key sur un set

`for_each` accepte une map ou un **set**. Sur un set, il y a une subtilité
documentée : **`key` est identique à `value`**, et ne devrait pas être utilisé.

```hcl
locals {
  lignes = toset(["alpha", "bravo"])
}

dynamic "source" {
  for_each = local.lignes
  content {
    filename = "${source.key}.txt"
    content  = source.value
  }
}
```

```bash
terraform output noms
```

```text
["alpha.txt", "bravo.txt"]
```

`source.key` vaut ici `"alpha"` puis `"bravo"`, exactement comme `source.value` :
sur un set, les deux sont confondus. Utilisez `source.value`, et réservez
`source.key` aux maps, où la clé a un sens propre.

## Le mur : dynamic ne génère pas un bloc de méta-arguments

Un `dynamic` répète un bloc **du provider** (`source`, `ingress`, `setting`). Il
**ne peut pas** générer un bloc de méta-arguments comme `lifecycle` ou
`provisioner`, parce que Terraform doit traiter ces blocs **avant** d'évaluer la
moindre expression. Ces blocs s'écrivent toujours littéralement.

Si vous tentez un `dynamic` sur un bloc que le contexte n'attend pas, le message
nomme le **label** visé, jamais le mot `dynamic` :

```hcl
dynamic "reglage" {
  for_each = [1]
  content { option = reglage.value }
}
```

```text
Error: Unsupported block type
Blocks of type "reglage" are not expected here.
```

Retenez ce message : c'est celui que vous verrez si vous posez un `dynamic` sur
un bloc inexistant, ou sur un méta-argument. Le challenge vous fera buter dessus
avec un `dynamic "lifecycle"`, précisément pour vous faire écrire le bloc
`lifecycle` à la main.

## À utiliser avec parcimonie

Un `dynamic` rend la configuration plus difficile à lire qu'une suite de blocs
littéraux. La documentation officielle le déconseille pour les cas simples :
réservez-le aux blocs dont le **nombre** dépend vraiment d'une variable. Un bloc
qui ne varie jamais, comme un en-tête commun, reste littéral.

## À vous de jouer

Vous savez générer des blocs, filtrer dans le `for_each`, renommer avec
`iterator`, et reconnaître le mur des méta-arguments. Le challenge applique tout
cela à un document cloud-init, avec un `dynamic "lifecycle"` piégé à démonter :

```bash
dsoxlab run write-code-dynamic-blocks
dsoxlab check write-code-dynamic-blocks
dsoxlab hint write-code-dynamic-blocks
```

Sous-objectif d'examen visé : **2d** (Terraform Authoring and Operations
Professional).

Référence : [Les blocs dynamiques en Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/blocs-dynamiques/)
