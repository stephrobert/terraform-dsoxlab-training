# Scénario : quatre niveaux de validation, un seul qui ne bloque pas

**Sous-objectif d'examen visé : 2a, utiliser les fonctionnalités du langage pour valider une configuration.**

Terraform offre quatre dispositifs de validation qui se ressemblent à l'écrit et ne se comportent pas pareil à l'exécution. Ce lab les fait coexister pour faire constater lequel arrête l'opération et lequel se contente d'avertir.

## Capacité visée

Placer une contrainte au bon niveau selon l'effet voulu : refuser une entrée avant le plan (`validation` dans une variable, y compris une validation croisée qui référence une autre variable), refuser une hypothèse avant la création (`precondition` dans `lifecycle`), refuser un résultat après la création (`postcondition`, seule à disposer de `self`), ou surveiller sans bloquer (bloc `check`). Puis lire le verdict des quatre en un seul appel machine, le tableau `checks` de `terraform show -json`.

## D'où part l'apprenant

`challenge/work` contient une configuration incomplète : providers `random` et `local` uniquement, aucune VM, aucun cloud. `versions.tf` est fourni et complet (`required_version >= 1.15.0`).

- `variables.tf` : `nom_projet`, `taille_lot` et `taille_max` déclarées, leurs blocs `validation` présents mais `condition` et `error_message` valent `???`. La validation de `taille_lot` porte sur `taille_max` : elle référence donc une autre variable.
- `main.tf` : un `random_pet` en `count = var.taille_lot` et un `local_file` écrivant un manifeste (un nom par ligne). Le bloc `lifecycle` a une `precondition` et une `postcondition` trouées, avec en commentaire ce que chacune garantit.
- `outputs.tf` : une sortie `noms` dont le bloc `precondition` est troué.
- `checks.tf` : un bloc `check` avec un data source scopé qui relit le manifeste, et un `assert` troué que la consigne demande de faire échouer sur l'état final.

## L'état à atteindre

1. La configuration s'applique et converge, **malgré** le bloc `check` en échec : `random_pet` et `local_file` sont dans le state en `mode: managed`, le manifeste compte autant de lignes que `taille_lot`. L'apply rend 0.
2. Le tableau `checks` de premier niveau de `show -json` porte les **quatre** `address.kind` : `var`, `resource`, `output_value` et `check`.
3. Les trois premiers sont en `status: pass`, le bloc `check` est en `status: fail` et porte le message rédigé par l'apprenant dans `instances[].problems[].message`.
4. Une `precondition` bloque un plan : `plan -var taille_max=20` échoue (le garde-fou `taille_max <= 10` est violé, et les instances existent).
5. `terraform validate -json` rend `valid: true` sur une valeur qui viole la validation croisée, alors que le plan correspondant (`plan -var taille_lot=10`) échoue : la commande dite de validation déclare valide ce que le plan refuse.
6. `plan -detailed-exitcode` rend **2** sur la configuration convergée, alors que le plan annonce zéro ajout, modification et destruction. La seule entrée non `no-op` de `resource_changes` est le data source scopé dans le bloc `check`, en action `read` : il est relu à chaque plan par construction.

## Comment on le prouve

Les tests n'ouvrent aucun `.tf` de l'apprenant et ne lisent aucune sortie destinée à un humain. Ils lancent Terraform dans `challenge/work` et travaillent sur du JSON et des codes retour.

1. `terraform show -json` : le tableau `checks` compte les `address.kind` distincts, exige les quatre, vérifie les `status` (trois `pass`, un `fail`) et que le `check` en échec porte un `error_message` non vide.
2. `terraform plan -var taille_max=20` : code retour non nul, avec « Resource precondition failed ».
3. `terraform validate -json` rend `valid: true` ; `terraform plan -var taille_lot=10` échoue. Le test compare les deux.
4. `terraform plan -detailed-exitcode` rend 2 ; le plan relu en JSON n'a qu'une entrée non `no-op`, le data source du `check`, en `read`.

Une chaîne d'intégration continue qui déciderait sur ce code retour croira toujours qu'il reste des changements.
