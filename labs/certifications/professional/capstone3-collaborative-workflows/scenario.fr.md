# Scénario : Pro · Objectif 3, workflows collaboratifs

**Objectif d'examen visé : 3** (3a contraintes de version sur le binaire, les
providers et les modules, 3b remote state, 3c workflow en automation, 3d partage
de données entre configurations et workspaces).

## Capacité visée

Faire **collaborer deux configurations séparées** par un state distant partagé,
en verrouillant les versions et en s'exécutant **sans interaction humaine**,
comme le ferait une CI.

## D'où part l'apprenant

Floci tourne en local et fournit le backend **S3**. Deux stacks indépendantes
existent dans `challenge/work` :

- `reseau/` : produit une infrastructure de base et doit **publier** ses
  identifiants en outputs.
- `application/` : doit **consommer** ces valeurs sans jamais les recopier en
  dur.

Les deux stacks ont un bloc `terraform {}` incomplet : ni backend, ni
`required_version`, ni `required_providers` contraints.

## L'état à atteindre

1. Les deux stacks écrivent leur state dans le **backend S3 sur Floci**, chacune
   sous une clé distincte. Plus aucun `terraform.tfstate` local.
2. `application/` lit les valeurs de `reseau/` via la data source
   `terraform_remote_state`. **Aucune valeur codée en dur** : changer une valeur
   dans `reseau/` doit se propager.
3. Les versions sont contraintes : `required_version` sur le binaire et une
   contrainte de version sur le provider.
4. Tout s'exécute en **mode automation** : `-input=false`, sans prompt, avec un
   plan sauvegardé puis appliqué (`plan -out` puis `apply` du fichier de plan).

## Comment on le prouve

- Le bucket S3 sur Floci contient bien les deux clés de state (interrogé via
  l'AWS CLI pointée sur l'endpoint local).
- Le state de `application/` montre que ses ressources portent des valeurs
  **issues des outputs** de `reseau/` : on change une valeur en amont, on
  re-planifie, et l'aval bouge.
- Un `apply` lancé avec `-input=false` sans aucune variable interactive
  aboutit : la configuration est réellement automatisable.
- Idempotence sur les deux stacks.
