# Scénario : un module réutilisable ne configure pas ses providers

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
