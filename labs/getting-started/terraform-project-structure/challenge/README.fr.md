# 🎯 Challenge : découper un monolithe sans bouger le plan

## Point de départ

`challenge/work` contient **un seul fichier**, `tout.tf`, qui empile dans le
désordre : le bloc `terraform`, trois blocs `provider`, quatre `variable`, un
`locals`, trois `resource` et trois `output`.

Il fonctionne parfaitement. Le problème n'est pas qu'il soit cassé, c'est qu'il
soit illisible.

Il n'y a ni fichier de valeurs, ni state, ni plan enregistré. La variable
`operateur` n'a **pas de défaut** : aucune commande ne passera sans la fournir.

## ✅ Objectif

1. **Figez le plan de référence AVANT tout**, avec `terraform plan -out` puis
   `terraform show -json`, dans un fichier `plan-reference.json`.
2. **Découpez** `tout.tf` en `terraform.tf`, `providers.tf`, `variables.tf`,
   `locals.tf`, `main.tf` et `outputs.tf`. **Aucun bloc n'est ajouté, supprimé
   ni modifié** : seul leur emplacement change. `tout.tf` doit disparaître.
3. **Refaites un plan** avec les mêmes entrées, dans `plan-apres.json`.
4. **Posez les fichiers de valeurs** :
   - `terraform.tfvars` : `projet = "catalogue"` et `environnement = "recette"` ;
   - `env.auto.tfvars` : `environnement = "production"`.
5. **Appliquez**, en fournissant `operateur` par `-var`.

## 🧭 Ce que le lab vous fait constater

- **Laisser `tout.tf` en place casse tout.** Terraform lit tous les `.tf` : vos
  six fichiers redéclarent chacun des blocs une seconde fois.
- **Le plan est strictement identique** avant et après découpage. Le nom des
  fichiers n'a aucun effet fonctionnel, et c'est justement ce qui rend le
  refactoring sûr.
- **`env.auto.tfvars` l'emporte sur `terraform.tfvars`.** Les fichiers `auto`
  sont chargés après, en ordre alphabétique.
- **`TF_VAR_projet` ne l'emporte PAS sur `terraform.tfvars`.** C'est le rang le
  plus souvent mal placé : une variable d'environnement est juste au-dessus du
  `default`, et en dessous de tout fichier de valeurs.
- **`-var` gagne toujours**, contre toutes les autres sources à la fois.

## 🔍 Validation

```bash
dsoxlab check getting-started-terraform-project-structure
```

Treize tests. L'invariance du plan se prouve en comparant les deux JSON, adresse
par adresse, après neutralisation des champs volatils. Le découpage se prouve
sans jamais faire un `ls` : le test dépose une sonde qui redéclare un bloc, et
`terraform validate -json` nomme le fichier de la déclaration d'origine. La
précédence se lit dans `terraform output -json`, jamais dans une sortie humaine.
