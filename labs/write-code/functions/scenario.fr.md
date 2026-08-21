# Scénario : composer des valeurs avec les fonctions HCL

**Sous-objectif d'examen visé : 2c.**

Les fonctions HCL passent pour la partie facile de l'examen, jusqu'au jour où un index hors bornes, une clé absente ou un template mal échappé fait échouer le plan. Ce lab enchaîne ces pièges et ajoute la nouveauté que presque aucun guide ne traite : les fonctions exposées par un provider.

## Capacité visée

Produire les valeurs exactes attendues par des ressources et des outputs en n'écrivant que des expressions de fonctions : normaliser une chaîne, dédupliquer une collection pour alimenter un `for_each`, fusionner des maps avec la bonne priorité, rendre un template sans corrompre son contenu littéral, et appeler une fonction fournie par un provider déclaré.

## D'où part l'apprenant

`challenge/work` contient une configuration qui refuse de se valider :

- `versions.tf` : `required_version = ">= 1.8"` et un bloc `required_providers` qui ne déclare que `local`. Le provider intégré `terraform` (`source = "terraform.io/builtin/terraform"`) n'y est pas.
- `variables.tf`, complet et non modifiable : `environments_csv = "prod,dev,prod,staging"`, `tags = { projet = "demo", equipe = "devops" }`, `environment = "qa"`, `memory_mib = 1536`.
- `locals.tf` : sept locals dont la valeur est remplacée par `???`.
- `outputs.tf`, complet et non modifiable : il expose chacun de ces locals.
- `main.tf` : une ressource `local_file` par environnement distinct, dont le `for_each` et le `content` sont eux aussi troués par des `???`.
- `templates/node.yaml.tftpl` : un template contenant un marqueur à substituer, une séquence `${...}` à conserver littéralement, et les chaînes `$HOME` et `$(date)` d'un script shell.

## L'état à atteindre

1. `terraform apply` se termine sans erreur, puis `terraform plan -detailed-exitcode` retourne 0.
2. Le state contient exactement trois instances de `local_file`, adressées par une valeur d'environnement (`["dev"]`, `["prod"]`, `["staging"]`) et non par un index numérique : la source du `for_each` est donc une collection dédupliquée, pas la liste brute issue du découpage du CSV.
3. L'output `env_recycle` vaut `"staging"` : c'est un accès par position, sur la liste triée des trois environnements, avec un index de 5. L'index reboucle en modulo et ne retombe donc pas sur le premier élément.
4. L'output `taille` vaut `"small"` alors que `"qa"` est absent de la table de correspondance : la lecture fournit une valeur de repli au lieu d'interrompre le plan.
5. L'output `tags_effectifs` contient `projet`, `equipe` et `env`, et `env` vaut `"qa"` : la map ajoutée en dernier l'emporte.
6. L'output `memory_gib` vaut `2` pour 1536 Mio : l'arrondi va vers le haut, jamais vers le bas.
7. Chaque fichier écrit sur disque contient le nom d'hôte substitué, la séquence `${...}` restée littérale, et `$HOME` comme `$(date)` intacts.
8. L'output `tfvars_rendu` est produit par `provider::terraform::encode_tfvars`, ce qui suppose d'avoir déclaré le provider intégré `terraform` dans `required_providers` et relancé `terraform init`.

## Comment on le prouve

- `terraform output -json` fournit les six valeurs scalaires attendues. Un accès par position mal calculé, une lecture de map sans repli, une fusion dans le mauvais ordre ou un arrondi vers le bas changent la valeur et font échouer le test correspondant.
- `terraform show -json` donne la liste des ressources : on filtre `mode == "managed"` et `type == "local_file"`, puis on vérifie que l'ensemble des `index` vaut exactement `{"dev", "prod", "staging"}`. Un `for_each` sur la liste non dédupliquée échoue à l'apply, un `count` produit des index entiers, et les deux sont détectés ici.
- Le même document expose l'attribut `content` de chaque instance : le test y cherche le nom d'hôte substitué, la présence littérale de `${` et celle de `$HOME` et `$(date)`. Un échappement de tous les `$` en `$$`, comme le suggèrent beaucoup de tutoriels, laisse `$$HOME` dans le rendu et échoue.
- L'output `tfvars_rendu` prouve l'appel à la fonction du provider : le test compare la chaîne exacte que produit l'encodage, et cette valeur reste indisponible tant que le provider intégré n'est pas déclaré.
- `terraform plan -detailed-exitcode` doit retourner 0 après l'apply. Le code 2 signale une expression non stable, typiquement un horodatage glissé dans le template.
- Aucun test ne lit les fichiers `.tf` de l'apprenant. Un `challenge/work` laissé en l'état ne produit ni state ni output : la première commande échoue et rien ne passe.
