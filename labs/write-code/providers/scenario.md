# Scenario: explicit source and provider alias

**Exam objective: 5b (provider configuration, aliases and local name).**

Two confusions dominate the providers topic: the implicit `hashicorp/` prefix, wrongly presented as normal when it is discouraged, and conflating local name with alias. The learner must declare an explicit source, an aliased configuration, and wire the right resource, without ever reopening a `.tf` file to prove it.

## Target capability

Write an explicit source address in `required_providers`, declare a second configuration of the same provider distinguished by an `alias`, and attach a resource to that aliased configuration with the `provider =` meta-argument. Know how to prove the wiring via the plan JSON configuration representation.

## Where the learner starts

`challenge/work/` holds an incomplete project. No VM, no remote account: only `hashicorp/random` is used, `terraform init` already in place. The lab runs anywhere `terraform` is on the PATH, offline.

The directory has `versions.tf` and `main.tf`, both holed:

```hcl
# versions.tf
required_providers {
  random = {
    source  = ???        # the EXPLICIT source address
    version = "~> 3.6"
  }
}
```

```hcl
# main.tf
provider "random" {}
provider "random" { ??? }        # a SECOND config, distinguished by an alias
resource "random_pet" "defaut" { length = 2 }
resource "random_pet" "autre" { ???  length = 2 }   # attached to the alias
```

`terraform apply` fails as-is: the `???` are not valid HCL, and a second provider block without an alias would be a rejected duplicate.

## The state to reach

1. `random`'s source is explicit (`hashicorp/random`), resolving to the full address `registry.terraform.io/hashicorp/random`.
2. A second configuration of the `random` provider carries `alias = "secondaire"`. Without the alias, the second block would be `Duplicate provider configuration`.
3. `random_pet.autre` is attached to the aliased config via `provider = random.secondaire`; `random_pet.defaut` stays on the default config.
4. Both `random_pet` are created.
5. The project converges: a second plan right after apply proposes nothing.

## How it is proven

The tests never open the learner's `.tf` files and parse no human output. They drive Terraform in `challenge/work` and read only JSON or return codes.

1. `terraform version -json`: `provider_selections` contains `registry.terraform.io/hashicorp/random`. The explicit source resolved to the full address.
2. `terraform plan -out=tfplan` then `terraform show -json tfplan`: in `configuration.provider_config`, an entry `random.secondaire` carries `alias: "secondaire"` and the right `full_name`.
3. Still in that JSON, `random_pet.autre` has a `provider_config_key` of `random.secondaire`, and `random_pet.defaut` of `random`.
4. `terraform show -json`: two `random_pet` in the state.
5. `terraform plan -detailed-exitcode` returns 0 right after apply.

Reference: https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/providers-terraform/
