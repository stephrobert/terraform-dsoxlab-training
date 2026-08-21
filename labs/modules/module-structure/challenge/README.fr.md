# 🎯 Challenge : éclater un monolithe, et prouver qu'un nom de fichier compte

## 📦 Le point de départ

`challenge/work` ne contient **qu'un seul fichier**, `tout.tf` : le bloc
`terraform`, trois variables, deux ressources et une sortie, empilés dans le
désordre. Rien n'a été appliqué.

Deux `???` empêchent même l'analyse : le **type** de la variable
`environnements`, et la **description** de l'output `chemins`. Commencez par eux.

## ✅ Objectif

Refactorer cette configuration selon la **Standard Module Structure**, y ajouter
un **module imbriqué** et un **exemple autonome**, puis démontrer qu'un fichier
nommé `override.tf` modifie réellement le résultat.

## 📋 Ce qu'il faut obtenir

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

## ⚠️ Le cœur du sujet

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

## 🔍 Validation

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
