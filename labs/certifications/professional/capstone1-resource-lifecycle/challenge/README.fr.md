# 🎯 Challenge : reprendre, sans détruire, ce que Terraform ignore

## 📦 Le point de départ

Deux objets **existent déjà** chez le fournisseur, créés à la main :

| Objet | Ce qu'il porte |
| --- | --- |
| une instance EC2 | les tags `Name = capstone-facturation`, `Owner = finops`, `Env = prod` |
| un bucket S3 | le nom `capstone-archives-legacy` |

`challenge/work` contient `providers.tf` (**fourni**, il vise Floci) et
`main.tf` (**troué**). Aucun state.

**Personne ne vous tend les identifiants.** Les retrouver est la première étape.

```bash
aws --endpoint-url http://localhost:14566 ec2 describe-instances \
    --filters 'Name=tag:Name,Values=capstone-facturation' \
    --query 'Reservations[].Instances[].InstanceId' --output text
```

L'instance est créée au démarrage du lab, en parallèle : si la commande ne rend
rien, attendez quelques secondes et relancez-la.

## ✅ Objectif

1. **Importer les deux objets** sous les adresses `aws_instance.facturation` et
   `aws_s3_bucket.archives`, sans les recréer.
2. **Rendre la configuration fidèle** : un `plan` ordinaire ne propose plus rien.
3. **Provoquer une dérive** hors Terraform, en passant le tag `Owner` à
   `plateforme` :

   ```bash
   aws --endpoint-url http://localhost:14566 ec2 create-tags \
       --resources <id> --tags 'Key=Owner,Value=plateforme'
   ```

4. **L'accepter** : aligner le code sur la réalité, et non l'inverse.

## 🧭 Les deux critères qui comptent

**Un import n'est pas fini quand la ressource est dans le state.** Tant qu'un
`plan` ordinaire propose quelque chose, votre code décrit autre chose que
l'objet réel, et le prochain `apply` modifiera cet objet. Relevez ses valeurs
réelles avant d'écrire la configuration.

**Deux codes de retour doivent tomber ensemble** à la fin :

```bash
terraform plan -detailed-exitcode                 # 0 : le réel colle au code
terraform plan -refresh-only -detailed-exitcode   # 0 : le state colle au réel
```

Le premier seul ne suffit pas : il peut sortir en 0 sur un state périmé.

## ⚠️ Écraser une dérive est un réflexe, pas une décision

Un `apply` « remet en ordre » et efface un changement que quelqu'un a fait pour
une raison qu'on ignore. Le collègue ne saura jamais pourquoi son tag a disparu.

Accepter la dérive, c'est décider que la réalité a raison, et le dire dans le
code.

## 🔍 Validation

```bash
dsoxlab check certifications-professional-capstone1-resource-lifecycle
```

Cinq tests. Aucun ne lit vos `.tf` : ils comparent l'identifiant du state à
celui que Floci connaît, vérifient le tag **des deux côtés**, et exigent les deux
codes de retour.

Le dernier test **détruit**, et il s'exécute même si les autres ont échoué : un
lab raté qui laisse une instance derrière lui fait payer le lab suivant.

Bloqué ? `dsoxlab hint certifications-professional-capstone1-resource-lifecycle`.
