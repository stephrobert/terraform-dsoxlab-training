# 1. Designer le subnet « public » SANS jamais indexer une liste.
#    La documentation ne garantit aucun ordre des identifiants renvoyes par
#    `aws_subnets` : `ids[0]` n'est donc pas « le premier subnet », c'est un
#    tirage. Filtrez sur le tag.
data "aws_subnet" "retenu" {
  ???
}

# 2. Un security group SANS aucune regle inline.
#    Melanger les blocs `ingress` / `egress` et les ressources de regle dediees
#    produit des differences perpetuelles et des regles ecrasees.
resource "aws_security_group" "lab" {
  ???
}

# 3. Les trois flux de `var.flux_entrants`, par UN SEUL bloc.
#    Trois blocs copies-colles seraient refuses : c'est `for_each` qui est vise.
resource "aws_vpc_security_group_ingress_rule" "entrant" {
  ???
}

# 4. La sortie, explicitement.
#    Sans cette regle, l'instance ne peut joindre personne.
resource "aws_vpc_security_group_egress_rule" "sortant" {
  ???
}

# 5. L'instance, dans le subnet retenu, rattachee au groupe.
resource "aws_instance" "lab" {
  ami           = var.ami_id
  instance_type = var.instance_type
  ???
}
