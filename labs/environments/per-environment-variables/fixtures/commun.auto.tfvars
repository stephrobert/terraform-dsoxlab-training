# Valeurs partagees par TOUS les environnements.
#
# Le suffixe .auto.tfvars suffit a les charger : aucun -var-file n'est
# necessaire. C'est exactement ce qu'on veut pour des valeurs communes, qui
# n'ont donc pas a etre repetees dans chaque fichier d'environnement.

base_image = "debian-13-genericcloud-amd64.qcow2"

tags = {
  equipe = "infra"
  projet = "formation-terraform"
}
