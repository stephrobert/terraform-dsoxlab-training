# Le bareme. FOURNI, A NE PAS MODIFIER.
#
# Il ne contient AUCUNE reponse en clair : seulement l'empreinte sha256 salee
# de chacune.
#
# Ce que cela protege : lire les reponses en ouvrant un fichier.
# Ce que cela ne protege pas : les retrouver. Le sel est juste en dessous, et
# une question a choix unique n'a que quatre reponses possibles. Le dispositif
# demande un effort deliberé, il n'empeche pas la triche : un examen blanc
# qu'on triche ne mesure que la volonte de se mentir.

variable "reponses" {
  description = "Les douze reponses de la tache 6."
  type        = map(string)
}

locals {
  sel = "dsoxlab-mock-pro"

  objectif_de = {
    q01 = "6a"
    q02 = "6a"
    q03 = "6a"
    q04 = "6a"
    q05 = "6b"
    q06 = "6b"
    q07 = "6b"
    q08 = "6b"
    q09 = "6c"
    q10 = "6c"
    q11 = "6c"
    q12 = "6d"
  }

  empreinte_de = {
    q01 = "48694d338ecc1eefd1ed64f0828c21698864e71b7ac75ffd63a227814c532513"
    q02 = "48694d338ecc1eefd1ed64f0828c21698864e71b7ac75ffd63a227814c532513"
    q03 = "7cffe56da09261a120a627178b337527657eb99d4c2d7bcf3880c199e5debb83"
    q04 = "efa9dacc5794488de380fa422650f32b704014e343ed2d1aa6eaf47609f7783d"
    q05 = "ad869ef9f2ff54154f1f3ba7a1601fa0e29c1ca11f5f3113b347b0daed05d94e"
    q06 = "ad869ef9f2ff54154f1f3ba7a1601fa0e29c1ca11f5f3113b347b0daed05d94e"
    q07 = "ad869ef9f2ff54154f1f3ba7a1601fa0e29c1ca11f5f3113b347b0daed05d94e"
    q08 = "48694d338ecc1eefd1ed64f0828c21698864e71b7ac75ffd63a227814c532513"
    q09 = "ad869ef9f2ff54154f1f3ba7a1601fa0e29c1ca11f5f3113b347b0daed05d94e"
    q10 = "48694d338ecc1eefd1ed64f0828c21698864e71b7ac75ffd63a227814c532513"
    q11 = "ad869ef9f2ff54154f1f3ba7a1601fa0e29c1ca11f5f3113b347b0daed05d94e"
    q12 = "ad869ef9f2ff54154f1f3ba7a1601fa0e29c1ca11f5f3113b347b0daed05d94e"
  }

  normalisee = { for q, v in var.reponses : q => lower(trimspace(v)) }

  sans_reponse = sort([
    for q, _ in local.empreinte_de : q
    if lookup(local.normalisee, q, "") == "" || lookup(local.normalisee, q, "") == "???"
  ])

  corrige = {
    for q, h in local.empreinte_de :
    q => sha256("${local.sel}:${lookup(local.normalisee, q, "")}") == h
  }

  justes = length([for q, ok in local.corrige : q if ok])
  total  = length(local.empreinte_de)

  sous_objectifs = distinct(sort([for q, o in local.objectif_de : o]))
}

output "corrige" {
  description = "Quelles questions sont justes."
  value       = local.corrige
}

output "score" {
  description = "Le score de la tache 6, sur 100."
  value       = floor(100 * local.justes / local.total)
}

output "score_par_sous_objectif" {
  description = "Ou se situe la faiblesse, sous-objectif par sous-objectif."

  value = {
    for o in local.sous_objectifs : o => floor(
      100 * length([for q, x in local.objectif_de : q if x == o && local.corrige[q]])
      / length([for q, x in local.objectif_de : q if x == o])
    )
  }
}

output "sans_reponse" {
  description = "Ce qui reste a remplir."
  value       = local.sans_reponse
}

output "empreintes" {
  description = "La table, exposee pour que les tests voient un bareme retouche."
  value       = local.empreinte_de
}
