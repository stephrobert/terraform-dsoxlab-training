# Scénario : le state sait tout, y compris ce qu'il ne devrait pas

**Sous-objectif d'examen visé : 1e.**

Le state n'est pas une simple table de correspondance : il conserve les secrets en clair, il refuse d'être réécrit par un état antérieur, et il ne signale une dérive que si Terraform a relu le monde réel juste avant. Le piège traité ici est le plan qui annonce « aucun changement » alors que l'infrastructure a bougé.

## Capacité visée

Reprendre la main sur un objet qui existe déjà **sans le recréer** (bloc `import`), constater que le secret qu'il porte se retrouve **en clair** dans le state, distinguer un plan qui a rafraîchi d'un plan qui ne l'a pas fait, et savoir qu'un état antérieur ne peut pas être remis en place par `state push`.

## D'où part l'apprenant

`challenge/work` ne contient ni `terraform.tfstate` ni `.terraform`. Providers `local` et `random` uniquement, aucune VM, aucun cloud.

- `versions.tf`, `variables.tf` : complets, à ne pas toucher.
- `mot-de-passe-existant.txt` : fixture. Vingt caractères, sans retour à la ligne final. C'est le mot de passe **déjà en service** dans l'application, celui qu'il est **interdit de régénérer**.
- `main.tf` : trois ressources, des `???`. `random_password.db` a une `length` trouée. `local_file.configuration` écrit `app.conf` en `0600` avec un `content` troué. `local_file.journal` écrit `service.log` et se suffit à lui-même. Le **bloc `import`** est à ajouter.

Le raccourci qui vient à l'esprit est interdit : un `terraform apply` seul tirerait un mot de passe neuf, `app.conf` porterait une valeur inconnue de l'application, et le lab serait perdu **sans message d'erreur**. Il faut d'abord **rattacher** le mot de passe existant.

## L'état à atteindre

1. Le state contient exactement **trois** ressources en `mode: managed`, aucune en `mode: data`.
2. `random_password.db.result` vaut **exactement** la chaîne de `mot-de-passe-existant.txt` : la valeur n'a pas été tirée au sort, elle a été **rattachée** par un bloc `import` appliqué au premier `apply`.
3. `app.conf` contient cette même chaîne (`content` de `local_file.configuration`).
4. Un `terraform plan` juste après l'apply ne propose rien.

## Comment on le prouve

Les tests pilotent Terraform et ne lisent jamais les `.tf` de l'apprenant. La fixture `mot-de-passe-existant.txt` est lue : c'est la référence attendue.

1. **Reprise sans régénération** : `show -json`, `random_password.db.result` égal, caractère pour caractère, au contenu de la fixture (comparaison après décodage JSON, jamais sur le texte brut). Un apprenant qui a simplement appliqué obtient une autre chaîne et échoue. `app.conf` contient la même valeur.
2. **Secret en clair** : `terraform state pull`, l'instance de `random_password.db` a `attributes.result` en clair **et** `result` dans `sensitive_attributes`. La marque existe, la protection non.
3. **Dérive et refresh** : le test écrit une ligne dans `service.log` hors Terraform, puis exige `plan -detailed-exitcode` = `2` et `plan -refresh=false -detailed-exitcode` = `0` sur cette dérive. Un `apply` rétablit, puis `plan` retombe à `0`. Ce couple de codes prouve que la détection vient du **rafraîchissement**, pas du state.
4. **Garde-fou du state** : le test fabrique une copie du state courant de `serial` inférieur, la pousse par `terraform state push`, et exige un refus (`cannot import state with serial ... over newer state ...`) ainsi qu'un `serial` courant inchangé. Il rejoue sur une copie de `lineage` différent : le refus est également attendu, mais le message **diffère** (`unrelated state with lineage ...`).
5. **Idempotence** : `plan -detailed-exitcode` = `0`, et aucune ressource gérée hors des trois attendues.

Aucun de ces contrôles ne passe sur un `challenge/work` vide, ni sur un répertoire où l'apprenant se serait contenté d'un `init` suivi d'un `apply`.

Référence : https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/comprendre-state/
