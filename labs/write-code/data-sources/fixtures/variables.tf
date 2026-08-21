variable "revision" {
  description = "Révision fonctionnelle. La faire bouger met la ressource gérée en changement, ce qui décale le moment de lecture des data sources qui en dépendent."
  type        = number
  default     = 1
}
