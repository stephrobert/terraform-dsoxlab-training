# CE FICHIER PARSE, ET NE VALIDE PAS.
#
# Trois erreurs y sont semees, et elles ne tombent PAS au meme moment. Mesure du
# 2026-09-24 :
#
#   terraform init       echoue sur la premiere, parce que `init` PARSE la
#                        configuration. Tant qu'elle est la, aucun provider
#                        n'est installe, et `validate` ne peut rien valider :
#                        il repond « Missing required provider », ce qui envoie
#                        chercher au mauvais endroit.
#
#   terraform validate   une fois l'init passe, nomme les DEUX autres d'un coup,
#                        avec leur numero de ligne.
#
# D'ou la methode : init, corriger ce qu'il refuse, init de nouveau, puis
# validate.
#
# Les valeurs marquees « A COMPLETER » sont, elles, syntaxiquement correctes et
# fonctionnellement fausses : la configuration validera avant de faire ce qu'on
# lui demande. Les tests, eux, ne s'y trompent pas.

locals {
  # A COMPLETER : normaliser la cle d'un environnement en un nom utilisable.
  #
  #   minuscules, les soulignes changes en tirets, le prefixe devant, et le
  #   tout tronque a `var.longueur_nom` caracteres.
  #
  # Attendu pour "PreProd_EU" avec le prefixe "lab" : "lab-preprod-eu"
  noms = { for cle, _ in var.environnements : cle => cle }
}

# ERREUR 1 : cette ressource porte DEUX meta-arguments de multiplicite.
# Terraform refuse : il faut choisir. Gardez celui qui adresse par CLE, pas par
# position, parce qu'une entree retiree au milieu ne doit pas decaler les
# autres.
resource "random_password" "secret" {
  count    = length(var.environnements)
  for_each = var.environnements

  length  = 20
  special = false
}

# ERREUR 2 : cet argument attend un NOMBRE, et la valeur passee ici n'en est
# pas un. Le message de Terraform nomme le type attendu.
resource "random_pet" "etiquette" {
  for_each = var.environnements

  length = "deux"
}

resource "local_file" "manifeste" {
  for_each = var.environnements

  # A COMPLETER : le chemin doit porter le nom NORMALISE de l'environnement,
  # pas la cle brute.
  filename = "${path.module}/out/${each.key}.json"

  # A COMPLETER : un JSON serialise PAR UNE FONCTION, jamais concatene a la
  # main. Il porte trois cles : `nom` (le nom normalise), `taille`, et
  # `etiquette` (l'identifiant du random_pet de cet environnement).
  content = "a completer"
}

# ERREUR 3 : cette expression reference une variable qui n'est declaree nulle
# part. Regardez `variables.tf` : trois variables y sont declarees, et
# celle-ci n'en fait pas partie.
resource "null_resource" "marqueur" {
  for_each = var.environnements

  triggers = {
    region = var.region_par_defaut
    nom    = local.noms[each.key]
  }
}

data "archive_file" "options" {
  for_each = var.environnements

  type        = "zip"
  output_path = "${path.module}/out/${local.noms[each.key]}-options.zip"

  # Ce bloc `source` fixe est toujours present : une archive vide serait
  # refusee par le provider, et un environnement peut n'avoir aucune option.
  source {
    filename = "environnement.txt"
    content  = "${local.noms[each.key]}\n"
  }

  # A COMPLETER : un bloc `dynamic` qui genere UN bloc `source` par option de
  # l'environnement courant, nomme `<option>.txt`.
  #
  # Un environnement sans option ne doit produire aucun bloc supplementaire.
  # Le nombre de blocs se regle dans le `for_each` du dynamic, jamais par un
  # `if` dans son `content` : a ce stade le bloc est deja decide.
}
