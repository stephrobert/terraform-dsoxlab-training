# Deux ressources gérées, complètes : ne pas y toucher.
# Elles servent de point de comparaison, parce qu'une data source ne se
# comprend qu'en regard d'une ressource gérée.

resource "random_pet" "empreinte" {
  length = 2

  keepers = {
    revision = var.revision
  }
}

resource "local_file" "rapport" {
  filename = "${path.module}/sortie/rapport-${random_pet.empreinte.id}.txt"
  content  = "revision=${var.revision}\n"
}

# --------------------------------------------------------------------------
# Trois data sources et deux outputs, à écrire UN PAR UN.
#
# Ils sont commentés pour que la configuration s'applique dès maintenant :
# lancez `terraform init` puis `terraform apply` avant toute chose, vous aurez
# ainsi un point de départ stable.
#
# Décommentez ensuite un bloc à la fois, complétez son `???`, et relancez la
# commande d'observation donnée par le tutoriel. C'est la comparaison entre
# deux étapes qui fait comprendre le sujet, pas le résultat final.
# --------------------------------------------------------------------------

# ??? Étape 1. Lire le fichier catalogue.txt livré à côté de la configuration.
#     L'argument doit rester connu au plan : aucune référence à une ressource
#     gérée, uniquement path.module.
#
# data "local_file" "catalogue" {
#   filename = ???
# }

# ??? Étape 2. Relire le fichier PRODUIT par local_file.rapport, en référençant
#     son attribut filename. Ne recopiez pas le chemin à la main : c'est la
#     référence qui crée la dépendance, et donc le report de lecture.
#
# data "local_file" "rapport_relu" {
#   filename = ???
# }

# ??? Étape 3. Lire le même catalogue.txt qu'à l'étape 1, en déclarant en plus
#     une dépendance EXPLICITE vers random_pet.empreinte.
#     Beaucoup de tutoriels affirment que cela force la lecture à l'apply.
#     Ce lab est bâti pour vérifier cette affirmation.
#
# data "local_file" "catalogue_ordonne" {
#   filename = ???
#   ???
# }

# ??? Étape 4. Exposer le contenu de la data source de l'étape 1. Cet output
#     est connu dès le plan, parce que sa source l'est.
#
# output "catalogue" {
#   value = ???
# }

# ??? Étape 4 (suite). Exposer le contenu de la data source de l'étape 2. Au
#     plan où la ressource gérée change, cet output est inconnu : il porte
#     after_unknown dans le JSON.
#
# output "rapport" {
#   value = ???
# }
