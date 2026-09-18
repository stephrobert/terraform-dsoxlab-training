# 🎯 Challenge : rendre la configuration portable, et voir où ça s'arrête

## Point de départ

`challenge/work` contient **un seul fichier**, `main.tf`, fourni et complet :
un `random_pet` de deux mots, un `local_file` qui écrit son identifiant dans
`rapport.txt`, une `null_resource` dont le déclencheur en dépend, et une sortie
`nom_animal`.

Il n'y a aucun bloc `terraform {}`, ni `.terraform/`, ni state, ni verrou.

**Cette configuration ne s'applique pas telle quelle.** La première ressource
désigne son provider par un alias, `random.principal`, et Terraform répond
`Provider configuration not present`. Ce n'est pas un défaut à contourner :
c'est le fichier qui manque au projet.

## ✅ Objectif

Écrivez `versions.tf`, puis appliquez.

1. Un bloc `terraform` avec **`required_version`** et un **`required_providers`**
   nommant explicitement `source` et `version` pour `random`, `local` et `null`.
2. Des contraintes **pessimistes** (`~> x.y`) : ni version figée, ni version
   flottante.
3. Un bloc **`provider "random"`** portant l'alias attendu par `main.tf`.

Puis, si `tofu` est installé, reprenez le **même state** avec lui, **sur une
copie du répertoire**, et regardez ce qu'il laisse derrière lui.

## 🧭 Ce que le lab vous fait constater

- **`tofu` relit le state de `terraform` sans rien détruire.** Plan vide, même
  identifiant, mêmes versions de providers. La compatibilité annoncée existe.
- **Mais il résout sur `registry.opentofu.org`**, là où `terraform` résout sur
  `registry.terraform.io`. Le préfixe de registre est la seule chose qui change.
- **Et il réécrit `.terraform.lock.hcl`.** Après son passage, `terraform`
  s'arrête sur `Inconsistent dependency lock file` et exige un `init -upgrade`.
  La portabilité porte sur le **state**, pas sur le **verrou**.
- **Un verrou n'enregistre ses contraintes qu'une fois.** Si vous avez lancé
  `init` avant d'écrire `versions.tf`, `constraints` restera vide, et même
  `init -upgrade` ne l'ajoutera pas. Supprimez le fichier et relancez `init`.

## 🔍 Validation

```bash
dsoxlab check getting-started-terraform-vs-opentofu
```

Huit tests. Les cinq premiers se jouent avec `terraform` seul : contraintes
pessimistes lues dans un verrou reconstruit à part, sourcing pleinement qualifié
lu dans `version -json`, state, sorties, et idempotence par code retour. Les
trois derniers exigent `tofu` et **skippent explicitement** s'il manque : un lab
ne recale personne pour un outil qu'il n'a pas installé. Aucun ne lit vos `.tf`.
