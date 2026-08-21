# Ce parametre SSM doit recevoir un secret et ne JAMAIS l'ecrire dans le state
# Terraform. Un argument ordinaire `value = var.secret_api` stockerait le secret
# en clair dans terraform.tfstate : n'importe qui lisant le fichier le verrait.
#
# Remplacez les deux ??? par les DEUX arguments qui forment un couple :
#   - le premier envoie la valeur au provider SANS jamais la persister ;
#   - le second, obligatoire avec le premier, versionne l'envoi (un entier).
#     Sans lui, Terraform ne sait pas quand renvoyer la valeur au service.
#
# Indice de nommage : ces arguments portent tous le meme suffixe conventionnel.
resource "aws_ssm_parameter" "jeton_api" {
  name = var.param_name
  type = "SecureString"

  ??? = var.secret_api
  ??? = 1
}
