# 🎯 Challenge : extraire du state ce que la fiche humaine refuse de montrer

## ✅ Objectif

Dans `challenge/work`, `main.tf` et `versions.tf` sont **complets et à ne pas
modifier**. Le seul fichier à compléter est **`outputs.tf`**, qui porte cinq
`???`.

Appliquez d'abord, sinon il n'y a rien à inspecter :

```bash
terraform init
terraform apply
```

Puis remplissez les cinq outputs :

1. **`adresse_data`** : l'adresse de la data source, telle que le state la porte.
   Attention au préfixe.
2. **`adresse_replica`** : l'adresse de la **deuxième** instance de
   `random_pet.replicas`. Sans index, `terraform state show` refuse l'adresse.
3. **`empreinte_inventaire`** : l'empreinte **SHA-256** du fichier relu par la
   data source. Une **référence HCL**, pas une valeur recopiée.
4. **`secret_api`** : le mot de passe généré. Terraform refusera l'output tant
   qu'il n'est pas déclaré sensible, et la fiche de `state show` ne vous le
   montrera pas.
5. **`attributs_masques`** : la liste **triée** des attributs de `random_pet.env`
   qui valent `null` dans le state. `terraform state show` ne les affiche pas du
   tout.

Deux commandes suffisent, et elles ne se valent pas :

```bash
terraform state show random_pet.env      # la fiche, pour vos yeux
terraform show -json | jq '.values...'   # le document, pour un script
```

## 🔍 Validation

`dsoxlab check state-terraform-state-show` **recalcule chaque vérité** depuis
`terraform show -json` et n'utilise jamais la sortie de `state show` pour en
déduire une valeur. Il ne la lance que pour prouver ce qu'elle **cache**.

Sont prouvés, par exécution :

- le state porte **six** ressources en `mode: managed` et **une** en `mode: data` ;
- vos deux adresses existent réellement dans le state, index compris, et une
  adresse **sans** index échoue en code 1 sur
  `No instance found for the given address!` ;
- `secret_api` porte bien `sensitive = true` et vaut le mot de passe du state,
  que la fiche caviarde en `(sensitive value)` et que `sensitive_values` signale ;
- votre liste d'attributs masqués est comparée à celle que le test **recalcule**
  depuis le JSON, et le test vérifie qu'ils sont bien absents de la fiche ;
- `terraform state show` n'a pas d'option `-json` (code 1) et **ne rafraîchit
  rien** : après une modification hors Terraform, sa sortie est inchangée alors
  que `plan -detailed-exitcode` rend 2 ;
- `plan -detailed-exitcode` rend 0 à la fin : renseigner des outputs ne change
  rien à l'infrastructure.

Bloqué ? `dsoxlab hint state-terraform-state-show`.
