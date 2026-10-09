resource "libvirt_volume" "disque" {
  for_each      = var.machines
  name          = "${var.prefixe}-${each.key}.qcow2"
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

resource "libvirt_domain" "machine" {
  for_each    = var.machines
  name        = "${var.prefixe}-${each.key}"
  type        = "kvm"
  memory      = each.value.memoire_mib
  memory_unit = "MiB"
  vcpu        = each.value.vcpu
  running     = true

  os = {
    type = "hvm"
  }

  devices = {
    disks = [{
      device = "disk"
      source = {
        file = { file = libvirt_volume.disque[each.key].path }
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
