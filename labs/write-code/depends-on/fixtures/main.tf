resource "random_pet" "nom" {
  length = 2
}

resource "local_file" "manifeste" {
  filename = "${var.racine}/manifeste.json"
  content = jsonencode({
    livraison = random_pet.nom.id
  })

  # ??? Ce depends_on est REDONDANT : le content ci-dessus référence déjà
  #     random_pet.nom.id, ce qui ordonne les deux ressources. Supprimez-le.
  depends_on = [random_pet.nom]
}

# Service lent, complet, à ne pas toucher. Il crée le répertoire, attend, puis
# pose le marqueur .pret. Il n'expose aucun attribut exploitable.
resource "null_resource" "socle" {
  provisioner "local-exec" {
    command = "mkdir -p ${var.racine} && sleep 2 && touch ${var.racine}/.pret"
  }
}

resource "null_resource" "publication" {
  # ??? Deux corrections ici.
  #  1. La commande écrit le chemin du manifeste EN DUR. Remplacez-le par une
  #     référence à local_file.manifeste.filename : la dépendance devient alors
  #     implicite, comme la doc le recommande dès qu'une donnée de l'amont sert.
  #  2. Rien ne relie cette ressource au socle, alors qu'elle a besoin de .pret.
  #     null_resource.socle n'expose aucune donnée : ajoutez un depends_on
  #     explicite vers lui, la seule dépendance qu'aucune référence ne peut dire.
  provisioner "local-exec" {
    command = "test -f ${var.racine}/.pret && cp ${var.racine}/manifeste.json ${var.racine}/publie.json"
  }
}
