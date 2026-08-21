# 🎯 Challenge : trois projets, un module public, trois résolutions

## 🌐 Prérequis

Ce lab a besoin d'un **accès réseau** : les `terraform init` joignent
`registry.terraform.io` et `github.com`. Aucun compte cloud n'est nécessaire, le
module visé ne déclare aucun provider.

## 📦 Le point de départ

`challenge/work` contient trois projets indépendants et aucun state :

| Dossier | Ce qu'il faut y écrire |
| --- | --- |
| `projet-epingle/` | `source` et `version` d'un appel, en version **exacte** |
| `projet-souple/` | **deux** appels du même module, deux contraintes différentes |
| `projet-sous-module/` | un `source` **Git** vers un sous-répertoire, sur un tag |

Le module visé est publié par l'organisation **`cloudposse`**, dans le dépôt
**`terraform-null-label`**. Son adresse de registre ne s'invente pas, elle se
**déduit** : la convention de publication impose un nom de dépôt en
`terraform-<PROVIDER>-<NAME>`, et l'adresse s'écrit
`<NAMESPACE>/<NAME>/<PROVIDER>`.

## ✅ Objectif

Obtenir **trois résolutions différentes** du même module, puis prouver depuis les
artefacts de Terraform laquelle a été installée où.

## 📋 Ce qu'il faut obtenir

1. `projet-epingle` installe **exactement** la `0.24.1`, avec une contrainte de
   version **exacte**.
2. Le `.terraform.lock.hcl` de ce projet ne mentionne **que** le provider
   `hashicorp/local`, jamais le module.
3. `projet-souple` ne produit **aucun** `.terraform.lock.hcl`.
4. Son appel `etiquette` accepte toute la série `0.x` **sans** autoriser un `1.x`,
   et résout donc la `0.25.0`.
5. Son appel `etiquette_patch` reste dans les **correctifs** de la `0.24.1`, et
   résout donc la `0.24.1` alors que la `0.25.0` est disponible.
6. `projet-sous-module` est **initialisé** (jamais appliqué) avec une adresse Git
   qui vise le sous-répertoire `exports`, sur le tag `0.25.0`.
7. Les deux projets appliqués exposent `atelier-nord`, `atelier-sud` et
   `atelier-sud-patch`, et convergent.

## ⚠️ Le cœur du sujet

Le fichier de verrouillage **ne verrouille aucun module** : « the dependency lock
file tracks only **provider** dependencies ». La seule chose qui fige une version
de module, c'est la **contrainte** que vous écrivez.

| Ce que vous écrivez | Ce que Terraform installe |
| --- | --- |
| rien du tout | la **plus récente** disponible |
| `"0.24.1"` | exactement celle-là |
| `"~> 0.24"` | la plus récente des `0.x` |
| `"~> 0.24.1"` | la plus récente des `0.24.x` |

Et l'ordre compte dans une adresse Git : « the sub-directory portion must be
**before** those arguments ». Le sous-répertoire vient donc **avant** le `?ref=`,
sinon la révision devient `0.25.0//exports`, ce qui n'existe pas.

## 🔍 Validation

`dsoxlab check modules-module-registry` prouve, par exécution :

- les trois `.terraform/modules/modules.json`, lus en JSON et indexés par `Key` :
  `Source`, `Version` et `Dir` portent les résolutions ;
- le JSON du plan, dont `module_calls.<nom>.version_constraint` donne la
  contrainte **écrite**, distincte de la version **résolue** ;
- la présence du verrou côté `projet-epingle` avec zéro mention du module, et son
  **absence** côté `projet-souple` ;
- deux versions du même module coexistant dans un seul `modules.json` ;
- l'ordre `//` puis `?ref=` dans l'adresse Git, et l'entrée chaînée
  `exports.this` ;
- `output -json` pour les trois étiquettes, et `plan -detailed-exitcode` à 0.

Aucun test ne lit vos fichiers `.tf`.

Bloqué ? `dsoxlab hint modules-module-registry`.
