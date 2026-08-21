# Scenario: the secret that never lands in the state

**Target exam objective: 2f (manage sensitive data), Professional level.**

`sensitive` hides display but leaves the secret **in clear text in the state**. A **write-only** argument instead passes the value to the provider without ever writing it to the state. The learner must store a secret in an SSM parameter while making sure it leaks **nowhere** into the state file.

## Target capability

Convert an ordinary argument into its **write-only** variant (`_wo`), understand that this variant forms a **mandatory pair** with a version number (`_wo_version`), that only that number is persisted, and that it drives the re-send of the value to the service. Tell a write-only argument apart from an ordinary one, which writes the secret in clear text into the state.

## Where the learner starts

`challenge/work/` holds an incomplete project pointing at **Floci**, a local AWS emulator listening on `http://localhost:4566`. Under `dsoxlab run`, Floci is started automatically by the lab's `runtime.services` mechanism: no Docker command to type, no AWS account, no bill.

Complete already: `versions.tf` (`hashicorp/aws` provider at `~> 6.0`), `providers.tf` (fake credentials, `endpoints` to Floci, `skip_*`), `variables.tf`, `terraform.tfvars` (which supplies the secret value) and `outputs.tf`. Only `main.tf` has holes:

```hcl
resource "aws_ssm_parameter" "jeton_api" {
  name = var.param_name
  type = "SecureString"

  ??? = var.secret_api   # pass the secret WITHOUT writing it into the state
  ??? = 1                # the version number that must always come with it
}
```

`terraform apply` fails as is: the `???` are not valid HCL.

## The target state

1. The secret is passed by a **write-only** argument (`_wo`): after apply, its value is `null` in the state, never the real string.
2. The **version** argument (`_wo_version`) is supplied, at `1`: it, and only it, is persisted in the state.
3. The secret value appears **nowhere** in `terraform.tfstate`. That is the whole promise of write-only: an ordinary argument (`value`) would write it there in clear text.
4. The project converges: a second plan right after apply proposes nothing, as long as the version number does not change.

## How it is proven

The tests never open the learner's `.tf` files and never parse human output. They run Terraform in `challenge/work` against Floci and read only JSON, the raw state file, or return codes.

1. `terraform show -json`: there is **exactly one** `aws_ssm_parameter`, and its `value_wo` is `null`. A non-null value would betray an ordinary argument, hence a persisted secret.
2. The raw `terraform.tfstate` file does **not** contain the secret's sentinel value. That is the direct proof of non-leakage.
3. `terraform show -json` and `terraform output -json`: `value_wo_version` is `1`, present in the state.
4. `terraform plan -detailed-exitcode` returns 0 right after apply.

Reference: https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/gestion-donnees-sensibles/write-only-arguments/
