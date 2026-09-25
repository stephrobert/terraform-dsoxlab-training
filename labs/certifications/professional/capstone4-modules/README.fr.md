# Extraire un module sans détruire ce qui tourne

Le quatrième objectif du Professional est celui du refactor. Écrire un module
depuis une page blanche est facile. En extraire un d'une configuration **déjà
appliquée**, sans rien détruire, ne l'est pas — et c'est là que se joue le
niveau.

Un refactor qui détruit la production est un refactor raté, même si l'état final
est correct.

## Le point de départ : trois fois la même chose

Trois services, neuf ressources, trois valeurs qui changent. Ajouter un
quatrième service demande aujourd'hui de recopier neuf lignes. C'est exactement
ce qu'un module existe pour supprimer.

## Changer d'adresse n'est pas changer d'objet

Une ressource est identifiée dans le state par son **adresse**. Passer de
`random_pet.api_nom` à `module.service["api"].random_pet.nom` change cette
adresse. Sans rien d'autre, Terraform voit neuf adresses disparaître et neuf
apparaître : il **détruit et recrée tout**.

Le bloc `moved` déclare le réadressage :

```hcl
moved {
  from = random_pet.api_nom
  to   = module.service["api"].random_pet.nom
}
```

Trois propriétés en font la bonne méthode, préférable à `terraform state mv` :
il est **versionné** avec le code, **rejoué automatiquement** par toute l'équipe
et par la CI, et **déclaratif**, donc personne n'a à se souvenir d'une commande.

Le plan attendu :

```console
$ terraform plan
  # local_file.api_config has moved to module.service["api"].local_file.config
  ...
Plan: 0 to add, 0 to change, 0 to destroy.
```

## Un plan vide ne prouve pas qu'on n'a rien détruit

C'est la nuance qui fait la valeur de ce capstone. Une configuration qui aurait
tout détruit puis tout recréé **converge elle aussi** : son plan est vide, et
son état final est correct.

Ce qui les distingue, ce sont les **identifiants**. Le lab fournit l'état de
départ avec ses neuf identifiants, et exige de les retrouver tous, aux nouvelles
adresses. Une ressource recréée en porte un autre.

## Deux pièges mesurés en écrivant ce lab

**`version` ne s'applique qu'aux modules de registry.** Sur une source locale,
Terraform refuse dès l'`init` :

```text
Error: Invalid registry module source address
you also set the argument "version", which applies only to registry modules.
```

Versionner un module local passe donc par le dépôt qui le porte, pas par cet
argument.

**Un bloc à plusieurs arguments ne tient pas sur une ligne.** La forme compacte
`moved { from = X  to = Y }` répond `The argument "to" is required`, un message
qui ne parle pas de mise en forme. Elle n'est valide qu'avec **un seul**
argument.

## Le module ne configure aucun provider

Un module destiné à être appelé plusieurs fois **ne doit contenir aucun bloc
`provider`** : les configurations lui sont passées par l'appelant. Avec un
`for_each`, Terraform refuse purement et simplement.

Il garde en revanche ses propres `required_providers` : les **configurations**
s'héritent, les **exigences de source et de version**, jamais.

## Et un détail qui déplacerait les fichiers

Le module écrit avec `path.root`, non `path.module`. Sinon les fichiers
partiraient dans le sous-répertoire du module, et Terraform, voyant un chemin
différent, les recréerait — ce que le réadressage devait justement éviter.

## À vous de jouer

```bash
dsoxlab run certifications-professional-capstone4-modules
dsoxlab check certifications-professional-capstone4-modules
dsoxlab hint certifications-professional-capstone4-modules
```

Six tests, hors ligne. Trois portent une garde qui refuse de mesurer tant que
les ressources ne vivent pas sous un module : sans elle, l'état de départ fourni
les rendait verts avant tout travail.

Objectif d'examen visé : **4**, et surtout **4d**.

Référence : [le programme du Terraform Authoring and Operations Professional](https://developer.hashicorp.com/terraform/tutorials/pro-cert/pro-review)
