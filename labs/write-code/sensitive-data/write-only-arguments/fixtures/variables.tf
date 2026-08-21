variable "aws_region" {
  type    = string
  default = "eu-west-3"
}

# Adresse de Floci. Le service SSM y est redirige par le bloc endpoints.
variable "floci_endpoint" {
  type    = string
  default = "http://localhost:4566"
}

variable "param_name" {
  type    = string
  default = "/lab/jeton-api"
}

# Le secret a stocker dans SSM. sensitive pour qu'il n'apparaisse pas dans les
# logs de plan/apply. Sa valeur est fournie par terraform.tfvars.
variable "secret_api" {
  type      = string
  sensitive = true
}
