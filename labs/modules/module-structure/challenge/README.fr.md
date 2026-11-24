# Structure standard d'un module

## La situation

**Sous-objectif d'examen visé : 4a.**

Un module monolithique fonctionne, mais le registre, la génération de documentation et les relecteurs attendent la *Standard Module Structure*. Ce lab traite le piège inverse de celui qu'on croit : les noms de fichiers sont bien cosmétiques, sauf `override.tf` et `*_override.tf`, que Terraform charge en dernier et qui écrasent réellement la configuration.

## Capacité visée

Refactorer une configuration monolithique en module au format standard : socle `main.tf` / `variables.tf` / `outputs.tf` / `README.md`, bloc `terraform` isolé, module imbriqué sous `modules/` appelé par chemin relatif, exemple autonome sous `examples/`, et démontrer par l'état appliqué qu'un fichier `override.tf` modifie le résultat alors qu'aucun autre nom de fichier ne le fait.

## D'où part l'apprenant

`challenge/work` ne contient qu'un seul fichier, `tout.tf`, d'une soixantaine de lignes, où tout est empilé dans le désordre :

- le bloc `terraform`, avec `required_version` et `required_providers` pour `local` et `random` ;
- trois blocs `variable` : `nom_service`, `environnements` et `permissions_index` ;
- deux blocs `resource` : `random_pet.id`, unique au lieu d'être créé par environnement, et `local_file.index` avec `file_permission = "0644"` ;
- un bloc `output` nommé `chemins`.

Deux trous empêchent l'application en l'état : la variable `environnements` porte `type = ???` et l'output `chemins` porte `description = ???` sans ligne `type`. Aucun `README.md`, aucun `LICENSE`, aucun sous répertoire. Rien n'a encore été appliqué : pas de `.terraform`, pas de state, pas de fichier généré.

## L'état à atteindre

