resource "local_file" "conf" {
  # ??? : iterer sur l'ENSEMBLE des services. ATTENTION : une valeur SENSIBLE ne
  # peut PAS servir de cle for_each (« Invalid for_each argument »). Iterez sur la
  # variable NON sensible. Remplacez ce ??? par l'ensemble adapte.
  for_each = ???

  filename = "${path.module}/out/${each.key}.conf"

  # Le contenu injecte le mot de passe SENSIBLE : l'attribut `content` en devient
  # contamine (marque sensible dans le state). Ne pas modifier.
  content = "service=${each.key}\npassword=${var.db_password}\n"
}
