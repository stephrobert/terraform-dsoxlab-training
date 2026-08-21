# 🎯 Challenge : transformer un catalogue de serveurs

## Point de départ

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

## ✅ Objectif

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

## 🧭 Le piège à connaître

Le **splat `[*]` sur une map ne lève aucune erreur** : il enveloppe la map
entière dans un tuple d'un seul élément. `var.serveurs[*]` a une longueur de 1,
pas de 6. Sur une map, une expression `for` explicite est la seule forme fiable.

## 🔍 Validation

```bash
dsoxlab check write-code-for-loops
```

Neuf tests. Ils décodent `terraform output -json` et `terraform show -json` : type
de chaque racine, longueur exacte, contenu attendu, et l'ensemble des instances
de `local_file.fiche`. Aucun test ne lit vos `.tf` : c'est la **forme du
résultat** qui prouve la bonne expression.
