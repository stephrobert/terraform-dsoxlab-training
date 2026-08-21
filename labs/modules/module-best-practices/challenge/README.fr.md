# 🎯 Challenge : rendre un module composable

## 📦 Le point de départ

`challenge/work` fonctionne **hors ligne**, avec le seul provider `local` :

| Fichier | Ce que c'est |
| --- | --- |
| `bibliotheque/plaque/main.tf` | le module **fautif** : il configure son provider et décide seul de son répertoire |
| `projet/main.tf` | un appel **unique**, qui subit ce que le module a décidé |
| `projet/outputs.tf` | fourni et correct : sa sortie est une **map**, donc l'appel doit être multiple |
| `CIBLE.md` | les trois pratiques à rétablir, et ce que le projet doit obtenir |

## ✅ Objectif

Refactorer le module jusqu'à ce qu'il soit **appelable deux fois** depuis un seul
bloc, avec une configuration de provider fournie par le projet et un répertoire de
sortie choisi par lui.

## 📋 Ce qu'il faut obtenir

1. Le module ne déclare **plus aucune** configuration de provider.
2. Le module **déclare** attendre une configuration aliasée, et le projet la lui
   **passe**.
3. Le répertoire de sortie devient une **entrée** du module ; le projet choisit
   `sorties`.
4. Le projet produit **deux** plaques, `nord` et `sud`, depuis un **seul** appel.
5. Le module porte un `README.md` non vide.
6. Le projet est appliqué et **converge**.

## ⚠️ Le cœur du sujet

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

## 🔍 Validation

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
