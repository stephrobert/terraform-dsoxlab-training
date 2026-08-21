# Un module qui configure son provider n'est plus composable

Trois pratiques distinguent un module **réutilisable** d'un module qui marche une
fois : il ne configure pas son **provider**, il **reçoit** ses dépendances, et il
se **documente**. Les trois se vérifient dans les artefacts que Terraform produit,
sans lire une ligne de configuration.

## Pourquoi un module ne configure pas son provider

La raison n'est pas le confort, c'est le **cycle de vie**. La documentation est
nette : « A provider configuration must always stay present in the overall
Terraform configuration for longer than all of the resources it manages. » Un
module qui embarque **à la fois** ses ressources et la configuration qui les gère
disparaît d'un bloc, et il devient impossible de détruire proprement ce qu'il
avait créé.

Terraform sanctionne d'ailleurs l'appel, dès que ce bloc `provider` **configure**
réellement quelque chose :

```text
Error: Module is incompatible with count, for_each, and depends_on

The module at module.cle is a legacy module which contains its own local
provider configurations, and so calls to it may not use the count, for_each,
or depends_on arguments.

If you also control the module "./mod", consider updating this module to
instead expect provider configurations to be passed by its caller.
```

Nuance mesurée : un bloc `provider` **vide** ne déclenche que
`Warning: Redundant empty provider block`. C'est le bloc qui **porte des
arguments** qui rend le module incompatible avec `count`, `for_each` et
`depends_on`.

## Faire passer une configuration à un module

L'héritage implicite ne vaut que pour la configuration **par défaut** : « Aliased
providers are never inherited automatically and must be passed explicitly using
the `providers` argument. » Il faut donc deux déclarations, une de chaque côté.

Côté module, l'attente se déclare dans `required_providers` :

```hcl
terraform {
  required_providers {
    local = {
      source                = "hashicorp/local"
      version               = ">= 2.5"
      configuration_aliases = [local.plaques]
    }
  }
}

resource "local_file" "plaque" {
  provider = local.plaques

  filename = "${path.root}/${var.repertoire}/${var.nom}.txt"
  content  = "plaque ${var.nom}\n"
}
```

Côté appelant, la configuration se **passe** :

```hcl
provider "local" {
  alias = "atelier"
}

module "plaque" {
  source = "../bibliotheque/plaque"

  providers = {
    local.plaques = local.atelier
  }

  nom        = "nord"
  repertoire = "sorties"
}
```

Oubliez l'argument `providers`, et l'`init` s'arrête en nommant ce qui manque :

```text
Error: Missing required provider configuration

The child module requires an additional configuration for provider
hashicorp/local, with the local name "local.secondaire".
```

## L'inversion de dépendance

C'est le cœur de la page officielle sur la composition : un module **reçoit** ce
dont il dépend, il ne le **fabrique** pas. Un module qui décide seul de son
répertoire de sortie, de son réseau ou de son groupe de sécurité impose ses choix
à tous ses appelants.

```hcl
# avant : le module decide
locals {
  repertoire = "plaques"
}

# apres : l'appelant decide
variable "repertoire" {
  type        = string
  description = "Repertoire ou ecrire la plaque."
}
```

Le bénéfice est concret : l'appelant peut passer une ressource qu'il **crée**, ou
une `data source` qui **lit** un existant, sans que le module change d'une ligne.

## Prouver tout cela sans lire le code

Le JSON du plan expose la configuration **telle que Terraform l'a comprise**. Deux
clés suffisent.

```bash
terraform plan -out=plan.tfplan
terraform show -json plan.tfplan | jq '.configuration.provider_config'
```

```json
{
  "local": { "name": "local", "full_name": "registry.terraform.io/hashicorp/local" },
  "module.plaque:local": {
    "name": "local",
    "full_name": "registry.terraform.io/hashicorp/local",
    "module_address": "module.plaque"
  }
}
```

Le champ **`module_address`** n'apparaît que pour une configuration déclarée
**dans un module** : c'est le détecteur exact de la violation. À l'inverse, une
configuration **aliasée** passée par l'appelant apparaît avec son `alias`, au
niveau racine.

Le reste se lit dans le même document : `module_calls.<nom>.module.variables`
donne l'interface réelle du module, `expressions` ce que l'appelant lui passe, et
`resources[].mode` distingue ce qu'il **gère** de ce qu'il **lit**.

## Les autres règles qui comptent

L'arbre des modules reste **plat** : « we strongly recommend keeping the module
tree flat, with only one level of child modules ». Les relations passent par des
**expressions** entre appels, pas par une hiérarchie profonde.

Un module se **documente** : la Standard Module Structure met le `README.md` dans
le **minimum**, et c'est ce fichier que le registre et les générateurs de
documentation exploitent.

Enfin, un module réutilisable ne contraint que son **plancher** de version, la
borne haute appartenant au module racine.

## À vous de jouer

Vous savez pourquoi un module ne configure pas son provider, comment lui en passer
une, ce qu'est l'inversion de dépendance, et où lire la preuve. Le challenge vous
remet un module legacy à rendre composable, et un projet qui doit en tirer deux
plaques depuis un seul appel.

```bash
dsoxlab run modules-module-best-practices
dsoxlab check modules-module-best-practices
dsoxlab hint modules-module-best-practices
```

Il se joue **hors ligne**.

Sous-objectif d'examen visé : **5b** (configurations de providers dans les
modules).

Référence : [bonnes pratiques des modules](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/bonnes-pratiques-modules/)
