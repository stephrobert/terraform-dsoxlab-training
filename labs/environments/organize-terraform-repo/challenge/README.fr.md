# 🎯 Challenge : découper sans changer le plan

## 📦 Le point de départ

`challenge/work` fonctionne **hors ligne** :

| Fichier | Ce que c'est |
| --- | --- |
| `projet/main.tf` | quatre-vingts lignes portant **tout** : bloc `terraform`, providers, variables, ressources, sorties |
| `CIBLE.md` | le socle attendu, l'invariant, et les règles du dépôt |

## ✅ Objectif

Découper cette configuration selon le socle **officiel**, sans que le plan bouge
d'une ligne, et rendre le dépôt présentable.

## 📋 Ce qu'il faut obtenir

1. `terraform.tf`, `providers.tf`, `variables.tf`, `outputs.tf`, et un `main.tf`
   qui ne garde que les ressources.
2. `terraform.tf` porte **un seul** bloc `terraform` et **aucun** `provider`.
3. Variables et sorties en **ordre alphabétique**.
4. Le plan est **identique** à celui d'avant le découpage.
5. `terraform fmt -check -recursive` sort en **0**.
6. Un `.gitignore` ignore `.terraform/`, l'état, ses sauvegardes et un plan
   enregistré nommé `tfplan`, mais **laisse passer** `.terraform.lock.hcl`.

## ⚠️ Le cœur du sujet

`terraform validate` ne prouve **rien** ici : « The `validate` command does not
check if argument values are valid for a specific provider [...] It does not
evaluate any existing state. » Un découpage qui perd une ressource affiche
tranquillement :

```text
Success! The configuration is valid
```

Comparez donc les **plans**, pas les avis de `validate` :

```bash
terraform plan -out=apres.tfplan
terraform show -json apres.tfplan | jq -S '.planned_values, .resource_changes'
```

Deux détails coûtent cher si on les rate. `terraform fmt -check` ne voit que le
répertoire **courant**. Et `terraform plan -out=tfplan` produit un fichier **sans
extension**, qu'un motif `*.tfplan` n'attrape pas.

## 🔍 Validation

`dsoxlab check environments-organize-terraform-repo` prouve, par exécution :

- le plan de la fixture monolithique est **rejoué** dans un répertoire temporaire,
  et son empreinte comparée à la vôtre ;
- le socle, l'unicité du bloc `terraform`, l'ordre alphabétique ;
- `terraform fmt -check -recursive` depuis la racine ;
- votre `.gitignore`, mis à l'épreuve par `git check-ignore` dans une copie
  jetable.

Bloqué ? `dsoxlab hint environments-organize-terraform-repo`.
