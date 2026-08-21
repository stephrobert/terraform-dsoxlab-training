# Scénario : ajouter une instance sans détruire les autres

**Sous-objectif d'examen visé : 2d, les meta-arguments.**

Le vrai sujet de `for_each` n'est pas sa syntaxe, c'est ce qu'il évite : avec
`count`, insérer une entrée au milieu d'une liste décale tous les index suivants
et Terraform détruit puis recrée des ressources qui n'avaient aucune raison de bouger.

## Capacité visée

Faire évoluer un ensemble de ressources déjà appliquées en les réadressant de
l'index vers la clé, de façon déclarative, et prouver qu'aucune ressource
existante n'est détruite ni remplacée au passage.

## D'où part l'apprenant

`challenge/work` contient une configuration **déjà initialisée et déjà appliquée**
(state présent, fichiers produits aussi), limitée aux providers `random` et
`local`. Rien n'y est troué par des `???` : c'est du code correct mais fragile.

- `variables.tf` déclare `services`, une **liste** de trois chaînes, dans cet
  ordre : `web`, `cache`, `db`. `outputs.tf` en expose une liste positionnelle.
- `main.tf` crée, avec `count`, un `random_pet` par service (son nom généré est
  l'identité observable de l'instance) et un `local_file` qui écrit sa fiche
  dans `out/`.
- `DEMANDE.md` annonce le besoin : ajouter le service `api`, à ranger entre
  `web` et `cache`.

## L'état à atteindre

1. Plus aucun `count` : les deux ressources sont pilotées par `for_each` sur une
   collection dont les clés sont les noms de service, chaînes littérales connues
   au plan comme l'exige Terraform.
2. Les trois instances existantes sont réadressées de `[0]`, `[1]`, `[2]` vers
   `["web"]`, `["cache"]`, `["db"]` **par des blocs `moved` écrits dans la
   configuration**, pas par une manipulation manuelle du state.
3. Les noms `random_pet` de `web`, `cache` et `db` sont **identiques** à ceux
   d'avant la migration : aucune des trois n'a été recréée.
4. Le service `api` est ajouté : une seule nouvelle instance par type de
   ressource, aucune autre ne bouge.
5. L'output racine est une **map** indexée par clé, construite avec une
   expression `for` : le splat `[*]` est invalide sur une ressource `for_each`.
6. La configuration est stabilisée : un plan supplémentaire ne propose rien.

## Comment on le prouve

Les tests ne lisent jamais les `.tf`, ils pilotent Terraform et assèrent le JSON.

- `terraform show -json` : toutes les instances de `values.root_module.resources`
  portent un `index` de type chaîne (`web`, `cache`, `db`, `api`), jamais entier.
- **Preuve centrale** : le plan de l'ajout, enregistré par `plan -out` puis relu
  par `show -json`, contient dans `resource_changes` **exactement une action
  `create` par type de ressource, zéro `delete`, zéro `["delete","create"]`**.
- **Non recréation** : les noms `random_pet` conservés sont comparés à ceux
  capturés avant migration (fixture posée à la préparation).
- **Réadressage déclaratif** : dans le plan JSON du réadressage, les changements
  concernés portent un `previous_address` vers l'ancienne adresse indexée.
- `terraform output -json` renvoie un objet dont les clés sont exactement les
  quatre noms de service, pas un tableau.
- **Idempotence** : `terraform plan -detailed-exitcode` sort en 0, pas en 2.
