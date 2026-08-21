# Ce que vous avez OBSERVE, pas ce que vous avez lu quelque part.
#
# Les tests refont l'experience : ils lancent un apply, attendent le verrou,
# relevent eux memes les codes de retour, puis comparent leurs mesures a ces
# valeurs. Une reponse recopiee d'un article qui se trompe ressort ici en rouge.

output "fichier_verrou" {
  description = "Chemin du fichier de verrou observe, relatif a la racine du projet."
  # ??? : le nom n'est pas fixe, il se derive du chemin du state.
  value = ???
}

output "codes_pendant_verrou" {
  description = "Code de retour de chaque geste tente PENDANT qu'un verrou est tenu."
  # ??? : un entier par geste. 0 = la commande a abouti, 1 = elle a ete rejetee.
  value = {
    plan            = ???
    apply           = ???
    plan_lock_false = ???
    force_unlock    = ???
    state_list      = ???
    show_json       = ???
  }
}

output "verrou_residuel" {
  description = "Sort d'un fichier de verrou laisse sur le disque par un arret brutal."
  # ??? : code de retour du plan relance alors que le fichier traine encore,
  # et presence de ce fichier APRES ce plan (true ou false).
  value = {
    plan_rc          = ???
    fichier_subsiste = ???
  }
}

output "backend_s3" {
  description = "Verrouillage natif du backend S3, tel que documente."
  # ??? : le nom de l'argument, s'il est actif sans rien configurer (true ou
  # false), et le statut du verrouillage par table DynamoDB (true si deprecie).
  value = {
    argument          = ???
    actif_par_defaut  = ???
    dynamodb_deprecie = ???
  }
}
