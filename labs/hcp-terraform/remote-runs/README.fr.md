# Le résumé d'un run dit ce qui était prévu, pas ce qui a eu lieu

L'objectif 6 du Professional est évalué **en QCM** et ne demande aucun compte.
Mais ce qu'une CLI reçoit d'un run distant n'a rien de mystérieux : c'est le flux
structuré que `terraform apply -json` produit en local, un message JSON par
ligne, ce qui permet justement à HCP Terraform d'afficher un run au fil de l'eau
plutôt qu'à la fin.

Ce lab en enregistre un vrai, issu d'un run qui **échoue en cours de route**, et
le lit.

## Un type de message par moment du run

| Type | Ce qu'il dit |
| --- | --- |
| `version` | la version de Terraform, une fois, au début |
| `planned_change` | un par ressource que le plan compte changer |
| `change_summary` | les comptes, par opération |
| `apply_start` | une application commence |
| `apply_complete` | une application a **abouti** |
| `apply_errored` | une application a **échoué** |
| `diagnostic` | le détail de l'erreur, avec l'adresse fautive |

## La mesure sur laquelle ce lab est bâti

Mesuré le 2026-09-25 sur Terraform 1.16.1, sur la même configuration selon
qu'elle aboutit ou non :

| Run | Messages `change_summary` |
| --- | --- |
| qui aboutit | deux, `operation: plan` puis `operation: apply` |
| qui échoue en cours | **un**, `operation: plan` seul |

Sur un run interrompu, le seul résumé du flux est donc celui que le plan
**annonçait** :

```json
{"type":"change_summary","changes":{"add":3,"change":0,"remove":0,"operation":"plan"}}
```

Il annonce trois ajouts. Deux ressources ont été créées. Rien dans ce message ne
le dit, et l'écart ne se lit qu'en comptant les messages `apply_complete`.

C'est pourquoi filtrer sur `operation == "apply"`, qui est le réflexe juste sur
un run qui aboutit, ne rend rien ici.

## Lire un flux JSONL en HCL

Un fichier JSONL n'est pas du JSON : c'est un objet par ligne. Il se découpe,
puis se décode, et la garde vient **avant** le décodage, parce que
`jsondecode("")` échoue :

```hcl
locals {
  messages = [
    for ligne in split("\n", file("${path.module}/../flux/run.jsonl")) :
    jsondecode(ligne) if trimspace(ligne) != ""
  ]
}
```

Ensuite, `distinct` évite d'écrire la liste des types à la main : elle se lit
dans le flux, et un flux plus riche se compte sans rien changer.

## Trois workflows, et ce que chacun interdit

| Workflow | Ce qu'il fait | Ce qu'il interdit |
| --- | --- | --- |
| **UI/VCS** | le dépôt est la source de vérité | **aucun remote apply depuis la CLI** |
| **CLI** | envoie une archive du répertoire local | exige une saisie console pour approuver |
| **API** | vous envoyez la configuration version | rien, et c'est pourquoi il est recommandé en CI |

Deux détails à retenir. Un run CLI prend son **code** dans le répertoire local
mais ses **valeurs de variables** dans le workspace. Et `.terraformignore`,
supporté depuis Terraform 0.12.11, exclut des fichiers de ce qui est envoyé.

## À vous

```bash
dsoxlab run hcp-terraform-remote-runs
dsoxlab check hcp-terraform-remote-runs
dsoxlab hint hcp-terraform-remote-runs
```

Douze tests. Ils relisent votre flux et recalculent ce que votre analyse aurait
dû rendre : rien n'est gelé, et un flux écrit à la main échoue, parce que l'état
du système doit concorder avec lui.

Sous-objectif d'examen visé : **6a**.

Référence : [le workflow de run par la CLI](https://developer.hashicorp.com/terraform/cloud-docs/run/cli)
