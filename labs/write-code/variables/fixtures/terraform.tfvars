env            = "dev"
retention_days = null

nodes = {
  web = { size = "small" }
  db  = { size = "large", replicas = 2, public = true }
}
