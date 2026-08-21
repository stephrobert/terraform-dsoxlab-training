# 🎯 Challenge : le secret qui ne touche jamais le state

## ✅ Objectif

Dans `challenge/work`, complétez `main.tf` pour que le paramètre SSM
`aws_ssm_parameter.jeton_api` reçoive le secret **sans jamais l'écrire dans le
state Terraform**. Le provider vise déjà Floci (émulateur AWS local, démarré tout
seul), tout le reste est fourni : seule la ressource est à compléter.

Deux `???` à remplacer, qui forment un couple :

```hcl
resource "aws_ssm_parameter" "jeton_api" {
  name = var.param_name
  type = "SecureString"

  ??? = var.secret_api   # transmettre la valeur SANS la persister
  ??? = 1                # le numero de version, obligatoire avec le premier
}
```

Rappel : un argument ordinaire `value = var.secret_api` écrirait le secret en
clair dans `terraform.tfstate`. Ce n'est pas ce qu'on veut.

## 🔍 Validation

`dsoxlab check write-code-sensitive-data-write-only-arguments`
démarre Floci, applique la configuration, et prouve sur le JSON et sur le fichier
d'état que :

- `value_wo` vaut `null` dans le state (la valeur ne round-trip jamais) ;
- la valeur du secret n'apparaît **nulle part** dans `terraform.tfstate` ;
- `value_wo_version` vaut `1`, bien présent dans le state ;
- la configuration est idempotente (un second plan ne propose rien).

Bloqué ? `dsoxlab hint write-code-sensitive-data-write-only-arguments`.
