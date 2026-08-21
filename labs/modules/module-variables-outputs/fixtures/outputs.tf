# LES SORTIES DE LA RACINE, A ECRIRE.
#
# Elles republient ce que les modules exposent. L'une des deux transporte une
# valeur venue d'un `random_password` : Terraform refuse qu'une sortie racine
# expose une donnee sensible sans que ce soit dit.

# ??? : le `resume` de l'appel minimal.
output "resume_minimal" {
  ???
}

# ??? : le `secret` de l'appel complet.
output "secret_partage" {
  ???
}
