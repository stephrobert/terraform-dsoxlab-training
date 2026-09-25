# La contrainte de provider est a completer.
#
# Attention : `~> 0.8` n'interdit PAS la serie 0.9, et la 0.9 a reecrit le
# schema des ressources. Ce fichier doit designer sans ambiguite la serie dont
# le code ci-contre utilise le schema.

terraform {
  required_version = ">= 1.11.0"

  required_providers {
    libvirt = {
      source  = "dmacvicar/libvirt"
      version = ???
    }
  }
}

provider "libvirt" {
  uri = "qemu:///system"
}
