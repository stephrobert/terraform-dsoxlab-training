# Scénario : Pro · Objectif 2, configuration dynamique et troubleshooting

**Objectif d'examen visé : 2** (2a valider la configuration, 2b data sources,
2c fonctions HCL, 2d meta-arguments, 2e variables et outputs en types complexes,
2f données sensibles).

## Capacité visée

Produire une configuration **pilotée par la donnée** : une seule entrée en type
complexe génère N ressources correctement nommées, sans duplication de code. Et
savoir **réparer** une configuration qui ne valide pas.

## D'où part l'apprenant

Dans `challenge/work`, une configuration qui **échoue à `terraform validate`** :
trois erreurs volontaires y sont semées (une référence à une variable
inexistante, un type incompatible, un meta-argument mal employé).

Une variable `environnements` de type `map(object({...}))` décrit plusieurs
environnements avec des tailles et des options différentes. Les ressources
utilisent les providers `null`, `local` et `random` : aucun cloud, tout est
local et gratuit.

## L'état à atteindre

1. `terraform validate` passe : les trois erreurs sont corrigées.
2. Un `for_each` sur la map produit **exactement autant de ressources que
   d'entrées**, chacune nommée par une fonction HCL qui normalise la clé
   (minuscules, préfixe, longueur bornée).
3. Un bloc `dynamic` génère un nombre variable de sous-blocs selon l'option
   présente dans chaque objet.
4. Une valeur sensible est exposée en output **sans fuiter en clair**.
5. Les outputs exposent une structure agrégée (une map dérivée), pas une liste
   de valeurs brutes.

## Comment on le prouve

- `terraform validate` sort en 0.
- Le plan est lu en JSON : on compte les instances produites par le `for_each` et
  on vérifie que les noms calculés correspondent à ce que la fonction doit
  produire, clé par clé.
- `terraform output -json` : l'output sensible est marqué `"sensitive": true` et
  sa valeur n'apparaît pas dans la sortie non masquée.
- Idempotence : un second plan sort en 0.
