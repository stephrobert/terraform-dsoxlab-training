# Scenario: the config that works but no CI accepts

**Exam objective: 2a (validate the configuration), with a spillover to 2e for typing variables and outputs.**

A style guide is not something you re-read, it is something a CI rejects. This lab tackles the guide's inverse trap: file names change nothing in Terraform's behavior, so checking them proves nothing. What proves is the exit code of `terraform fmt -check` and the JSON of `terraform validate`.

## Target capability

Take a working but non-conforming Terraform configuration, make it pass `terraform fmt`, fix the internal inconsistency that breaks `terraform validate`, rename resources per the official convention, type and document variables and outputs, mark sensitive values, and write a correct `.gitignore`, without changing a single one of the resources created.

## Where the learner starts

`challenge/work/` holds a single-file project, `infra.tf`. No VM, no remote account: only `hashicorp/local` and `hashicorp/random` are used, with `terraform init` already in place. The lab runs anywhere `terraform` is on the PATH, offline.

The file is deliberately degraded on five axes at once:

- **Formatting**: four-space indentation, unaligned `=`. `terraform fmt -check` exits with code 3.
- **Consistency**: the generated file's `content` references `var.env_name`, a never-declared variable (the existing variable is `environment`). `terraform validate` fails and `terraform plan` refuses to start.
- **Naming**: the resources are `local_file.localFileAppConfig` and `random_pet.randomPetInstanceName`, in camelCase and repeating the type the address already carries.
- **Typing**: the variables `app_name`, `environment`, `replica_count` and `api_token` have neither `type` nor `description`. The provided `terraform.tfvars` sets `replica_count = "3"`, quoted, which passes silently as long as the variable is untyped.
- **Sensitivity and documentation**: no output has a `description`, and the output exposing `var.api_token` is not marked `sensitive`.

There is neither a `.gitignore` nor any file split.

## The state to reach

1. `terraform fmt -check -recursive` reports nothing.
2. `terraform validate` declares the configuration valid: the orphan reference `var.env_name` is resolved (by using the existing `environment` variable, or declaring the missing one).
3. The configuration still creates exactly the same resources: one `local_file` and one `random_pet`, no more, no less.
4. Their addresses follow the official convention: snake_case name, descriptive, not repeating the type. No uppercase, no dash.
5. Every variable has a non-empty `description`.
6. `replica_count` is genuinely typed `number`: a non-numeric value passed via `-var` is rejected, which an untyped variable would accept.
7. Every output has a non-empty `description`, and the output exposing the API token is marked `sensitive`.
8. The output exposing the replica count is declared `type = number`, as 1.15 now recommends: its value comes out as a JSON number even though `terraform.tfvars` provides it quoted.
9. A `.gitignore` excludes `.terraform/`, `terraform.tfstate*` and `.tfvars`, but does **not** ignore `.terraform.lock.hcl` (to be committed). The pattern `.terraform*` would therefore be a mistake: use `.terraform/`.
10. The project converges: a second plan right after apply proposes nothing.

The official style guide further recommends **splitting** this single file into `terraform.tf`, `providers.tf`, `variables.tf`, `main.tf` and `outputs.tf`: that is the taught best practice, and the learner is invited to do it, but the automated check covers the invariants above, independent of the split.

## How it is proven

The tests never open the learner's `.tf` files to parse them. They drive Terraform in `challenge/work` and read only JSON, return codes, and the `.gitignore` (a deliverable, not HCL).

1. `terraform fmt -check -recursive` returns 0.
2. `terraform validate -json` returns `valid: true`.
3. `terraform show -json` contains exactly one `local_file` and one `random_pet`.
4. Each resource's `name` field matches `^[a-z][a-z0-9_]*$`.
5. The plan JSON (`configuration.root_module.variables`) gives a non-empty `description` for each variable.
6. `terraform plan -var replica_count=abc` exits non-zero.
7. `terraform output -json` marks `api_token` sensitive; `replicas` has `type: number` and `value: 3`; the plan JSON gives a `description` to each output.
8. The `.gitignore` ignores `.terraform/` and `terraform.tfstate*`, and no pattern ignores `.terraform.lock.hcl`.
9. `terraform plan -detailed-exitcode` returns 0 right after apply.

Reference: https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/style-guide-terraform/
