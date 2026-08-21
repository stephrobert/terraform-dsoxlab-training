# 🎯 Challenge : refactorer sans rien détruire

## 📦 Le point de départ

`challenge/work` fonctionne **hors ligne** et le projet est **déjà appliqué** :

| Fichier | Ce que c'est |
| --- | --- |
| `projet/main.tf` | deux `local_file` et deux `random_pet` **copiés-collés** à la racine |
| `projet/outputs.tf` | les sorties `chemins` et `jetons`, dont la forme ne doit pas changer |
| `projet/terraform.tfstate` | le state **de départ** : ces ressources existent déjà |
| `CIBLE.md` | les trois défauts à corriger, et l'interdit |

## ✅ Objectif

Remplacer le copier-coller par un module **typé**, appelé **une seule fois**, sans
détruire ni recréer quoi que ce soit.

## 📋 Ce qu'il faut obtenir

1. Un module `bibliotheque/plaque/` porte la ressource, écrite **une** fois.
2. Le projet l'appelle **deux** fois depuis un **seul** bloc.
3. L'entrée du module est un **objet**, et chaque variable comme chaque sortie
   porte une `description`.
4. Les **jetons** du state sont inchangés.
5. `terraform plan` n'annonce plus **aucun** changement.
6. Les sorties gardent leur forme.
7. Le module n'en appelle **aucun** autre.

## ⚠️ Le cœur du sujet

Terraform suit des **adresses**. Déplacer une ressource sans le déclarer donne :

```text
Plan: 4 to add, 0 to change, 4 to destroy.
```

Il existe un bloc, prévu pour cela, qui déclare qu'une adresse en remplace une
autre. Avec lui, le plan devient :

```text
  # local_file.plaque_nord has moved to module.plaque["nord"].local_file.plaque

Plan: 0 to add, 0 to change, 0 to destroy.
```

Le témoin du contrôle est le **jeton** `random_pet`, pas l'`id` du fichier : ce
dernier n'est qu'un hachage du contenu, donc **identique** après une destruction
suivie d'une recréation.

## 🔍 Validation

`dsoxlab check modules-module-anti-patterns` prouve, par exécution :

- le state : toutes les ressources sous `module.`, et les deux jetons **inchangés** ;
- le JSON du plan : un **seul** appel de module référençant `each` ou `count`,
  aucune action `create` ni `delete`, aucun module imbriqué ;
- les `description` des variables et sorties du module ;
- `plan -detailed-exitcode` à 0.

Les tests de non-destruction ne s'exécutent qu'une fois le refactoring fait : sans
cela, ne rien toucher les satisferait.

Bloqué ? `dsoxlab hint modules-module-anti-patterns`.
