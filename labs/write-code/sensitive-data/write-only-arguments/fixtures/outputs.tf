output "param_name" {
  value = aws_ssm_parameter.jeton_api.name
}

# Le numero de version write-only EST persiste dans le state (contrairement a
# la valeur elle-meme) : c'est lui qui dit a Terraform quand renvoyer le secret.
output "value_wo_version" {
  value = aws_ssm_parameter.jeton_api.value_wo_version
}
