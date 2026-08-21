output "mot_de_passe_admin" {
  # ??? : exposer random_password.admin.result. C'est une valeur SENSIBLE, le
  # plan la refuse tant que l'output n'est pas marque en consequence.
  # Contraignez aussi son type a string. Remplacez ce ??? par les arguments.
  ???
}

output "resume" {
  # ??? : un objet { longueur = number, empreinte = string }. Contraignez le
  # TYPE de l'output. empreinte = sha256 du mot de passe, MAIS le sha256 d'une
  # valeur sensible reste sensible : declassifiez-la explicitement pour l'exposer
  # dans cet output non sensible. N'exposez JAMAIS le mot de passe en clair.
  ???
}

output "empreinte_rapport" {
  value = sha256(local_file.rapport.content)

  # ??? : ajoutez un bloc precondition (avec error_message, obligatoire) qui
  # exige var.longueur_mot_de_passe >= 20.
  ???
}
