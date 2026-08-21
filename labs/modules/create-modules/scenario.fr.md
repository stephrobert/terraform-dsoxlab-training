# Scénario : un module ne configure pas ses providers

**Sous-objectif d'examen visé : 4a.**

Un module enfant qui porte son propre bloc `provider` marche tant qu'on l'appelle une fois, et casse dès qu'on lui met un `for_each`. Le piège traité ici est celui-là : la règle officielle « a module intended to be called by one or more other modules must not contain any `provider` blocks » ne se découvre presque jamais en lisant la doc, mais en butant sur le refus de Terraform.

## Capacité visée

Écrire un module enfant réutilisable : le vider de toute configuration de provider tout en lui conservant ses propres `required_providers`, lui faire déclarer par `configuration_aliases` la configuration aliasée qu'il attend, la lui passer depuis la racine par l'argument `providers`, et instancier le module autant de fois qu'il le faut par un seul bloc muni de `for_each`.

## D'où part l'apprenant

`challenge/work` ne contient ni state ni `.terraform`. Aucun compte cloud : seuls `hashicorp/local`, `hashicorp/random` et `hashicorp/tls` sont utilisés, tous les trois hors ligne une fois installés.

**Le choix de `tls` n'est pas décoratif, il est imposé par la mesure.** Le refus de Terraform ne se déclenche que si le module enfant porte une configuration de provider **réellement configurable**. Vérifié sur 1.15.4 : avec `local`, `random` ou `null`, qui n'acceptent aucun argument, un bloc `provider` dans un enfant appelé avec `for_each` ne produit qu'un **avertissement**, `Redundant empty provider block`, et `validate` reste vert. Avec `tls`, dont le bloc `proxy` est une vraie configuration, l'appel échoue dès l'`init`.

- `versions.tf` (racine) : complet, à ne pas toucher. `required_version = ">= 1.15.0"`, les trois providers épinglés, une configuration `provider "local" {}` par défaut et une seconde `provider "local" { alias = "archive" }`.
- `variables.tf` (racine) : complet. `environnements`, une `map(object({ cible = string, retention = number }))` à trois entrées : `dev`, `preprod`, `prod`.
- `main.tf` (racine) : un unique bloc `module "livrable"` avec `source = "./modules/livrable"` et `for_each = var.environnements`. Ses arguments sont troués par `???`, et il ne porte aucun argument `providers`.
- `outputs.tf` (racine) : `empreintes` et `chemins_archives` amorcés, valeurs trouées.
- `modules/livrable/versions.tf` : un bloc `required_providers` qui déclare bien `local`, `null` et `random`, mais dont la ligne `configuration_aliases` est trouée par `???`.
- `modules/livrable/main.tf` : en tête, un bloc `provider "local" {}` hérité d'un vieux copier-coller. Puis `random_pet.etiquette`, `local_file.manifeste`, `local_file.archive` (qui porte déjà `provider = local.archive`) et `null_resource.scellement`.
- `modules/livrable/variables.tf` : `nom`, `cible` et `retention` déclarées avec leur `type`, mais sans aucune `description`.
- `modules/livrable/outputs.tf` : `empreinte` et `chemin_archive` amorcés, valeurs trouées, sans `description`.

L'énoncé impose un `init` avant toute modification, et c'est **l'init lui-même qui refuse**, avant tout `validate` :

```text
Error: Module is incompatible with count, for_each, and depends_on

The module at module.livrable is a legacy module which contains its own local
provider configurations, and so calls to it may not use the count, for_each,
or depends_on arguments.

If you also control the module "./modules/livrable", consider updating this
module to instead expect provider configurations to be passed by its caller.
```

Le message dit le problème **et** la solution. Une fois la configuration de provider retirée de l'enfant, deux refus s'enchaînent, chacun désignant l'étape suivante : `Provider configuration not present` tant que le module référence `local.archive` sans l'avoir déclarée, puis `Missing required provider configuration` tant que l'appelant ne la lui passe pas.

