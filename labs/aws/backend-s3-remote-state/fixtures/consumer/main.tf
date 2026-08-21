# La stack AVAL : elle ne cree rien, elle CONSOMME ce que le producer publie.
#
# Aucune expression ne traverse la frontiere entre deux configurations : la
# seule passerelle est la lecture de l'ETAT distant, par ses outputs declares.

data "terraform_remote_state" "producer" {
  # A COMPLETER : quel type de backend, et quelle configuration pour l'atteindre.
  # Ce sont les memes arguments que ceux du producer, a une difference pres :
  # ici, on LIT, on ne verrouille pas.
  backend = ???

  config = {
    ???
  }

  # A COMPLETER : une valeur de repli pour `maintenance_window`, que le producer
  # ne publie PAS.
  #
  # Attention a ce que `defaults` couvre reellement : il comble un output
  # MANQUANT dans un etat qui EXISTE. Pointe sur une cle de state inexistante,
  # il ne sauve rien, et Terraform rend « Unable to find remote state ».
  defaults = {
    ???
  }
}

# Ces quatre sorties sont ecrites. Ne pas les modifier : c'est par elles que la
# validation compare les deux stacks.

output "network_name" {
  description = "Nom du reseau, lu dans l'etat du producer."
  value       = data.terraform_remote_state.producer.outputs.network_name
}

output "network_cidr" {
  description = "Plage reseau, lue dans l'etat du producer."
  value       = data.terraform_remote_state.producer.outputs.network_cidr
}

output "region" {
  description = "Region, lue dans l'etat du producer."
  value       = data.terraform_remote_state.producer.outputs.region
}

output "maintenance_window" {
  description = "Fenetre de maintenance : le producer ne la publie pas, le repli joue."
  value       = data.terraform_remote_state.producer.outputs.maintenance_window
}
