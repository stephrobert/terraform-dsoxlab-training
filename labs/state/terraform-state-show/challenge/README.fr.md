# Lire le state sans le parser à la main

## La situation

**Sous-objectif d'examen visé : 1e (inspecter et manipuler le state).**

`terraform state show` produit une fiche destinée à un humain, et la doc
officielle interdit d'en extraire quoi que ce soit par programme. Le piège :
cette fiche ment par omission (les attributs nuls disparaissent) et par prudence
(les sensibles sont caviardés), si bien qu'un `grep` sur sa sortie renvoie du
vide là où la valeur existe bel et bien.

## Capacité visée

Extraire de façon fiable l'adresse et les attributs d'une ressource enregistrée
dans le state, y compris quand la valeur est sensible ou nulle, en interrogeant
`terraform show -json` plutôt que la sortie humaine de `terraform state show`.

## D'où part l'apprenant

`challenge/work` contient une configuration complète et déjà écrite, qui n'a
jamais été initialisée ni appliquée :

- `main.tf` : fourni intégralement, à ne pas modifier. Il déclare
  `random_password.api` (24 caractères), `random_pet.env`, trois instances
  `random_pet.replicas` créées par `count = 3`, un `local_file.inventaire`
  dérivé de `random_pet.env` et une data source `data.local_file.relecture`.
- `outputs.tf` : cinq blocs `output` dont la valeur est remplacée par `???`,
  seul fichier à compléter. Trois trous exigent une valeur que seul le state
  contient, deux une adresse dont la forme exacte s'obtient en listant le state.
- Aucun `.terraform/`, aucun `terraform.tfstate`, aucun `.terraform.lock.hcl`.

## L'état à atteindre

1. Un state local existe, avec six ressources en `mode: managed` et une en
   `mode: data`.
2. L'output `adresse_data` porte l'adresse de la data source telle qu'elle
   figure dans le state, préfixe `data.` compris.
3. L'output `adresse_replica` porte l'adresse de la **deuxième** instance de
   `random_pet.replicas`, index compris : sans index, l'adresse ne désigne
   aucune instance et ne vaut rien.
4. L'output `empreinte_inventaire` vaut le `content_sha256` enregistré pour la
   data source, obtenu par référence HCL et non recopié.
5. L'output `secret_api` est marqué `sensitive = true` et vaut le mot de passe
   généré, que `state show` caviarde et que seul le JSON rend lisible.
6. L'output `attributs_masques` est la liste triée des attributs de
   `random_pet.env` à `null` dans le state, donc absents de la fiche humaine.
7. Un nouveau plan ne propose plus aucun changement.

## Comment on le prouve

Les tests pytest n'ouvrent jamais un fichier `.tf` ni la sortie humaine de
Terraform. Ils lancent `terraform show -json` dans `challenge/work` : le décompte
par `mode` valide l'état 1, les adresses trouvées dans
`values.root_module.resources[].address` valident 2 et 3.
`terraform output -json` fournit les cinq outputs, dont les valeurs sont
comparées à celles lues dans le state pour 4 et 5, drapeau `sensitive` compris.
Pour l'état 6, le test recalcule lui même la liste des attributs nuls de
`random_pet.env` depuis le JSON et exige l'égalité, ce qui interdit de deviner.
L'objet `sensitive_values` de `random_password.api` confirme que le caviardage
vient bien de Terraform. Enfin, `terraform plan -detailed-exitcode` doit sortir
en 0 pour l'état 7.

## 🎯 Challenge : extraire du state ce que la fiche humaine refuse de montrer

### ✅ Objectif

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

### 🔍 Validation

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
- `terraform state show` et `-json` : le test lit votre **version** au lieu de
  la supposer. Jusqu'à la 1.15 le drapeau n'existe pas et la commande sort en 1 ;
  depuis la 1.16 il existe et rend une ressource, là où `show -json` rend le
  state entier. Ce qui ne change pas, c'est le périmètre de chacune ;
- `terraform state show` **ne rafraîchit rien** : après une modification hors
  Terraform, sa sortie est inchangée alors que `plan -detailed-exitcode` rend 2 ;
- `plan -detailed-exitcode` rend 0 à la fin : renseigner des outputs ne change
  rien à l'infrastructure.

Bloqué ? `dsoxlab hint state-terraform-state-show`.
