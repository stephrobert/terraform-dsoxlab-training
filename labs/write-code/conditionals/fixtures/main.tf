locals {
  # ??? memory_mib_override s'il n'est pas null, sinon 2048 en prod et 512 ailleurs.
  memory_mib = ???

  # ??? 4 en prod, 2 en staging, 1 sinon.
  vcpu = ???

  # ??? "<environment>-data.qcow2" si enable_second_disk, sinon null.
  #     La valeur null fait DISPARAITRE l'output correspondant.
  second_disk_name = ???
}

resource "local_file" "manifest" {
  filename = "${path.module}/manifest.json"

  # ??? Un JSON portant au moins les cles env, memory_mib et vcpu.
  content = ???

  lifecycle {
    # ??? Refuser moins de 256 MiB par vCPU.
    #     Les deux termes sont des locals : aucun bloc validation ne peut
    #     porter ce controle, il faut le placer ici.
    precondition {
      ???
    }

    # ??? Relire self.content apres ecriture et exiger un JSON portant env.
    postcondition {
      ???
    }
  }
}

# ??? Avertir quand memory_mib depasse 1024, SANS bloquer l'apply.
check "budget_prod" {
  ???
}
