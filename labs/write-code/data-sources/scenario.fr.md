# Scénario : maîtriser le moment où une data source est lue

**Sous-objectif d'examen visé : 2b, utiliser des data sources.**

Écrire un bloc `data` est trivial. Savoir **quand** Terraform le lit l'est
beaucoup moins, et c'est ce qui explique qu'un plan bouge sans changement de code.

## Capacité visée

Construire une configuration où le moment de lecture de chaque data source est
délibéré : l'une lue au plan, l'autre reportée à l'apply parce qu'elle dépend
d'une ressource en cours de changement. Prouver la différence dans le JSON.

## D'où part l'apprenant

`challenge/work` ne repose que sur les providers `local`, `null` et `random` :
aucun cloud, aucune VM, aucun coût. Le répertoire est vierge, sans `.terraform/`,
sans fichier de verrouillage, sans state. Il contient `catalogue.txt`
déjà rempli, un `versions.tf` complet, et un `main.tf` troué par des `???` :
l'argument d'une data source qui doit rester connu au plan, celui d'une seconde
qui doit au contraire dépendre d'une ressource produite par la configuration, et
les outputs qui exposent les deux lectures. Un encart du guide affirme que
`depends_on` suffit à forcer la lecture à l'apply : c'est faux, et le lab est
bâti pour le constater.

## L'état à atteindre

1. Le répertoire est initialisé et le fichier de verrouillage existe.
2. Une data source lit le fichier fourni avec un argument connu au plan. Elle
   figure dans `prior_state` avec ses valeurs réelles, dans aucune entrée de
   `resource_changes`, et l'output qui en dérive est connu dès le plan.
3. Une seconde data source lit un fichier produit par une ressource gérée de la
   configuration. Au plan initial, elle figure dans `planned_values` et dans
   `resource_changes` avec `"mode": "data"` et `"actions": ["read"]`, et
   l'output qui en dérive est inconnu.
4. Une troisième data source porte un `depends_on` explicite vers une ressource
   gérée. Une fois cette ressource créée et stable, un nouveau plan la lit au
   plan : le report tient au changement en attente, pas au seul `depends_on`.
5. Après l'apply, le state porte les data sources en `mode: data` et les
   ressources gérées en `mode: managed`, et rejouer un plan n'annonce rien.
6. Modifier `catalogue.txt` sans toucher un fichier `.tf` fait
   apparaître un changement en attente : la dérive vient de la donnée externe.
7. Le plan de destruction ne comporte aucune action portant sur une data
   source : Terraform ne détruit pas ce qu'il n'a jamais créé.

## Comment on le prouve

Aucun test ne relit le `.tf` de l'apprenant, aucun ne parse une sortie humaine.

- Le plan est enregistré puis converti par `terraform show -json` : les tests
  parcourent `prior_state`, `planned_values`, `resource_changes` et
  `output_changes` et situent chaque data source via `mode`, `actions` et
  `after_unknown`.
- `terraform show -json` sur le state final classe chaque adresse par `mode`,
  ce qui interdit de faire passer une ressource gérée pour une data source, et
  `terraform output -json` confirme les valeurs lues.
- `terraform plan -detailed-exitcode` sort en 0 après l'apply, puis en 2 une
  fois le fichier d'entrée modifié : la dérive est prouvée par un code retour.
- Le plan de destruction est converti en JSON : aucune entrée `mode: data` dans
  `resource_changes`.
