# Scenario: the configuration that refuses absurd values

**Exam objective targeted: 2a (validate the configuration), supported by 2c for conditional expressions.**

The reference guide teaches only one of Terraform's four validation mechanisms, the variables' `validation` block. This lab restores all four and puts the score on what separates them: the moment each one runs, and the fact that only one of them warns without blocking.

## Capability targeted

Make a configuration self-defending: compute values with conditional expressions, then prevent an absurd value from reaching the infrastructure, by placing each check at the right level. The central trap is believing `validation` covers everything: a `validation` block only lives on an input variable and can therefore say nothing about a **computed** value. Checking a ternary's result requires a `precondition`. Second trap: a failing `check` stops nothing, it emits a warning and the `apply` exits with code 0.

## Where the learner starts

`challenge/work/` holds an incomplete project, with no VM and no network: only `hashicorp/local` is used, with a `terraform init` and a `.terraform.lock.hcl` already in place. `versions.tf` is correct and imposes `required_version = ">= 1.9.0"`, the version from which a validation condition may reference another variable. `variables.tf`, `main.tf` and `outputs.tf` are holed:

```hcl
variable "environment" { }          # string, default "dev", accept only dev, staging, prod
variable "backup_bucket" { }        # string, default "", mandatory IF environment is prod
variable "enable_second_disk" { }   # bool, default false
variable "memory_mib_override" { }  # number, nullable, default null
locals {
  memory_mib       = ???            # override, otherwise 2048 in prod, 512 elsewhere
  vcpu             = ???            # 4 in prod, 2 in staging, 1 elsewhere
  second_disk_name = ???            # "<name>-data.qcow2" if the flag is true, null otherwise
}
resource "local_file" "manifest" {
  filename = "${path.module}/manifest.json"
  content  = ???                    # JSON carrying at least env, memory_mib, vcpu
  lifecycle {
    precondition  { ??? }           # refuse less than 256 MiB per vCPU
    postcondition { ??? }           # the content must be JSON carrying an env key
  }
}
check "budget_prod" { ??? }         # warn if memory_mib exceeds 1024
```

`terraform plan` fails as it stands: the `???` are not valid HCL.

## The state to reach

1. `environment` rejects any value outside `dev`, `staging`, `prod`, before the plan is even generated.
2. `backup_bucket` is refused empty when `environment` is `prod`, and accepted empty otherwise: the condition references **another** variable, which requires Terraform 1.9 or later.
3. `local.memory_mib` is 512 in `dev`, 2048 in `prod`, and gives way to `memory_mib_override` as soon as that is not `null`. `local.vcpu` is 1, 2 or 4 depending on the environment.
4. `local.second_disk_name` is `null` when the flag is false. The matching output then **disappears**, instead of being `null`.
5. The `precondition` on `local_file.manifest` blocks the plan as soon as the memory per vCPU ratio falls below 256 MiB, a case unreachable by a `validation` since both terms are `locals`.
6. The `postcondition` reads `self.content` back after writing and requires JSON carrying an `env` key.
7. The `check` block fails in `prod` and that is intended: the `apply` must succeed in spite of it.
8. The project converges: a second plan right after the apply proposes nothing.

## How it is proven

The tests never open the learner's `.tf` files and read no human message. They run Terraform inside `challenge/work` and use only JSON and exit codes.

1. `terraform show -json` after the apply exposes a top-level `checks` array. The tests check four addresses are present with their `status`: `var.environment` and `var.backup_bucket` under `kind: var`, `local_file.manifest` under `kind: resource`, `check.budget_prod` under `kind: check`. A missing `kind` proves a mechanism was not written.
2. `terraform plan -var 'environment=qa'` exits non-zero. Likewise for `-var 'environment=prod' -var 'backup_bucket='`, whereas `-var 'environment=dev' -var 'backup_bucket='` exits 0: the cross-variable validation is indeed conditional.
3. `terraform output -json`: `memory_mib` and `vcpu` hold the expected pair for each environment tested.
4. `terraform output -json` with `enable_second_disk=false`: the `second_disk_name` key is **absent** from the document. The test fails if the key exists with a null value. With `true`, the key is present and non-empty.
5. `terraform plan -var 'memory_mib_override=64'` exits non-zero, although that value violates no variable constraint: only a `precondition` can produce that refusal.
6. `terraform show -json`: the `local_file.manifest` resource is in `mode: managed`, and its `content` attribute decodes to JSON carrying `env`, `memory_mib` and `vcpu`. The postcondition is therefore satisfied on data actually written.
7. The decisive rung: `terraform apply -auto-approve -var 'environment=prod' -var 'backup_bucket=lab-backup'` exits with **code 0** while `checks` marks `check.budget_prod` as `fail`. Blocking and non-blocking are separated by proof, not by reading.
8. `terraform plan -detailed-exitcode` returns 0 right after the apply. A code 2 fails the lab, including when the plan announces zero changes: putting a `data` source inside the `check` block makes it re-read on every plan and is enough to bring back a 2. The assertion must bear on an already known value.
