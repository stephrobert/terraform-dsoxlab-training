# Les sorties RACINE de la stack plateforme.
#
# Une sortie de module imbrique n'est PAS lisible depuis une autre
# configuration : seules les sorties de la racine le sont. Ce qui doit
# traverser la frontiere se re-exporte donc ici, explicitement.
#
# A ecrire : `network_name` et `network_cidr`.
#
# Et ce qui ne doit PAS traverser n'a rien a faire ici.
