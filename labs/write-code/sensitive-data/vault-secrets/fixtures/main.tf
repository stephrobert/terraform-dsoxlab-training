# Le secret source `kvv2/app/db` PREEXISTE dans Vault : Terraform ne le cree
# pas, il le consomme. La voie historique, une data "vault_kv_secret_v2", le
# recopierait EN CLAIR dans le state (et sensitive_values ne cache rien). On
# veut au contraire qu'il ne laisse aucune trace.

# ??? : lire le secret source SANS le persister. Quel mot-cle de bloc lit un
#       secret de facon EPHEMERE (jamais dans le state) ? Remplacez aussi mount
#       (le moteur KV) et name (le chemin du secret).
??? "vault_kv_secret_v2" "source" {
  mount = ???
  name  = ???
}

resource "vault_kv_secret_v2" "replique" {
  mount = "kvv2"
  name  = "app/db-replique"

  # ??? : ecrire le password dans la replique SANS le persister (argument
  #       write-only), en reprenant la valeur lue de facon ephemere.
  ??? = jsonencode({ password = ??? })

  # ??? : l'entier de version write-only, qui seul declenche la reecriture.
  ??? = var.copie_version
}

output "chemin" {
  # ??? : le chemin de la replique (mount/name), une chaine non sensible.
  value = ???
}
