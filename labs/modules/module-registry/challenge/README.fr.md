# Consommer un module du registre et maîtriser la version installée

## La situation

**Sous-objectif d'examen visé : 4b (utiliser un module).**

Brancher un module public est trivial, savoir quelle version tourne réellement ne
l'est pas : le fichier de verrouillage ne couvre **que** les providers, et
« Terraform does not remember version selections for remote modules ».

## Capacité visée

Déduire l'adresse de registre d'un module depuis le nom de son dépôt, l'appeler
avec trois contraintes différentes en obtenant trois résolutions distinctes,
adresser un sous-répertoire d'un dépôt Git, puis prouver depuis les seuls
artefacts de Terraform quelle version a été **installée** et quelle contrainte a
été **écrite**.

## D'où part l'apprenant

**Prérequis réseau** : les `terraform init` doivent joindre
`registry.terraform.io` et `github.com`. Le module retenu,
`cloudposse/label/null`, ne déclare aucun provider et s'applique sans compte
cloud : il ne produit que des locales et des sorties.

`challenge/work` contient trois projets indépendants, aucun state.

- `projet-epingle/` : un `module "etiquette"` dont `source` et `version` valent
  `"???"`, plus un `local_file` déjà écrit qui consomme la sortie du module, et
  un `outputs.tf` correct. C'est le seul projet qui déclare un provider.
- `projet-souple/` : **deux** appels du même module, `etiquette` et
  `etiquette_patch`, tous deux troués. Le premier doit accepter toute la série
  `0.x`, le second rester dans les correctifs de la `0.24.1`.
- `projet-sous-module/` : un `module "exports"` dont le `source` doit viser le
  sous-répertoire `exports` du dépôt `cloudposse/terraform-null-label`, figé sur
  le tag `0.25.0`. Ce projet s'initialise seulement, il ne s'applique jamais.

Le commentaire de chaque fixture donne la consigne sans donner l'adresse : le
dépôt et la convention `terraform-<PROVIDER>-<NAME>` suffisent à reconstituer
`cloudposse/label/null`.

## L'état à atteindre

1. `projet-epingle` installe **exactement** la `0.24.1`, et son `modules.json`
   porte la clé `Version`, qu'aucun module local ne possède.
2. La contrainte écrite dans ce projet est une version **exacte**, lisible dans le
   JSON du plan sous `module_calls.etiquette.version_constraint`.
3. Le `.terraform.lock.hcl` de ce projet mentionne le provider `hashicorp/local`
   et **aucune** trace du module.
4. `projet-souple` ne produit **aucun** fichier de verrouillage : sa seule
   dépendance est un module de registre.
5. Son appel `etiquette` porte une contrainte **souple** et résout la `0.25.0`, la
   plus récente qui la satisfait, tout en restant sous la `1.0.0`.
6. Son appel `etiquette_patch` résout la `0.24.1` : deux versions du **même**
   module coexistent dans un seul `modules.json`, la résolution se faisant par
   **appel**.
7. `projet-sous-module` est initialisé avec un `source` dont le `//exports`
   précède le `?ref=0.25.0`, son `Dir` pointant vers le sous-répertoire, et son
   `modules.json` portant l'entrée chaînée `exports.this`.
8. Les deux projets appliqués exposent `atelier-nord`, `atelier-sud` et
   `atelier-sud-patch`, et ne proposent plus aucun changement.

## Comment on le prouve

Aucun test ne lit un `.tf` de l'apprenant ni ne parse une sortie humaine.

- Les trois `.terraform/modules/modules.json`, écrits par Terraform à
  l'installation, chargés en JSON et indexés par `Key` : les champs `Source`,
  `Version` et `Dir` portent les points 1, 5, 6 et 7. C'est la seule preuve
  possible de la version résolue, ce module ne déclarant aucune ressource, donc
  `terraform show -json` n'expose aucun `child_modules`.
- `plan -out` puis `show -json` du plan : `version_constraint` donne la contrainte
  **écrite**, distincte de la version résolue (points 2, 5 et 6).
- Le `.terraform.lock.hcl`, également produit par l'outil : présent avec le seul
  provider dans un cas (point 3), **absent** dans l'autre (point 4).
- `output -json` pour les trois étiquettes, et `plan -detailed-exitcode` à 0 pour
  la convergence (point 8).

Un `challenge/work` nu échoue partout (l'`init` s'arrête sur `Invalid version
constraint`), recopier la même contrainte dans les deux appels de
`projet-souple` échoue sur le seul point 6, et inverser `//` et `?ref=` fait
échouer l'`init` sur `invalid ref: "0.25.0//exports"`.

## 🎯 Challenge : trois projets, un module public, trois résolutions

### 🌐 Prérequis

Ce lab a besoin d'un **accès réseau** : les `terraform init` joignent
`registry.terraform.io` et `github.com`. Aucun compte cloud n'est nécessaire, le
module visé ne déclare aucun provider.

### 📦 Le point de départ

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

### ✅ Objectif

Obtenir **trois résolutions différentes** du même module, puis prouver depuis les
artefacts de Terraform laquelle a été installée où.

### 📋 Ce qu'il faut obtenir

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

### ⚠️ Le cœur du sujet

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

### 🔍 Validation

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
