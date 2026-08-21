# Remplacez chaque ??? par une expression de fonctions.
# Aucune valeur ne doit etre ecrite en dur : tout se derive des variables.

locals {
  # 1. Decouper le CSV en liste.
  environments = ???

  # 2. Collection DEDUPLIQUEE, utilisable comme source d'un for_each.
  #    Elle doit produire des cles d'instance, pas des index numeriques.
  env_uniques = ???

  # 3. Acces par POSITION, index 5, sur la liste TRIEE des environnements
  #    uniques. Attention au comportement hors bornes.
  env_recycle = ???

  # 4. Taille derivee de var.environment via cette table de correspondance :
  #      dev = "small", staging = "medium", prod = "large"
  #    var.environment vaut "qa", absent de la table : la lecture ne doit pas
  #    interrompre le plan, elle doit retomber sur "small".
  taille = ???

  # 5. Les tags du projet, auxquels on ajoute la cle `env` valant
  #    var.environment. En cas de collision, c'est `env` qui doit gagner.
  tags_effectifs = ???

  # 6. var.memory_mib convertie en Gio. 1536 Mio doivent donner 2, jamais 1.
  memory_gib = ???

  # 7. Encoder l'objet { env = <var.environment>, gib = <memory_gib> } au format
  #    tfvars, en appelant la fonction exposee par le provider integre.
  tfvars_rendu = ???
}
