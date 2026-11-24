# Maîtriser le moment où une data source est lue

## La situation

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

## 🎯 Challenge : à quel moment Terraform lit-il une data source ?

### Point de départ

`challenge/work` contient deux ressources gérées déjà écrites, et **trois blocs
`data` plus deux `output` laissés en commentaire**, chacun troué par un `???`.
Chaque trou porte au-dessus de lui un commentaire qui énonce l'attendu.

La configuration s'applique donc **telle quelle**. Commencez par là, vous aurez
un point de départ stable :

```bash
terraform init
terraform apply
```

Décommentez ensuite un bloc à la fois et complétez-le. C'est la comparaison
entre deux étapes qui fait comprendre le sujet, pas le résultat final : le
tutoriel (`README.fr.md`) donne pour chacune la commande d'observation et la
sortie attendue.

Ne touchez ni à `versions.tf`, ni à `variables.tf`, ni à `catalogue.txt`.

### ✅ Objectif

1. **Une lecture connue au plan.** `data.local_file.catalogue` lit
   `catalogue.txt`. Son argument ne doit référencer aucune ressource gérée :
   uniquement `path.module`.

2. **Une lecture reportée.** `data.local_file.rapport_relu` relit le fichier
   **produit** par `local_file.rapport`, en référençant son attribut `filename`.
   Ne recomposez pas le chemin à la main : c'est la référence qui crée la
   dépendance, et donc le report.

3. **Un `depends_on` qui ne reporte rien.** `data.local_file.catalogue_ordonne`
   lit le même `catalogue.txt` que la première, avec en plus un `depends_on`
   explicite vers `random_pet.empreinte`. Une fois cette ressource stable, elle
   est lue **au plan**, exactement comme la première. C'est le cœur du lab.

4. **Deux outputs.** `catalogue` expose la première lecture, connue dès le plan.
   `rapport` expose la deuxième, inconnue au plan initial.

Après votre `apply`, `terraform plan` ne doit plus rien proposer.

### 🧭 Comment observer par vous-même

C'est la manipulation qui fait comprendre le sujet :

```bash
terraform apply
terraform plan -out=tf.plan
terraform show -json tf.plan | jq '.resource_changes[] | {address, mode, actions: .change.actions}'
```

Rien ne devrait apparaître. Puis mettez la ressource gérée en mouvement :

```bash
terraform plan -var 'revision=2' -out=tf.plan
terraform show -json tf.plan | jq '.resource_changes[] | select(.mode == "data")'
```

Cette fois, `rapport_relu` apparaît avec `"actions": ["read"]`. Comparez avec
`catalogue_ordonne`, qui porte pourtant un `depends_on`.

### 🔍 Validation

```bash
dsoxlab check write-code-data-sources
```

Douze tests. Ils parcourent `prior_state`, `resource_changes`, `output_changes`
et le `mode` de chaque adresse du state. Recopier le contenu du catalogue dans
un `local_file` au lieu de le lire produirait `mode: managed` et serait détecté.
