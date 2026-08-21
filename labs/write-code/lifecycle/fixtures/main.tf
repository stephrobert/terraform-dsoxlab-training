# Cette configuration s'applique telle quelle. Elle ne contient volontairement
# aucun bloc `lifecycle` : c'est votre travail de les poser, au bon endroit.
#
# Lancez `terraform init` puis `terraform apply` AVANT toute modification.
# Le constat de départ se fait ensuite avec :
#
#     terraform plan -var 'revision=2'
#
# Vous y verrez l'ordre par défaut : Terraform détruit avant de créer.

data "local_file" "modele" {
  filename = "${path.module}/modele.txt"
}

# Le nom du fichier applicatif dépend de ce jeton. Faire bouger `revision`
# remplace le pet, donc le nom, donc le fichier.
resource "random_pet" "version" {
  length = 2

  keepers = {
    revision = var.revision
  }
}

resource "local_file" "app" {
  filename = "${path.module}/out/app-${random_pet.version.id}.txt"
  content  = replace(data.local_file.modele.content, "{{env}}", var.env)
}

# Donnée critique : elle ne doit jamais partir sur un plan de destruction.
resource "local_file" "donnees" {
  filename = "${path.module}/out/donnees.txt"
  content  = "donnee critique"
}

# Le contenu de ce journal bouge sans arrêt et pollue les plans.
# Ses permissions, en revanche, doivent rester sous contrôle.
resource "local_file" "journal" {
  filename        = "${path.module}/out/journal.txt"
  content         = var.message
  file_permission = var.permissions
}

# Ce marqueur ne dépend de rien. Il doit pourtant être remplacé
# chaque fois que `revision` change.
resource "local_file" "marqueur" {
  filename = "${path.module}/out/marqueur.txt"
  content  = "marqueur"
}
