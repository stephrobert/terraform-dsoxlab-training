# 🎯 Challenge : quatre ressources, quatre opérations

## Point de départ

`challenge/work` contient quatre blocs `resource {}` et deux `output`, tous
troués par des `???`. `versions.tf` et `variables.tf` sont **complets, à ne pas
modifier** : ils déclarent les variables `etiquette` (string) et `generation`
(number).

Les `???` sont des erreurs de syntaxe : `terraform init` échoue en l'état.
Chaque trou porte au-dessus de lui un commentaire qui énonce l'attendu.

## ✅ Objectif

Câbler la configuration pour que le state contienne exactement quatre ressources
gérées, aux adresses `random_pet.hote`, `local_file.fiche`,
`terraform_data.sceau`, `local_file.journal` :

1. **`random_pet.hote`** porte des `keepers` liés à `var.generation` : un
   changement de génération doit le remplacer.

2. **`local_file.fiche`** tire l'id de l'hôte dans son `filename` (dépendance
   **implicite**, sans `depends_on`), et porte `create_before_destroy = true`.

3. **`terraform_data.sceau`** porte `input = var.etiquette` (mise à jour en place
   quand l'étiquette change) et `triggers_replace` valant l'id de l'hôte
   (remplacement quand il change).

4. **`local_file.journal`** dépend du sceau par le **seul** `depends_on`, sans
   référencer aucune de ses données : c'est une dépendance de comportement.

5. Les outputs exposent le chemin de la fiche et l'attribut `output` du sceau.

Après votre `apply`, `terraform plan` ne doit plus rien proposer.

## 🧭 Ce que les tests lisent

Le tableau `resource_changes[].actions` du plan JSON. Les tests vérifient les
signatures des quatre opérations :

- `etiquette=v2` : le sceau doit être en **`["update"]`** (mise à jour en place).
- `generation=2` : la fiche doit être en **`["create", "delete"]`**
  (`create_before_destroy`), pas `["delete", "create"]`.

Des blocs mal câblés ne produisent pas ces signatures.

## 🔍 Validation

```bash
dsoxlab check write-code-declare-resources
```

Sept tests. Ils décodent `terraform show -json` (state et configuration),
`output -json` et le plan JSON. Aucun ne lit vos `.tf`.