## L'état à atteindre

1. Plus aucune configuration de provider ne vit ailleurs que dans le module racine : le bloc `provider "local"` a disparu de `modules/livrable/`.
2. Le module conserve ses trois `required_providers` : les configurations sont héritées, les exigences de source et de version ne le sont jamais.
3. `modules/livrable/versions.tf` déclare `configuration_aliases = [local.archive]` sous son exigence `local`.
4. Le bloc `module "livrable"` de la racine porte un argument `providers` qui associe la configuration aliasée de la racine au nom que l'enfant attend, `local.archive = local.archive`. Les autres configurations restent **héritées** sans rien écrire : mesuré sur 1.15.4, un `providers` partiel n'annule pas l'héritage des configurations qu'il ne nomme pas, et `local_file.manifeste` reste bien rattachée à la configuration `local` par défaut. Repasser explicitement `local = local` est une clarté d'écriture, pas une obligation technique.
5. `for_each` produit trois instances `module.livrable["dev"]`, `["preprod"]` et `["prod"]`, dont les arguments sont câblés depuis `each.key` et `each.value`.
6. Dans le module, `local_file.archive` est rattachée à la configuration aliasée, les trois autres ressources à la configuration par défaut.
7. Chaque variable et chaque output du module porte une `description` non vide ; `nom` et `cible` n'ont pas de `default` et restent donc obligatoires.
8. Les deux outputs de la racine agrègent les outputs des trois instances, indexés par nom d'environnement.
9. Un `apply` passe de bout en bout, les fichiers des trois environnements existent, et un `plan` juste après ne propose plus rien.

## Comment on le prouve

Les tests pilotent Terraform et ne lisent jamais les fichiers `.tf`.

- `terraform plan -out=tfplan` puis `terraform show -json tfplan`, table `configuration.provider_config` : elle contient une entrée d'`alias` `archive` pour `local`, et **aucune** entrée dont le `module_address` désigne `module.livrable`. Aucune configuration de provider ne vit dans l'enfant. Le simple fait que ce plan existe prouve déjà le point, puisque l'`init` échoue tant que l'enfant configure un provider et que l'appel porte `for_each`.
- Même document, `configuration.root_module.module_calls.livrable` : la clé **`for_each_expression`** est présente, au premier niveau. Attention, elle ne vit **pas** sous `expressions`, qui ne porte que les arguments du module ; et le JSON n'expose **aucune** clé `providers`, l'argument devant donc être prouvé autrement.
- Même document, `configuration.root_module.module_calls.livrable.module.resources` : le `provider_config_key` de `local_file.archive` vaut `local.archive`, celui de `local_file.manifeste` vaut `local`. Deux configurations d'un même provider cohabitent dans un seul module, et **c'est ce champ qui prouve le câblage de l'argument `providers`**, puisque le JSON ne l'expose pas directement.
- Même document, `...module_calls.livrable.module.variables` : chaque variable a une `description` non vide, et ni `nom` ni `cible` ne portent de clé `default`. Idem sur `...module.outputs` pour les descriptions.
- `resource_changes` du plan : douze entrées, toutes en `mode: "managed"`, dont les adresses commencent par `module.livrable["dev"]`, `module.livrable["preprod"]` et `module.livrable["prod"]`. Un seul bloc `module` produit trois instances.
- Après apply, `terraform show -json` : `values.root_module.child_modules` compte trois entrées dont les `address` sont les trois adresses indexées.
- `terraform output -json` : `empreintes` et `chemins_archives` sont des objets à exactement trois clés, et chaque chemin annoncé correspond à un fichier réellement présent sur le disque.
- `terraform plan -detailed-exitcode` : code 0 juste après l'apply final.

Aucun de ces contrôles ne passe sur un répertoire vide, ni sur la configuration de départ, dont le `validate` échoue.

Référence : https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/creation-modules/
