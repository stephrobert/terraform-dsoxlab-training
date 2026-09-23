# Deux mots de vocabulaire que le guide d'origine confond, et qu'il faut avoir
# droits avant d'ecrire une ligne.
#
# La TRUST POLICY dit QUI a le droit d'endosser le role. C'est la seule policy
# « basee sur la ressource » qu'IAM connaisse pour un role. Le guide l'appelle
# parfois autrement : ne le suivez pas.
#
# La POLICY DE PERMISSIONS dit CE QUE le role a le droit de faire. Elle vit dans
# un objet separe, et se rattache au role.
#
# `aws_iam_policy_document` est une data source LOCALE : elle n'interroge rien,
# elle fabrique du JSON. C'est pour cela qu'elle apparait en `mode: data` dans
# le state alors qu'aucun appel reseau n'a lieu.

# 1. Qui a le droit d'endosser le role.
data "aws_iam_policy_document" "confiance" {
  statement {
    actions = ["sts:AssumeRole"]

    # A completer : le service AWS autorise a endosser ce role.
    ???
  }
}

# 2. Ce que le role a le droit de faire.
#
#    Deux statements, et DEUX ARN differents : lister un bucket et lire ses
#    objets ne visent pas la meme ressource. L'un porte l'ARN du bucket, l'autre
#    le meme ARN suffixe. Se tromper ici donne une policy qui semble juste et
#    qui ne marche pas.
data "aws_iam_policy_document" "permissions" {
  statement {
    actions   = ["s3:ListBucket"]
    resources = [???]
  }

  statement {
    actions   = ["s3:GetObject"]
    resources = [???]
  }
}

# 3. Le role. Il ne detient AUCUNE permission : seulement la trust policy.
resource "aws_iam_role" "application" {
  name = "role-application"

  ??? = data.aws_iam_policy_document.confiance.json
}

# 4. La policy de permissions, comme objet IAM reel.
#
#    Le document n'est que du texte tant qu'un objet ne le porte pas.
resource "aws_iam_policy" "lecture_s3" {
  name = "policy-lecture-s3"

  ??? = data.aws_iam_policy_document.permissions.json
}

# 5. Le rattachement. Le role par son NOM, la policy par son ARN.
resource "aws_iam_role_policy_attachment" "lecture" {
  role       = aws_iam_role.application.name
  policy_arn = aws_iam_policy.lecture_s3.arn
}

# 6. Le profil d'instance.
#
#    AWS autorise EXACTEMENT UN role par profil, quoi qu'en dise le guide.
resource "aws_iam_instance_profile" "application" {
  name = "profil-application"

  ??? = aws_iam_role.application.name
}

# 7. L'instance. Elle recoit le NOM du profil, pas son ARN.
resource "aws_instance" "application" {
  ami           = var.ami_id
  instance_type = var.instance_type

  ??? = aws_iam_instance_profile.application.name
}
