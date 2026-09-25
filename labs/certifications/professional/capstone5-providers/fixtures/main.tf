# CETTE CONFIGURATION NE S'APPLIQUE PAS.
#
# Trois choses lui manquent, et elles ne se manifestent pas au meme moment :
#
#   - aucune contrainte de version sur le provider ;
#   - le provider va chercher une identite qui n'existe pas. Lancez un `plan` et
#     LISEZ l'erreur : elle nomme ce qu'il n'a pas trouve, et ou il a cherche ;
#   - une exigence nouvelle est tombee : les archives doivent vivre dans une
#     SECONDE region, ce qu'une seule configuration de provider ne peut pas
#     faire.
#
# Les deux premieres se diagnostiquent. La troisieme se construit.

terraform {
  required_version = ">= 1.11.0"

  required_providers {
    # A COMPLETER : une contrainte de version. Sans elle, rien ne garantit que
    # le collegue obtiendra le meme provider que vous, et le verrou n'en portera
    # aucune.
    aws = {
      source = "hashicorp/aws"
    }
  }
}

variable "emulateur_endpoint" {
  description = "Ou joindre l'emulateur."
  type        = string
  default     = "http://localhost:14566"
}

# A COMPLETER : ce provider vise bien l'emulateur, mais il cherche quand meme
# des identifiants la ou il n'y en a pas, puis une identite aupres du vrai AWS.
#
# Il lui faut des identifiants factices NON VIDES, et les trois options qui le
# dispensent d'aller verifier une identite, un compte et une metadonnee
# d'instance.
provider "aws" {
  region = "eu-west-3"

  endpoints {
    ec2 = var.emulateur_endpoint
  }
}

# A COMPLETER : une SECONDE configuration du MEME provider, pour la region
# `us-east-1`. Un seul argument la distingue de la premiere, et c'est lui qui
# permet de la designer ensuite.
#
# Elle a besoin des memes options que la premiere : chaque configuration est
# independante, rien ne s'herite d'une configuration a l'autre.
???

resource "aws_instance" "principal" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "t3.micro"

  tags = {
    Name = "capstone5-principal"
  }
}

# A COMPLETER : cette ressource doit etre creee par la SECONDE configuration.
#
# Sans rien, une ressource utilise la configuration PAR DEFAUT de son provider :
# celle-ci serait creee dans la premiere region, et rien ne le signalerait.
resource "aws_instance" "archives" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "t3.micro"

  tags = {
    Name = "capstone5-archives"
  }
}
