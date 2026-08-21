# Écrire un module qu'on peut appeler plusieurs fois

Un module Terraform est un **répertoire de fichiers `.tf`**, rien de plus. Votre
projet en est déjà un : c'est le **module racine**. Écrire un module « enfant »,
c'est donc surtout décider ce qu'il **reçoit**, ce qu'il **expose**, et ce qu'il
laisse à son appelant.

Ce dernier point est celui qui décide si votre module sera réutilisable ou non,
et il tient en une phrase de la documentation : **un module destiné à être
appelé par d'autres ne contient aucun bloc `provider`**. Ce tutoriel montre
pourquoi, sur une configuration jetable.

## Un module minimal

Un module se réduit à un répertoire, des variables en entrée, des ressources, et
des outputs en sortie :

```hcl
# modules/compteur/main.tf
terraform {
  required_providers {
    local  = { source = "hashicorp/local", version = ">= 2.5" }
    random = { source = "hashicorp/random", version = ">= 3.6" }
  }
}

variable "libelle" {
  description = "Libelle du compteur, sert de nom de fichier."
  type        = string
}

resource "random_integer" "tirage" {
  min = 1
  max = 99
}

resource "local_file" "releve" {
  filename = "${path.root}/releves/${var.libelle}.txt"
  content  = "${var.libelle} : ${random_integer.tirage.result}\n"
}

output "valeur" {
  description = "Valeur tiree pour ce compteur."
  value       = random_integer.tirage.result
}
```

Notez le bloc `required_providers` **dans le module** : un module déclare
toujours de quels providers il a besoin. En revanche il ne les **configure** pas,
et la nuance est au cœur de ce lab.

## L'appeler depuis la racine

```hcl
module "compteur" {
  source = "./modules/compteur"

  libelle = "atelier"
}

output "valeur_atelier" {
  value = module.compteur.valeur
}
```

`terraform init` installe le module comme il installerait un provider, et le
dit :

```text
Initializing modules...
- compteur in modules/compteur
```

L'`apply` préfixe les adresses par `module.<label>.` :

```text
module.compteur.random_integer.tirage: Creation complete after 0s [id=56]
module.compteur.local_file.releve: Creation complete after 0s [id=61a2097a...]

Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Outputs:

valeur_atelier = 56
```

**Un output est la seule chose qu'un module rend visible.** Sans le bloc
`output "valeur"`, l'appelant ne pourrait pas lire `random_integer.tirage.result` :
les ressources d'un module lui sont opaques.

## L'appeler plusieurs fois, avec un seul bloc

Le réflexe courant consiste à dupliquer le bloc `module`. La documentation
recommande l'inverse : « You can configure Terraform to provision multiple
instances of the same module resources in **one** `module` block, **instead of
adding multiple blocks** ».

```hcl
variable "ateliers" {
  type    = set(string)
  default = ["nord", "sud"]
}

module "compteur" {
  source   = "./modules/compteur"
  for_each = var.ateliers

  libelle = each.key
}

output "valeurs" {
  value = { for nom, instance in module.compteur : nom => instance.valeur }
}
```

Les adresses portent alors la clé, et `module.compteur` devient une **map** que
l'on parcourt :

```text
module.compteur["nord"].local_file.releve
module.compteur["nord"].random_integer.tirage
module.compteur["sud"].local_file.releve
module.compteur["sud"].random_integer.tirage
```

```text
valeurs = {
  "nord" = 17
  "sud" = 24
}
```

## Là où un module cesse d'être réutilisable

Ajoutez maintenant une **configuration de provider** dans le module enfant, comme
on en trouve dans beaucoup de modules hérités :

```hcl
# modules/compteur/main.tf
provider "tls" {
  proxy {
    url = "http://proxy.interne.lan:3128"
  }
}
```

L'`init` refuse, et son message contient déjà la solution :

```text
Error: Module is incompatible with count, for_each, and depends_on

The module at module.compteur is a legacy module which contains its own local
provider configurations, and so calls to it may not use the count, for_each,
or depends_on arguments.

If you also control the module "./modules/compteur", consider updating this
module to instead expect provider configurations to be passed by its caller.
```

Terraform appelle ce module **legacy**, et la raison est structurelle : il ne
peut pas instancier plusieurs fois un module qui configure lui-même ses
providers, parce qu'il ne saurait pas combien de configurations créer ni dans
quel ordre les détruire.

<!-- Le detail qui fait perdre du temps : le refus n'apparait que si le provider
     est REELLEMENT configurable. -->

Un détail vaut d'être connu, il évite une demi-heure de perplexité : ce refus ne
se déclenche que si le provider accepte une **vraie configuration**. Avec
`local`, `random` ou `null`, qui n'ont aucun argument, Terraform se contente d'un
avertissement, `Redundant empty provider block`, et laisse passer.

## Ce que le module attend, ce que l'appelant lui donne

Les **configurations** de provider sont héritées par les modules enfants ; les
**exigences** de source et de version ne le sont jamais. Un module garde donc son
`required_providers` et perd ses blocs `provider`.

L'héritage a une limite : il ne transmet que la configuration **par défaut**.
Pour qu'un module utilise une configuration **aliasée**, il doit la déclarer :

```hcl
# modules/compteur/versions.tf
terraform {
  required_providers {
    local = {
      source                = "hashicorp/local"
      version               = ">= 2.5"
      configuration_aliases = [local.secondaire]
    }
  }
}
```

Sans cette ligne, une ressource du module qui écrit `provider = local.secondaire`
échoue sur `Provider configuration not present`. Avec elle, mais sans rien côté
appelant, l'échec devient `Missing required provider configuration` : le module
réclame ce qu'on ne lui donne pas. C'est l'appelant qui referme la boucle :

```hcl
module "compteur" {
  source   = "./modules/compteur"
  for_each = var.ateliers

  providers = {
    local.secondaire = local.archivage
  }

  libelle = each.key
}
```

À gauche le nom **attendu par l'enfant**, à droite la configuration **de la
racine**. Les autres providers restent hérités sans qu'on écrive quoi que ce
soit : mesuré, un `providers` partiel n'annule pas l'héritage de ceux qu'il ne
nomme pas.

## Une réserve que la documentation pose et qu'on lit rarement

Tout ne mérite pas un module. La doc officielle est explicite : « We **do not**
recommend writing modules that are just thin wrappers around single other
resource types. If you have trouble finding a name for your module that isn't
the same as the main resource type inside it, that may be a sign that your module
is not creating any new abstraction ». Un module `reseau` qui contient une seule
ressource `..._network` ne factorise rien : autant utiliser la ressource
directement.

## À vous de jouer

Vous savez écrire un module, l'appeler, lire ses sorties, l'instancier plusieurs
fois avec un seul bloc, et surtout reconnaître ce qui le rendrait inutilisable :
une configuration de provider chez l'enfant. Le challenge vous remet un projet
dont le module hérité contient exactement ce défaut, et dont l'`init` échoue
avant même le premier plan.

```bash
dsoxlab run modules-create-modules
dsoxlab check modules-create-modules
dsoxlab hint modules-create-modules
```

Sous-objectif d'examen visé : **4a** (écrire et utiliser des modules), niveau
Associate et Professional.

Référence : [créer des modules](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/creation-modules/)
