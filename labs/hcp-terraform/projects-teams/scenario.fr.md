# Scénario : les permissions s'additionnent, elles ne s'écrasent pas

**Sous-objectif d'examen visé : 6b, les workspaces et leurs options de configuration,
gestion des accès comprise.**

L'objectif 6 est évalué en QCM, et ne demande aucun compte. Ce lab fait donc **écrire la
règle** plutôt que la réciter : une règle fausse se voit sur six cas, une phrase apprise par
cœur ne se voit pas.

Une organisation accorde des droits à trois niveaux, et deux équipes ne sont pas d'accord
sur ce qu'elles peuvent faire du même workspace. L'une détient une permission à l'échelle de
l'organisation et un rôle modeste sur le workspace ; l'autre l'inverse. Les deux croient que
c'est le droit le plus proche qui gagne.

## Capacité visée

Établir l'accès effectif d'une équipe sur un workspace à partir de ce qu'elle détient aux
niveaux organisation, projet et workspace, et connaître les deux échelles de rôles, qui ne
sont pas la même.

## D'où part l'apprenant

`challenge/work` contient deux répertoires :

1. `acces/`, six équipes décrites dans `equipes.auto.tfvars.json` par ce qu'elles détiennent
   à chacun des trois niveaux, avec l'échelle et les équivalences fournies, et deux `???` à
   compléter.
2. `questionnaire/`, cinq réponses à poser dans `reponses.auto.tfvars`.

## L'état à atteindre

1. `acces_effectif` associe à chaque équipe son accès réel, calculé par une règle qui ne
   nomme aucune équipe : une septième serait traitée sans rien réécrire.
2. Cette règle rend le **plus permissif** des trois niveaux, jamais le plus spécifique.
3. `equipes_qui_peuvent_appliquer` liste les équipes qui peuvent lancer un apply, ce qui
   demande au moins l'écriture : le rôle `plan` propose, il n'applique pas.
4. Les cinq réponses établissent ce qui tranche entre deux niveaux, qui peut en pratique
   faire partir un plan sur un workspace lié à un dépôt, combien de temps vit le jeton
   d'accès d'une run task, et quel rôle se situe entre la lecture et l'écriture sur un
   workspace, puis entre l'écriture et l'administration sur un projet.

## Le piège, et d'où il vient

Partout ailleurs, la permission posée au niveau le plus spécifique l'emporte. Ici, non :

> Each permission is additive, granting a user the highest level of permissions possible,
> regardless of which scope set that permission.

Les deux exemples de la documentation encadrent exactement la règle, et le lab les reprend
comme cas 1 et cas 2 : `Manage all workspaces` au niveau organisation l'emporte sur un
`Read` de workspace, tandis que `View all workspaces` ne l'emporte **pas** sur un `Write` de
workspace. Additif ne veut pas dire que l'organisation gagne ; cela veut dire que le droit
le plus large gagne.

## Deux échelles qui ne sont pas la même

Lues à leur source le 2026-09-25 :

| Portée | Rôles, du moins au plus permissif |
| --- | --- |
| workspace | `Read` < `Plan` < `Write` < `Admin` |
| projet | `Read` < `Write` < `Maintain` < `Admin` |

`Plan` n'existe qu'au niveau workspace, `Maintain` qu'au niveau projet, et les deux ne
tombent pas au même endroit. C'est ce qui interdit de comparer deux niveaux au jugé.

## Comment on le prouve

Les tests ne lisent que `terraform output -json` : ce que la configuration calcule, jamais
ce qu'elle contient. Chacun des six cas est asséré séparément, pour que le message dise
lequel est faux, et le dernier test fait **décider** le classement au lieu de seulement
classer : une équipe restée au `plan` doit être exclue de celles qui peuvent appliquer, et
les trois qui écrivent ou mieux doivent y figurer.

Vérifié en dégradant la solution : l'intuition ordinaire, où le niveau le plus spécifique
l'emporte, donne 10/13, et compter `plan` parmi ceux qui peuvent appliquer donne 12/13.
