# Scénario : Pro · Objectif 4, créer, maintenir et utiliser des modules

**Objectif d'examen visé : 4** (4a créer un module, 4b l'utiliser, 4c le
refactorer et le versionner, **4d refactorer une configuration existante en
modules**).

## Capacité visée

Transformer une configuration plate et répétitive en **module réutilisable**,
puis la réorganiser **sans détruire ni recréer** les ressources déjà en place.
C'est là que se joue le niveau Professional : un refactor qui détruit la
production est un refactor raté.

## D'où part l'apprenant

Dans `challenge/work`, une configuration plate qui **duplique trois fois** le
même ensemble de ressources, avec seulement quelques valeurs qui changent. Elle
est **déjà appliquée** : un state existe, les ressources sont créées.

## L'état à atteindre

1. Un module local expose une interface propre : des variables d'entrée typées
   et documentées, des outputs utiles, et **aucune valeur en dur**.
2. La racine appelle ce module **trois fois** (ou une fois avec `for_each`), et
   la duplication a disparu.
3. Le module est **versionné** : sa source est référencée avec une contrainte de
   version explicite.
4. **Le point décisif** : après le refactor, `terraform plan` annonce **zéro
   changement**. Les ressources ont changé d'adresse dans le state (elles vivent
   désormais sous `module.*`) mais n'ont pas été recréées. Cela suppose de
   déplacer les adresses correctement plutôt que de laisser Terraform détruire
   puis recréer.

## Comment on le prouve

- `terraform state list` montre des adresses préfixées par `module.`, et **plus
  aucune** ressource à l'ancienne adresse racine.
- Les identifiants des ressources dans le state sont **identiques** à ceux
  d'avant le refactor : la preuve qu'elles n'ont pas été recréées.
- `terraform plan -detailed-exitcode` sort en **0** juste après le refactor.
- Un test lit le module et vérifie qu'il n'expose aucune valeur en dur là où une
  variable est attendue.
