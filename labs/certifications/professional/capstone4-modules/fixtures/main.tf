# Une configuration PLATE, qui duplique trois fois le meme ensemble.
#
# Elle est DEJA APPLIQUEE : le state fourni decrit ces neuf objets, avec leurs
# identifiants. Votre refactor ne doit en recreer aucun.
#
# Trois services, trois blocs identiques a trois valeurs pres. Ajouter un
# quatrieme service demande aujourd'hui de recopier neuf lignes de plus.

resource "random_pet" "api_nom" {
  length    = 2
  separator = "-"
}

resource "local_file" "api_config" {
  filename = "${path.module}/out/api.json"
  content  = jsonencode({ service = "api", replicas = 3, nom = random_pet.api_nom.id })
}

resource "local_file" "api_journal" {
  filename = "${path.module}/out/api.log"
  content  = "service=api replicas=3\n"
}

resource "random_pet" "web_nom" {
  length    = 2
  separator = "-"
}

resource "local_file" "web_config" {
  filename = "${path.module}/out/web.json"
  content  = jsonencode({ service = "web", replicas = 2, nom = random_pet.web_nom.id })
}

resource "local_file" "web_journal" {
  filename = "${path.module}/out/web.log"
  content  = "service=web replicas=2\n"
}

resource "random_pet" "batch_nom" {
  length    = 2
  separator = "-"
}

resource "local_file" "batch_config" {
  filename = "${path.module}/out/batch.json"
  content  = jsonencode({ service = "batch", replicas = 1, nom = random_pet.batch_nom.id })
}

resource "local_file" "batch_journal" {
  filename = "${path.module}/out/batch.log"
  content  = "service=batch replicas=1\n"
}
