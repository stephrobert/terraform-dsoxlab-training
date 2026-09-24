# Fourni, complet.

terraform {
  required_version = ">= 1.11.0"

  required_providers {
    libvirt = {
      source  = "dmacvicar/libvirt"
      version = "~> 0.9.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }
}

provider "libvirt" {
  uri = "qemu:///system"
}