1. `tout.tf` a disparu. Le répertoire porte `main.tf`, `variables.tf`, `outputs.tf`, `README.md` et `LICENSE`, et le bloc `terraform` vit seul dans `terraform.tf`, le nom retenu par le style guide officiel (et non `versions.tf`, qui n'apparaît nulle part dans la documentation HashiCorp).
2. Un module imbriqué existe en `modules/fiche/`, avec ses propres `main.tf`, `variables.tf`, `outputs.tf` et un `README.md` qui le déclare utilisable de l'extérieur. Il crée un `random_pet` et un `local_file` par appel.
3. La racine appelle ce module par le chemin relatif `./modules/fiche`, et non par une adresse distante, pour que Terraform le traite comme faisant partie du même paquet.
4. Le module est instancié une fois par environnement : l'état contient `module.fiche["dev"]` et `module.fiche["prod"]`, chacun avec ses deux ressources.
5. Chaque `variable` et chaque `output`, à la racine comme dans le module imbriqué, porte un `type` et une `description`. L'output racine `chemins` est un `map(string)` qui remonte le chemin exposé par chaque instance du module.
6. `examples/minimal/` contient une configuration autonome qui appelle le module et que `terraform validate` accepte sans erreur.
7. Un `override.tf` à la racine ramène le `file_permission` de `local_file.index` de `0644` à `0600`. Le fichier `main.tf` continue de déclarer `0644` : c'est l'état appliqué qui doit valoir `0600`.
8. La configuration est appliquée et stable : un plan immédiatement rejoué ne propose aucun changement.

## Comment on le prouve

Les tests lancent `terraform init`, `terraform apply -auto-approve`, puis n'interrogent que du JSON, jamais les fichiers `.tf` de l'apprenant.

- `terraform show -json` : `values.root_module.child_modules[]` doit contenir les adresses `module.fiche["dev"]` et `module.fiche["prod"]`, chacune portant un `random_pet` et un `local_file`. Un module absent, non imbriqué ou non itéré fait échouer le test. La ressource racine `local_file.index` doit y porter `file_permission == "0600"` : c'est la preuve que `override.tf` a été chargé en dernier et a gagné, impossible à obtenir sans ce nom de fichier exact.
- `terraform plan -out` converti par `terraform show -json` : `configuration.root_module.module_calls.fiche.source` doit valoir exactement `./modules/fiche`, et `module_calls.fiche.module.outputs` doit exposer la sortie remontée. Cela prouve l'appel par chemin relatif et le contrat de sortie du module imbriqué.
- `terraform output -json` : la clé `chemins` doit avoir `"type": ["map","string"]` et une valeur par environnement. Un output déclaré **sans** `type` ressort typé autrement, et le test le détecte : mesuré sur 1.15.4, la même valeur sort alors en `["object", {"dev": "string", "prod": "string"}]`, le type inféré clé par clé.
- `terraform -chdir=examples/minimal init` puis `validate -json` : `valid` doit valoir `true` et `error_count` valoir `0`.
- `terraform plan -detailed-exitcode` doit sortir en `0` (aucun changement en attente) pour prouver que l'état est stable.
- Enfin, présence de `README.md` à la racine et dans `modules/fiche/`, et de `LICENSE` à la racine : le seul contrôle de fichiers du lab, parce que la documentation officielle en fait la frontière entre un sous module public et un sous module interne.

## 🎯 Challenge : éclater un monolithe, et prouver qu'un nom de fichier compte

### 📦 Le point de départ

`challenge/work` ne contient **qu'un seul fichier**, `tout.tf` : le bloc
`terraform`, trois variables, deux ressources et une sortie, empilés dans le
désordre. Rien n'a été appliqué.

Deux `???` empêchent même l'analyse : le **type** de la variable
`environnements`, et la **description** de l'output `chemins`. Commencez par eux.

### ✅ Objectif

Refactorer cette configuration selon la **Standard Module Structure**, y ajouter
un **module imbriqué** et un **exemple autonome**, puis démontrer qu'un fichier
nommé `override.tf` modifie réellement le résultat.

### 📋 Ce qu'il faut obtenir

1. `tout.tf` a disparu au profit de `main.tf`, `variables.tf`, `outputs.tf`,
   `README.md` et `LICENSE`. Le bloc `terraform` vit **seul** dans
   `terraform.tf`, le nom retenu par le style guide officiel.
2. Un module imbriqué existe en `modules/fiche/`, avec ses propres `main.tf`,
   `variables.tf`, `outputs.tf` et un **`README.md`** qui le déclare utilisable
   de l'extérieur. Il crée un `random_pet` et un `local_file` par appel.
3. La racine l'appelle par le chemin **relatif** `./modules/fiche`.
4. Le module est instancié **une fois par environnement** : `module.fiche["dev"]`
   et `module.fiche["prod"]`.
5. Chaque variable et chaque output, à la racine comme dans le module, porte un
   **`type`** et une **`description`**. L'output `chemins` est un `map(string)`
   qui remonte le chemin exposé par chaque instance.
6. `examples/minimal/` contient une configuration autonome qui appelle le module
   et que `terraform validate` accepte.
7. Un **`override.tf`** ramène le `file_permission` de `local_file.index` de
   `0644` à `0600`. `main.tf` continue de déclarer `0644` : c'est l'**état
   appliqué** qui doit valoir `0600`.
8. La configuration est appliquée et stable : `plan -detailed-exitcode` sort en
   **0**.

### ⚠️ Le cœur du sujet

On répète souvent que les noms de fichiers Terraform sont purement cosmétiques.
C'est vrai, **sauf pour une famille** : `override.tf` et `*_override.tf`, que
Terraform charge **en dernier** et **fusionne** par-dessus le reste.

Le même contenu dans un fichier au nom ordinaire ne surcharge rien, il **casse
la configuration** :

```text
Error: Duplicate resource "local_file" configuration
Resource names must be unique per type in each module.
```

C'est la seule exception, et c'est elle que le test vérifie.

### 🔍 Validation

`dsoxlab check modules-module-structure` prouve, par exécution :

- les fichiers de la structure standard existent, `LICENSE` et les deux `README`
  compris ;
- `module_calls.fiche.source` vaut exactement `./modules/fiche`, et le module
  expose bien une sortie ;
- le state porte les deux instances indexées, chacune avec ses deux ressources ;
- `local_file.index` porte `file_permission = "0600"` dans le state, ce qu'aucun
  autre nom de fichier ne permet d'obtenir ;
- l'output `chemins` ressort avec le type `["map","string"]` et une clé par
  environnement ;
- `examples/minimal` se valide seul, `valid: true` et `error_count: 0` ;
- `plan -detailed-exitcode` rend **0**.

Aucun test ne lit vos fichiers `.tf`.

Bloqué ? `dsoxlab hint modules-module-structure`.
