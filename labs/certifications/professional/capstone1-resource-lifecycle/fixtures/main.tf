# A COMPLETER.
#
# Deux objets existent DEJA chez le fournisseur, crees a la main, hors
# Terraform. Personne ne vous tend leurs identifiants : les retrouver est la
# premiere etape d'une reprise en main.
#
#   aws --endpoint-url http://localhost:14566 ec2 describe-instances \
#       --filters 'Name=tag:Name,Values=capstone-facturation' \
#       --query 'Reservations[].Instances[].InstanceId' --output text
#
#   aws --endpoint-url http://localhost:14566 s3api list-buckets \
#       --query 'Buckets[].Name' --output text
#
# Les deux blocs `resource` ci-dessous sont amorces mais troues. Les blocs
# `import` sont a ecrire : ils disent a Terraform quel objet reel rattacher a
# quelle adresse.
#
# RAPPEL DU CRITERE DE REUSSITE : un import n'est pas fini quand la ressource
# apparait dans `terraform state list`. Il est fini quand un `plan` ordinaire
# ne propose plus RIEN. Tant qu'il propose quelque chose, votre code decrit
# autre chose que l'objet reel, et le prochain apply modifiera cet objet.

# A COMPLETER : le bloc `import` qui rattache l'instance existante a l'adresse
# `aws_instance.facturation`.
???

resource "aws_instance" "facturation" {
  # A COMPLETER : les arguments doivent decrire l'objet TEL QU'IL EST, sinon le
  # plan proposera de le modifier. Relevez ses valeurs chez le fournisseur.
  ami           = ???
  instance_type = ???

  tags = ???
}

# A COMPLETER : le bloc `import` qui rattache le bucket existant a l'adresse
# `aws_s3_bucket.archives`.
???

resource "aws_s3_bucket" "archives" {
  # A COMPLETER : l'identifiant d'un bucket S3 est son nom.
  bucket = ???
}
