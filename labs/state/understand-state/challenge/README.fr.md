# 🎯 Challenge : reprendre la main sans régénérer le secret

## ✅ Objectif

Dans `challenge/work`, le mot de passe de `mot-de-passe-existant.txt` est **déjà
en service**. Complétez `main.tf` pour le **rattacher** à `random_password.db`
sans le régénérer, puis écrire `app.conf` avec cette valeur.

Un `terraform apply` seul est **interdit** : il tirerait un mot de passe neuf.

À faire dans `main.tf` :

1. **ajouter un bloc `import`** : `to = random_password.db`, `id =
   file("${path.module}/mot-de-passe-existant.txt")` ;
2. remplir la **`length`** de `random_password.db` (la longueur exacte du mot de
   passe existant) ;
3. remplir le **`content`** de `local_file.configuration`, de la forme
   `"mdp=${random_password.db.result}"`.

Puis appliquez : le bloc `import` rattache l'existant, sans régénération.

## 🔍 Validation

`dsoxlab check state-understand-state` prouve, sur du JSON et l'état réel :

- `random_password.db.result` vaut **exactement** le mot de passe de la fixture
  (pas une valeur tirée au hasard) ; `app.conf` le contient ;
- le secret est **en clair** dans `state pull`, tout en étant marqué
  `sensitive_attributes` ;
- une dérive de `service.log` est vue par `plan` (exit 2) mais pas par
  `plan -refresh=false` (exit 0) ;
- `state push` refuse un `serial` antérieur et un `lineage` différent ;
- idempotence, exactement 3 ressources managed.

Bloqué ? `dsoxlab hint state-understand-state`.
