# LE SEUL FICHIER A REMPLIR. Cinq ???, cinq reponses.
#
# Appliquez d'abord (terraform init && terraform apply), sans quoi il n'y a ni
# state ni identifiants a chercher. Puis interrogez le state pour resoudre
# chaque identifiant publie vers l'ADRESSE de l'instance qui le porte.
#
# Les adresses s'ecrivent exactement comme `terraform state list` les affiche,
# crochets, guillemets et prefixe de module compris.

# Adresse de l'instance de random_pet.worker dont l'id vaut id_worker_recherche.
# Indexee par position.
adresse_worker = ???

# Adresse de l'instance de random_pet.service dont l'id vaut
# id_service_recherche. Indexee par cle.
adresse_service = ???

# Adresse de l'archive dont l'id vaut id_archive_recherche. Elle vit dans un
# module : l'adresse complete est attendue.
adresse_archive = ???

# Adresse complete de la data source declaree dans modules/stockage/.
# Attention : ce n'est pas une adresse qui commence par « data ».
adresse_data_module = ???

# Nombre d'instances en mode managed dans le state, modules inclus, data
# sources exclues. Un nombre, sans guillemets.
nombre_managees = ???
