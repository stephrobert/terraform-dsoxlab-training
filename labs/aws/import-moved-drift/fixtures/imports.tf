# Une instance EC2 existe deja. Elle a ete creee A LA MAIN, hors Terraform, et
# porte les tags `Name = legacy-billing-api` et `Owner = finops`.
#
# Retrouvez son identifiant vous-meme :
#
#   aws --endpoint-url http://localhost:14566 ec2 describe-instances \
#       --filters 'Name=tag:Name,Values=legacy-billing-api' \
#                 'Name=instance-state-name,Values=running' \
#       --query 'Reservations[].Instances[].InstanceId' --output text
#
# Personne ne vous tendra cet identifiant dans un fichier : le retrouver EST la
# premiere etape d'un import.

# 1. Le bloc d'import. `to` designe l'adresse Terraform cible, `id` l'objet reel.
#
#    Un bloc `import` est DECLARATIF : il ne fait rien tant qu'un apply ne l'a
#    pas joue. Un `plan` seul n'ecrit rien dans le state.
import {
  to = ???
  id = ???
}

# 2. La ressource. A ECRIRE, pas a recopier.
#
#    `terraform plan -generate-config-out` sait produire un squelette, et il
#    produit TROP : des arguments que l'API rend et que la configuration n'a pas
#    a porter. Tant qu'ils sont la, le plan n'est jamais vide, et l'import n'est
#    pas termine.
#
#    Le vrai critere de reussite d'un import n'est pas « la ressource est dans
#    le state » : c'est « un plan ordinaire ne propose plus rien ».
