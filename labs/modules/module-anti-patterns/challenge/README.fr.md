# Refactorer un projet copié-collé sans rien détruire

## La situation

**Sous-objectif d'examen visé : 4d (refactorer une configuration existante en modules).**

Terraform suit des **adresses**, pas des ressources. Extraire du code recopié dans
un module change ces adresses, et sans déclaration explicite, l'outil détruit puis
recrée. Le lab impose donc la contrainte qui rend l'exercice réaliste : le projet
est **déjà appliqué**.

## Capacité visée

Remplacer deux blocs copiés-collés par un module typé, appelé une seule fois,
en déclarant les déplacements d'adresse de sorte qu'aucune ressource ne soit
détruite, et prouver ce dernier point depuis un témoin que Terraform ne sait pas
recalculer.

## D'où part l'apprenant

`challenge/work` fonctionne **hors ligne**, avec les providers `local` et
`random` :

- `projet/main.tf` : deux `local_file` et deux `random_pet`, déclarés en vrac à la
  racine, valeurs figées.
- `projet/outputs.tf` : les sorties `chemins` et `jetons`, dont la forme ne doit
  pas changer.
- `projet/terraform.tfstate` et `projet/plaques/*.txt` : le projet est **déjà
  appliqué**, c'est une fixture pédagogique.
- `CIBLE.md` : les trois défauts, l'état à atteindre, et l'interdit.

## L'état à atteindre

1. Un module `bibliotheque/plaque/` porte la ressource, écrite **une** fois.
2. Le projet l'appelle **deux** fois depuis un **seul** bloc.
3. L'entrée du module est un **objet**, et chaque variable comme chaque sortie
   porte une `description`.
4. Les deux jetons du state sont **inchangés** : rien n'a été détruit.
5. Le plan n'annonce plus **aucun** changement.
6. Les sorties `chemins` et `jetons` gardent leur forme.
7. L'arbre reste **plat** : le module n'en appelle aucun autre.

## Comment on le prouve

Aucun test ne lit un `.tf`.

- Le state, via `terraform show -json` : toutes les ressources doivent vivre sous
  `module.`, et les **jetons** `random_pet` doivent être **exactement** ceux du
  state de départ. Le choix du témoin est délibéré : l'`id` d'un `local_file` est
  un hachage de son contenu, donc **identique** après une destruction suivie d'une
  recréation, tandis qu'un `random_pet` est retiré au hasard.
- Le JSON du plan : un **seul** `module_calls`, dont un argument référence
  `each` ou `count` ; aucune action `create` ni `delete` dans `resource_changes` ;
  aucun module imbriqué dans le module appelé.
- Les `description` des variables et sorties du module, exposées dans ce même JSON.
- `plan -detailed-exitcode` à 0.

Un témoin garde ces contrôles honnêtes : les tests de non-destruction ne
s'exécutent que si le refactoring a **eu lieu**, sinon un `challenge/work` intact
les satisferait tous.

Un `challenge/work` nu rend 0 sur 8. Le même refactoring **sans** blocs `moved`
détruit et recrée les quatre ressources, et ne fait tomber que le test des jetons.
Deux appels recopiés au lieu d'un `for_each` ne font tomber que celui de l'appel
unique.

## 🎯 Challenge : refactorer sans rien détruire

### 📦 Le point de départ

`challenge/work` fonctionne **hors ligne** et le projet est **déjà appliqué** :

| Fichier | Ce que c'est |
| --- | --- |
| `projet/main.tf` | deux `local_file` et deux `random_pet` **copiés-collés** à la racine |
| `projet/outputs.tf` | les sorties `chemins` et `jetons`, dont la forme ne doit pas changer |
| `projet/terraform.tfstate` | le state **de départ** : ces ressources existent déjà |
| `CIBLE.md` | les trois défauts à corriger, et l'interdit |

### ✅ Objectif

Remplacer le copier-coller par un module **typé**, appelé **une seule fois**, sans
détruire ni recréer quoi que ce soit.

### 📋 Ce qu'il faut obtenir

1. Un module `bibliotheque/plaque/` porte la ressource, écrite **une** fois.
2. Le projet l'appelle **deux** fois depuis un **seul** bloc.
3. L'entrée du module est un **objet**, et chaque variable comme chaque sortie
   porte une `description`.
4. Les **jetons** du state sont inchangés.
5. `terraform plan` n'annonce plus **aucun** changement.
6. Les sorties gardent leur forme.
7. Le module n'en appelle **aucun** autre.

### ⚠️ Le cœur du sujet

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

### 🔍 Validation

`dsoxlab check modules-module-anti-patterns` prouve, par exécution :

- le state : toutes les ressources sous `module.`, et les deux jetons **inchangés** ;
- le JSON du plan : un **seul** appel de module référençant `each` ou `count`,
  aucune action `create` ni `delete`, aucun module imbriqué ;
- les `description` des variables et sorties du module ;
- `plan -detailed-exitcode` à 0.

Les tests de non-destruction ne s'exécutent qu'une fois le refactoring fait : sans
cela, ne rien toucher les satisferait.

Bloqué ? `dsoxlab hint modules-module-anti-patterns`.
