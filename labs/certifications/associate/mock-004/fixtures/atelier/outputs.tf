# A COMPLETER.

# A COMPLETER : exposer la sortie de `terraform_data.jeton`, qui derive d'une
# variable sensible.
#
# Terraform REFUSE de planifier si vous exposez une valeur sensible sans le
# dire. La question q40 vous fera ensuite constater ou cette valeur se trouve
# vraiment une fois l'apply passe.
output "jeton_expose" {
  value = ???
  ???
}

# A COMPLETER : le nom genere par `random_pet.socle`. Celui-ci n'est pas
# sensible.
output "socle" {
  value = ???
}
