# A CORRIGER : deux `???`, et le second est un piege que la section a mesure.
#
# Ce repertoire ecrit la fiche d'un service. Elle doit permettre a un auditeur
# de VERIFIER qu'un jeton presente est bien celui qu'on attend, sans que le
# jeton lui-meme se retrouve dans le state.
#
# Rappel de ce que la section a etabli, et qui vaut ici :
#
#   - `sensitive` protege l'AFFICHAGE, pas le stockage. Une valeur sensible
#     posee dans un attribut de ressource se retrouve en clair dans le state ;
#   - la sensibilite se propage A TRAVERS les fonctions, sans que Terraform
#     regarde ce qu'elles font. Un output racine qui derive d'une valeur
#     sensible doit donc etre annote, meme quand ce qu'il rend ne permet pas de
#     remonter au secret.

resource "local_file" "fiche" {
  filename = "${path.module}/fiche-service.txt"

  # A COMPLETER : le contenu de la fiche. Il porte le nom du service et de quoi
  # verifier le jeton, mais JAMAIS le jeton.
  content = ???
}

output "empreinte_publiee" {
  description = "Ce qu'un auditeur peut comparer, sans rien apprendre du jeton."

  # A COMPLETER : l'empreinte du jeton. Attention a ce que Terraform exige d'un
  # output qui derive d'une valeur sensible.
  ???
}
