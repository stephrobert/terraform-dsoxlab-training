variable "cidr_de_base" {
  description = "Reseau dont derivent toutes les adresses du parc."
  type        = string
  default     = "10.20.0.0/16"
}

# A completer : le type du parc.
#
# Chaque serveur porte un nom logique, un role et un index reseau. Un `any`
# accepterait n'importe quoi et ne prouverait rien : le type doit dire
# EXACTEMENT ce que chaque entree contient, et refuser le reste AU PLAN.
variable "parc" {
  description = "Les serveurs a decrire, par nom logique."

  type = ???

  default = {
    web1 = {
      role  = "web"
      index = 11
    }
    web2 = {
      role  = "web"
      index = 12
    }
    bdd1 = {
      role  = "bdd"
      index = 21
    }
  }
}
