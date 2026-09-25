# A COMPLETER.
#
# Ces trois sorties parsent en l'etat, et ne rendent pas ce qu'on attend. Les
# tests lisent `terraform output -json`, pas vos fichiers.

# A COMPLETER : une MAP derivee, indexee par le nom NORMALISE, dont chaque
# valeur porte la taille et le nombre d'options de l'environnement.
#
# Une liste de valeurs brutes ne conviendrait pas : le lab demande une
# structure que l'on peut interroger par cle.
output "environnements" {
  value = {}
}

# A COMPLETER : exposer les mots de passe generes, indexes par nom normalise.
#
# Ils derivent de `random_password`, donc Terraform les considere comme
# sensibles. Il REFUSE de planifier si vous les exposez sans le dire, et le
# message parle de « sensitive values ».
output "secrets" {
  value = {}
}

# A COMPLETER : le nombre d'archives reellement produites. Un compte, qui doit
# suivre la variable sans jamais etre ecrit en dur.
output "nombre_archives" {
  value = 0
}
