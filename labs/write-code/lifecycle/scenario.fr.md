# Scénario : le bloc lifecycle décide de l'ordre, pas vous

**Sous-objectif d'examen visé : 2d.**

Le bloc `lifecycle` ne se contente pas de quatre interrupteurs : il réordonne le graphe, il se propage aux dépendances dans un sens contre-intuitif, et il héberge les seules validations qui voient les valeurs résolues au plan. Le piège traité ici est double : croire que `create_before_destroy` se propage vers les ressources qui dépendent de la vôtre, et croire que `prevent_destroy` protège vraiment.

## Capacité visée

Régler le cycle de vie d'une configuration appliquée pour que le remplacement se fasse sans fenêtre de trou, qu'une donnée critique refuse d'être détruite, qu'une dérive externe cesse de polluer les plans sans pour autant aveugler la ressource entière, qu'un déclencheur porté par une simple variable force un remplacement, et qu'une entrée invalide échoue au plan plutôt qu'à l'apply.

## D'où part l'apprenant

`challenge/work` ne contient ni state ni `.terraform` :

- `versions.tf` : complet, à ne pas toucher. `required_version = ">= 1.15.0"`, `hashicorp/local` et `hashicorp/random` épinglés. Aucun provider payant, aucune VM.
- `variables.tf` : complet. `env` (string, défaut `"prod"`), `revision` (number, défaut `1`), `message` (string), `permissions` (string, défaut `"0644"`).
- `modele.txt` : fixture lue par un bloc `data "local_file" "modele"`, elle contient le jeton `{{env}}`.
- `main.tf` : applicable **en l'état**, sans un seul bloc `lifecycle`. `random_pet.version` porte `keepers = { revision = var.revision }`, `local_file.app` a un `filename` qui contient `random_pet.version.id`, `local_file.donnees` tient la donnée à protéger, `local_file.journal` a `content = var.message` et `file_permission = var.permissions`, `local_file.marqueur` ne dépend de rien. La ressource `terraform_data` dont le cinquième objectif a besoin n'existe pas : elle est à écrire.

Il n'y a **pas** de fichier `lifecycle.tf` amorcé avec des `???`. Deux raisons, et elles sont dans le sujet : un bloc `lifecycle` ne peut pas vivre hors d'un bloc `resource`, et des `???` ne sont pas du HCL valide, ce qui rendrait impossible l'`apply` initial que l'énoncé impose comme constat de départ. Tout se pose donc dans `main.tf`, à l'intérieur des ressources concernées.

L'énoncé impose un `init` puis un `apply` avant toute modification. Un `plan -var 'revision=2'` sur cette version est le constat de départ : la nouvelle valeur en place détruit avant de créer.

## L'état à atteindre

1. `local_file.app` porte `create_before_destroy`, et `random_pet.version`, dont il dépend, **n'en porte pas** : c'est Terraform qui le lui applique implicitement, parce que la propagation descend vers les dépendances.
2. `local_file.donnees` refuse tout plan de destruction tant que sa règle est présente dans la configuration.
3. `local_file.journal` ignore un changement de `content` venu de la **configuration**, mais continue de planifier un changement de permissions : le raccourci `all` est donc exclu. Précision vérifiée sur 1.15.4 : `ignore_changes` compare la configuration à l'état, il n'absorbe **pas** une dérive du fichier sur le disque. Pour `local_file`, une modification externe fait disparaître la ressource de l'état, et Terraform planifie alors une création qu'aucun `ignore_changes` ne peut supprimer.
4. Une ressource `terraform_data` porte `input = var.revision`, et `local_file.marqueur` est remplacé chaque fois que cette valeur bouge, sans dépendre d'aucun attribut du marqueur lui-même.
5. `local_file.app` refuse au plan un `env` hors de `dev`, `staging`, `prod`, et refuse après création un contenu où le jeton `{{env}}` n'a pas été substitué.
6. Après l'apply final, un plan sans variable surchargée ne propose plus rien.

## Comment on le prouve

Les tests pilotent Terraform et ne lisent jamais les fichiers `.tf`.

- Ordre du remplacement : `terraform plan -var 'revision=2' -out` puis `terraform show -json` du plan. `resource_changes[]` pour `local_file.app` doit porter `actions == ["create", "delete"]`, et non `["delete", "create"]`. La propagation est prouvée par la même sortie : `random_pet.version` porte lui aussi `["create", "delete"]` alors que l'apprenant n'a rien écrit sur lui. Si l'apprenant a posé la règle sur `random_pet.version` au lieu de `local_file.app`, `local_file.app` reste en `["delete", "create"]` et le test échoue.
- Protection : `terraform plan -destroy -json` doit sortir en code non nul et émettre un message de type `diagnostic`, `severity: error`, dont l'`address` est `local_file.donnees`. Le test relance ensuite un `plan -destroy` après avoir déplacé la configuration dans un répertoire temporaire amputé de ce bloc `resource` : la destruction y est planifiée sans erreur, ce qui démontre la limite documentée de la règle.
- Dérive ignorée : le test lance `terraform plan -var 'message=v2' -out` puis lit le plan en JSON. `local_file.journal` doit y porter `actions == ["no-op"]`. Le même test enchaîne un `plan -var 'permissions=0600'` qui doit, lui, porter un changement sur la même ressource : la portée est bien limitée à un attribut, et le raccourci `all` ferait échouer ce second contrôle. Précision relevée sur 1.15.4 : ce changement de permissions produit un **remplacement** (`["delete", "create"]`) et non une mise à jour en place, `local_file` recréant le fichier. Le test se contente donc d'exiger que le plan ne soit pas `["no-op"]`.
- Déclencheur externe : `terraform plan -var 'revision=2' -json` doit contenir un `resource_changes` sur `local_file.marqueur` avec `actions == ["delete", "create"]` et `action_reason` valant exactement **`replace_by_triggers`** (valeur relevée sur Terraform 1.15.4 ; c'est la seule qui prouve un `replace_triggered_by`, une autre trahirait un remplacement venu d'un changement d'attribut). Un `replace_triggered_by` pointant directement `var.revision` ne peut pas produire ce plan : Terraform répond `Only resources, count.index, and each.key may be used in replace_triggered_by`.
- Validation : `terraform plan -var 'env=bidon' -json` doit produire un `diagnostic` en erreur portant le texte du `error_message` de la précondition, sans qu'aucune ressource ne soit planifiée. La postcondition est vérifiée sur la sortie d'apply avec une fixture dont le jeton n'est pas substitué.
- Idempotence : `terraform plan -detailed-exitcode` rend 0 juste après l'apply final, et `terraform show -json` ne compte aucune ressource en `mode: managed` en dehors des six attendues.

Aucun de ces contrôles ne passe sur un répertoire vide, ni si l'apprenant se contente de recopier les blocs sans les rattacher à la bonne ressource.

Référence : https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/lifecycle-terraform/
