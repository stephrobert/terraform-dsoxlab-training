# Fourni, complet. A ne pas modifier.
#
# Une seule entree decrit tout un environnement. Le lab demande que N entrees
# produisent N ressources, sans une ligne de code dupliquee.

variable "environnements" {
  description = "Les environnements a produire, par nom logique."

  type = map(object({
    taille  = number
    options = list(string)
  }))

  default = {
    "Dev_Local"   = { taille = 1, options = ["trace"] }
    "PreProd_EU"  = { taille = 2, options = ["trace", "metriques"] }
    "PROD_EU"     = { taille = 4, options = [] }
  }
}

variable "prefixe" {
  description = "Prefixe commun a tous les noms produits."
  type        = string
  default     = "lab"
}

variable "longueur_nom" {
  description = "Longueur maximale d'un nom normalise."
  type        = number
  default     = 18
}
