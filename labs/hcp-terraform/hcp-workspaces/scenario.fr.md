# Scénario : un mot, deux sens, deux stratégies de rattachement

**Sous-objectif d'examen visé : 6b, les workspaces HCP Terraform et leurs options de
configuration.**

L'objectif 6 est évalué en QCM : ni compte HCP Terraform, ni run distant. Ce lab ne demande
donc **aucun compte et aucun `terraform login`**, et il prouve pourtant quelque chose de
réel, parce qu'un bloc `cloud` est contrôlé bien avant toute authentification.

Deux équipes partagent un dépôt. L'une rattache son répertoire à un workspace unique
désigné par son nom, l'autre en sélectionne tout un ensemble par étiquettes. Ni l'une ni
l'autre configuration ne s'initialise, et `terraform validate` répond que tout va bien.

## Capacité visée

Distinguer les deux choses que le mot *workspace* désigne, rattacher un répertoire à HCP
Terraform par la bonne stratégie, et savoir où un bloc `cloud` est contrôlé, ce qui décide
de ce que `validate` peut dire et de ce qu'il ne peut pas dire.

## D'où part l'apprenant

`challenge/work` contient trois répertoires :

1. `nomme/`, qui doit se rattacher **par nom** au workspace `app-prod` de l'organisation
   `atelier-dsoxlab`. Il porte trois fautes, et elles ne tombent pas au même endroit.
2. `etiquete/`, qui doit se rattacher **par étiquettes**, avec un `project` et aucun
   `name`. Il porte deux fautes d'une autre nature.
3. `questionnaire/`, cinq réponses à poser dans `reponses.auto.tfvars`. Le type est fourni
   et validé : une réponse hors de l'énuméré est refusée **au plan**, avec un message qui
   dit quoi écrire.

## L'état à atteindre

1. `nomme/` se rattache par nom, avec `organization` en **chaîne littérale** : un bloc
   `cloud` est résolu avant toute évaluation d'expression, il ne peut donc référencer
   aucune valeur nommée, pas même une variable avec une valeur par défaut.
2. `nomme/` ne porte plus de bloc `backend` : un bloc `cloud` **est** le backend, et les
   deux ne peuvent pas cohabiter.
3. `nomme/` ne porte plus de `tags` à côté de `name` : ce sont deux stratégies de
   rattachement, et elles s'excluent.
4. `etiquete/` déclare un seul bloc `cloud`, avec `project` et `tags`, et aucun `name`.
5. Les cinq réponses établissent ce que crée un workspace CLI (un state), ce qu'est un
   workspace HCP (une unité d'exécution), où vivent les variables d'entrée d'un run (le
   workspace), pourquoi `name` et `tags` s'excluent (deux stratégies) et ce que `validate`
   attrape des trois fautes de `nomme/` (le seul conflit de backend).

## Comment on le prouve

Les deux répertoires réparés sont initialisés, et les tests exigent que l'initialisation
s'arrête **au jeton**, et nulle part ailleurs. C'est la frontière assumée du lab : un bloc
`cloud` correct va jusqu'à `Required token could not be found`, qu'aucune configuration
fautive n'atteint.

Ce seul marqueur ne suffirait pas, et la mesure dit pourquoi. Le 2026-09-25, sur Terraform
1.16.1, une configuration portant à la fois un `backend` et un `cloud`, comme une
configuration portant deux blocs `cloud`, affichent **aussi** `Required token could not be
found`, à côté de leur faute. Les tests exigent donc les deux : le message de jeton
présent, et aucun des messages de faute. Chacun de ces messages a été relevé sur un cas
minimal, et non supposé.

Les tests neutralisent par ailleurs tout jeton présent sur le poste, fichier de
configuration CLI vide et aucune variable `TF_TOKEN_*`, car la même configuration correcte
répond `Failed to read organization` sur un poste ayant fait `terraform login`. Sans cela,
un apprenant qui utilise HCP Terraform par ailleurs serait recalé pour un travail juste.

Le questionnaire se lit dans `terraform output -json`, jamais dans le fichier.
