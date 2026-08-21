# Scénario : count indexe par position, et la position ment

**Sous-objectif d'examen visé : 2d.**

`count` est facile à écrire et coûteux à défaire : ses instances sont identifiées par leur rang, pas par leur identité. Le piège traité ici est le retrait au milieu d'une liste, qui décale les rangs suivants et fait détruire des objets que personne n'avait demandé de toucher.

## Capacité visée

Placer `count` et `for_each` chacun sur la famille de ressources qui le mérite, migrer une ressource déjà appliquée de l'adressage par index vers l'adressage par clé sans détruire un seul objet, et démontrer dans le plan JSON qu'un retrait au milieu ne touche plus que l'élément retiré.

## D'où part l'apprenant

`challenge/work` ne contient ni state ni `.terraform` :

- `versions.tf` et `variables.tf` : complets, à ne pas toucher. `required_version = ">= 1.15.0"`, providers `hashicorp/local` et `hashicorp/random` épinglés, variables `services` (`list(string)`, défaut `["web", "api", "cache"]`), `workers` (number, défaut `3`), `rapport` (bool, défaut `false`).
- `main.tf` : `local_file.service` est écrit et applicable **en l'état**, avec `count = length(var.services)` et `filename = "${var.services[count.index]}.txt"`. C'est la version piégée, volontairement fonctionnelle.
- `workers.tf`, `rapport.tf` et `outputs.tf` : blocs amorcés, avec des `???` sur le meta-argument, sur l'index, sur la condition et sur les trois valeurs de sortie.
- `challenge/reference/` : copie figée de la version `count` d'origine, utilisée par les tests.

L'énoncé impose un `init` puis un `apply` **avant toute modification** : la migration part d'une infrastructure vivante, trois fichiers réels et un état qui porte `local_file.service[0]`, `[1]` et `[2]`. Un `plan -var 'services=["web","cache"]'` sur cette version est le constat de départ : deux objets bougent pour un seul service retiré.

## L'état à atteindre

1. `local_file.service` est adressé par clé : l'état porte `local_file.service["web"]`, `["api"]` et `["cache"]`, via `for_each = toset(var.services)` et `each.key` au lieu de `count.index`.
2. Les trois objets du premier apply ont survécu à la migration : des blocs `moved` relient `local_file.service[0]` à `["web"]`, `[1]` à `["api"]`, `[2]` à `["cache"]`.
3. `random_pet.worker` reste en `count = var.workers` : trois instances vraiment interchangeables, le seul cas où `count` est le bon outil.
4. `local_file.rapport` porte `count = var.rapport ? 1 : 0` et n'existe pas par défaut.
5. Les sorties sont câblées : `noms_workers` par le splat `random_pet.worker[*].id`, `chemins_services` par une expression `for` sur la map (le splat ne s'applique pas à `for_each`), `rapport` par `one(local_file.rapport[*].filename)`.
6. Rien d'autre n'est en `mode: managed`, et un `plan` après l'apply final ne propose plus rien.

## Comment on le prouve

Les tests pilotent Terraform et ne lisent jamais les fichiers `.tf`.

- `terraform show -json` : `values.root_module.resources` contient exactement `local_file.service["web"|"api"|"cache"]` et `random_pet.worker[0..2]`, tous en `mode: managed`. La forme de l'adresse tranche seule : une clé prouve `for_each`, un index prouverait que `count` est resté en place.
- `terraform plan -var 'services=["web","cache"]' -json` : un seul `resource_changes`, adresse `local_file.service["api"]`, `actions == ["delete"]`, aucun changement sur les survivants. Sur la version d'origine, le même plan porte `["delete", "create"]` sur `[1]` et `["delete"]` sur `[2]` : la destruction parasite est chiffrée, pas racontée.
- Blocs `moved` : le test recopie `challenge/reference/` et le `.terraform` du workdir dans un répertoire temporaire, y applique la version `count`, écrase la configuration par celle de l'apprenant, puis lance `plan -json`. Les trois `resource_changes` doivent porter `actions: ["no-op"]` et un `previous_address` en `local_file.service[0..2]`. Sans les blocs `moved`, le même plan annonce trois destructions et trois créations.
- `terraform plan -var 'workers=2' -json` : un seul changement, `random_pet.worker[2]` détruit. Réduire `count` retire l'index le plus haut, ce qui est légitime pour des instances interchangeables.
- `terraform output -json` : `noms_workers` est une liste de trois chaînes, `chemins_services` une map à trois clés nommées, `rapport` vaut `null`. Puis `plan -var 'rapport=true' -json` : une seule création planifiée, `local_file.rapport[0]`, preuve du `count` conditionnel.
- `terraform plan -detailed-exitcode` : code 0 juste après l'apply final.

Aucun de ces contrôles ne passe sur un répertoire vide, ni si l'apprenant détruit puis recrée au lieu de réadresser.

Référence : https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/count-terraform/
