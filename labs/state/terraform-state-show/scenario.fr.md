# Scénario : lire le state sans le parser à la main

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
