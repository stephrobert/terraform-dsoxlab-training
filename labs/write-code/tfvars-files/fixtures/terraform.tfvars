region = "eu-west-3"

# BUG : "bukcet" au lieu de "bucket". Une variable NON declaree dans un .tfvars
# ne fait qu'un AVERTISSEMENT, pas une erreur : `plan` reussit, mais `bucket`
# reste a son defaut "app-defaut". Corrigez le nom pour que bucket vaille "prod".
bukcet = "prod"

replicas = 2
