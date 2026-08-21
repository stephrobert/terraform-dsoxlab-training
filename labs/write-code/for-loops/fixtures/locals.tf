locals {
  # ??? 1. Un tuple des NOMS (clés) des serveurs dont env vaut "prod".
  #        Crochets. L'ordre lexicographique est imposé par Terraform.
  noms_prod = ???

  # ??? 2. Un objet role => liste des noms portant ce rôle. Deux serveurs
  #        partagent un rôle : il faut GROUPER, pas écraser la clé.
  #        Accolades, et l'ellipsis après l'expression de valeur.
  par_role = ???

  # ??? 3. Un tuple des mémoires, UNE entrée par serveur. Six, pas un.
  #        Un tuple de longueur 1 trahirait un splat appliqué à la map.
  memoires = ???

  # ??? 4. Un tuple de chaînes "<serveur>:<tag>", une par couple existant.
  #        Deux niveaux à croiser, puis aplatir. Le serveur sans tag
  #        disparaît de lui-même.
  tags_plats = ???
}
