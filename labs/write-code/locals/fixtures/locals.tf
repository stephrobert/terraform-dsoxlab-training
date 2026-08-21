# Trois blocs locals distincts, volontairement. Terraform les fusionne : un
# local d'un bloc peut en référencer un autre déclaré ailleurs.

locals {
  # ??? project en minuscules, les underscores changés en tirets.
  slug = ???
  # ??? slug et environment, joints par un tiret. Un local qui en référence un autre.
  base_name = ???
}

locals {
  # ??? vrai seulement si environment vaut "prod".
  is_production = ???
  # ??? PIÈGE : la mémoire DOUBLÉE en prod, sinon la valeur de la variable.
  #     Les deux branches doivent rester des NOMBRES. Terraform convertit sans
  #     broncher un mélange nombre/chaîne vers une chaîne : ne mettez pas de
  #     guillemets autour d'un nombre.
  effective_ram = ???
  # ??? base_name suffixé -001, -002, ... sur node_count (trois chiffres).
  #     Une expression for et la fonction format.
  node_names = ???
}

locals {
  # ??? les 8 premiers caractères de random_id.build.hex. Dérivé d'une ressource,
  #     donc INCONNU au plan.
  build_digest = ???
  # ??? base_name, un tiret, build_digest, puis l'extension .json.
  manifest_name = ???
  # ??? postgres://app:<db_password>@localhost/<base_name>.
  #     Hérite de la sensibilité de var.db_password.
  db_dsn = ???
}
