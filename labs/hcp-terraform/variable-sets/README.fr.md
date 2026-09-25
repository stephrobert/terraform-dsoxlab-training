# Quinze niveaux de précédence, et une inversion

HCP Terraform empile **quinze** sources de valeur pour une même variable. La
liste se lit en une minute et se retient mal, parce qu'elle contient une
inversion que presque personne ne voit.

Ce lab ne requiert **aucun compte HCP Terraform** : l'objectif 6 est évalué en
QCM, et tout se simule en local.

## La table, du plus fort au plus faible

| Rang | Source |
| --- | --- |
| 1 | `-var` en ligne de commande |
| 2 | `TF_VAR_` dans l'environnement |
| 3 | variable set **priority**, global |
| 4 | variable set **priority**, org, portée projet |
| 5 | variable set **priority**, org, portée workspace |
| 6 | variable set **priority**, projet, portée projet |
| 7 | variable set **priority**, projet, portée workspace |
| 8 | variable de **workspace** |
| 9 | variable set normal, projet, portée workspace |
| 10 | variable set normal, projet, portée projet |
| 11 | variable set normal, org, portée workspace |
| 12 | variable set normal, org, portée projet |
| 13 | variable set normal, **global** |
| 14 | `*.auto.tfvars` |
| 15 | `terraform.tfvars` |

## L'inversion

Regardez les rangs 3 à 7, puis 9 à 13. Ils descendent dans des sens opposés.

Chez les variable sets **normaux**, la portée la plus **étroite** gagne :
workspace bat projet, qui bat global. C'est l'intuition, et c'est juste.

Chez les sets **priority**, c'est l'**inverse** : global bat projet, qui bat
workspace.

> When a variable set is priority, the values take precedence over any variables
> with the same key set at a more specific scope.

C'est cohérent une fois qu'on l'a lu : « priority » sert justement à imposer une
valeur depuis le haut, contre ce qu'un échelon plus proche du terrain aurait
posé. Mais qui apprend la table sans lire cette phrase la retiendra à l'envers
pour la moitié des cas.

## Deux autres surprises

**Les fichiers sont en bas.** `terraform.tfvars` ne bat rien du tout, et
`*.auto.tfvars` à peine plus. Le moindre variable set global les écrase. C'est
l'inverse du Terraform local, où ces fichiers dominent les `default`.

**Une map HCL n'a pas d'ordre.** Quand deux variable sets ont la **même** portée
et le **même** propriétaire, rien dans la précédence ne les sépare : c'est
l'ordre **lexicographique de leur nom** qui tranche, par points de code Unicode.
Les chiffres précèdent les majuscules, qui précèdent les minuscules.

## Le contrôle qui empêche d'écrire la réponse

Les six cas fournis se résolvent à la main en dix minutes, et une résolution qui
les nomme un par un passerait.

Les tests rejouent donc la configuration avec **huit cas qu'ils génèrent
eux-mêmes**, que vous n'avez jamais vus, dont deux visent l'inversion et un est
vide. Une résolution qui **parcourt la table** les traite tous ; une résolution
écrite cas par cas n'en traite aucun.

D'où la contrainte de l'énoncé : ne nommer aucun cas en dur.

## Le cas vide, et pourquoi il compte

Un cas sans aucune source renseignée doit résoudre sur une **sentinelle**, pas
sur `null` et surtout pas sur une erreur.

C'est un détail d'écriture qui coûte cher : indexer `[0]` sur une liste vide
fait tomber le **plan entier**, donc tous les autres cas avec. Un `try()` rend la
sentinelle et laisse le reste fonctionner.

## À vous de jouer

```bash
dsoxlab run hcp-terraform-variable-sets
dsoxlab check hcp-terraform-variable-sets
dsoxlab hint hcp-terraform-variable-sets
```

Douze tests, hors ligne. La table est comparée **position par position** : une
seule inversion fait échouer, et le message nomme le rang fautif plutôt que de
rendre quinze lignes illisibles.

Sous-objectif d'examen visé : **6b**.

Référence : [les variables dans HCP Terraform](https://developer.hashicorp.com/terraform/cloud-docs/workspaces/variables)
