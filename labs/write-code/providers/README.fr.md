# Providers : source explicite et alias

Un **provider** traduit vos ressources en appels d'API. On le déclare dans
`required_providers`, on le configure dans un bloc `provider`. Deux confusions
piègent, et ce lab les traite : l'**adresse source** (le préfixe `hashicorp/`
implicite est en fait déconseillé) et la différence entre **nom local** et
**alias**. Ce tutoriel les montre sur un exemple **jetable** AWS ; le challenge
vous les fait poser sur un autre cas.

## L'adresse source : toujours explicite

Depuis Terraform 0.13, **`source` est requis**. L'écrire de façon implicite pour
les providers HashiCorp n'est qu'une **rétro-compatibilité** ; la doc recommande
l'inverse, « use explicit source addresses for all providers » :

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

L'adresse complète est **`[HOSTNAME/]NAMESPACE/TYPE`**. `hashicorp/aws` est en
réalité `registry.terraform.io/hashicorp/aws` : le **hostname**, souvent omis,
est la porte des **registres privés** et des **miroirs**.

## Nom local et alias : à ne pas confondre

Ce sont **deux mécanismes distincts** :

- Le **nom local** (la clé dans `required_providers`) identifie le provider dans
  le module, et rattache un type de ressource par son préfixe : `aws_instance`
  va au provider de nom local `aws`.
- L'**alias** crée une **configuration supplémentaire** du **même** provider,
  pour cibler par exemple deux régions.

```hcl
provider "aws" {
  region = "eu-west-3"
}

provider "aws" {
  alias  = "us"
  region = "us-east-1"
}

resource "aws_instance" "paris" {
  # config par defaut
}

resource "aws_instance" "virginie" {
  provider = aws.us
}
```

Sans alias, un second bloc `provider "aws" {}` serait un **doublon refusé**
(`Duplicate provider configuration`). Et la ressource `virginie` ne prend la
configuration `us` que parce qu'elle porte `provider = aws.us`.

## La preuve est dans le JSON

`terraform version -json` expose `provider_selections`, l'adresse complète vers
la version retenue de chaque provider. Et le **plan JSON** liste chaque
configuration dans `configuration.provider_config` (avec son `full_name` et son
`alias`), et chaque ressource porte un `provider_config_key` (`aws` ou `aws.us`) :

```bash
terraform plan -out=tfplan
terraform show -json tfplan | jq '.configuration.provider_config'
```

## Un mot sur les modules

Un **module destiné à être appelé ne contient aucun bloc `provider`** : la config
vit dans le module racine et traverse la frontière par `configuration_aliases`
(côté enfant) et `providers = { ... }` (côté appelant). Un module qui hérite d'un
bloc `provider` devient incompatible avec `count`, `for_each` et `depends_on`.

## À vous de jouer

Vous savez qu'une source s'écrit **explicitement**, qu'un **alias** ajoute une
configuration du même provider, et qu'une ressource s'y rattache par
`provider =`. Le challenge vous fait déclarer une source explicite, une config
aliasée, et câbler la bonne ressource, et les tests le prouvent dans le JSON.

```bash
dsoxlab run write-code-providers
dsoxlab check write-code-providers
dsoxlab hint write-code-providers
```

Sous-objectif d'examen visé : **5b** (configuration des providers, alias).

Référence : [Les providers en Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/providers-terraform/)
