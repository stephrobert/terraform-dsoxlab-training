# Un run est un plan, puis un apply de ce plan

L'objectif 6 du Professional est le seul évalué **en QCM**. Mais un run n'est pas
une devinette : c'est une discipline, et cette discipline se joue en local. Ce
lab ne réclame donc **aucun compte**, et il vous fait pourtant exécuter quelque
chose.

## Le plan enregistré est le pendant local d'un run

HCP Terraform « impose la division de Terraform entre les opérations de plan et
d'apply. Il planifie toujours d'abord, puis se sert de la sortie de ce plan pour
l'apply. » Un plan enregistré fait exactement cela :

```bash
terraform plan -out=run1.tfplan
terraform apply run1.tfplan        # aucune confirmation : le plan a tranché
```

Trois refus donnent tout son sens à cette division, et les trois ont été mesurés
le 2026-09-25 sur Terraform 1.16.1.

**Rejouer un plan déjà appliqué est refusé.**

```
Error: Saved plan is stale

The given plan file can no longer be applied because the state was changed by
another operation after the plan was created.
```

C'est le pendant local de la file de runs d'un workspace : « s'il y a déjà un run
en cours, le nouveau run ne démarrera pas avant que le précédent soit
entièrement terminé — HCP Terraform ne le planifiera même pas, parce que le run
en cours pourrait changer ce qu'un run suivant ferait. »

**Changer une variable au moment de l'apply est refusé.**

```
Error: Can't change variable when applying a saved plan
```

Même propriété qu'un run, verrouillé sur une configuration version et un jeu de
variables : « si vous changez des variables ou committez du code avant la fin du
run, cela n'affectera que les runs futurs. »

**Un plan sans changement n'est pas applicable.** `terraform show -json` le dit
dans un champ, `applyable: false`, et HCP Terraform dit la même chose avec un
état de run : **Planned and finished**. Le mode `allow empty apply` est le seul
moyen de passer outre.

## Ce qui décide qu'un run s'applique tout seul

Quatre choses, et le réglage d'auto-apply n'en est qu'une :

| Situation | Issue |
| --- | --- |
| pull request sur un workspace VCS | **plan spéculatif**, ne peut jamais appliquer |
| `terraform plan` via l'intégration CLI | **plan spéculatif** |
| plan sans changement | **planned and finished** |
| auto-apply actif, commit sur la branche suivie, auteur habilité | **s'applique seul** |
| auto-apply actif, run mis en file par un **run trigger** | **attend une confirmation** |
| mode d'exécution `local` | **aucun run distant** |

Les deux derniers sont ceux que les candidats manquent. « Certains plans ne
peuvent pas être auto-appliqués, comme ceux mis en file par des run triggers ou
par des utilisateurs sans permission d'appliquer » : le réglage est actif, le
déclencheur n'y donne pas droit. Et un workspace en mode d'exécution `local`
« n'agit plus que comme un backend distant pour le state », sans Sentinel, sans
estimation de coût et sans notifications, qui reposent toutes sur l'exécution
distante.

## Les onze étapes, et celle qui surprend

| # | Étape | | # | Étape |
| --- | --- | --- | --- | --- |
| 1 | pending | | 7 | **cost estimation** |
| 2 | fetching | | 8 | **sentinel policy check** |
| 3 | pre-plan | | 9 | pre-apply |
| 4 | plan | | 10 | apply |
| 5 | post-plan | | 11 | post-apply |
| 6 | **opa policy check** | | | |

La vérification OPA passe **avant** l'estimation de coût, celle de Sentinel
**après**. Ce n'est pas un détail d'érudition : c'est ce qui fait qu'une règle
Sentinel peut lire un coût estimé, et qu'une règle OPA ne le peut pas.

Une autre asymétrie vaut d'être retenue : les run tasks s'exécutent à plusieurs
étapes, et une tâche en échec arrête le run à chacune d'elles **sauf
post-apply** : il n'y a plus rien à arrêter, l'infrastructure est déjà
provisionnée.

## À vous

```bash
dsoxlab run hcp-terraform-hcp-terraform-overview
dsoxlab check hcp-terraform-hcp-terraform-overview
dsoxlab hint hcp-terraform-hcp-terraform-overview
```

Quinze tests. Les quatre premiers jouent un vrai run et lisent les plans
enregistrés par `terraform show -json` ; les autres lisent ce que la
configuration calcule, jamais ce qu'elle contient.

Sous-objectif d'examen visé : **6a**.

Références : [les états et étapes d'un run](https://developer.hashicorp.com/terraform/cloud-docs/run/states)
et [les opérations distantes](https://developer.hashicorp.com/terraform/cloud-docs/run/remote-operations)
