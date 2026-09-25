# Professional mock exam, task 6: HCP Terraform

Twelve questions covering the four sub-objectives of objective 6.
Answer in `reponses.auto.tfvars`.

| Type | Answer format |
| --- | --- |
| single choice | one lowercase letter: `b` |
| multiple choice | the letters SORTED and JOINED: `ab`, never `ba` |

An answer in the wrong format counts as wrong: the real exam is no
more forgiving.


## q01, sous-objectif 6a

Un plan sans changement, sur un workspace sans policy ni estimation de cout, se termine dans quel etat ?

- **a.** planned and finished
- **b.** applied
- **c.** needs confirmation
- **d.** discarded


## q02, sous-objectif 6a

Dans l'ordre officiel des etapes d'un run, la verification OPA passe :

- **a.** avant l'estimation de cout
- **b.** apres l'estimation de cout
- **c.** apres l'apply
- **d.** en meme temps que Sentinel


## q03, sous-objectif 6a

Quelles operations ne bloquent PAS la file de runs d'un workspace ? (deux reponses, lettres triees et collees)

- **a.** les runs plan-only
- **b.** la planification des saved plan runs
- **c.** l'apply d'un plan enregistre
- **d.** les runs declenches par un commit


## q04, sous-objectif 6a

Une run task en echec n'arrete PAS le run a une seule etape. Laquelle ?

- **a.** pre-plan
- **b.** post-plan
- **c.** pre-apply
- **d.** post-apply


## q05, sous-objectif 6b

Une equipe detient « Manage all workspaces » sur l'organisation et le role « Read » sur un workspace. Son acces effectif sur ce workspace est :

- **a.** Read
- **b.** Manage all workspaces
- **c.** aucun
- **d.** Write


## q06, sous-objectif 6b

Dans un bloc `cloud`, `name` et `tags` :

- **a.** se completent
- **b.** s'excluent
- **c.** sont tous deux obligatoires
- **d.** sont tous deux optionnels et cumulables


## q07, sous-objectif 6b

Un bloc `cloud` accepte-t-il `organization = var.nom` ?

- **a.** oui
- **b.** non


## q08, sous-objectif 6b

Dans l'echelle des roles de WORKSPACE, quel role se situe entre Read et Write ?

- **a.** Plan
- **b.** Maintain
- **c.** Admin
- **d.** aucun


## q09, sous-objectif 6c

Une variable marquee `sensitive` et posee dans un attribut de ressource se retrouve :

- **a.** nulle part
- **b.** en clair dans le state
- **c.** chiffree dans le state
- **d.** uniquement dans les journaux


## q10, sous-objectif 6c

Avec les identifiants dynamiques, ce que HCP Terraform envoie a la plateforme cloud est :

- **a.** un workload identity token OIDC
- **b.** la cle privee du workspace
- **c.** les identifiants statiques du workspace
- **d.** un mot de passe a usage unique


## q11, sous-objectif 6c

Combien de temps vivent les identifiants temporaires rendus par la plateforme ?

- **a.** trente jours
- **b.** le temps du run
- **c.** jusqu'a rotation manuelle
- **d.** une heure


## q12, sous-objectif 6d

Ce qui autorise a passer outre une policy en echec est :

- **a.** le niveau d'enforcement seul
- **b.** le reglage du policy set croise avec la permission de l'utilisateur
- **c.** la permission seule
- **d.** l'appartenance a l'organisation
