# A COMPLETER : deux `???`.
#
# La question a laquelle cette configuration doit repondre : sur UN workspace
# donne, quel acces chacune de ces six equipes detient-elle reellement ?
#
# L'intuition ordinaire est celle d'une liste de controle d'acces : le niveau le
# plus SPECIFIQUE l'emporte, donc le workspace ecrase le projet, qui ecrase
# l'organisation. HCP Terraform ne fonctionne pas ainsi, et c'est tout l'objet
# de ce lab. La documentation le dit en une phrase :
#
#   « Each permission is additive, granting a user the highest level of
#     permissions possible, regardless of which scope set that permission. »
#
# Les deux exemples qu'elle donne suffisent a fixer la regle :
#
#   - `Manage all workspaces` au niveau organisation, avec `Read` sur un
#     workspace, donne `Manage all workspaces` SUR CE WORKSPACE ;
#   - `View all workspaces` au niveau organisation n'ecrase PAS un `Write` pose
#     sur un workspace.
#
# L'echelle ci-dessous est donnee complete, et elle reunit les trois
# vocabulaires. Deux details y meritent un regard, parce qu'ils se mesurent et
# ne se devinent pas :
#
#   - un workspace connait `plan`, entre `lecture` et `ecriture` ; un projet ne
#     le connait pas ;
#   - un projet connait `maintenance`, entre `ecriture` et `administration` ; un
#     workspace ne le connait pas.

locals {
  # Du moins permissif au plus permissif. `vue_de_tous_les_workspaces` vaut une
  # lecture, et `gestion_de_tous_les_workspaces` est le niveau le plus large
  # qu'une equipe puisse detenir.
  echelle = [
    "aucun",
    "lecture",
    "plan",
    "ecriture",
    "maintenance",
    "administration",
    "gestion_de_tous_les_workspaces",
  ]

  # Ce que vaut une permission d'organisation sur l'echelle commune.
  equivalences = {
    aucun                          = "aucun"
    vue_de_tous_les_workspaces     = "lecture"
    gestion_de_tous_les_workspaces = "gestion_de_tous_les_workspaces"
  }
}

output "acces_effectif" {
  description = "L'acces dont chaque equipe dispose reellement sur le workspace."

  # A COMPLETER : une regle, pas une liste de reponses. Aucune cle d'equipe ne
  # doit apparaitre ici, et une septieme equipe doit etre traitee sans rien
  # reecrire.
  value = ???
}

output "equipes_qui_peuvent_appliquer" {
  description = "Les equipes qui peuvent lancer un apply, triees."

  # A COMPLETER : une liste triee.
  #
  # Appliquer demande au moins l'ecriture. Une equipe qui en reste au plan peut
  # proposer un changement, jamais le poser : c'est la separation qui rend le
  # role `plan` utile, et c'est le seul endroit de ce lab ou la position exacte
  # de `plan` dans l'echelle compte.
  value = ???
}
