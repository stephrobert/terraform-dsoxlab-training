# Pro · Objectif 1, cycle de vie, import et réconciliation de drift

## La situation

**Objectif d'examen visé : 1** (1a `init`, 1b `plan`, 1c `apply`, 1d `destroy`,
et surtout **1e : gérer le state, importer des ressources, réconcilier le
drift**).

C'est le seul objectif pour lequel HashiCorp publie des practice labs officiels,
et c'est le plus discriminant : reprendre en main une infrastructure qu'on n'a
pas créée est le quotidien d'un profil Professional.

## Capacité visée

Placer sous contrôle de Terraform une ressource **créée en dehors de lui**, sans
la détruire, puis **détecter et réconcilier un écart** apparu hors du code.

## D'où part l'apprenant

Floci tourne en local (socket Docker monté, `-u root`). Deux ressources ont été
créées **hors Terraform**, directement via l'AWS CLI : une instance EC2 et un
bucket S3. Elles portent des tags précis.

Dans `challenge/work`, un `main.tf` déclare le provider `aws` visant Floci, et
les deux ressources à trous : les blocs existent, mais les arguments sont des
`???`. Aucun state n'existe encore.

## L'état à atteindre

1. Les deux ressources figurent dans le state, **sans avoir été recréées** :
   l'identifiant de l'instance importée est le même qu'avant.
2. La configuration est **fidèle** à la réalité : juste après l'import, un
   `terraform plan` ne propose **aucun changement**. C'est le vrai critère de
   réussite d'un import, et le piège classique : un import qui « marche » mais
   dont le plan veut ensuite modifier la ressource est un import raté.
3. Un **drift** est ensuite provoqué hors Terraform (un tag modifié via l'AWS
   CLI). L'apprenant doit le détecter, puis choisir et appliquer la
   réconciliation.
4. Le `destroy` final laisse un state vide et plus aucune ressource côté Floci.

## Comment on le prouve

Les tests interrogent l'état, jamais le fichier de l'apprenant :

- `terraform show -json` : les deux adresses sont présentes, et l'`instance_id`
  correspond à celui créé hors Terraform (preuve de l'import, pas d'une
  recréation).
- `terraform plan -detailed-exitcode` sort en **0** après import : la config est
  fidèle.
- Après injection du drift, le même plan sort en **2** : le drift est bien
  détecté. Après réconciliation, il retombe à **0**.
- Après `destroy` : `terraform state list` est vide et l'AWS CLI pointée sur
  Floci ne retrouve plus les ressources.

## 🎯 Challenge : reprendre, sans détruire, ce que Terraform ignore

### 📦 Le point de départ

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

### ✅ Objectif

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

### 🧭 Les deux critères qui comptent

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

### ⚠️ Écraser une dérive est un réflexe, pas une décision

Un `apply` « remet en ordre » et efface un changement que quelqu'un a fait pour
une raison qu'on ignore. Le collègue ne saura jamais pourquoi son tag a disparu.

Accepter la dérive, c'est décider que la réalité a raison, et le dire dans le
code.

### 🔍 Validation

```bash
dsoxlab check certifications-professional-capstone1-resource-lifecycle
```

Cinq tests. Aucun ne lit vos `.tf` : ils comparent l'identifiant du state à
celui que Floci connaît, vérifient le tag **des deux côtés**, et exigent les deux
codes de retour.

Le dernier test **détruit**, et il s'exécute même si les autres ont échoué : un
lab raté qui laisse une instance derrière lui fait payer le lab suivant.

Bloqué ? `dsoxlab hint certifications-professional-capstone1-resource-lifecycle`.
