# Les identifiants ne vivent ni dans le code, ni dans le state

## La situation

**Sous-objectif d'examen visé : 6c, gérer les identifiants de provider dans HCP Terraform.**

L'objectif 6 est évalué en QCM, mais ce qu'il enseigne se mesure, et ce lab le mesure sur un
vrai provider face à un émulateur local. Aucun compte, aucune carte bancaire.

Une équipe livre une configuration qui fonctionne. Le provider porte ses clés dans le
fichier, et un jeton de service est écrit dans une étiquette ; la variable est marquée
`sensitive`, alors tout le monde la croit protégée. Le state, que tout le monde lit, dit le
contraire.

## Capacité visée

Écrire une configuration qui **reçoit** ses identifiants au lieu de les contenir, comme HCP
Terraform les fournit dans l'environnement du run, et empêcher un secret d'atteindre le
state, ce que `sensitive` n'empêche pas.

## D'où part l'apprenant

`challenge/work` contient deux répertoires :

1. `configuration/`, une configuration AWS pointée vers l'émulateur. Son provider porte
   `access_key` et `secret_key` en clair, et son instance porte une étiquette `Jeton` qui
   contient le jeton de service. `jeton.auto.tfvars` en fournit la valeur.
2. `questionnaire/`, cinq réponses à poser dans `reponses.auto.tfvars`, sur les identifiants
   dynamiques.

## L'état à atteindre

1. Le provider ne déclare plus aucun identifiant. Il les trouve dans son environnement,
   `AWS_ACCESS_KEY_ID` et `AWS_SECRET_ACCESS_KEY`, là où HCP Terraform les pose.
2. L'instance ne porte plus le jeton. Une étiquette `Empreinte` porte son empreinte SHA-256
   à la place, ce qui suffit à vérifier un jeton présenté sans le conserver.
3. Le jeton n'apparaît nulle part dans le state.
4. Les cinq réponses établissent ce que protège `sensitive`, ce que HCP Terraform envoie à
   la plateforme cloud, ce qui le vérifie, combien de temps vivent les identifiants rendus,
   et où se déclarent les identifiants d'un workspace.

## La mesure au cœur du lab

Le 2026-09-25, sur Terraform 1.16.1, sur cette configuration même :

| Où | Le jeton |
| --- | --- |
| `terraform show` | `(sensitive value)` |
| `terraform.tfstate` | `"Jeton": "svc-7f3a91c4e2b8-prod"`, **deux fois** |

`sensitive` agit sur ce que Terraform affiche, pas sur ce qu'il enregistre. Il en va de même
d'un plan enregistré, qui porte la valeur lui aussi.

## Comment on le prouve

Les tests appliquent la configuration **dans un environnement de run qu'ils construisent
eux-mêmes** : toutes les variables `AWS_*` du poste sont retirées, `HOME` pointe sur un
répertoire vide pour qu'aucun `~/.aws` ne contribue, et les identifiants sont posés comme
HCP Terraform les pose. Une configuration écrite pour recevoir ses identifiants y
fonctionne ; une configuration qui les contient fonctionne aussi, et c'est justement
pourquoi un second contrôle lit les fichiers.

Ces deux moitiés sont assérées **ensemble**, dans un seul test, et le premier cycle dit
pourquoi : quand elles étaient séparées, la moitié « une instance existe » était **verte
avant tout travail**, puisque la configuration de départ s'authentifie parfaitement avec ses
clés en dur. Mesuré le 2026-09-25 : 1/9 sans avoir rien fait. Réunies, elles ne sont
atteignables qu'une fois les deux moitiés du travail faites.

Vérifié en dégradant la solution : retirer les clés en laissant le jeton dans l'étiquette
donne 6/8, et poser l'empreinte en laissant les clés dans le provider donne 7/8.

## 🎯 Challenge : sortir les secrets du code et du state

### 📦 Point de départ

`challenge/work` contient deux répertoires. **Aucun compte** : un émulateur local
tient lieu d'AWS.

| Fichier | État |
| --- | --- |
| `configuration/versions.tf` | provider portant **deux clés en clair** |
| `configuration/main.tf` | une instance portant le **jeton** dans une étiquette |
| `configuration/variables.tf`, `jeton.auto.tfvars` | **fournis**, à ne pas modifier |
| `questionnaire/questionnaire.tf` | **fourni**, à ne pas modifier |
| `questionnaire/reponses.auto.tfvars` | cinq `???` à renseigner |

### ✅ Objectif

1. **Sortir les identifiants du provider.** C'est l'environnement qui les
   fournit, comme HCP Terraform le fait dans l'environnement d'un run.
2. **Cesser d'écrire le jeton dans l'instance.** Remplacer l'étiquette `Jeton`
   par une étiquette `Empreinte` portant son empreinte SHA-256.
3. **Répondre aux cinq questions** sur les identifiants dynamiques.

### 🧭 Regardez avant de corriger

Appliquez en l'état et ouvrez `terraform.tfstate`. La variable est marquée
`sensitive`, `terraform show` affiche `(sensitive value)`, et le state porte le
jeton en clair, deux fois.

C'est tout l'objet de ce lab, et c'est l'une des cinq questions.

### ⚠️ Retirer les clés n'est que la moitié du travail

Sans aucun identifiant nulle part, le provider répond :

```
Error: No valid credential sources found
```

La configuration doit être écrite pour **recevoir** ses identifiants, pas pour
fonctionner sans. Les tests les fournissent comme la plateforme le fait, par
l'environnement.

### 🔍 Validation

```bash
dsoxlab check hcp-terraform-shared-credentials
```

Huit tests. Ils appliquent votre configuration dans un environnement expurgé de
tout `AWS_*` du poste et sans `~/.aws`, puis balaient le fichier de state entier
à la recherche du jeton, et pas seulement l'étiquette que vous devez changer :
un secret déplacé ailleurs serait tout aussi exposé.

Bloqué ? `dsoxlab hint hcp-terraform-shared-credentials`.
