# Scénario : Pro · Objectif 1, cycle de vie, import et réconciliation de drift

**Objectif d'examen visé : 1** (1a `init`, 1b `plan`, 1c `apply`, 1d `destroy`,
et surtout **1e : gérer le state, importer des ressources, réconcilier le
drift**).

C'est le seul objectif pour lequel HashiCorp publie des practice labs officiels,
et c'est le plus discriminant : reprendre en main une infrastructure qu'on n'a
pas créée est le quotidien d'un profil Professional.

## Capacité visée

Placer sous contrôle de Terraform une ressource **créée en dehors de lui**, sans
la détruire, puis **détecter et réconcilier un écart** apparu hors du code.

## D'où part l'apprenant

Floci tourne en local (socket Docker monté, `-u root`). Deux ressources ont été
créées **hors Terraform**, directement via l'AWS CLI : une instance EC2 et un
bucket S3. Elles portent des tags précis.

Dans `challenge/work`, un `main.tf` déclare le provider `aws` visant Floci, et
les deux ressources à trous : les blocs existent, mais les arguments sont des
`???`. Aucun state n'existe encore.

## L'état à atteindre

1. Les deux ressources figurent dans le state, **sans avoir été recréées** :
   l'identifiant de l'instance importée est le même qu'avant.
2. La configuration est **fidèle** à la réalité : juste après l'import, un
   `terraform plan` ne propose **aucun changement**. C'est le vrai critère de
   réussite d'un import, et le piège classique : un import qui « marche » mais
   dont le plan veut ensuite modifier la ressource est un import raté.
3. Un **drift** est ensuite provoqué hors Terraform (un tag modifié via l'AWS
   CLI). L'apprenant doit le détecter, puis choisir et appliquer la
   réconciliation.
4. Le `destroy` final laisse un state vide et plus aucune ressource côté Floci.

## Comment on le prouve

Les tests interrogent l'état, jamais le fichier de l'apprenant :

- `terraform show -json` : les deux adresses sont présentes, et l'`instance_id`
  correspond à celui créé hors Terraform (preuve de l'import, pas d'une
  recréation).
- `terraform plan -detailed-exitcode` sort en **0** après import : la config est
  fidèle.
- Après injection du drift, le même plan sort en **2** : le drift est bien
  détecté. Après réconciliation, il retombe à **0**.
- Après `destroy` : `terraform state list` est vide et l'AWS CLI pointée sur
  Floci ne retrouve plus les ressources.
