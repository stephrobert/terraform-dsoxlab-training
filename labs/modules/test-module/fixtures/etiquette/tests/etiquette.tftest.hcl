# Suite de tests du module `etiquette`, a completer.
#
# Elle s'execute depuis le repertoire du module : `terraform test` prend la
# configuration du repertoire courant, et les sorties du module s'y lisent
# directement par `output.<nom>`.
#
# Un bloc `variables` au niveau du fichier s'applique a TOUS les runs ; un bloc
# `variables` a l'interieur d'un run l'emporte pour ce run-la.

variables {
  prefixe = "atelier"
}

# 1. Sans rien de plus, l'etiquette doit valoir le prefixe seul, et sa longueur
#    doit correspondre.
run "???" {
  assert {
    condition     = ???
    error_message = "???"
  }

  assert {
    condition     = ???
    error_message = "???"
  }
}

# 2. Avec un suffixe, l'etiquette doit valoir `atelier-nord`.
run "???" {
  ???
}

# 3. En majuscules, l'etiquette doit valoir `ATELIER`.
run "???" {
  ???
}

# 4. Un prefixe trop court doit etre REFUSE par le module. Ce run ne doit rien
#    appliquer, et il doit declarer quel objet est attendu en echec.
run "???" {
  ???
}
