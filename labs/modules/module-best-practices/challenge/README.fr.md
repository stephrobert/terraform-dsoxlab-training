# Un module réutilisable ne configure pas ses providers

## La situation

**Sous-objectif d'examen visé : 5b (configurations de providers dans les
modules).**

Un module qui embarque sa configuration de provider n'est pas seulement moins
souple : il devient **indestructible proprement**, et son appel refuse `count`,
`for_each` et `depends_on`. Le reste des bonnes pratiques suit le même principe :
ce que le module **décide** à la place de son appelant lui interdit d'être
réutilisé.

## Capacité visée

Refactorer un module « legacy » pour qu'il devienne composable : lui retirer sa
configuration de provider et la faire passer par l'appelant, transformer une
dépendance fabriquée en **entrée**, et le documenter, puis prouver chaque point
depuis les artefacts que Terraform produit.

## D'où part l'apprenant

`challenge/work` fonctionne **hors ligne**, avec le seul provider `local` :

- `bibliotheque/plaque/main.tf` : le module fautif. Il déclare un bloc
  `provider "local" {}`, et décide seul de son répertoire de sortie par une
  `locals`. Il n'a pas de `README.md`.
- `projet/main.tf` : un appel **unique**, sans `for_each`, qui subit le répertoire
  choisi par le module.
- `projet/outputs.tf` : fourni et correct. Sa sortie `chemins` est une **map**
  construite par `for` sur `module.plaque` : elle suppose donc un appel multiple.
- `CIBLE.md` : les trois pratiques à rétablir et le résultat attendu, sans donner
  la syntaxe.

## L'état à atteindre

1. Le module ne déclare **plus** de configuration de provider.
2. Le module **attend** une configuration aliasée, et le projet la lui **passe**.
3. Le répertoire de sortie est une **entrée** du module, et le projet choisit
   `sorties`.
4. Le projet produit **deux** plaques, `nord` et `sud`, depuis un **seul** appel.
5. Le module porte un `README.md` non vide.
6. Le projet est appliqué et converge.

## Comment on le prouve

Aucun test ne lit un `.tf`. Tout se lit dans le JSON du plan et celui de l'état.

- `configuration.provider_config` : une configuration déclarée **dans** un module
  y apparaît avec un champ **`module_address`**. Son absence prouve le point 1, et
  une entrée portant un `alias` prouve le point 2, complétée par le
  `provider_config_key` des ressources du module.
- `module_calls.plaque.module.variables` donne l'**interface réelle** du module et
  `expressions` ce que l'appelant lui passe : les deux ensemble portent le point 3.
- Les **références** des arguments passés (`each.key`) prouvent le point 4 côté
  configuration ; le JSON de l'état le confirme avec deux `child_modules` adressés
  `module.plaque["nord"]` et `module.plaque["sud"]`, toutes ressources en
  `mode: managed`.
- La sortie `chemins` de l'état donne les deux chemins réels, donc le répertoire
  effectivement retenu.
- `plan -detailed-exitcode` rend 0 pour le point 6.

Un `challenge/work` nu rend 0 sur 9. Remettre le bloc `provider` dans le module ne
fait tomber que le premier test, garder le répertoire en `locals` ne fait tomber
que celui de l'inversion, et dupliquer l'appel au lieu d'employer `for_each` en
fait tomber deux.

## 🎯 Challenge : rendre un module composable

### 📦 Le point de départ

`challenge/work` fonctionne **hors ligne**, avec le seul provider `local` :

| Fichier | Ce que c'est |
| --- | --- |
| `bibliotheque/plaque/main.tf` | le module **fautif** : il configure son provider et décide seul de son répertoire |
| `projet/main.tf` | un appel **unique**, qui subit ce que le module a décidé |
| `projet/outputs.tf` | fourni et correct : sa sortie est une **map**, donc l'appel doit être multiple |
| `CIBLE.md` | les trois pratiques à rétablir, et ce que le projet doit obtenir |

### ✅ Objectif

Refactorer le module jusqu'à ce qu'il soit **appelable deux fois** depuis un seul
bloc, avec une configuration de provider fournie par le projet et un répertoire de
sortie choisi par lui.

### 📋 Ce qu'il faut obtenir

1. Le module ne déclare **plus aucune** configuration de provider.
2. Le module **déclare** attendre une configuration aliasée, et le projet la lui
   **passe**.
3. Le répertoire de sortie devient une **entrée** du module ; le projet choisit
   `sorties`.
4. Le projet produit **deux** plaques, `nord` et `sud`, depuis un **seul** appel.
5. Le module porte un `README.md` non vide.
6. Le projet est appliqué et **converge**.

### ⚠️ Le cœur du sujet

Un bloc `provider` dans un module n'est pas un détail de style : « A provider
configuration must always stay present in the overall Terraform configuration for
longer than all of the resources it manages. » Et l'appel s'en trouve bridé :

```text
Error: Module is incompatible with count, for_each, and depends_on
```

L'héritage implicite ne sauve rien ici : « Aliased providers are **never**
inherited automatically and must be passed explicitly using the `providers`
argument ». Il faut donc **deux** déclarations, une dans le `required_providers`
du module, l'autre dans le bloc `module` de l'appelant.

### 🔍 Validation

`dsoxlab check modules-module-best-practices` prouve, par exécution :

- `configuration.provider_config` du JSON du plan : aucune entrée ne doit porter
  de champ **`module_address`**, qui trahit une configuration déclarée **dans** un
  module ; une entrée doit porter un **`alias`** ;
- `module_calls.plaque.module.variables` et `expressions` : l'interface réelle du
  module et ce que l'appelant lui passe ;
- les **références** des arguments (`each.key`), puis le JSON de l'état, avec deux
  `child_modules` adressés `module.plaque["nord"]` et `["sud"]` ;
- la sortie `chemins` de l'état, et `plan -detailed-exitcode` à 0.

Aucun test ne lit vos fichiers `.tf`.

Bloqué ? `dsoxlab hint modules-module-best-practices`.
