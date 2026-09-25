# Scenario: the typo that breaks nothing

**Exam objective: 2e (configure input variables and outputs)**, the precedence
of value sources being the heart of it.

A misspelled variable in a `.tfvars` does not fail the plan: it produces a warning, and the real variable stays at its default. It is a classic false diagnostic. The learner must fix such a typo and prove that a `terraform.tfvars.json` outranks `terraform.tfvars`.

## Target capability

Understand the precedence of value files (including `terraform.tfvars.json` above `terraform.tfvars`) and the behavior of an undeclared variable: warning in a file, error via `-var`, ignored via `TF_VAR_`. Know that a typo in a `.tfvars` leaves the variable at its default.

## Where the learner starts

`challenge/work/` holds a complete, applicable project. No VM, no remote account: only `local` is used. The lab runs anywhere `terraform` is on the PATH, offline.

The directory has `versions.tf`, `variables.tf` (`region`, `bucket` default `app-defaut`, `replicas` default 1), `main.tf` (provided), and a **degraded** `terraform.tfvars`:

```hcl
region   = "eu-west-3"
bukcet   = "prod"     # TYPO: "bukcet" instead of "bucket"
replicas = 2
```

`terraform apply` **succeeds** as-is (the undeclared variable is only a warning), but `bucket` stays at `app-defaut`: the result is not the intended one.

## The state to reach

1. The typo is fixed in `terraform.tfvars`: `bucket` is `prod` (no longer the `app-defaut` default).
2. A `terraform.tfvars.json` is created setting `replicas = 5`. Since the JSON variant outranks `terraform.tfvars` (which sets 2), `replicas` is **5**.
3. `region` is `eu-west-3` (already provided by `terraform.tfvars`).
4. The project converges: a second plan right after apply proposes nothing.

## How it is proven

The tests never open the learner's `.tf` files. They read `terraform output -json` and return codes.

1. `terraform output -json`: `bucket` is `prod`. As long as the typo remains, it is `app-defaut`, and the test fails.
2. `replicas` is `5`, a number: the `terraform.tfvars.json` overrode the `2` from `terraform.tfvars`.
3. `region` is `eu-west-3`.
4. `terraform plan -detailed-exitcode` returns 0 right after apply.

Reference: https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/fichiers-tfvars/
