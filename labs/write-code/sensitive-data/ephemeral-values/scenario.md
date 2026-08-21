# Scenario: the value that never touches the state

**Exam objective: 2f (managing sensitive data), Professional level.**

`sensitive` masks display but leaves the secret in cleartext in the state. An **ephemeral** value, on the other hand, is **never written** to it. The learner must generate an ephemeral token, keep it out of the state, and expose it cleanly, with evidence.

## Target capability

Declare an ephemeral value with an `ephemeral` block, understand that it can only go into an ephemeral context (otherwise `Invalid use of ephemeral value`), that a root output rejects it (`Ephemeral value not allowed`), and expose it without disclosing it using `ephemeralasnull()`. Distinguish an ephemeral value from an ordinary `random_password`, persisted in cleartext in the state.

## Where the learner starts

`challenge/work/` holds an incomplete project. No VM, no remote account: only `hashicorp/local` and `hashicorp/random` (>= 3.7 for the ephemeral resource) are used, `terraform init` is already run. The lab runs anywhere `terraform` 1.15 is on the PATH, offline.

The directory has `versions.tf`, `variables.tf` (`longueur`, number, default 20), a `main.tf` where the token block is holed and a holed `outputs.tf`:

```hcl
??? "random_password" "jeton" {        # which keyword produces an ephemeral value?
  length = var.longueur
}
resource "random_password" "persistant" { length = var.longueur }   # contrast, persisted
resource "local_file" "marqueur" { ... }                            # non-secret, do not leak the token here
```

```hcl
output "jeton_masque" { value = ??? }  # expose the ephemeral token WITHOUT disclosing it
```

`terraform apply` fails as-is: the `???` are not valid HCL, and exposing an ephemeral at the root without care would be rejected anyway.

## The state to reach

1. The token block is declared **`ephemeral`**: its value is generated during the operation but **never written** to the state.
2. `random_password.persistant` stays an ordinary resource: its `result` is present **in cleartext** in the state. This contrast is what gives the ephemeral its meaning.
3. `jeton_masque` exposes the ephemeral token's result via **`ephemeralasnull()`**, and is therefore `null`. Exposing `ephemeral.random_password.jeton.result` directly would raise `Ephemeral value not allowed`.
4. The ephemeral token appears **nowhere** in the state: no ephemeral address, no value.
5. The project converges: a second plan right after apply proposes nothing, even though the ephemeral value is regenerated on each run.

## How it is proven

The tests never open the learner's `.tf` files and parse no human output. They drive Terraform in `challenge/work` and read only JSON or return codes.

1. `terraform show -json`: there is **exactly one** `random_password` in the state, named `persistant`, and its `result` is 20 cleartext characters. Two `random_password` would betray a token declared `resource` instead of `ephemeral`.
2. Still in `show -json`: no address contains `ephemeral`, and all resources are `mode: managed`. The ephemeral value is absent from the state.
3. `terraform output -json`: `jeton_masque` is `null`. `ephemeralasnull()` neutralizes the ephemeral; a non-ephemeral value would have come out as is, so this `null` proves the ephemeral nature.
4. `terraform plan -detailed-exitcode` returns 0 right after apply.

Reference: https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/gestion-donnees-sensibles/ephemeral-values/
