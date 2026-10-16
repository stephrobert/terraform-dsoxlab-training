# LE SEUL FICHIER À REMPLIR. Cinq réponses.
#
# Les valeurs ci-dessous sont des PLACEHOLDERS qui s'appliquent : ce fichier est
# un `*.auto.tfvars`, donc chargé automatiquement, et une valeur qui ne parse
# pas empêcherait `terraform apply` de tourner. Or il faut appliquer AVANT de
# pouvoir chercher : sans state, il n'y a ni ressources ni identifiants.
#
# L'ordre est donc :
#   1. terraform init && terraform apply    (avec les placeholders ci-dessous)
#   2. terraform output                      (les trois identifiants à résoudre)
#   3. terraform state list                  (les adresses réelles)
#   4. remplacer chaque placeholder par votre réponse, puis `dsoxlab check`
#
# Les adresses s'écrivent exactement comme `terraform state list` les affiche,
# crochets, guillemets et préfixe de module compris.

# Adresse de l'instance de random_pet.worker dont l'id vaut id_worker_recherche.
# Indexée par position.
adresse_worker = "???"

# Adresse de l'instance de random_pet.service dont l'id vaut
# id_service_recherche. Indexée par clé.
adresse_service = "???"

# Adresse de l'archive dont l'id vaut id_archive_recherche. Elle vit dans un
# module : l'adresse complète est attendue.
adresse_archive = "???"

# Adresse complète de la data source déclarée dans modules/stockage/.
# Attention : ce n'est pas une adresse qui commence par « data ».
adresse_data_module = "???"

# Nombre d'instances en mode managed dans le state, modules inclus, data
# sources exclues. Un nombre, sans guillemets. Zéro vaut « pas répondu ».
nombre_managees = 0
