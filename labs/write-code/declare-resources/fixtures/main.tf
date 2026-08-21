resource "random_pet" "hote" {
  length = 2

  # ??? Des keepers liés à var.generation : changer generation doit remplacer
  #     cette ressource (donc régénérer son id).
  keepers = {
    generation = ???
  }
}

resource "local_file" "fiche" {
  # ??? Le nom du fichier tire l'id de random_pet.hote : dépendance IMPLICITE,
  #     sans depends_on. Ainsi, un changement d'id force un remplacement.
  filename = "${path.module}/out/fiche-${???}.txt"
  content  = "hote=${random_pet.hote.id}\n"

  # ??? Créer le nouveau fichier avant de détruire l'ancien.
  lifecycle {
    ??? = true
  }
}

resource "terraform_data" "sceau" {
  # ??? input porte l'étiquette (mise à jour en place quand elle change) ;
  #     triggers_replace vaut l'id de l'hôte (remplacement quand il change).
  input            = ???
  triggers_replace = ???
}

resource "local_file" "journal" {
  filename = "${path.module}/out/journal.txt"
  content  = "livraison\n"

  # ??? Ce journal dépend du sceau par COMPORTEMENT : il n'utilise aucune de ses
  #     données. Seul un depends_on peut exprimer ce lien.
  ??? = [terraform_data.sceau]
}
