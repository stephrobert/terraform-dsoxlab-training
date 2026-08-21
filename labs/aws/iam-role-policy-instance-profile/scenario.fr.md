# Scénario : donner une identité à une instance sans jamais poser de clé

**Sous-objectif d'examen visé : 2b, utiliser des data sources.**

`aws_iam_policy_document` est une data source **locale** : elle n'interroge rien,
elle fabrique du JSON. Le lab rend cette évidence démontrable et dissipe
l'inversion de vocabulaire sur les deux policies d'un rôle.

## Capacité visée

Composer la chaîne policy, rôle, instance profile, instance en pilotant le JSON
IAM depuis HCL, et prouver dans l'état structuré que trust policy et permissions
empruntent deux chemins distincts jusqu'au rôle.

## D'où part l'apprenant

Floci tourne sur `localhost:4566` : aucun compte AWS, aucune facture. Le
répertoire `challenge/work` est vierge, sans `.terraform/`, sans fichier de
verrouillage, sans state. Le `versions.tf` fourni est complet : il épingle
`hashicorp/aws` en `~> 6.0` et vise Floci par un bloc `endpoints` et les trois
`skip_*` d'usage. Le `main.tf` et le `outputs.tf` sont troués par des `???` : le
bloc désignant le service autorisé à endosser le rôle, l'argument qui transforme
le document en objet IAM réel, les deux ARN S3 du statement de lecture, le rôle
du profil, l'argument d'instance qui reçoit ce profil. Deux pièges attendent en
commentaire : le guide appelle « resource policy » la policy de permissions,
alors que la seule policy basée sur la ressource qu'IAM connaisse est la **trust
policy** ; et il prête au profil « un ou plusieurs rôles », alors qu'AWS en
autorise **exactement un**.

## L'état à atteindre

1. Le répertoire est initialisé et le fichier de verrouillage existe.
2. Deux `aws_iam_policy_document` figurent dans le state en `mode: data` : la
   trust policy, avec un bloc `principals` de type `Service` visant
   `ec2.amazonaws.com` et l'action `sts:AssumeRole` ; la policy de permissions,
   dont un statement porte l'ARN du bucket pour `s3:ListBucket` et un autre
   l'ARN suffixé par `/*` pour `s3:GetObject`.
3. Un `aws_iam_role` porte le premier document dans `assume_role_policy`, et rien
   d'autre : il ne détient aucune permission. Un `aws_iam_policy` porte le second
   et expose un `arn`. Aucun `description` ni `tags` : Floci ne les relit pas.
4. Un `aws_iam_role_policy_attachment` relie les deux, le rôle par son `name`, la
   policy par son `arn` ; une `aws_instance` reçoit le **nom** du profil, pas son
   ARN. Rejouer un plan après l'apply n'annonce aucun changement.
5. Retirer l'attachement du code laisse une seule suppression en attente : le
   rôle survit, la policy aussi.

## Comment on le prouve

Aucun test ne relit le `.tf` de l'apprenant, aucun ne parse une sortie humaine.
`terraform show -json` classe chaque adresse par `mode` : les deux documents en
`data`, les cinq objets créés en `managed`. Leur JSON, relu via `terraform output
-json` puis désérialisé, livre le `Principal` et l'`Action` de la trust policy et
les **deux** ARN S3 distincts de la seconde. Côté Floci, `iam get-policy-version`
confirme le document effectivement reçu, `iam get-instance-profile` un tableau
`Roles` d'un seul élément, `ec2 describe-iam-instance-profile-associations`
l'état `associated`. `terraform plan -detailed-exitcode` sort en 0 après l'apply,
puis en 2 une fois l'attachement retiré, le plan en JSON ne portant plus qu'une
entrée dont les `actions` valent `["delete"]`. Le `description` que le guide
recommande reste **hors de portée d'un apply sur Floci**, qui répond
`UnsupportedOperation` : ce point est validé **au plan seulement**.
