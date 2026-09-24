# Le bareme. FOURNI, A NE PAS MODIFIER.
#
# Il ne contient AUCUNE reponse en clair : seulement l'empreinte sha256 salee de
# chacune. Les tests comparent la table d'empreintes a celle qu'ils detiennent,
# donc un bareme retouche se voit.
#
# Ce que cela protege : lire les reponses en ouvrant un fichier.
# Ce que cela ne protege pas : les retrouver. Le sel est juste en dessous, et
# une question a choix unique n'a que quatre reponses possibles. Aucun bareme
# local ne peut faire mieux, et ce lab prefere le dire.

variable "reponses" {
  type        = map(string)
  description = "Vos reponses, une par question, posees dans reponses.auto.tfvars."
}

locals {
  sel = "dsoxlab-mock-004"

  objectif_de = {
    q01 = "1a"
    q02 = "1b"
    q03 = "2a"
    q04 = "2a"
    q05 = "2b"
    q06 = "2d"
    q07 = "3b"
    q08 = "3c"
    q09 = "3c"
    q10 = "3d"
    q11 = "3e"
    q12 = "3f"
    q13 = "3g"
    q14 = "4a"
    q15 = "4b"
    q16 = "4c"
    q17 = "4c"
    q18 = "4d"
    q19 = "4d"
    q20 = "4e"
    q21 = "4e"
    q22 = "4f"
    q23 = "4g"
    q24 = "4h"
    q25 = "5a"
    q26 = "5b"
    q27 = "5c"
    q28 = "5d"
    q29 = "6a"
    q30 = "6b"
    q31 = "6c"
    q32 = "6d"
    q33 = "6d"
    q34 = "7a"
    q35 = "7c"
    q36 = "8c"
    q37 = "7b"
    q38 = "7b"
    q39 = "7b"
    q40 = "4h"
  }

  empreinte_de = {
    q01 = "57f65c245f4b8210e774db13d0fb9b13bfe23473024d6195f8cedca821a4dbd1"
    q02 = "205c35dae3f4ac3b68e809798d9e68dac3b99bf416f4e2e507866a5fa5ac5134"
    q03 = "57f65c245f4b8210e774db13d0fb9b13bfe23473024d6195f8cedca821a4dbd1"
    q04 = "57f65c245f4b8210e774db13d0fb9b13bfe23473024d6195f8cedca821a4dbd1"
    q05 = "cc9000fdde8e315da7ebca31d258df856ac4cd2bd0c1eed6be8476da2fd514b1"
    q06 = "57f65c245f4b8210e774db13d0fb9b13bfe23473024d6195f8cedca821a4dbd1"
    q07 = "57f65c245f4b8210e774db13d0fb9b13bfe23473024d6195f8cedca821a4dbd1"
    q08 = "cc9000fdde8e315da7ebca31d258df856ac4cd2bd0c1eed6be8476da2fd514b1"
    q09 = "57f65c245f4b8210e774db13d0fb9b13bfe23473024d6195f8cedca821a4dbd1"
    q10 = "4f63cc0938d249ffd0bab51de411d30b0dadb55914ba665a58a12ce553a6c460"
    q11 = "0929f95519a034b10f9d9bd3db77263e1118d583ab75667b53cafc90d5a056f2"
    q12 = "cc9000fdde8e315da7ebca31d258df856ac4cd2bd0c1eed6be8476da2fd514b1"
    q13 = "4f63cc0938d249ffd0bab51de411d30b0dadb55914ba665a58a12ce553a6c460"
    q14 = "57f65c245f4b8210e774db13d0fb9b13bfe23473024d6195f8cedca821a4dbd1"
    q15 = "fda8f9f1153d1dfca1ed939fd120f7af992c15809f6ebee7913c501af05b13ef"
    q16 = "8044b1d7aed67b69b660b3ca3fddaedfb6737e9483956ff73cb546c475b8ba30"
    q17 = "57f65c245f4b8210e774db13d0fb9b13bfe23473024d6195f8cedca821a4dbd1"
    q18 = "57f65c245f4b8210e774db13d0fb9b13bfe23473024d6195f8cedca821a4dbd1"
    q19 = "cc9000fdde8e315da7ebca31d258df856ac4cd2bd0c1eed6be8476da2fd514b1"
    q20 = "4f63cc0938d249ffd0bab51de411d30b0dadb55914ba665a58a12ce553a6c460"
    q21 = "4f63cc0938d249ffd0bab51de411d30b0dadb55914ba665a58a12ce553a6c460"
    q22 = "57f65c245f4b8210e774db13d0fb9b13bfe23473024d6195f8cedca821a4dbd1"
    q23 = "a958423a90cc5a2b28b58a06882545d92c47a2780d9ddd8c7cfaa7321c9be542"
    q24 = "57f65c245f4b8210e774db13d0fb9b13bfe23473024d6195f8cedca821a4dbd1"
    q25 = "0929f95519a034b10f9d9bd3db77263e1118d583ab75667b53cafc90d5a056f2"
    q26 = "cc9000fdde8e315da7ebca31d258df856ac4cd2bd0c1eed6be8476da2fd514b1"
    q27 = "57f65c245f4b8210e774db13d0fb9b13bfe23473024d6195f8cedca821a4dbd1"
    q28 = "57f65c245f4b8210e774db13d0fb9b13bfe23473024d6195f8cedca821a4dbd1"
    q29 = "fda8f9f1153d1dfca1ed939fd120f7af992c15809f6ebee7913c501af05b13ef"
    q30 = "57f65c245f4b8210e774db13d0fb9b13bfe23473024d6195f8cedca821a4dbd1"
    q31 = "cc9000fdde8e315da7ebca31d258df856ac4cd2bd0c1eed6be8476da2fd514b1"
    q32 = "0929f95519a034b10f9d9bd3db77263e1118d583ab75667b53cafc90d5a056f2"
    q33 = "57f65c245f4b8210e774db13d0fb9b13bfe23473024d6195f8cedca821a4dbd1"
    q34 = "cc9000fdde8e315da7ebca31d258df856ac4cd2bd0c1eed6be8476da2fd514b1"
    q35 = "57f65c245f4b8210e774db13d0fb9b13bfe23473024d6195f8cedca821a4dbd1"
    q36 = "57f65c245f4b8210e774db13d0fb9b13bfe23473024d6195f8cedca821a4dbd1"
    q37 = "5fa19c3947458525e6e91a9eda33a6270f0f962f68e7a73f4a632a537feeecfc"
    q38 = "8e1b22d44bc66a5c29d786b16e1d1d33ecc0dcafe771d16636afbb2ec160a3a1"
    q39 = "a458bde1f32e825f27124275219e52e785a72d06ed5e8a6ef2f2a612de2ae515"
    q40 = "fda8f9f1153d1dfca1ed939fd120f7af992c15809f6ebee7913c501af05b13ef"
  }

  # La casse et les espaces ne doivent pas faire echouer une bonne reponse.
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

  numeros = distinct(sort([for q, o in local.objectif_de : substr(o, 0, 1)]))

  score_par_objectif = {
    for n in local.numeros : n => floor(
      100 * length([for q, o in local.objectif_de : q if substr(o, 0, 1) == n && local.corrige[q]])
      / length([for q, o in local.objectif_de : q if substr(o, 0, 1) == n])
    )
  }
}

output "corrige" {
  description = "Une reponse juste ou fausse par question."
  value       = local.corrige
}

output "score" {
  description = "Le score global, en pourcentage."
  value       = floor(100 * local.justes / local.total)
}

output "score_par_objectif" {
  description = "Le score, en pourcentage, pour chacun des huit objectifs."
  value       = local.score_par_objectif
}

output "sans_reponse" {
  description = "Les questions laissees sans reponse, triees."
  value       = local.sans_reponse
}

output "empreintes" {
  description = "La table d'empreintes, pour que les tests detectent un bareme retouche."
  value       = local.empreinte_de
}
