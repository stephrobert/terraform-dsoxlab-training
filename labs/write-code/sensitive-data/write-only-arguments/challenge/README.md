# 🎯 Challenge: the secret that never touches the state

## ✅ Objective

In `challenge/work`, complete `main.tf` so that the SSM parameter
`aws_ssm_parameter.jeton_api` receives the secret **without ever writing it into
the Terraform state**. The provider already points at Floci (a local AWS
emulator, started on its own), everything else is provided: only the resource
needs completing.

Two `???` to replace, forming a pair:

```hcl
resource "aws_ssm_parameter" "jeton_api" {
  name = var.param_name
  type = "SecureString"

  ??? = var.secret_api   # pass the value WITHOUT persisting it
  ??? = 1                # the version number, mandatory with the first
}
```

Reminder: an ordinary argument `value = var.secret_api` would write the secret in
clear text into `terraform.tfstate`. That is not what we want.

## 🔍 Validation

`dsoxlab check write-code-sensitive-data-write-only-arguments` starts
Floci, applies the configuration, and proves on the JSON and on the state file
that:

- `value_wo` is `null` in the state (the value never round-trips);
- the secret value appears **nowhere** in `terraform.tfstate`;
- `value_wo_version` is `1`, present in the state;
- the configuration is idempotent (a second plan proposes nothing).

Stuck? `dsoxlab hint write-code-sensitive-data-write-only-arguments`.
