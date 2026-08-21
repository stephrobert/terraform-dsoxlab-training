# Le mot de passe de mot-de-passe-existant.txt est DEJA EN SERVICE dans
# l'application. Il est INTERDIT de le regenerer : un `terraform apply` seul
# tirerait un mot de passe neuf, app.conf porterait une valeur inconnue de
# l'appli, et le lab serait perdu sans le moindre message d'erreur.

# ??? : ajoutez un bloc `import` qui RATTACHE ce mot de passe existant a
#       random_password.db, sans le regenerer. Le bloc s'ecrit :
#         to = random_password.db
#         id = le contenu du fichier, via
#              file("${path.module}/mot-de-passe-existant.txt")
#       Il s'applique par `terraform apply`.

resource "random_password" "db" {
  length = ??? # la longueur EXACTE du mot de passe existant (comptez-le)
}

resource "local_file" "configuration" {
  filename        = "${path.module}/app.conf"
  file_permission = "0600"

  # ??? : le contenu, de la forme "mdp=<le mot de passe rattache>".
  content = ???
}

resource "local_file" "journal" {
  filename = "${path.module}/service.log"
  content  = var.journal
}
