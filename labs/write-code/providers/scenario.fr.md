# Scénario : source explicite et alias de provider

**Sous-objectif d'examen visé : 5b (configuration des providers, alias et nom local).**

Deux confusions dominent le sujet des providers : le préfixe `hashicorp/` implicite, présenté à tort comme normal alors qu'il est déconseillé, et l'amalgame entre nom local et alias. L'apprenant doit déclarer une source explicite, une configuration aliasée, et câbler la bonne ressource, sans jamais rouvrir un fichier `.tf` pour le prouver.

## Capacité visée

Écrire une adresse source explicite dans `required_providers`, déclarer une seconde configuration du même provider distinguée par un `alias`, et rattacher une ressource à cette configuration aliasée avec le meta-argument `provider =`. Savoir prouver le câblage par la représentation de configuration du plan JSON.

## D'où part l'apprenant

`challenge/work/` contient un projet incomplet. Aucune VM, aucun compte distant : seul `hashicorp/random` est utilisé, `terraform init` déjà en place. Le lab tourne partout où `terraform` est sur le PATH, sans réseau.

Le répertoire contient `versions.tf` et `main.tf`, tous deux troués :

```hcl
# versions.tf
required_providers {
  random = {
    source  = ???        # l'adresse source EXPLICITE
    version = "~> 3.6"
  }
}
```

```hcl
# main.tf
provider "random" {}
provider "random" { ??? }        # une SECONDE config, distinguee par un alias
resource "random_pet" "defaut" { length = 2 }
resource "random_pet" "autre" { ???  length = 2 }   # rattachee a l'alias
```

`terraform apply` échoue en l'état : les `???` ne sont pas du HCL valide, et un second bloc provider sans alias serait un doublon refusé.

## L'état à atteindre

1. La source de `random` est explicite (`hashicorp/random`), et se résout en l'adresse complète `registry.terraform.io/hashicorp/random`.
2. Une seconde configuration du provider `random` porte `alias = "secondaire"`. Sans l'alias, le second bloc serait `Duplicate provider configuration`.
3. `random_pet.autre` est rattachée à la configuration aliasée par `provider = random.secondaire` ; `random_pet.defaut` reste sur la configuration par défaut.
4. Les deux `random_pet` sont créés.
5. Le projet converge : un second plan juste après l'apply ne propose plus rien.

## Comment on le prouve

Les tests n'ouvrent jamais les `.tf` de l'apprenant et ne parsent aucune sortie humaine. Ils lancent Terraform dans `challenge/work` et ne lisent que du JSON ou des codes retour.

1. `terraform version -json` : `provider_selections` contient `registry.terraform.io/hashicorp/random`. La source explicite s'est bien résolue en adresse complète.
2. `terraform plan -out=tfplan` puis `terraform show -json tfplan` : dans `configuration.provider_config`, une entrée `random.secondaire` porte `alias: "secondaire"` et le bon `full_name`.
3. Toujours dans ce JSON, `random_pet.autre` a un `provider_config_key` valant `random.secondaire`, et `random_pet.defaut` valant `random`.
4. `terraform show -json` : deux `random_pet` dans le state.
5. `terraform plan -detailed-exitcode` retourne 0 juste après l'apply.

Référence : https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/providers-terraform/
