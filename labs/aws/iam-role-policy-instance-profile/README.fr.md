# IAM : le rôle, ses deux policies, et le profil qui n'en porte qu'un

IAM a la réputation d'être confus. Il l'est surtout à cause de deux mots qu'on
emploie l'un pour l'autre, et d'un tableau qui laisse croire à une liberté qui
n'existe pas. Ce tutoriel règle les deux.

## Une data source qui n'interroge rien

`aws_iam_policy_document` **ne fait aucun appel réseau**. C'est un constructeur
de JSON, écrit en HCL, qui vous évite d'enfouir du JSON dans une chaîne.

```hcl
data "aws_iam_policy_document" "confiance" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}
```

Elle apparaît pourtant en `"mode": "data"` dans le state, exactement comme une
data source qui appelle une API. C'est une bonne occasion de retenir ce que ce
mode signifie vraiment : **lu**, et non **distant**. Terraform ne le crée pas,
ne le détruit pas, et le recalcule à chaque plan.

## Les deux policies d'un rôle, et leurs vrais noms

Un rôle IAM porte **deux** choses, qui n'ont rien à voir.

| | Ce qu'elle dit | Où elle vit |
|---|---|---|
| **trust policy** | **qui** a le droit d'endosser le rôle | dans le rôle, argument `assume_role_policy` |
| **policy de permissions** | **ce que** le rôle a le droit de faire | dans un objet séparé, rattaché |

La trust policy est la seule policy **basée sur la ressource** qu'IAM connaisse
pour un rôle. Si un texte appelle « resource policy » la policy de permissions,
il se trompe, et cette confusion coûte cher au moment de déboguer un refus.

```hcl
resource "aws_iam_role" "application" {
  name               = "role-application"
  assume_role_policy = data.aws_iam_policy_document.confiance.json
}

resource "aws_iam_policy" "lecture_s3" {
  name   = "policy-lecture-s3"
  policy = data.aws_iam_policy_document.permissions.json
}

resource "aws_iam_role_policy_attachment" "lecture" {
  role       = aws_iam_role.application.name
  policy_arn = aws_iam_policy.lecture_s3.arn
}
```

Trois objets, et c'est délibéré : une policy rattachée peut servir à plusieurs
rôles. Retirer le rattachement ne détruit ni l'un ni l'autre.

## Les deux ARN de S3, et le refus qu'on ne comprend pas

Voici l'erreur la plus fréquente d'IAM sur S3 :

```hcl
# Incomplet : on pourra lister, jamais lire.
statement {
  actions   = ["s3:ListBucket", "s3:GetObject"]
  resources = ["arn:aws:s3:::mon-bucket"]
}
```

Lister s'exerce sur le **bucket**, lire s'exerce sur ses **objets**. Ce sont
deux ressources différentes :

```hcl
statement {
  actions   = ["s3:ListBucket"]
  resources = ["arn:aws:s3:::mon-bucket"]
}

statement {
  actions   = ["s3:GetObject"]
  resources = ["arn:aws:s3:::mon-bucket/*"]
}
```

<Aside type="caution" title="AWS ne dira pas pourquoi">
Un `AccessDenied` sur `GetObject` ne mentionne pas l'ARN manquant. Vous verrez
une policy qui contient bien `s3:GetObject`, et un refus quand même. Le suffixe
`/*` est la première chose à vérifier.
</Aside>

## Un profil, un rôle, et un tableau trompeur

```bash
aws iam get-instance-profile --instance-profile-name profil-application
```

```json
{ "InstanceProfile": { "Roles": [ { "RoleName": "role-application" } ] } }
```

`Roles` est un **tableau**, et beaucoup en concluent qu'on peut en mettre
plusieurs. **On ne peut pas.** AWS en autorise exactement un, et l'argument
Terraform le dit sans ambiguïté : `role`, au singulier. Le tableau est un
héritage de l'API, pas une possibilité.

L'instance, elle, reçoit le **nom** du profil :

```hcl
resource "aws_instance" "application" {
  iam_instance_profile = aws_iam_instance_profile.application.name
}
```

## À vous de jouer

Vous savez maintenant qu'une data source peut être purement locale, que la trust
policy et les permissions sont deux objets distincts, que S3 exige deux ARN, et
qu'un profil ne porte qu'un rôle malgré ce que son API laisse croire.

```bash
dsoxlab run aws-iam-role-policy-instance-profile
dsoxlab check aws-iam-role-policy-instance-profile
dsoxlab hint aws-iam-role-policy-instance-profile
```

Sous-objectif d'examen visé : **2b** (utiliser des data sources).

Référence : [IAM, rôle, policy et instance profile](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/aws/iam-role-policy-instance-profile/)
