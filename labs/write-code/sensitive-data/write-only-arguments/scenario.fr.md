# Scénario : le secret qui n'atterrit jamais dans le state

**Sous-objectif d'examen visé : 2f (gérer les données sensibles), niveau Professional.**

`sensitive` masque l'affichage mais laisse le secret **en clair dans le state**. Un argument **write-only**, lui, transmet la valeur au provider sans jamais l'écrire dans le state. L'apprenant doit stocker un secret dans un paramètre SSM en s'assurant qu'il ne fuite **nulle part** dans le fichier d'état.

## Capacité visée

Convertir un argument ordinaire en sa variante **write-only** (`_wo`), comprendre que cette variante forme un **couple obligatoire** avec un numéro de version (`_wo_version`), que seul ce numéro est persisté et qu'il pilote le renvoi de la valeur au service. Distinguer un argument write-only d'un argument ordinaire, qui, lui, écrit le secret en clair dans le state.

## D'où part l'apprenant

`challenge/work/` contient un projet incomplet qui vise **Floci**, un émulateur AWS local écoutant sur `http://localhost:14566`. Sous `dsoxlab run`, Floci est démarré automatiquement par le mécanisme `runtime.services` du lab : aucune commande Docker à taper, aucun compte AWS, aucune facture.

Sont **complets** : `versions.tf` (provider `hashicorp/aws` en `~> 6.0`), `providers.tf` (identifiants factices, `endpoints` vers Floci, `skip_*`), `variables.tf`, `terraform.tfvars` (qui fournit la valeur du secret) et `outputs.tf`. Seul `main.tf` est troué :

```hcl
resource "aws_ssm_parameter" "jeton_api" {
  name = var.param_name
  type = "SecureString"

  ??? = var.secret_api   # transmettre le secret SANS l'ecrire dans le state
  ??? = 1                # le numero de version qui accompagne obligatoirement
}
```

`terraform apply` échoue en l'état : les `???` ne sont pas du HCL valide.

## L'état à atteindre

1. Le secret est transmis par un argument **write-only** (`_wo`) : après l'apply, sa valeur vaut `null` dans le state, jamais la chaîne réelle.
2. L'argument de **version** (`_wo_version`) est fourni, à `1` : c'est lui, et lui seul, qui est persisté dans le state.
3. La valeur du secret n'apparaît **nulle part** dans `terraform.tfstate`. C'est toute la promesse du write-only : un argument ordinaire (`value`) l'y écrirait en clair.
4. Le projet converge : un second plan juste après l'apply ne propose plus rien, tant que le numéro de version ne change pas.

## Comment on le prouve

Les tests n'ouvrent jamais les `.tf` de l'apprenant et ne parsent aucune sortie humaine. Ils lancent Terraform dans `challenge/work` contre Floci et ne lisent que du JSON, le fichier d'état brut, ou des codes retour.

1. `terraform show -json` : il y a **exactement un** `aws_ssm_parameter`, et son `value_wo` vaut `null`. Une valeur non nulle trahirait un argument ordinaire, donc un secret persisté.
2. Le fichier `terraform.tfstate` brut ne contient **pas** la valeur sentinelle du secret. C'est la preuve directe de non-fuite.
3. `terraform show -json` et `terraform output -json` : `value_wo_version` vaut `1`, présent dans le state.
4. `terraform plan -detailed-exitcode` retourne 0 juste après l'apply.

Référence : https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/gestion-donnees-sensibles/write-only-arguments/
