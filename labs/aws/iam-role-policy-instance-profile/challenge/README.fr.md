# 🎯 Challenge : composer la chaîne IAM sans se tromper de mot

## Point de départ

`challenge/work` contient quatre fichiers. `versions.tf` et `variables.tf` sont
**fournis et complets**. `main.tf` et `outputs.tf` sont **troués**.

Floci tourne en local : aucun compte AWS, aucune facture.

## ⚠️ Deux erreurs de vocabulaire à ne pas reprendre

Beaucoup de tutoriels, y compris certains guides, disent ces deux choses. Elles
sont fausses toutes les deux.

- « la **resource policy** du rôle » pour désigner ses permissions. La seule
  policy basée sur la ressource qu'IAM connaisse pour un rôle est sa **trust
  policy**, celle qui dit *qui* a le droit de l'endosser. Les permissions, elles,
  vivent dans un objet séparé.
- « un instance profile porte **un ou plusieurs rôles** ». AWS en autorise
  **exactement un**. L'argument Terraform s'appelle `role`, au singulier. Le
  champ `Roles` de l'API est un tableau parce qu'il l'a toujours été, pas parce
  qu'on peut en mettre deux.

## ✅ Objectif

1. **La trust policy** : un `principals` de type `Service` visant
   `ec2.amazonaws.com`, pour l'action `sts:AssumeRole`.
2. **Les permissions** : deux statements, et **deux ARN différents**.
   `s3:ListBucket` s'exerce sur le bucket, `s3:GetObject` sur ses objets.
3. **Le rôle** porte le premier document, et **rien d'autre**.
4. **La policy** porte le second, et devient un objet IAM réel.
5. **Le profil** reçoit le rôle, **l'instance** reçoit le nom du profil.
6. **Les cinq sorties**, qui sont le seul moyen de montrer aux tests le JSON
   produit sans relire vos `.tf`.

## 🧭 Ce que le lab vous fait constater

- **Les deux documents sont en `mode: data`** alors qu'aucun appel réseau n'a
  lieu. « data » ne veut pas dire « distant », cela veut dire **lu**.
- **Une policy qui ne porte que l'ARN du bucket laisse lister et refuse de
  lire.** C'est l'erreur la plus fréquente d'IAM sur S3, et le message d'AWS ne
  dit pas pourquoi.
- **`get-instance-profile` rend un tableau `Roles` d'un seul élément.**
- **Retirer le rattachement ne détruit que lui** : le rôle et la policy
  survivent. C'est ce qui distingue un rattachement d'une appartenance.

## 🔍 Validation

```bash
dsoxlab check aws-iam-role-policy-instance-profile
```

Sept tests. Le JSON produit arrive par `terraform output -json` puis est
désérialisé ; l'inventaire vient de `show -json` ; et ce que l'émulateur a
**réellement reçu** est relu par l'API AWS. Le dernier test retire le
rattachement sur une **copie** de votre travail : un test ne casse pas ce qu'il
mesure. Aucun ne lit vos `.tf`.
