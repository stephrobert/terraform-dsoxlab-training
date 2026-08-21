# Rien a changer ici. Cette ressource ne declare AUCUN `tags` : c'est
# volontaire, les tags doivent lui arriver par la configuration du provider.
resource "aws_instance" "lab" {
  ami           = var.ami_id
  instance_type = var.instance_type
}
