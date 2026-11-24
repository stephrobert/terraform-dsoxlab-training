# Transformer un catalogue de serveurs avec les expressions for

## La situation

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

## 🎯 Challenge : transformer un catalogue de serveurs

### Point de départ

`challenge/work` contient une map `var.serveurs` de six entrées, déjà écrite et
**à ne pas modifier**. `outputs.tf` est complet lui aussi. Deux fichiers sont
troués par des `???` :

- `locals.tf` : quatre `locals` dont le corps est à écrire.
- `main.tf` : le `for_each` de `local_file.fiche`.

Tant que les `???` sont là, la configuration ne parse pas. Chaque trou porte
au-dessus de lui un commentaire qui énonce l'attendu.

Le catalogue est construit pour piéger les raccourcis : deux serveurs partagent
un rôle, un serveur `prod` est **inactif** (`web2`), un serveur a une liste de
tags **vide** (`db`).

### ✅ Objectif

Produire, depuis la seule map `var.serveurs`, ces cinq résultats :

1. **`noms_prod`** : un **tuple** des noms des serveurs dont `env` vaut `prod`.
   Crochets, et laissez Terraform trier les clés.

2. **`par_role`** : un **object** dont chaque clé est un rôle et chaque valeur la
   **liste** des noms portant ce rôle. Deux serveurs partagent un rôle : il faut
   **grouper**, pas écraser la clé.

3. **`memoires`** : un **tuple** des mémoires, **une entrée par serveur**. Six,
   pas une. Un tuple de longueur 1 trahirait un splat appliqué à la map.

4. **`tags_plats`** : un **tuple** de chaînes `"<serveur>:<tag>"`, une par couple
   existant. Croisez deux niveaux, puis aplatissez. Le serveur sans tag doit
   disparaître **de lui-même**, sans clause `if`.

5. **`local_file.fiche`** : une fiche pour chaque serveur à la fois `prod` **et**
   actif, et pour aucun autre. Filtrez le `for_each` de la ressource.

Après votre `apply`, `terraform plan` ne doit plus rien proposer.

### 🧭 Le piège à connaître

Le **splat `[*]` sur une map ne lève aucune erreur** : il enveloppe la map
entière dans un tuple d'un seul élément. `var.serveurs[*]` a une longueur de 1,
pas de 6. Sur une map, une expression `for` explicite est la seule forme fiable.

### 🔍 Validation

```bash
dsoxlab check write-code-for-loops
```

Neuf tests. Ils décodent `terraform output -json` et `terraform show -json` : type
de chaque racine, longueur exacte, contenu attendu, et l'ensemble des instances
de `local_file.fiche`. Aucun test ne lit vos `.tf` : c'est la **forme du
résultat** qui prouve la bonne expression.
