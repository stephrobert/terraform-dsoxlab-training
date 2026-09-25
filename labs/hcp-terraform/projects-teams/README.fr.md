# C'est le plus permissif qui gagne, pas le plus spécifique

L'objectif 6 du Professional est évalué **en QCM**, et ne demande aucun compte.
Ce lab fait écrire la règle au lieu de la réciter, parce qu'une règle fausse se
voit sur six cas et qu'une phrase apprise par cœur ne se voit pas.

Il se referme sur une habitude que tous les autres systèmes de permissions ont
construite.

## Additif, et ce que cela veut dire exactement

> Each permission is additive, granting a user the highest level of permissions
> possible, **regardless of which scope set that permission**.

Les droits se posent à trois niveaux, organisation, projet, workspace, et les
permissions effectives d'une équipe sont la somme de tous. Deux exemples de la
documentation encadrent la règle :

| Une équipe détient | Accès effectif |
| --- | --- |
| `Manage all workspaces` sur l'organisation **+** `Read` sur le workspace | **Manage all workspaces** |
| `View all workspaces` sur l'organisation **+** `Write` sur le workspace | **Write** |

Le premier surprend qui attend que le workspace ait le dernier mot. Le second
corrige la sur-correction : additif ne veut pas dire que l'organisation gagne,
cela veut dire que **le droit le plus large gagne**, quel que soit celui qui l'a
accordé.

Notez ce que cela ne veut pas dire non plus : deux `Read` ne font pas un `Write`.
Rien ne s'accumule, c'est le maximum qui est retenu.

## Deux échelles, et ce n'est pas la même

Lues à leur source le 2026-09-25 :

| Portée | Rôles, du moins au plus permissif |
| --- | --- |
| **workspace** | `Read` < `Plan` < `Write` < `Admin` |
| **projet** | `Read` < `Write` < `Maintain` < `Admin` |

`Plan` n'existe qu'au niveau workspace ; `Maintain` n'existe qu'au niveau projet,
et il se place **au-dessus** de l'écriture. Comparer deux niveaux au jugé est
donc hasardeux, et la règle doit les classer explicitement.

`Plan` mérite un regard : il laisse une équipe proposer un changement sans jamais
l'appliquer. C'est ce qui le rend utile, il ouvre la revue sans ouvrir la
production, et c'est pourquoi « peut appliquer » commence à l'écriture, pas au
plan.

## Les permissions que vous n'avez pas accordées

Deux cas où l'accès entre par un système que vous avez branché :

- sur un workspace lié à un dépôt, **quiconque peut fusionner dans la branche
  suivie** peut indirectement y faire partir des plans, « regardless of whether
  they have explicit permission to queue plans or are even a member of your HCP
  Terraform organization ». Avec l'auto-apply, fusionner démarre des runs ;
- une run task reçoit un jeton d'accès, et **tous vivent 10 minutes**.

« An integrated system is able to delegate any level of access that it has been
granted. » Votre matrice de permissions ne vaut que ce que vaut ce que vous y
avez branché.

## À vous

```bash
dsoxlab run hcp-terraform-projects-teams
dsoxlab check hcp-terraform-projects-teams
dsoxlab hint hcp-terraform-projects-teams
```

Treize tests, tous lisant `terraform output -json`. Les six cas sont assérés un à
un, pour que le message dise lequel est faux, et le dernier fait décider le
classement au lieu de seulement classer.

Sous-objectif d'examen visé : **6b**.

Référence : [le fonctionnement des permissions](https://developer.hashicorp.com/terraform/cloud-docs/users-teams-organizations/permissions)
