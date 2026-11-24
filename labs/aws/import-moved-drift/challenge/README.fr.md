# Reprendre une EC2 existante, la renommer, accepter sa dérive

## La situation

**Sous-objectif d'examen visé : 1e (gérer le state, importer des ressources, réconcilier le drift).**

Ce lab traite les trois pièges que la lecture d'un tutoriel ne révèle jamais : un
`moved` que l'on croit passé alors qu'il n'a jamais été appliqué, un `moved` dont
l'adresse `from` est fausse et que Terraform ignore **en silence**, et une dérive
que l'on écrase par réflexe au lieu de décider quoi en faire.

## Capacité visée

Placer sous contrôle de Terraform une instance EC2 créée en dehors de lui, en
changer l'adresse logique sans que l'objet réel soit recréé, puis réconcilier une
dérive en **acceptant** la réalité, c'est-à-dire en alignant le code sur elle et
non l'inverse.

## D'où part l'apprenant

Floci tourne en local sur `localhost:14566` (socket Docker monté, `-u root`).
L'étape de mise en place a créé, **via l'AWS CLI et non via Terraform**, une
instance EC2 taguée `Name = legacy-billing-api` et `Owner = finops`. Son
identifiant est déposé dans `challenge/work/existing-instance.txt`.

Dans `challenge/work` : un `providers.tf` **complet** (provider `aws` visant
Floci par un bloc `endpoints`, identifiants factices, `skip_credentials_validation`,
`skip_requesting_account_id`, `skip_metadata_api_check`), un `imports.tf` dont le
bloc `import` est à trous (`to = ???`, `id = ???`), **aucun bloc `resource`** (il
est à produire, pas à recopier), et aucun state.

## L'état à atteindre

1. L'instance figure dans le state avec **l'identifiant déjà présent dans
   `existing-instance.txt`** : elle a été importée, pas recréée.
2. Juste après l'import, la configuration est **fidèle** : un plan ordinaire ne
   propose plus rien. C'est le vrai critère de réussite d'un import, et le piège
   de la génération automatique de configuration, qui produit des arguments en
   trop qu'il faut retirer.
3. L'adresse dans le state est `aws_instance.billing_api`, alors que l'import
   s'est fait sous un autre nom, et l'identifiant de l'objet **n'a pas bougé** :
   le renommage est passé par un `moved` réellement **appliqué**, un `plan` seul
   n'écrivant rien dans le state.
4. Le bloc `moved` est **toujours présent** en fin de lab. Le supprimer est un
   changement cassant pour quiconque part encore de l'ancienne adresse.
5. Le tag `Owner` a été modifié hors Terraform et l'apprenant **accepte** cette
   dérive : côté Floci le tag garde sa valeur manuelle, le state la reflète, et
   le code aussi. Les deux critères d'arrêt tombent ensemble : plus de dérive à
   réconcilier, plus de changement à appliquer.
6. Aucune instance supplémentaire n'existe côté Floci : ni destroy, ni create.

## Comment on le prouve

Les tests interrogent l'état structuré, jamais le fichier `.tf` de l'apprenant :

- `terraform show -json` : une ressource en `mode: managed` à l'adresse
  `aws_instance.billing_api`, dont `values.id` est **égal** à l'identifiant lu
  dans `existing-instance.txt`. Preuve de l'import et de l'absence de recréation.
- `terraform plan -detailed-exitcode` sort en **0**, et
  `terraform plan -refresh-only -detailed-exitcode` sort en **0** lui aussi. Le
  premier prouve que le réel colle au code, le second que le state colle au réel.
- L'AWS CLI pointée sur Floci montre le tag `Owner` à sa valeur **manuelle**, et
  ne retourne qu'une seule instance non terminée : la dérive a été acceptée et le
  code aligné, sans recréation.
- Preuve du `moved` : le test copie le répertoire de travail à part, réécrit dans
  le state copié l'adresse vers son ancien nom, lance `terraform plan -out` et
  lit le plan en JSON. Il exige une entrée portant `previous_address` avec
  `actions: ["no-op"]`. Un bloc `moved` supprimé ou dont le `from` est faux
  produirait un `create`, sans la moindre erreur.

## 🎯 Challenge : import, moved et dérive

### Point de départ

Une instance EC2 **existe déjà**. Elle a été créée à la main, hors Terraform, et
porte les tags `Name = legacy-billing-api` et `Owner = finops`.

`challenge/work` contient `providers.tf` (**complet**) et `imports.tf`
(**troué**). Il n'y a **aucun bloc `resource`** : il est à produire, pas à
recopier. Aucun state.

Personne ne vous tend l'identifiant de l'instance : le retrouver est la première
étape d'un import.

```bash
aws --endpoint-url http://localhost:14566 ec2 describe-instances \
    --filters 'Name=tag:Name,Values=legacy-billing-api' \
              'Name=instance-state-name,Values=running' \
    --query 'Reservations[].Instances[].InstanceId' --output text
```

### ✅ Objectif

1. **Importez** l'instance sous l'adresse `aws_instance.legacy`.
2. **Renommez-la** en `aws_instance.billing_api` par un bloc `moved`, et
   **appliquez-le**. Le bloc `moved` reste en place à la fin.
3. **Provoquez une dérive** : changez le tag `Owner` à la main, hors Terraform.

   ```bash
   aws --endpoint-url http://localhost:14566 ec2 create-tags \
       --resources <id> --tags 'Key=Owner,Value=plateforme'
   ```

4. **Acceptez-la** : alignez le code sur la réalité, et non l'inverse.

### 🧭 Les trois pièges, et pourquoi ils sont silencieux

- **Un `plan` seul n'écrit rien dans le state.** On croit le `moved` passé, il
  ne l'est pas.
- **Un `moved` dont le `from` est faux est ignoré sans le moindre
  avertissement.** Terraform ne trouve rien à cette adresse, ne dit rien, et
  crée la nouvelle ressource. L'objet réel se retrouve **dupliqué**.
- **Écraser une dérive est un réflexe.** Un `apply` « remet en ordre » et efface
  un changement qui était peut-être volontaire. Le collègue qui l'avait fait ne
  saura jamais pourquoi son tag a disparu.

Et un quatrième, sur l'import lui-même : **la ressource dans le state ne suffit
pas**. Tant qu'un plan ordinaire propose quelque chose, l'import n'est pas fini.
`-generate-config-out` produit des arguments que l'API rend et que la
configuration n'a pas à porter.

### 🔍 Validation

```bash
dsoxlab check aws-import-moved-drift
```

Six tests. Le `moved` est prouvé **sans ouvrir un `.tf`** : le test copie votre
répertoire, remet l'ancienne adresse dans le state copié, et exige que le plan
porte un `previous_address` en `no-op`. Deux codes retour tombent ensemble, le
plan ordinaire **et** le `-refresh-only` : le premier dit que le réel colle au
code, le second que le state colle au réel.
