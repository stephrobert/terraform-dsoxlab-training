# Scénario : le local qui ne se calcule pas au plan

**Sous-objectif d'examen visé : 2c (utiliser les fonctions HCL intégrées et les expressions), avec un débord assumé sur 2f pour la propagation de la sensibilité.**

Un local n'est pas une variable : rien ne le surcharge de l'extérieur, il n'accepte ni type ni description, et sa valeur n'est pas toujours connue au plan. L'apprenant doit construire une chaîne de locals qui traverse ces trois pièges et le prouver sans jamais rouvrir un fichier `.tf`.

## Capacité visée

Centraliser dans des blocs `locals` les expressions d'une configuration : normalisation d'identifiants par fonctions HCL, calcul conditionnel typé, génération d'une liste par expression `for`, dérivation à partir d'un attribut de ressource, et assemblage d'une valeur héritant de la sensibilité d'une variable. Savoir dire, pour chaque local, s'il est résolu au plan ou seulement à l'apply, et pourquoi.

## D'où part l'apprenant

`challenge/work/` contient un projet incomplet. Aucune VM, aucun compte distant : seuls `hashicorp/local` et `hashicorp/random` sont utilisés, avec un `terraform init` et un `.terraform.lock.hcl` déjà en place. Le lab tourne partout où `terraform` est sur le PATH, sans réseau.

Le répertoire contient `versions.tf` et `variables.tf` (déjà corrects), `locals.tf`, `main.tf` et `outputs.tf`. Les variables fournies sont `project` (valeur `Atelier_Locaux`), `environment`, `node_count`, `memory_mb` et `db_password`, cette dernière déclarée `sensitive = true`. `locals.tf` arrive avec **trois blocs `locals` distincts**, volontairement, pour que l'apprenant constate que Terraform les fusionne. Tout leur contenu est troué :

```hcl
locals {                      # nommage
  slug      = ???             # project en minuscules, underscores changés en tirets
  base_name = ???             # slug et environment joints par un tiret
}

locals {                      # calcul
  is_production   = ???       # vrai seulement si environment vaut prod
  effective_ram   = ???       # mémoire doublée en prod, sinon la valeur de la variable
  node_names      = ???       # base_name suffixé -001, -002, ... sur node_count
}
locals {                      # dérivé d'une ressource, donc inconnu au plan
  build_digest  = ???         # 8 premiers caractères de random_id.build.hex
  manifest_name = ???         # base_name, tiret, build_digest, extension .json
  db_dsn        = ???         # postgres://app:<db_password>@localhost/<base_name>
}
```

`main.tf` déclare déjà `random_id.build` et un `local_file.manifest` dont le `filename` et le `content` pointent vers des locals inexistants. `terraform plan` échoue en l'état.

## L'état à atteindre

1. `base_name` vaut `atelier-locaux-prod` : la casse et l'underscore de `Atelier_Locaux` ont été normalisés, et un local en référence un autre dans le même bloc.
2. `node_names` est une liste de `node_count` chaînes de la forme `atelier-locaux-prod-001`, numérotées sur trois chiffres. Elle consomme un local déclaré dans un autre bloc, ce qui prouve que les blocs fusionnent.
3. `effective_ram` est un **nombre** JSON, jamais une chaîne. En `prod` il vaut le double de la variable, ailleurs sa valeur exacte. Le piège est que Terraform convertit sans broncher les deux branches d'un ternaire vers un type commun : écrire `4096 : "2048"` produit une configuration valide mais un résultat de type chaîne.
4. `manifest_name` vaut `atelier-locaux-prod-<8 caractères hexadécimaux>.json`, ces huit caractères étant réellement le préfixe de `random_id.build.hex`.
5. Avant apply, sur un état vide, la sortie exposant `manifest_name` est annoncée comme inconnue : un local dérivé d'un attribut de ressource ne se résout pas au plan.
6. `db_dsn` hérite de la sensibilité de `var.db_password` : la sortie qui l'expose est marquée sensible, faute de quoi Terraform refuse d'exécuter.
7. `local_file.manifest` existe, son chemin est `manifest_name` et son contenu est un JSON portant `base_name`, la liste des noeuds et la mémoire calculée.
8. Le projet converge : un second plan juste après l'apply ne propose plus rien.

## Comment on le prouve

Les tests n'ouvrent jamais les `.tf` de l'apprenant et ne parsent aucune sortie humaine. Ils lancent Terraform dans `challenge/work` et ne lisent que du JSON ou des codes retour.

1. `terraform plan -out=tfplan` sur un état vide, puis `terraform show -json tfplan` : dans `output_changes`, l'entrée `manifest_name` porte `after_unknown` à vrai, alors que `base_name` porte déjà sa valeur définitive. La frontière entre plan et apply est prouvée par le même document.
2. `terraform apply -auto-approve` puis `terraform output -json` : `base_name` vaut exactement `atelier-locaux-prod`, ce qui ne peut pas sortir de `Atelier_Locaux` sans normalisation.
3. Toujours dans ce JSON, `node_names` est une liste de longueur `node_count` dont chaque élément est confronté au gabarit `atelier-locaux-prod-\d{3}`, élément par élément.
4. `effective_ram` est vérifié par son **type JSON** avant sa valeur : un nombre, jamais une chaîne. Le lab est rejoué avec `-var environment=dev` et la double vérification type puis valeur est refaite.
5. `terraform show -json` : une ressource de `mode: managed` et de type `random_id` expose `hex`, et le `filename` du `local_file` commence par `atelier-locaux-prod-` suivi des huit premiers caractères de ce `hex`. Les deux valeurs sont comparées dans le même document, jamais recopiées à la main.
6. Dans ce même `terraform show -json`, `values.outputs.db_dsn.sensitive` vaut vrai. Une configuration dont la sortie ne serait pas marquée sensible n'aurait de toute façon pas atteint l'apply.
7. Le contenu du `local_file` est relu via l'attribut `content` du JSON, désérialisé, et ses trois clés sont confrontées aux sorties correspondantes.
8. `terraform plan -detailed-exitcode` retourne 0 juste après l'apply. Un code 2 fait échouer le lab.
