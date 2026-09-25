# A CORRIGER.
#
# L'instance porte le jeton de service EN CLAIR dans une etiquette. La variable
# est pourtant marquee `sensitive`, et Terraform n'affichera effectivement pas
# sa valeur a l'ecran.
#
# Mesure du 2026-09-25, sur cette configuration meme : le state la porte
# malgre tout, deux fois, dans `tags` et dans `tags_all`. `sensitive` protege
# l'ecran, pas le fichier.
#
# Ce qu'il faut a la place : une EMPREINTE. Elle permet de verifier qu'un jeton
# presente est bien celui qu'on attend, sans jamais conserver le jeton. C'est
# le meme raisonnement qu'un mot de passe, qu'aucun service serieux ne stocke.

data "aws_ami" "socle" {
  most_recent = true
  owners      = ["amazon"]
}

resource "aws_instance" "service" {
  ami           = data.aws_ami.socle.id
  instance_type = "t3.micro"

  tags = {
    Name = "service-authentifie"

    # A REMPLACER par une etiquette `Empreinte`, qui porte l'empreinte SHA-256
    # du jeton et non le jeton.
    Jeton = var.jeton_de_service
  }
}
