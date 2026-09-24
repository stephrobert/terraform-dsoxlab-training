# Une seule VM minimale, en copie sur ecriture depuis l'image cloud.
#
# L'image n'est jamais modifiee : le disque de la VM ne porte que les blocs qui
# changent. C'est ce qui permet de recreer une machine en une seconde plutot
# que de recopier 600 Mio.

resource "libvirt_volume" "disque" {
  name          = "${var.nom_de_la_vm}.qcow2"
  pool          = "default"
  capacity      = 4
  capacity_unit = "GiB"

  target = {
    format = { type = "qcow2" }
  }

  backing_store = {
    path   = var.image_de_base
    format = { type = "qcow2" }
  }
}

resource "libvirt_domain" "vm" {
  # A completer : les attributs du domaine.
  #
  # Le nom, le type d'hyperviseur, la memoire et son unite, le nombre de vCPU,
  # et le fait que la machine doit TOURNER.
  ???

  os = {
    type = "hvm"
  }

  devices = {
    disks = [{
      device = "disk"
      source = {
        file = { file = libvirt_volume.disque.path }
      }
      target = { dev = "vda", bus = "virtio" }
      driver = { name = "qemu", type = "qcow2" }
    }]
    interfaces = [{
      source = {
        network = { network = "default" }
      }
    }]
  }
}
