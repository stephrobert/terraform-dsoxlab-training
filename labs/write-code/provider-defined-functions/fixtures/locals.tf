locals {
  # Les fonctions du provider integre s'appellent provider::tfcore::<fonction>
  # (le nom local tfcore vient de versions.tf). Celles du provider local
  # s'appellent provider::local::<fonction>.

  # ??? n1 : decoder le fichier tfvars amont en OBJET. La fonction inverse de
  #          l'encodage tfvars restitue les TYPES (un nombre reste un nombre).
  #          L'entree se lit avec file("${path.module}/amont.tfvars.txt").
  config = ???

  # ??? n2 : re-encoder config en syntaxe tfvars APRES y avoir ajoute
  #          environment = "prod" (indice : merge(local.config, { ... })).
  aval = ???

  # ??? n3 : produire la representation en syntaxe d'EXPRESSION Terraform de la
  #          liste config.zones (pas du JSON compact).
  zones_expr = ???

  # ??? n4 : la fonction direxists du provider `local` sur path.module, qui
  #          existe.
  dir_present = ???

  # ??? n5 : la meme fonction sur un chemin qui n'existe pas
  #          (ex. "${path.module}/nexiste-pas").
  dir_absent = ???
}
