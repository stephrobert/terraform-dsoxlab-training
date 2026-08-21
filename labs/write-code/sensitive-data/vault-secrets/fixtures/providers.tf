# Le provider vise le serveur Vault de developpement demarre par dsoxlab
# (runtime.services). Jeton racine `root` du mode dev, adresse locale. Bloc
# complet : rien a modifier ici, l'exercice porte sur la ressource.
provider "vault" {
  address          = "http://127.0.0.1:8200"
  token            = "root"
  skip_child_token = true
}
