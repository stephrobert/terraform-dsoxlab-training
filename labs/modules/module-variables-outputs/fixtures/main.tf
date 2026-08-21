# La racine appelle le MEME module deux fois, avec deux niveaux de detail.
# CE FICHIER EST COMPLET, ne pas y toucher : c'est lui qui met votre interface
# a l'epreuve.

# L'appel complet : tous les attributs sont fournis.
module "complet" {
  source = "./modules/artefact"

  depot = {
    nom             = "archives"
    retention_jours = 30
    chiffre         = true
  }
  etiquette       = "production"
  longueur_secret = 24
}

# L'appel minimal : un seul attribut. C'est le contrat du module qui doit
# combler le reste, sans que l'appelant ait a le savoir.
module "minimal" {
  source = "./modules/artefact"

  depot = { nom = "livraison" }
}
