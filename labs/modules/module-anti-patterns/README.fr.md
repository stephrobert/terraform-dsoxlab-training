# Refactorer un projet copié-collé sans rien détruire

L'anti-pattern le plus courant n'est pas exotique : c'est la **ressource
recopiée**. Deux blocs presque identiques, puis trois, puis dix, et plus rien
n'est réutilisable. Le corriger est facile ; le corriger **sans détruire** ce qui
tourne l'est beaucoup moins, et c'est là que le sujet devient sérieux.

## Ce que voit Terraform quand vous refactorez

Terraform ne suit pas des ressources, il suit des **adresses**. Extraire
`local_file.plaque_nord` vers `module.plaque["nord"].local_file.plaque` change
cette adresse, et par défaut il en tire la seule conclusion possible : l'ancienne a
disparu, la nouvelle est à créer.

```text
Plan: 2 to add, 0 to change, 2 to destroy.
```

Sur des fichiers, c'est bénin. Sur une base de données, un disque ou un
enregistrement DNS, c'est un **incident**. Le bloc `moved` existe pour cela : il
déclare qu'une adresse en **remplace** une autre.

```hcl
moved {
  from = local_file.plaque_nord
  to   = module.plaque["nord"].local_file.plaque
}
```

Le plan change alors complètement de nature :

```text
  # local_file.plaque_nord has moved to module.plaque["nord"].local_file.plaque
  # random_pet.jeton_nord has moved to module.plaque["nord"].random_pet.jeton

Plan: 0 to add, 0 to change, 0 to destroy.
```

## Comment savoir si vous avez vraiment détruit

Un contrôle honnête ne peut pas s'appuyer sur n'importe quel identifiant. Celui
d'un `local_file` est un **hachage de son contenu** : détruisez le fichier,
recréez-le à l'identique, l'`id` est le **même**. Un identifiant **non
déterministe**, lui, ne ment pas.

```bash
terraform output jetons
```

```text
{
  "nord" = "becoming-gull"
  "sud"  = "stirring-porpoise"
}
```

Ces jetons viennent d'un `random_pet`. S'ils changent, la ressource a été
**recréée**, quoi qu'annonce le résumé du plan. C'est le principe à retenir bien
au-delà de ce lab : **choisissez comme témoin une valeur que l'outil ne sait pas
recalculer**.

## Ce que `moved` ne fait pas

L'erreur symétrique consiste à en faire une baguette magique. Un `moved` traite
des **adresses**, rien d'autre :

| Défaut | `moved` le corrige ? |
| --- | --- |
| ressource déplacée, renommée, passée dans un module | **oui** |
| ressource gérée à transformer en source de données | **non**, la documentation l'interdit explicitement |
| variable non typée, valeur figée | **non**, aucun rapport avec l'adressage |
| bloc `provider` déclaré dans un module | **non**, et le retrait a son propre piège |

Ce dernier point mérite une ligne de plus. Retirer une configuration de provider
avant les ressources qu'elle gère produit une **erreur de planification** : « you
must ensure that all resources that belong to a particular provider configuration
are destroyed before you can remove that provider configuration's block ».

## L'abstraction, pas seulement la factorisation

Extraire du code recopié dans un module ne suffit pas à en faire un **bon**
module. La documentation donne un test simple : « If you have trouble finding a
name for your module that isn't the same as the main resource type inside it, that
may be a sign that your module is not creating any new abstraction. » Un module
nommé `local_file` n'abstrait rien, il **enveloppe**.

Le module de ce lab s'appelle `plaque`, et c'est justifié : il produit un objet du
domaine, composé d'un fichier **et** d'un jeton. L'appelant manipule des plaques,
pas des fichiers.

## Typer l'entrée, documenter le contrat

Une variable sans `type` accepte **`any`** : une erreur d'appel ne se voit alors
qu'au moment où la valeur est **utilisée**, parfois jamais. Un objet explicite
ferme la porte, et fait de la variable un **contrat**.

```hcl
variable "plaque" {
  type = object({
    etiquette = string
    intitule  = string
  })
  description = "Etiquette de la plaque et intitule a y inscrire."
}
```

La `description` n'est pas décorative : la Standard Module Structure demande que
« all variables and outputs should have one or two sentence descriptions », et
c'est la seule chose que l'outillage sache **extraire** pour documenter le module.

## Garder l'arbre plat

Dernier anti-pattern, le plus discret : le module qui appelle un module qui appelle
un module. La recommandation officielle est franche, « we strongly recommend
keeping the module tree flat, with only one level of child modules ». Les relations
passent par des **expressions** entre appels, pas par des étages.

## À vous de jouer

Vous savez ce que Terraform voit d'un refactoring, comment lui déclarer un
déplacement, quel témoin choisir pour prouver que rien n'a été détruit, et ce
qu'un `moved` ne corrigera jamais. Le challenge vous remet un projet **déjà
appliqué**, à refactorer sans perdre un seul jeton.

```bash
dsoxlab run modules-module-anti-patterns
dsoxlab check modules-module-anti-patterns
dsoxlab hint modules-module-anti-patterns
```

Il se joue **hors ligne**.

Sous-objectif d'examen visé : **4c** (refactorer une configuration existante).

Référence : [anti-patterns des modules](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/anti-patterns-modules/)
