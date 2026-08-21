# La version write-only de la copie. Seul son changement declenche la
# reecriture du secret dans la replique.
variable "copie_version" {
  type    = number
  default = 1
}
