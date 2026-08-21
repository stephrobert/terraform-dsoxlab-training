# 🎯 Challenge : un seul répertoire, trois états

## 📦 Le point de départ

`challenge/work` est **déjà initialisé** et tourne hors ligne (`local`,
`random`).

| Fichier | Ce que c'est |
| --- | --- |
| `versions.tf`, `outputs.tf` | **complets**, à ne pas toucher |
| `main.tf` | troué par des `???` |
| `variables.tf` | une variable `nom_env`. **Lisez son commentaire** |
| `terraform.tfstate.d/bac-a-sable/` | un workspace **hérité**, déjà appliqué |
| `sorties/app-bac-a-sable-0.conf` | le fichier qu'il a produit |
| `CIBLE.md` | l'état à atteindre, et les commandes utiles |

## ✅ Ce qu'il faut obtenir

1. Exactement **trois** workspaces : `default`, `dev`, `prod`. `bac-a-sable` a
   disparu.
2. `default` ne suit **aucune** ressource.
3. `dev` suit **2** ressources et produit **1** fichier ; `prod` en suit **4** et
   produit **3**.
4. Chaque fichier porte le nom du workspace qui l'a créé, **sans** aucune valeur
   littérale `dev` ou `prod` dans la configuration.
5. Ni `dev` ni `prod` n'a de changement en attente.
6. `sorties/app-bac-a-sable-0.conf` n'existe **plus**.
7. Le workspace sélectionné à la fin est `default`.

## ⚠️ Le cœur du sujet

Supprimer un workspace ne **détruit** rien. Terraform refuse même de le faire
tant qu'il suit des ressources :

```text
Error: Workspace is not empty
```

L'option `-force` passe outre, supprime l'**état** et laisse les fichiers sur le
disque. Plus rien ne les gère : ce sont des orphelins. L'ordre correct est
**détruire**, puis supprimer.

Second piège : une **variable** ne suit pas le workspace. Le nom du workspace
courant se lit dans l'expression `terraform.workspace`.

## 🔍 Validation

`dsoxlab check environments-workspace` prouve, par exécution :

- l'inventaire des workspaces, lu dans `terraform.tfstate.d/` ;
- le compte de ressources et de fichiers **par workspace**, sans toucher à votre
  sélection (grâce à `TF_WORKSPACE`) ;
- que le nommage suit bien `terraform.workspace`, en appliquant dans un workspace
  **témoin** que vous n'avez jamais vu ;
- la convergence de `dev` et de `prod` ;
- la disparition du fichier hérité ;
- le workspace sélectionné en fin de travail, lu dans `.terraform/environment`.

Bloqué ? `dsoxlab hint environments-workspace`.
