# 🎯 Challenge : la valeur qui gagne, et pourquoi

## 📦 Le point de départ

Une seule configuration sert trois environnements. Elle n'est ni initialisée ni
appliquée, et elle tourne **hors ligne** (`local` et `random`).

| Fichier | Ce que c'est |
| --- | --- |
| `versions.tf` | **complet**, à ne pas toucher |
| `variables.tf` | `env_name` et `disk_size_gb` **sans** `default`, deux types laissés en `???` |
| `main.tf` | `random_pet.suffixe` et `local_file.profil`, troués par des `???` |
| `outputs.tf` | `profil` et `taille_octets`, expressions à écrire |
| `terraform.tfvars` | présent à la racine, et c'est le **problème** (voir plus bas) |
| `commun.auto.tfvars` | les valeurs partagées par tous les environnements |
| `envs/dev.tfvars` | complet |
| `envs/staging.tfvars` | une clé **mal orthographiée** |
| `envs/prod.tfvars` | **incomplet** |
| `CIBLE.md` | l'échelle de précédence et les valeurs attendues |

## ✅ Ce qu'il faut obtenir

1. `terraform plan -input=false`, **sans aucune option**, doit **échouer** sur
   `No value for required variable`.
2. Les types manquants de `variables.tf` sont déclarés, les blocs de `main.tf` et
   `outputs.tf` complétés.
3. `envs/staging.tfvars` ne déclenche plus aucun avertissement.
4. `envs/prod.tfvars` est complété : **8** Go et **90** jours.
5. Les valeurs partagées restent dans le fichier auto chargé, sans être
   recopiées dans les trois fichiers d'environnement.
6. L'environnement `prod` est **appliqué**, et un plan relancé ne propose plus
   rien.

## ⚠️ Le cœur du sujet

Un `terraform.tfvars` est chargé **automatiquement**. Celui qui est là donne une
valeur aux deux variables sans `default` : le garde-fou de `variables.tf` ne
protège donc plus rien, et `terraform plan` réussit alors qu'aucun environnement
n'a été choisi.

Et une clé mal orthographiée dans un fichier de valeurs ne fait **pas** échouer
le plan :

```text
Warning: Value for undeclared variable
```

La variable reste à son `default`, le plan est valide, et la taille est fausse.

## 🔍 Validation

`dsoxlab check environments-per-environment-variables` prouve, par exécution :

- la valeur **réellement retenue** pour chaque variable, lue dans
  `terraform show -json` (jamais dans vos fichiers) ;
- que `TF_VAR_` bat le `default` mais **perd** contre un fichier de valeurs ;
- que `-var` et `-var-file` se départagent par l'**ordre des arguments** ;
- que les `*.auto.tfvars` s'appliquent en ordre **lexical** ;
- l'état appliqué de `prod` et son idempotence.

Bloqué ? `dsoxlab hint environments-per-environment-variables`.
