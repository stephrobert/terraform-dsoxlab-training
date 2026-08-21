# Les trois environnements a livrer. CE FICHIER EST COMPLET.
#
# C'est cette map qui alimente le `for_each` du bloc `module` : un seul appel,
# trois instances.

variable "environnements" {
  description = "Environnements a livrer, indexes par leur nom."
  type = map(object({
    cible     = string
    retention = number
  }))
  default = {
    dev     = { cible = "poste", retention = 3 }
    preprod = { cible = "recette", retention = 7 }
    prod    = { cible = "production", retention = 30 }
  }
}
