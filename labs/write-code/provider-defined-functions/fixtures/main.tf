# Ecrit le tfvars re-encode sur disque, pour prouver que la valeur circule bien
# jusqu'a un attribut de ressource.
resource "local_file" "aval" {
  filename = "${path.module}/aval.tfvars"

  # ??? : le contenu du fichier est le tfvars re-encode (un des locals).
  content = ???
}
