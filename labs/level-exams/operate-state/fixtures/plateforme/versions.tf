terraform {
  required_version = "~> 1.16.0"

  required_providers {
    libvirt = {
      source  = "dmacvicar/libvirt"
      version = "0.9.9"
    }
  }

  # Le state vit dans le stockage S3 partagé de l'équipe. Les valeurs du banc
  # (point d'accès, bucket, clé) sont dans backend.hcl :
  #   terraform init -backend-config=backend.hcl
  backend "s3" {}
}

provider "libvirt" {
  uri = "qemu:///system"
}
