# Scenario: version constraints and the lock file

**Exam objective: 3a (version constraints, dependency lock file).**

A version constraint reads fast and is understood poorly: `~>` bounds a series, `=` pins a single version, and the `terraform` block accepts no variable. The learner must set the right constraints and prove it via the actual selection and the lock file, without reopening a `.tf`.

## Target capability

Constrain the Terraform version with a literal, pin a provider to an exact version, bound another with the pessimistic operator, and know that the lock file freezes providers with `h1:` hashes and is committed. Know how to read the selection with `terraform version -json`.

## Where the learner starts

`challenge/work/` holds an incomplete project. No VM, no remote account: `local` and `random` are used. The lab runs anywhere `terraform` is on the PATH, with registry access for init.

The directory has `versions.tf` (holed) and `main.tf` (provided, two trivial resources):

```hcl
terraform {
  required_version = ???        # a LITERAL: the terraform block accepts no variable
  required_providers {
    local  = { source = "hashicorp/local", version = ??? }    # PIN 2.5.1
    random = { source = "hashicorp/random", version = ??? }   # PESSIMISTIC: 3.x, not 4.0
  }
}
```

`terraform init` fails as-is: the `???` are not valid HCL.

## The state to reach

1. `required_version` is a **literal** satisfied by Terraform 1.15 (for example `>= 1.15.0`). A variable would raise `Variables not allowed`.
2. The `local` provider is **pinned exactly** to `2.5.1`: `terraform version -json` shows it resolved to that version.
3. The `random` provider is bounded **pessimistically** (`~> 3.6`): it resolves in the `3.x` series, never `4.0`.
4. The lock file `.terraform.lock.hcl` is generated, with `h1:` hashes for both providers and local's `2.5.1`.
5. The project converges: `apply` succeeds and a second plan proposes nothing.

## How it is proven

The tests never open the learner's `.tf` files. They read `terraform version -json`, the lock file (a generated artifact) and return codes.

1. `terraform version -json`: `provider_selections` gives `registry.terraform.io/hashicorp/local` at exactly `2.5.1`. A different pin would show.
2. Still in `provider_selections`, `hashicorp/random` is in the `3.x` series and at least `3.6`.
3. `.terraform.lock.hcl` contains at least two `h1:` hashes and the `2.5.1` version.
4. `terraform apply` succeeds (the literal required_version is satisfied), then `terraform plan -detailed-exitcode` returns 0.

Reference: https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/version-constraints-terraform/
