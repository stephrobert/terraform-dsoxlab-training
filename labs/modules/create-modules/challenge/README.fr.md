# Un module ne configure pas ses providers

## La situation

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

Référence : https://www.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/creation-modules/

## 🎯 Challenge : rendre un module hérité réutilisable

### 📦 Le point de départ

`challenge/work` contient un projet à deux niveaux : une racine et un module
local `modules/livrable/`. La racine veut livrer **trois environnements** avec un
seul bloc `module` muni de `for_each`.

Commencez par le constat, avant toute modification :

```bash
terraform init
```

L'`init` **échoue**, et son message nomme le problème et la solution. C'est le
point de départ du lab : lisez-le en entier.

| Fichier | Ce que c'est |
| --- | --- |
| `versions.tf`, `variables.tf` (racine) | complets, **à ne pas toucher** |
| `main.tf` (racine) | l'appel du module, il manque un argument |
| `outputs.tf` (racine) | deux sorties à écrire, livrées en commentaire |
| `modules/livrable/main.tf` | le module, avec **un défaut hérité** |
| `modules/livrable/versions.tf` | ses exigences, une ligne à ajouter |
| `modules/livrable/variables.tf` | trois variables, sans documentation |
| `modules/livrable/outputs.tf` | deux sorties à compléter |

### ✅ Objectif

Rendre ce module **appelable plusieurs fois**, en lui retirant ce qui l'en
empêche, puis en lui passant proprement la configuration de provider dont il a
besoin.

### 📋 Ce qu'il faut obtenir

1. Plus **aucune configuration de provider** ne vit dans `modules/livrable/`.
   Elles restent à la racine, et le module conserve ses `required_providers` :
   les configurations s'héritent, les exigences de source et de version jamais.
2. Le module **déclare** la configuration aliasée qu'il attend, sous son exigence
   `local`.
3. L'appel de la racine **lui passe** cette configuration, sous le nom que
   l'enfant attend.
4. Dans le module, `local_file.archive` reste rattachée à la configuration
   aliasée, `local_file.manifeste` à la configuration par défaut.
5. Le `for_each` produit **trois instances**, `module.livrable["dev"]`,
   `["preprod"]` et `["prod"]`.
6. Chaque variable du module porte une **`description`** non vide, et **aucune**
   n'a de `default` : elles restent obligatoires.
7. Les deux outputs du module sont complétés, et ceux de la racine **agrègent**
   les trois instances en un objet indexé par environnement.
8. `terraform apply` passe, les six fichiers de `livraisons/` existent, et
   `terraform plan -detailed-exitcode` sort en **0**.

### ⚠️ Le cœur du sujet

La règle officielle tient en une phrase : **« a module intended to be called by
one or more other modules must not contain any `provider` blocks »**. Terraform
ne l'applique pas par principe, il l'applique parce qu'il ne peut pas faire
autrement : un module qui configure ses providers ne peut être instancié qu'une
fois.

Trois erreurs vous attendent, dans cet ordre, et chacune désigne l'étape
suivante :

| Message | Ce qu'il réclame |
| --- | --- |
| `Module is incompatible with count, for_each, and depends_on` | retirer la configuration de provider de l'enfant |
| `Provider configuration not present` | déclarer l'alias attendu dans le module |
| `Missing required provider configuration` | passer cette configuration depuis l'appelant |

Retirer le `for_each` ferait disparaître la première erreur. Ce n'est pas la
solution : les tests exigent les trois instances.

### 🔍 Validation

`dsoxlab check modules-create-modules` prouve, par exécution :

- aucune entrée de `provider_config` ne porte de `module_address`, et l'alias
  `archive` est toujours déclaré à la racine ;
- le bloc `module` porte bien un `for_each`, et le state contient les trois
  adresses indexées ;
- le `provider_config_key` de chaque ressource de l'enfant pointe vers la bonne
  configuration, ce qui prouve le câblage de l'argument `providers` ;
- chaque variable du module a une `description` et aucun `default` ;
- les deux outputs de la racine ont trois clés, et les chemins annoncés
  correspondent à des fichiers réels ;
- `plan -detailed-exitcode` rend **0**.

Aucun test n'ouvre vos fichiers `.tf`.

Bloqué ? `dsoxlab hint modules-create-modules`.
