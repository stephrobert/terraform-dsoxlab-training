# sensitive: a mask, and a side effect

`sensitive = true` masks a value in output, but **does not remove it from the
state**. And the marking has a **side effect** you would not suspect: sensitivity
propagates, and it **forbids** some constructs like `for_each`. This tutorial
shows it on a throwaway example; the challenge makes you avoid the trap and
expose a hash without leaking.

## sensitive masks display, not the state

```hcl
variable "cle_api" {
  type      = string
  sensitive = true
}
```

`terraform output -json` and `terraform output -raw` return the value **in
cleartext**, and the state keeps it. `sensitive` is a display filter.

## The side effect: sensitive breaks for_each

Here is the Professional trap. **A sensitive value cannot be a `for_each` key**:

```hcl
variable "zones" {
  type      = set(string)
  sensitive = true
}

resource "local_file" "f" {
  for_each = var.zones # forbidden
}
```

```text
Error: Invalid for_each argument
```

Terraform uses the `for_each` value as an **instance identifier** and always
displays it, which would disclose the secret. Marking a variable `sensitive` can
therefore **break** a working `for_each`. The fix: iterate over a **non-sensitive**
set, and inject the secret only into an attribute.

## Contamination is tracked in sensitive_values

An attribute fed by a sensitive value becomes sensitive, and `show -json` flags
it in a **`sensitive_values`** object per resource:

```bash
terraform show -json | jq '.values.root_module.resources[] | {address, sensitive_values}'
```

It is the machine trace to audit what propagation actually contaminated.

## Expose a hash without leaking: nonsensitive()

The `sha256` of a secret **stays sensitive** (the contagion crosses functions).
To publish a safe fingerprint in a non-sensitive output, declassify it:

```hcl
output "hash_cle" {
  value = nonsensitive(sha256(var.cle_api))
}
```

`nonsensitive()` puts the responsibility on you: reserve it for a value that
leaks nothing, such as a hash.

## Your turn

```bash
dsoxlab run write-code-sensitive-data-sensitive-values
dsoxlab check write-code-sensitive-data-sensitive-values
dsoxlab hint write-code-sensitive-data-sensitive-values
```

Exam objective: **2f** (sensitive data).

Reference: [sensitive in Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/gestion-donnees-sensibles/sensitive-terraform/)
