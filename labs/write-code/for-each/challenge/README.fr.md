# 🎯 Challenge : ajouter un service sans rien détruire

## ✅ Objectif

`challenge/work` contient une configuration **correcte et déjà appliquée** :
un `terraform.tfstate` est présent, trois services tournent. Rien n'est troué
par des `???`.

Le fichier `DEMANDE.md` porte le besoin : **ajouter le service `api` entre `web`
et `cache`**, sans détruire ni recréer les trois services existants.

Appliquer la demande naïvement détruit de la production. C'est tout l'enjeu.

## 🚦 Commencez par mesurer le dégât

Avant de corriger quoi que ce soit, ajoutez simplement `api` dans la liste et
regardez le plan. Ne l'appliquez pas.

```bash
cd challenge/work
terraform init
terraform plan
```

Notez le nombre de ressources détruites. C'est ce chiffre que vous devez ramener
à zéro.

## 🎯 L'état à atteindre

| # | Exigence |
|---|---|
| 1 | Plus aucun `count` : les deux ressources sont pilotées par `for_each` |
| 2 | Les instances existantes sont réadressées de `[0]`, `[1]`, `[2]` vers `["web"]`, `["cache"]`, `["db"]` **par des blocs `moved`** |
| 3 | Les identités `random_pet` des trois services d'origine sont **inchangées** |
| 4 | `api` est ajouté : **une seule création par type de ressource**, aucune destruction |
| 5 | L'output `identites` est une **map** indexée par nom de service |
| 6 | `terraform plan -detailed-exitcode` retourne **0** en fin de parcours |

## 🧩 Les trois pièges

1. **`for_each` refuse une liste.** Il attend une map ou un set de chaînes, et
   les clés doivent être connues au moment du plan.
2. **Changer `count` en `for_each` change l'adresse des instances.** Sans bloc
   `moved`, Terraform détruit et recrée tout. Le réadressage doit être
   **déclaratif**, pas fait à la main avec `terraform state mv`.
3. **Le splat `[*]` est invalide sur une ressource `for_each`.** Il ne s'applique
   qu'aux listes, sets et tuples. Utilisez une expression `for`.

## 💡 La signature d'un réadressage réussi

Dans le plan JSON, une instance correctement réadressée porte
`"actions": ["no-op"]` **et** un champ `previous_address`. Si vous lisez
`["delete", "create"]`, la ressource est remplacée : c'est raté.

## 🔍 Validation

```bash
dsoxlab check write-code-for-each
```

Les tests ne lisent jamais vos `.tf`. Ils comparent les identités finales à
celles enregistrées dans le state de départ, et analysent le plan de l'ajout
pour compter les créations et les destructions.
