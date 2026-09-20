# 🎯 Challenge : classer un plan avant de l'appliquer

## Point de départ

`challenge/work` contient trois fichiers, **tous fournis** :

- `versions.tf` : épingle `local`, `null` et `random`.
- `main.tf` : **cinq ressources**, une seule variable `etiquette`. Elles ne
  réagissent pas toutes de la même façon à un changement de cette variable.
- `terraform.tfvars` : pose `etiquette = "v1"`.

Le répertoire n'est pas initialisé et il n'y a pas de state.

## ✅ Objectif

1. **Posez l'état de référence** : initialisez et appliquez la configuration
   telle quelle.
2. **Changez la valeur** : faites passer `etiquette` à `"v2"` dans
   `terraform.tfvars`.
3. **Enregistrez le plan** dans un fichier nommé `tfplan`, avec
   `terraform plan -out=tfplan`.
4. **Convertissez-le** en `plan.json`, avec `terraform show -json tfplan`.
5. **Classez** chaque adresse qui change dans un fichier `analyse.json` :

   ```json
   {
     "mise_a_jour_en_place": ["..."],
     "remplacement": ["..."]
   }
   ```

6. **Appliquez ce plan-là**, avec `terraform apply tfplan`. Pas de
   replanification, pas de confirmation interactive.

## 🧭 Ce que le lab vous fait constater

- **Une seule des cinq ressources est mise à jour en place.** Les quatre autres
  dépendent de l'étiquette par un argument qui force un remplacement :
  `triggers_replace`, le contenu d'un fichier, des `keepers`, des `triggers`.
- **`local_file` ne se met jamais à jour.** Chez ce provider, tout force un
  remplacement, jusqu'aux permissions du fichier.
- **L'ordre des actions varie, le sens non.** `["delete", "create"]` et
  `["create", "delete"]` désignent le même remplacement, le second avec
  `create_before_destroy`.
- **Le plan appliqué devient périmé.** Rejouez `terraform apply tfplan` et
  Terraform refuse : c'est la preuve qu'il a été consommé.
- **Un remplacement ne connaît pas son futur identifiant.** Il est marqué
  inconnu dans le plan, là où une mise à jour en place conserve le sien.

## 🔍 Validation

```bash
dsoxlab check getting-started-terraform-workflow
```

Huit tests. Le plan enregistré est rouvert **par l'outil** : un `tfplan`
fabriqué à la main ne passe pas. La vérité n'est jamais tirée de votre
`analyse.json` : elle est recalculée depuis les actions du plan, puis comparée
à votre classement, adresse par adresse. Aucun test ne lit vos `.tf`.
