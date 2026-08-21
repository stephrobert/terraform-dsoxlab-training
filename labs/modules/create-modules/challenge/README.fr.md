# 🎯 Challenge : rendre un module hérité réutilisable

## 📦 Le point de départ

`challenge/work` contient un projet à deux niveaux : une racine et un module
local `modules/livrable/`. La racine veut livrer **trois environnements** avec un
seul bloc `module` muni de `for_each`.

Commencez par le constat, avant toute modification :

```bash
terraform init
```

L'`init` **échoue**, et son message nomme le problème et la solution. C'est le
point de départ du lab : lisez-le en entier.

| Fichier | Ce que c'est |
| --- | --- |
| `versions.tf`, `variables.tf` (racine) | complets, **à ne pas toucher** |
| `main.tf` (racine) | l'appel du module, il manque un argument |
| `outputs.tf` (racine) | deux sorties à écrire, livrées en commentaire |
| `modules/livrable/main.tf` | le module, avec **un défaut hérité** |
| `modules/livrable/versions.tf` | ses exigences, une ligne à ajouter |
| `modules/livrable/variables.tf` | trois variables, sans documentation |
| `modules/livrable/outputs.tf` | deux sorties à compléter |

## ✅ Objectif

Rendre ce module **appelable plusieurs fois**, en lui retirant ce qui l'en
empêche, puis en lui passant proprement la configuration de provider dont il a
besoin.

## 📋 Ce qu'il faut obtenir

1. Plus **aucune configuration de provider** ne vit dans `modules/livrable/`.
   Elles restent à la racine, et le module conserve ses `required_providers` :
   les configurations s'héritent, les exigences de source et de version jamais.
2. Le module **déclare** la configuration aliasée qu'il attend, sous son exigence
   `local`.
3. L'appel de la racine **lui passe** cette configuration, sous le nom que
   l'enfant attend.
4. Dans le module, `local_file.archive` reste rattachée à la configuration
   aliasée, `local_file.manifeste` à la configuration par défaut.
5. Le `for_each` produit **trois instances**, `module.livrable["dev"]`,
   `["preprod"]` et `["prod"]`.
6. Chaque variable du module porte une **`description`** non vide, et **aucune**
   n'a de `default` : elles restent obligatoires.
7. Les deux outputs du module sont complétés, et ceux de la racine **agrègent**
   les trois instances en un objet indexé par environnement.
8. `terraform apply` passe, les six fichiers de `livraisons/` existent, et
   `terraform plan -detailed-exitcode` sort en **0**.

## ⚠️ Le cœur du sujet

La règle officielle tient en une phrase : **« a module intended to be called by
one or more other modules must not contain any `provider` blocks »**. Terraform
ne l'applique pas par principe, il l'applique parce qu'il ne peut pas faire
autrement : un module qui configure ses providers ne peut être instancié qu'une
fois.

Trois erreurs vous attendent, dans cet ordre, et chacune désigne l'étape
suivante :

| Message | Ce qu'il réclame |
| --- | --- |
| `Module is incompatible with count, for_each, and depends_on` | retirer la configuration de provider de l'enfant |
| `Provider configuration not present` | déclarer l'alias attendu dans le module |
| `Missing required provider configuration` | passer cette configuration depuis l'appelant |

Retirer le `for_each` ferait disparaître la première erreur. Ce n'est pas la
solution : les tests exigent les trois instances.

## 🔍 Validation

`dsoxlab check modules-create-modules` prouve, par exécution :

- aucune entrée de `provider_config` ne porte de `module_address`, et l'alias
  `archive` est toujours déclaré à la racine ;
- le bloc `module` porte bien un `for_each`, et le state contient les trois
  adresses indexées ;
- le `provider_config_key` de chaque ressource de l'enfant pointe vers la bonne
  configuration, ce qui prouve le câblage de l'argument `providers` ;
- chaque variable du module a une `description` et aucun `default` ;
- les deux outputs de la racine ont trois clés, et les chemins annoncés
  correspondent à des fichiers réels ;
- `plan -detailed-exitcode` rend **0**.

Aucun test n'ouvre vos fichiers `.tf`.

Bloqué ? `dsoxlab hint modules-create-modules`.
