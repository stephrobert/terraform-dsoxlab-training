# Scénario : reprendre une EC2 existante, la renommer, accepter sa dérive

**Sous-objectif d'examen visé : 1e (gérer le state, importer des ressources, réconcilier le drift).**

Ce lab traite les trois pièges que la lecture d'un tutoriel ne révèle jamais : un
`moved` que l'on croit passé alors qu'il n'a jamais été appliqué, un `moved` dont
l'adresse `from` est fausse et que Terraform ignore **en silence**, et une dérive
que l'on écrase par réflexe au lieu de décider quoi en faire.

## Capacité visée

Placer sous contrôle de Terraform une instance EC2 créée en dehors de lui, en
changer l'adresse logique sans que l'objet réel soit recréé, puis réconcilier une
dérive en **acceptant** la réalité, c'est-à-dire en alignant le code sur elle et
non l'inverse.

## D'où part l'apprenant

Floci tourne en local sur `localhost:4566` (socket Docker monté, `-u root`).
L'étape de mise en place a créé, **via l'AWS CLI et non via Terraform**, une
instance EC2 taguée `Name = legacy-billing-api` et `Owner = finops`. Son
identifiant est déposé dans `challenge/work/existing-instance.txt`.

Dans `challenge/work` : un `providers.tf` **complet** (provider `aws` visant
Floci par un bloc `endpoints`, identifiants factices, `skip_credentials_validation`,
`skip_requesting_account_id`, `skip_metadata_api_check`), un `imports.tf` dont le
bloc `import` est à trous (`to = ???`, `id = ???`), **aucun bloc `resource`** (il
est à produire, pas à recopier), et aucun state.

## L'état à atteindre

1. L'instance figure dans le state avec **l'identifiant déjà présent dans
   `existing-instance.txt`** : elle a été importée, pas recréée.
2. Juste après l'import, la configuration est **fidèle** : un plan ordinaire ne
   propose plus rien. C'est le vrai critère de réussite d'un import, et le piège
   de la génération automatique de configuration, qui produit des arguments en
   trop qu'il faut retirer.
3. L'adresse dans le state est `aws_instance.billing_api`, alors que l'import
   s'est fait sous un autre nom, et l'identifiant de l'objet **n'a pas bougé** :
   le renommage est passé par un `moved` réellement **appliqué**, un `plan` seul
   n'écrivant rien dans le state.
4. Le bloc `moved` est **toujours présent** en fin de lab. Le supprimer est un
   changement cassant pour quiconque part encore de l'ancienne adresse.
5. Le tag `Owner` a été modifié hors Terraform et l'apprenant **accepte** cette
   dérive : côté Floci le tag garde sa valeur manuelle, le state la reflète, et
   le code aussi. Les deux critères d'arrêt tombent ensemble : plus de dérive à
   réconcilier, plus de changement à appliquer.
6. Aucune instance supplémentaire n'existe côté Floci : ni destroy, ni create.

## Comment on le prouve

Les tests interrogent l'état structuré, jamais le fichier `.tf` de l'apprenant :

- `terraform show -json` : une ressource en `mode: managed` à l'adresse
  `aws_instance.billing_api`, dont `values.id` est **égal** à l'identifiant lu
  dans `existing-instance.txt`. Preuve de l'import et de l'absence de recréation.
- `terraform plan -detailed-exitcode` sort en **0**, et
  `terraform plan -refresh-only -detailed-exitcode` sort en **0** lui aussi. Le
  premier prouve que le réel colle au code, le second que le state colle au réel.
- L'AWS CLI pointée sur Floci montre le tag `Owner` à sa valeur **manuelle**, et
  ne retourne qu'une seule instance non terminée : la dérive a été acceptée et le
  code aligné, sans recréation.
- Preuve du `moved` : le test copie le répertoire de travail à part, réécrit dans
  le state copié l'adresse vers son ancien nom, lance `terraform plan -out` et
  lit le plan en JSON. Il exige une entrée portant `previous_address` avec
  `actions: ["no-op"]`. Un bloc `moved` supprimé ou dont le `from` est faux
  produirait un `create`, sans la moindre erreur.
