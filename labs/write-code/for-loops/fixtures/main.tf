resource "local_file" "fiche" {
  # ??? Une fiche pour chaque serveur à la fois "prod" ET actif, et pour aucun
  #     autre. for_each attend une map ou un set de chaînes : filtrez la map
  #     var.serveurs par une expression for avec une clause if.
  for_each = ???

  filename = "${path.module}/out/fiche-${each.key}.txt"
  content  = "serveur=${each.key} role=${each.value.role} memoire=${each.value.memoire_mo}\n"
}
