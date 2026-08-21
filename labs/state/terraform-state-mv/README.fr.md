# Renommer sans détruire : `terraform state mv` et le bloc `moved`

Renommer un bloc, ou le pousser dans un module, change son **adresse**. Or
l'adresse est l'identité d'un objet dans le state : par défaut, Terraform lit ce
changement comme « l'ancien objet a disparu, un nouveau apparaît », donc comme
une **destruction suivie d'une création**. Deux mécanismes évitent cela, et ils
ne se valent pas. Ce tutoriel montre les deux ; le challenge vous fera les
employer chacun à sa place.

## Le problème, en une commande

Prenons un projet appliqué, dont on renomme une ressource dans le code sans
toucher au state :

```bash
terraform plan
```

```text
Plan: 3 to add, 0 to change, 3 to destroy.
```

Trois créations et trois destructions, alors que rien n'a changé dans
l'infrastructure. Terraform ne devine pas un renommage : il compare des adresses,
et il n'en retrouve aucune. Sur un mot de passe généré ou une base de données,
cette lecture coûte cher.

## `terraform state mv` : réconcilier un state en retard

La commande déplace une entrée du state d'une adresse à une autre. Elle ne touche
**jamais** l'infrastructure réelle : elle ne change que le lien entre le state et
l'objet distant.

```bash
terraform state mv random_pet.web random_pet.frontend
```

```text
Move "random_pet.web" to "random_pet.frontend"
Successfully moved 1 object(s).
```

Deux contraintes ne s'inventent pas :

- les deux adresses doivent désigner le **même genre d'objet** (une instance vers
  une instance, un module entier vers un module entier) ;
- pour une ressource, le **type doit être identique** : on renomme
  `random_pet.web` en `random_pet.frontend`, jamais en `random_string.frontend`.

L'option `-dry-run` montre ce qui serait déplacé sans rien écrire. La commande
accepte aussi `-lock`, `-lock-timeout` et, pour le backend local seulement, les
options héritées `-state`, `-backup` et `-backup-out`.

**L'ordre compte, et c'est le point que l'on néglige.** Changez le code
**d'abord**, lancez la commande **ensuite**. Entre les deux, quiconque lance un
`plan` ou un `apply` sur le même state voit un objet à détruire et un autre à
créer, et peut appliquer cette lecture. La documentation en fait son seul
avertissement : il faut s'assurer que personne ne fasse d'autre changement dans
cet intervalle. Sur un backend partagé, une **seule** exécution suffit pour toute
l'équipe, puisqu'elle agit sur le state, pas sur votre poste.

## Le bloc `moved` : refactorer depuis le code

Depuis Terraform **1.1**, le déplacement se déclare dans le code. Deux
références, sans guillemets :

```hcl
moved {
  from = random_string.db_secret
  to   = module.secret.random_string.this
}
```

Au plan suivant, Terraform annonce un déplacement au lieu d'un remplacement :

```text
  # random_string.db_secret has moved to module.secret.random_string.this
Plan: 0 to add, 0 to change, 0 to destroy.
```

L'`apply` finalise sans rien détruire ni créer. La preuve machine est dans le
plan JSON, et c'est elle qui distingue les deux méthodes :

```bash
terraform plan -out=plan.tfplan
terraform show -json plan.tfplan | jq '.resource_changes[]
  | select(.previous_address) | {address, previous_address, actions: .change.actions}'
```

```json
{
  "address": "module.secret.random_string.this",
  "previous_address": "random_string.db_secret",
  "actions": ["no-op"]
}
```

**Terraform n'écrit `previous_address` que si un bloc `moved` a été pris en
compte.** `terraform state mv` ne le produit jamais : le state est déjà déplacé
quand le plan se calcule, il n'y a plus rien à signaler.

## Ne supprimez pas un bloc `moved` appliqué

C'est le piège qui coûte le plus cher, et il est contre-intuitif : une fois le
déplacement appliqué, on est tenté de retirer le bloc devenu inutile. Retirez-le,
et toute configuration qui référence encore l'ancienne adresse **planifie une
destruction** au lieu d'un déplacement.

Vérifiable en une minute : ramenez l'objet à son ancienne adresse, retirez le
bloc, replanifiez. Le `no-op` devient un `delete` plus un `create`.

La documentation est explicite : retirer un bloc `moved` est un **changement
cassant**, et elle recommande de **conserver tout l'historique** des blocs pour
préserver le chemin de mise à jour. La seule tolérance concerne un module
**privé** dont on est certain que tous les usagers ont appliqué.

## Laquelle des deux, et quand

| Situation | Méthode |
| --- | --- |
| Le code est déjà refactoré, le state est en retard | `terraform state mv` |
| Le refactoring part du code, en revue | bloc `moved` |
| Un module partagé, consommé par d'autres | bloc `moved`, conservé |
| Terraform antérieur à 1.1 | `terraform state mv`, seule option |

La documentation officielle inverse la hiérarchie que l'on croit : le bloc
`moved` est le mode **normal** du refactoring, et `state mv` la porte de sortie
pour les versions trop anciennes. La raison est simple : une commande impérative
ne laisse **aucune trace** dans le dépôt, là où un bloc versionné se relit, se
revoit et se rejoue à l'identique par toute l'équipe.

## À vous de jouer

Vous savez qu'un renommage non réconcilié vaut une destruction, que `state mv`
répare un state en retard sans toucher au réel, que le bloc `moved` déclare le
déplacement dans le code, que `previous_address` prouve lequel des deux a servi,
et qu'un bloc appliqué ne se supprime pas. Le challenge vous remet un projet dont
le code a été refactoré sans que personne ne touche au state : trois objets à
rattacher, deux méthodes à employer à bon escient.

```bash
dsoxlab run state-terraform-state-mv
dsoxlab check state-terraform-state-mv
dsoxlab hint state-terraform-state-mv
```

Sous-objectif d'examen visé : **1e** (inspecter et manipuler le state), niveau
Associate.

Référence : [terraform state mv](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/terraform-state-mv/)
