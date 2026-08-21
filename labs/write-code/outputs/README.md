# Outputs: type, sensitivity and precondition

An **output** exposes a value outside the module: the result of a configuration,
read by a human, another module or a pipeline. Declaring one is simple. The traps
are what `sensitive` does **not** mask, how sensitivity **propagates**, and the
fact that an output is not so passive: a `precondition` can fail the plan. This
tutorial shows them on a throwaway session example; the challenge makes you apply
them on a different case.

## An output exposes a value

Its minimal syntax is `value = <expression>`. The block also accepts
`description`, `type` (type constraint, Terraform 1.15), `sensitive`,
`depends_on`, `precondition` and `ephemeral`.

```hcl
output "adresse" {
  value       = "https://${random_pet.session.id}.example.test"
  description = "Public URL of the session."
}
```

Since Terraform 1.15, you can **constrain its type**, exactly like a variable. It
is the module's contract, documenting what the caller receives:

```hcl
output "profil" {
  type = object({
    nom   = string
    actif = bool
  })
  value = {
    nom   = "session"
    actif = true
  }
}
```

## sensitive: a display mask, not a protection

Here is the central misunderstanding. **`sensitive = true` does not protect the
secret.** It masks the value in the **human** output of `plan`, `apply` and
`terraform output`, nothing more. The documentation states:

> When you run Terraform commands with a local state file, Terraform stores the
> state as plain text, including variable values, even if you have flagged them
> as sensitive.

Concretely, `terraform output -json`, `terraform output -raw` and the state file
return the value **in cleartext**. `-raw` only works on a string, number or
boolean, never a list or object.

```hcl
output "cle" {
  value     = random_password.session.result
  sensitive = true
}
```

## Sensitivity propagates, even through a function

This is the trap few see coming. **Any expression that uses a sensitive value
becomes sensitive.** An output referencing a sensitive attribute **without**
`sensitive = true` is **rejected at plan time**:

```text
Error: Output refers to sensitive values
```

And the contagion crosses functions: the `sha256` of a password **stays
sensitive**, even though a hash is not reversible. To knowingly expose such a
derived value, **declassify** it with `nonsensitive()`:

```hcl
output "empreinte" {
  value = nonsensitive(sha256(random_password.session.result))
}
```

To truly exclude a value from state and plan, use `ephemeral = true` (reserved
for **child modules**, forbidden in the root module), not `sensitive`. And only
apply `nonsensitive()` to a value you have proven leaks nothing, such as a hash.

## An output is not passive: precondition and depends_on

An output is often presented as purely passive. That is wrong on two counts. A
**`precondition`** block (with a mandatory `error_message`) **fails the plan** if
its condition is false: it is a module's last-line guarantee.

```hcl
output "adresse" {
  value = "https://${random_pet.session.id}.example.test"

  precondition {
    condition     = var.duree >= 10
    error_message = "duree must be at least 10."
  }
}
```

And **`depends_on`** on an output orders operations: Terraform finishes the
upstream resources before computing the output, useful when the dependency is not
visible in the `value` expression.

## Your turn

```bash
dsoxlab run write-code-outputs
dsoxlab check write-code-outputs
dsoxlab hint write-code-outputs
```

Exam objectives: **2f** (sensitive data) and **2e** (outputs and complex types).

Reference: [Outputs in Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/outputs-terraform/)
