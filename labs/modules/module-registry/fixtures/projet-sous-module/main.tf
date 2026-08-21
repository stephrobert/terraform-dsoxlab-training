# Ce projet ne passe PAS par le registre : il vise le sous-repertoire `exports`
# du depot GitHub `cloudposse/terraform-null-label`, fige sur le tag `0.25.0`.
#
# Trois choses composent cette adresse : le raccourci GitHub du depot, le
# sous-repertoire, et la revision. L'ordre de ces deux dernieres parties n'est
# pas libre : l'une doit venir avant l'autre, sinon le telechargement echoue.
#
# Ce projet s'initialise seulement, il ne s'applique jamais.
module "exports" {
  source = "???"
}
