# Scénario : découper une configuration sans changer le plan

**Sous-objectif d'examen visé : 2a (écrire et organiser une configuration).**

Le découpage d'un `main.tf` est présenté partout comme sans risque parce que
`terraform validate` passe ensuite. Or `validate` « does not check if argument
values are valid for a specific provider [...] It does not evaluate any existing
state » : un bloc perdu au copier-coller le passe sans un mot. La seule preuve
d'invariance est la **comparaison de deux plans**.

## Capacité visée

Découper une configuration monolithique selon le socle de fichiers officiel, en
prouvant par comparaison de plans que le résultat est **inchangé**, puis rendre le
dépôt correct : formatage récursif et `.gitignore` qui ignore les artefacts sans
ignorer le fichier de verrouillage.

## D'où part l'apprenant

`challenge/work` fonctionne **hors ligne**, providers `local` et `random` :

- `projet/main.tf` : quatre-vingts lignes portant **tout**, bloc `terraform`,
  providers, trois variables, trois ressources dont une dépendant des deux autres,
  et trois sorties.
- `CIBLE.md` : le socle attendu, l'invariant à préserver, et les règles du dépôt.

## L'état à atteindre

1. Le socle est en place : `terraform.tf`, `providers.tf`, `variables.tf`,
   `outputs.tf`, et un `main.tf` qui ne garde que les ressources.
2. `terraform.tf` porte **un seul** bloc `terraform` et **aucun** `provider`.
3. Les variables et les sorties sont déclarées en **ordre alphabétique**.
4. Le plan est **identique** à celui de la configuration monolithique.
5. `terraform fmt -check -recursive` sort en **0**.
6. Un `.gitignore` ignore `.terraform/`, l'état, ses sauvegardes et le plan
   enregistré **sans extension**, mais laisse passer `.terraform.lock.hcl`.

## Comment on le prouve

- Les tests **replanifient** la fixture monolithique dans un répertoire
  temporaire, et comparent son empreinte à celle du plan de l'apprenant :
  `planned_values`, `resource_changes`, `output_changes` et `variables`. La section
  `configuration` est volontairement **exclue**, puisqu'elle reflète le découpage.
- Un **témoin** n'exécute ces contrôles d'invariance que si le socle existe : sans
  cela, un `challenge/work` intact serait trivialement identique à lui-même.
- Le socle, l'unicité du bloc `terraform` et l'ordre alphabétique se lisent dans
  les fichiers, qui sont ici le **livrable**.
- `terraform fmt -check -recursive` est lancé depuis la **racine** du workdir.
- Le `.gitignore` est mis à l'épreuve par `git check-ignore` dans une **copie**
  jetable initialisée en dépôt : c'est le verdict que git appliquerait vraiment,
  motifs de négation compris.

Un `challenge/work` nu rend 0 sur 8. Un découpage qui **perd** une ressource passe
`terraform validate` avec `Success!` et ne fait tomber que le test de comparaison
des plans. Nommer le fichier `versions.tf` au lieu de `terraform.tf` fait tomber le
socle et, avec lui, les contrôles qui en dépendent.
