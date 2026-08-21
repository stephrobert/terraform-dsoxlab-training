locals {
  compose   = var.suffixe == "" ? var.prefixe : "${var.prefixe}-${var.suffixe}"
  etiquette = var.majuscules ? upper(local.compose) : local.compose
}
