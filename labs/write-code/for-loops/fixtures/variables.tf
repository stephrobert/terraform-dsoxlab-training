variable "serveurs" {
  description = "Catalogue de serveurs. À ne pas modifier."
  type = map(object({
    env        = string
    role       = string
    memoire_mo = number
    actif      = bool
    tags       = list(string)
  }))
  default = {
    web1  = { env = "prod", role = "frontend", memoire_mo = 512, actif = true, tags = ["dmz", "prod"] }
    web2  = { env = "prod", role = "frontend", memoire_mo = 512, actif = false, tags = ["dmz"] }
    api   = { env = "prod", role = "backend", memoire_mo = 1024, actif = true, tags = ["prod"] }
    db    = { env = "prod", role = "backend", memoire_mo = 2048, actif = true, tags = [] }
    cache = { env = "staging", role = "backend", memoire_mo = 256, actif = true, tags = ["staging"] }
    ci    = { env = "dev", role = "tooling", memoire_mo = 512, actif = true, tags = ["dev"] }
  }
}
