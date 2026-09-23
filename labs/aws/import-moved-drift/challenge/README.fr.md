# 🎯 Challenge : import, moved et dérive

## Point de départ

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

## ✅ Objectif

1. **Importez** l'instance sous l'adresse `aws_instance.legacy`.
2. **Renommez-la** en `aws_instance.billing_api` par un bloc `moved`, et
   **appliquez-le**. Le bloc `moved` reste en place à la fin.
3. **Provoquez une dérive** : changez le tag `Owner` à la main, hors Terraform.

   ```bash
   aws --endpoint-url http://localhost:14566 ec2 create-tags \
       --resources <id> --tags 'Key=Owner,Value=plateforme'
   ```

4. **Acceptez-la** : alignez le code sur la réalité, et non l'inverse.

## 🧭 Les trois pièges, et pourquoi ils sont silencieux

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

## 🔍 Validation

```bash
dsoxlab check aws-import-moved-drift
```

Six tests. Le `moved` est prouvé **sans ouvrir un `.tf`** : le test copie votre
répertoire, remet l'ancienne adresse dans le state copié, et exige que le plan
porte un `previous_address` en `no-op`. Deux codes retour tombent ensemble, le
plan ordinaire **et** le `-refresh-only` : le premier dit que le réel colle au
code, le second que le state colle au réel.
