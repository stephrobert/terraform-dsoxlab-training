# Ce fichier est charge AUTOMATIQUEMENT, sans aucune option.
#
# Il donne une valeur a env_name et a disk_size_gb, les deux variables qui
# n'ont pas de default. Consequence : `terraform plan` reussit sans qu'aucun
# environnement ait ete choisi, et le garde-fou voulu par variables.tf ne
# protege plus rien.
#
# Ce n'est pas une faute de frappe, c'est le constat de depart.

env_name     = "bac-a-sable"
disk_size_gb = 1
