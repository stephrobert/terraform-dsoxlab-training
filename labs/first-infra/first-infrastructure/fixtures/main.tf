# A ecrire entierement.
#
# Le lab ne demande pas de reciter `init`, `plan`, `apply`, `destroy` : il
# demande de les DEROULER sur une ressource reelle, et de prouver chaque etape
# par l'etat structure.
#
# Ce qu'il faut declarer :
#
#   - le provider `libvirt`, en `qemu:///system` ;
#   - UNE ressource `libvirt_volume` nommee `tf-lab-premiere.qcow2`, dans le
#     pool `default`, au format `qcow2`, d'une capacite de 1 Gio ;
#   - un `output` exposant le chemin du volume sur l'hote, CALCULE depuis
#     l'attribut de la ressource et non ecrit en dur.
#
# Aucune image cloud a telecharger : le volume est cree vierge, et cela suffit
# a prouver le cycle.
