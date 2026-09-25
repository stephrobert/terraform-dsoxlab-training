# 🎯 Challenge : sortir les secrets du code et du state

## 📦 Point de départ

`challenge/work` contient deux répertoires. **Aucun compte** : un émulateur local
tient lieu d'AWS.

| Fichier | État |
| --- | --- |
| `configuration/versions.tf` | provider portant **deux clés en clair** |
| `configuration/main.tf` | une instance portant le **jeton** dans une étiquette |
| `configuration/variables.tf`, `jeton.auto.tfvars` | **fournis**, à ne pas modifier |
| `questionnaire/questionnaire.tf` | **fourni**, à ne pas modifier |
| `questionnaire/reponses.auto.tfvars` | cinq `???` à renseigner |

## ✅ Objectif

1. **Sortir les identifiants du provider.** C'est l'environnement qui les
   fournit, comme HCP Terraform le fait dans l'environnement d'un run.
2. **Cesser d'écrire le jeton dans l'instance.** Remplacer l'étiquette `Jeton`
   par une étiquette `Empreinte` portant son empreinte SHA-256.
3. **Répondre aux cinq questions** sur les identifiants dynamiques.

## 🧭 Regardez avant de corriger

Appliquez en l'état et ouvrez `terraform.tfstate`. La variable est marquée
`sensitive`, `terraform show` affiche `(sensitive value)`, et le state porte le
jeton en clair, deux fois.

C'est tout l'objet de ce lab, et c'est l'une des cinq questions.

## ⚠️ Retirer les clés n'est que la moitié du travail

Sans aucun identifiant nulle part, le provider répond :

```
Error: No valid credential sources found
```

La configuration doit être écrite pour **recevoir** ses identifiants, pas pour
fonctionner sans. Les tests les fournissent comme la plateforme le fait, par
l'environnement.

## 🔍 Validation

```bash
dsoxlab check hcp-terraform-shared-credentials
```

Huit tests. Ils appliquent votre configuration dans un environnement expurgé de
tout `AWS_*` du poste et sans `~/.aws`, puis balaient le fichier de state entier
à la recherche du jeton, et pas seulement l'étiquette que vous devez changer :
un secret déplacé ailleurs serait tout aussi exposé.

Bloqué ? `dsoxlab hint hcp-terraform-shared-credentials`.
