# Les arguments write-only : un secret qui n'atterrit jamais dans le state

Un argument **write-only** transmet une valeur au provider **au moment de
l'opération**, mais Terraform ne l'écrit **jamais** dans le state ni dans le
plan. C'est la réponse au trou que `sensitive` ne bouche pas : `sensitive` masque
la valeur dans les logs, mais la laisse **en clair dans l'état**. Ce tutoriel
montre le principe sur un exemple **jetable** de mot de passe de base de données ;
le challenge vous fera le prouver sur un autre cas.

Les arguments write-only sont arrivés côté **Terraform 1.11** et demandent un
provider qui les expose. Ils se reconnaissent à leur **suffixe `_wo`**, toujours
accompagné d'un **`_wo_version`**.

## Le problème : `sensitive` ne protège pas le state

Un argument ordinaire persiste sa valeur dans le state, même déclaré `sensitive` :

```hcl
resource "aws_db_instance" "exemple" {
  # ...
  password = var.db_password   # ecrit en clair dans terraform.tfstate
}
```

`sensitive` empêche l'affichage dans `terraform plan`, mais quiconque lit
`terraform.tfstate` (ou un backend distant mal protégé) voit le mot de passe. Le
state n'est pas un coffre-fort : il faut que le secret **n'y entre pas**.

## La solution : l'argument `_wo` et son `_wo_version`

Le même provider expose une variante write-only de l'argument. Elle forme un
**couple obligatoire** : la valeur, et un **numéro de version entier**.

```hcl
resource "aws_db_instance" "exemple" {
  # ...
  password_wo         = var.db_password
  password_wo_version = 1
}
```

- **`password_wo`** est envoyé au provider pendant l'apply, puis **oublié** :
  après l'opération, il vaut `null` dans le state. Le secret n'y figure jamais.
- **`password_wo_version`** est le **seul** des deux qui est persisté. Il sert
  d'horloge : Terraform ne renvoie la valeur au service que lorsque ce numéro
  **change**. Tant qu'il reste à `1`, les apply suivants ne retouchent rien, et
  le plan est vide (idempotence).

Pour faire tourner un secret, on incrémente `_wo_version` (1 vers 2) en même
temps qu'on fournit la nouvelle valeur. Sans changement de version, une nouvelle
valeur dans `password_wo` seule serait **ignorée**.

## La règle qui fait échouer les distraits

`_wo` et `_wo_version` vont **toujours ensemble**. Fournir la valeur sans le
numéro de version (ou l'inverse) lève une erreur de validation à l'apply : le
provider réclame le couple complet. De même, un argument ordinaire et sa variante
write-only sont **mutuellement exclusifs** sur la même ressource : on choisit
`password` **ou** `password_wo`, jamais les deux.

## Write-only et valeurs éphémères : le duo

Un argument write-only est l'un des rares **contextes autorisés** pour une valeur
**éphémère** (voir le lab voisin sur l'éphémère). On génère un secret éphémère,
qui ne touche pas le state, et on l'envoie à un argument write-only, qui ne le
persiste pas non plus : le secret ne laisse **aucune trace sur le disque**, de
bout en bout.

## À vous de jouer

Vous savez qu'un argument `_wo` transmet une valeur sans la persister, que son
`_wo_version` est le seul stocké et pilote le renvoi, que les deux sont un couple
obligatoire, et que `sensitive` seul laisserait fuiter le secret dans le state.
Le challenge vous fait stocker un secret dans un paramètre, prouver qu'il
**n'apparaît nulle part** dans le state, et rester idempotent. Les tests le
prouvent sur le JSON et sur le fichier d'état lui-même.

```bash
dsoxlab run write-code-sensitive-data-write-only-arguments
dsoxlab check write-code-sensitive-data-write-only-arguments
dsoxlab hint write-code-sensitive-data-write-only-arguments
```

Le lab démarre tout seul un émulateur AWS local (Floci) : aucune commande Docker
à taper, aucun compte cloud, aucune facture.

Sous-objectif d'examen visé : **2f** (gérer les données sensibles), niveau
Professional.

Référence : [Les arguments write-only en Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/gestion-donnees-sensibles/write-only-arguments/)
