# 🎯 Challenge : à quel moment Terraform lit-il une data source ?

## Point de départ

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

## ✅ Objectif

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

## 🧭 Comment observer par vous-même

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

## 🔍 Validation

```bash
dsoxlab check write-code-data-sources
```

Douze tests. Ils parcourent `prior_state`, `resource_changes`, `output_changes`
et le `mode` de chaque adresse du state. Recopier le contenu du catalogue dans
un `local_file` au lieu de le lire produirait `mode: managed` et serait détecté.
