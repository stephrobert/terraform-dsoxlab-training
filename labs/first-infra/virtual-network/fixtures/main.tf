# Deux blocs, et une dependance que Terraform NE PEUT PAS deviner.

resource "libvirt_network" "lab" {
  name      = var.nom_du_reseau
  autostart = false

  # A completer : le mode de forwarding.
  #
  # Un reseau NAT donne aux machines un acces sortant sans les exposer.
  forward = {
    mode = ???
  }

  ips = [{
    address = var.passerelle
    netmask = var.masque

    # A completer : la plage DHCP, de .100 a .200.
    dhcp = {
      ranges = [{
        start = ???
        end   = ???
      }]
    }
  }]
}

# Le rapport. Il interroge libvirt AVEC LE NOM DU RESEAU, pris dans la variable.
#
# Regardez bien : ce bloc ne reference AUCUN attribut de la ressource ci-dessus.
# Il lit `var.nom_du_reseau`, pas `libvirt_network.lab.name`. Rien, dans le
# code, ne dit donc a Terraform que le reseau doit exister d'abord.
#
# Terraform est alors LIBRE d'executer les deux dans n'importe quel ordre, et
# il le fait : le rapport sortira vide une fois sur deux, sans la moindre
# erreur. C'est le genre de defaut qui passe la revue et casse en production.
#
# A completer : le meta-argument qui exprime une dependance qu'aucune reference
# ne porte.
resource "null_resource" "rapport" {
  ???

  provisioner "local-exec" {
    command = "virsh -c qemu:///system net-dumpxml ${var.nom_du_reseau} > rapport.xml"
  }
}
