# 🎯 Challenge : découper sans que le plan bouge

## 📦 Le point de départ

`challenge/work` contient **un seul fichier**, `tout.tf`, qui empile dans le
désordre le bloc `terraform`, les providers, quatre variables, un `locals`, trois
ressources et quatre sorties.

Il contient aussi `reference/monolithe.tf.txt` : une **copie de référence**,
fournie et non modifiable, dont l'extension n'est pas `.tf` pour que Terraform ne
la charge pas. Les tests s'en servent pour reconstruire le plan d'origine.

## ✅ Objectif

1. **Découper** `tout.tf` en six fichiers : `terraform.tf`, `providers.tf`,
   `variables.tf`, `locals.tf`, `main.tf`, `outputs.tf`. Aucun bloc n'est
   ajouté, supprimé ni modifié : seul leur emplacement change.
2. **Faire disparaître `tout.tf`.** Découper, c'est **déplacer**.
3. **Poser les valeurs** : un `terraform.tfvars` qui fixe `projet` et
   `environnement`, et un `env.auto.tfvars` qui redéfinit `environnement`.
4. **Appliquer** avec `revision` fournie par `-var`, la variable étant déclarée
   sans `default`.

L'énoncé fixe aussi une variable d'environnement, et elle compte :

```bash
export TF_VAR_projet="depuis-env"
```

## 🧭 Les valeurs attendues, et pourquoi

| Sortie | Valeur | Qui gagne |
| --- | --- | --- |
| `projet_effectif` | `depuis-tfvars` | `terraform.tfvars` bat `TF_VAR_` |
| `environnement_effectif` | `depuis-auto` | un `*.auto.tfvars` bat `terraform.tfvars` |
| `region_effective` | `eu-ouest` | personne ne la pose : son `default` gagne |
| `revision_effective` | `depuis-ligne-de-commande` | `-var` bat tout le reste |

La première ligne est celle qui surprend : `TF_VAR_` vit juste au-dessus du
`default`, et **en dessous de tout fichier de valeurs**.

## ⚠️ Copier n'est pas découper

Si `tout.tf` reste à côté des six fichiers, chaque nom est déclaré deux fois et
Terraform refuse : `Duplicate variable declaration`. Un nom ne se déclare qu'une
fois par **répertoire**, quel que soit le fichier.

## 🔍 Validation

```bash
dsoxlab check getting-started-terraform-project-structure
```

Neuf tests. Aucun n'ouvre vos `.tf`.

La preuve centrale est l'**invariance** : les tests reconstruisent le plan du
monolithe depuis la copie de référence, et le comparent au vôtre, adresse par
adresse et valeur par valeur.

La preuve du découpage se fait par **ablation** : chaque fichier est retiré dans
une copie, et quelque chose doit casser. Si retirer `variables.tf` ne change
rien, les variables ne sont pas dedans.

Bloqué ? `dsoxlab hint getting-started-terraform-project-structure`.
