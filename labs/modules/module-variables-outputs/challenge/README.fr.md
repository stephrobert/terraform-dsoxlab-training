# 🎯 Challenge : écrire l'interface d'un module appelé deux fois

## 📦 Le point de départ

`challenge/work` contient un module, `modules/artefact/`, appelé **deux fois**
depuis la racine. Le corps du module fonctionne ; c'est son **interface** qui est
à écrire.

| Fichier | État |
| --- | --- |
| `versions.tf`, `main.tf` | complets, **à ne pas toucher** |
| `modules/artefact/main.tf` | complet, **à ne pas toucher** |
| `modules/artefact/variables.tf` | trois variables, **à écrire** |
| `modules/artefact/outputs.tf` | trois sorties, **à écrire** |
| `outputs.tf` | deux sorties de la racine, **à écrire** |

Les deux appels de `main.tf` sont vos **cahiers des charges** :

```hcl
module "complet" {
  depot           = { nom = "archives", retention_jours = 30, chiffre = true }
  etiquette       = "production"
  longueur_secret = 24
}

module "minimal" {
  depot = { nom = "livraison" }
}
```

C'est l'appel **minimal** qui met l'interface à l'épreuve : il ne fournit qu'un
attribut sur trois, et aucune des deux autres variables.

## ✅ Objectif

Écrire une interface qui **absorbe** cette différence, **refuse** les valeurs
inacceptables, et **protège** ce qui doit l'être.

## 📋 Ce qu'il faut obtenir

1. L'appel minimal aboutit : `retention_jours` vaut **7** et `chiffre` vaut
   **true** sans que l'appelant les fournisse.
2. Un appel qui passerait `etiquette = null` obtient quand même `"artefact"` : la
   variable **refuse le null** au lieu de le propager.
3. `longueur_secret = 8` est **rejeté**, avec un message qui nomme les bornes
   `12` et `64`.
4. La sortie `resume` expose `nom`, `retention_jours`, `chiffre` et `etiquette`,
   défauts comblés compris.
5. Le secret produit remonte jusqu'à la racine **sans être lisible** dans les
   sorties courantes, et fait la longueur demandée par l'appel complet.
6. La sortie `chemin` **refuse de se publier** quand le dépôt n'est pas chiffré :
   le plan s'arrête.
7. `terraform plan -detailed-exitcode` sort en **0** après l'apply.

## ⚠️ Le cœur du sujet

`type` et `default` ne suffisent pas. Quatre mécanismes complètent l'interface :

| Besoin | Mécanisme |
| --- | --- |
| Un **attribut d'objet** facultatif | `optional(type, defaut)` |
| Un **`null` explicite** qui doit rendre le défaut | `nullable = false` |
| Une **valeur hors bornes** refusée | bloc `validation` |
| Une sortie qui **refuse de se publier** | bloc `precondition` |

Et un cinquième, qui ne se devine qu'en butant dessus : une valeur dérivée d'un
`random_password` **contamine** ce qu'elle traverse. Une sortie racine qui la
republie sans le déclarer fait **échouer le plan**.

## 🔍 Validation

`dsoxlab check modules-module-variables-outputs` prouve, par exécution :

- le state porte bien `module.complet` et `module.minimal` : une configuration à
  plat échoue ;
- `resume_minimal` vaut exactement
  `{"nom": "livraison", "retention_jours": 7, "chiffre": true, "etiquette": "artefact"}` ;
- dans une **copie** du projet où l'appel minimal reçoit `etiquette = null`,
  l'étiquette reste `"artefact"` ;
- dans une copie où `longueur_secret = 8`, `terraform validate -json` rend
  `valid: false` avec `Invalid value for variable` ;
- `secret_partage` est marqué sensible et fait 24 caractères ; retirer ce
  marquage dans une copie fait échouer le plan ;
- dans une copie où `chiffre = false`, le plan échoue sur une **precondition** de
  sortie ;
- `plan -detailed-exitcode` rend **0**.

Les variantes fautives sont produites dans des **copies temporaires** : votre
travail n'est jamais modifié.

Bloqué ? `dsoxlab hint modules-module-variables-outputs`.
