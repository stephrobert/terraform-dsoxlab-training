# Scénario : transformer un catalogue de serveurs avec les expressions for

**Sous-objectif d'examen visé : 2c.**

Une expression `for` rend un tuple entre crochets et un objet entre accolades,
et un splat `[*]` sur une map ne lève aucune erreur : il enveloppe la map entière
dans un tuple d'un seul élément. Ce lab traite ces deux pièges.

## Capacité visée

Dériver, depuis une seule map de serveurs et sans jamais dupliquer une donnée
source, les quatre collections exigées par la configuration : une liste filtrée,
un objet regroupé par rôle, un croisement de deux niveaux aplati, et un ensemble
qui alimente le `for_each` d'une ressource réelle.

## D'où part l'apprenant

`challenge/work` contient une configuration `local` et `null` déjà initialisée
(`terraform init` joué, aucun `apply`, pas de state) :

- `variables.tf` : `var.serveurs`, une `map(object({ env, role, memoire_mo,
  actif, tags }))` de six entrées avec valeurs par défaut. À ne pas modifier.
- `locals.tf` : quatre `locals` dont le corps de l'expression vaut `???`.
- `main.tf` : une ressource `local_file.fiche` dont le `for_each` vaut `???`,
  le contenu du fichier étant déjà écrit.
- `outputs.tf` : quatre `output` qui exposent les `locals`, déjà écrits, à ne
  pas modifier.

Deux serveurs partagent un rôle, un serveur `prod` est inactif, un serveur a une
liste de tags vide : chaque raccourci se voit.

## L'état à atteindre

1. `output "noms_prod"` : un tuple des noms des serveurs dont `env` vaut `prod`,
   dans l'ordre lexicographique des clés que Terraform impose de lui-même.
2. `output "par_role"` : un objet dont chaque clé est un rôle et chaque valeur
   la liste des noms portant ce rôle. Les rôles partagés doivent regrouper, pas
   écraser la clé.
3. `output "memoires"` : un tuple de six nombres, une entrée par serveur. Six,
   pas un : un tuple de longueur 1 signe un splat appliqué à la map.
4. `output "tags_plats"` : un tuple de chaînes `"<serveur>:<tag>"`, une par
   couple existant. Le serveur sans tag n'y figure pas.
5. Un fichier `local_file` existe pour chaque serveur à la fois `prod` et
   `actif`, et pour aucun autre : les clés d'instance de la ressource sont
   exactement cet ensemble.
6. Un second apply ne propose aucun changement.

## Comment on le prouve

Les tests décodent `terraform output -json` : type de la racine (liste pour les
tuples, dictionnaire pour l'objet regroupé), longueur exacte, contenu attendu.
La longueur 6 de `memoires` piège le splat ; une valeur de type liste sous
chaque clé de `par_role` prouve l'ellipsis ; l'absence du serveur sans tag dans
`tags_plats` prouve l'aplatissement plutôt qu'une concaténation à la main.

`terraform show -json` fournit `values.root_module.resources` : les tests y
retiennent les entrées `mode == "managed"` et `type == "local_file"`, puis
comparent l'ensemble de leurs `index` aux serveurs attendus. Un `for_each` non
filtré produit six instances et échoue. Enfin `terraform plan
-detailed-exitcode` doit rendre 0. Aucun test ne lit un fichier `.tf`.
