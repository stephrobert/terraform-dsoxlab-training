variable "services" {
  type    = list(string)
  default = ["web", "cache", "db"]
}
