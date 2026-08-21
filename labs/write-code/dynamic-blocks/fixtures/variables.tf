variable "modules" {
  description = "Modules cloud-init. À ne pas modifier."
  type = map(object({
    contenu = string
    actif   = bool
  }))
  default = {
    paquets = { contenu = "packages:\n  - htop\n", actif = true }
    users   = { contenu = "users:\n  - name: ops\n", actif = true }
    debug   = { contenu = "runcmd:\n  - echo debug\n", actif = false }
  }
}
