# Ephemeral values: the secret that never touches the state

An **ephemeral** value exists **during** a Terraform operation, then vanishes:
it is **never written** to the state or the plan. It is the only real answer to
the problem `sensitive` does not solve, since `sensitive` leaves the value in
cleartext in the state. This tutorial shows the `ephemeral` block, its golden
rule, and the `ephemeralasnull()` function, on a throwaway session example; the
challenge makes you prove it on a different case.

Ephemeral arrived in **Terraform 1.10** (ephemeral variables and outputs), and
the `ephemeral "random_password"` resource requires **random >= 3.7**.

## Declaring an ephemeral value

An **`ephemeral`** block produces a value generated on the fly, never persisted.
You reference it by `ephemeral.<TYPE>.<NAME>.<ATTR>`:

```hcl
ephemeral "random_password" "session" {
  length = 24
}
```

`ephemeral.random_password.session.result` is available during the run but
**appears nowhere in the state**. Unlike an ordinary `random_password`, whose
`result` is stored in cleartext in the state, the ephemeral one leaves no trace
on disk.

## The golden rule: never in a persisted attribute

An ephemeral value can only go into **ephemeral contexts**. Making it touch a
**persisted** attribute raises a clear error:

```hcl
resource "local_file" "leak" {
  content = ephemeral.random_password.session.result   # forbidden
}
```

```text
Error: Invalid use of ephemeral value
```

The **allowed** contexts are: a **write-only** argument of a resource, another
`ephemeral` block, a **provider** configuration, a **provisioner** (and its
connection configuration), a **local** consumed only in an ephemeral context, a
**variable** with `ephemeral = true`, and a **child-module ephemeral output**.

## The two root-module errors

At the **root** level, an output cannot carry an ephemeral, and this shows up in
**two** distinct ways:

- declaring an output **`ephemeral = true`** at the root:
  `Ephemeral output not allowed`;
- exposing in an **ordinary** root output a value **derived** from an ephemeral
  (even its length): `Ephemeral value not allowed`.

The second case is the one you hit first, as soon as you try to display an
ephemeral "just to see".

## ephemeralasnull(): expose without leaking

So how do you expose something at the root without breaking the run? The
**`ephemeralasnull()`** function renders **`null`** any ephemeral value outside
an ephemeral context:

```hcl
output "session_masquee" {
  value = ephemeralasnull(ephemeral.random_password.session.result)
}
```

The output is `null`. It is not a display of the secret, it is its neutral
setting-aside: the ephemeral value does not cross the state boundary. On a
**non**-ephemeral value, `ephemeralasnull()` would return the value as is, which
also makes it a good revealer: a `null` proves the input was indeed ephemeral.

## Ephemeral variables and outputs

A **variable** can be `ephemeral = true`: its value feeds the run but is never
persisted. A **child-module output** can be too, to bubble an ephemeral up to the
caller without ever writing it. The lifecycle of an ephemeral resource runs as
**open / renew / close** during the operation, invisible in the state.

## Your turn

```bash
dsoxlab run write-code-sensitive-data-ephemeral-values
dsoxlab check write-code-sensitive-data-ephemeral-values
dsoxlab hint write-code-sensitive-data-ephemeral-values
```

Exam objective: **2f** (managing sensitive data), Professional level.

Reference: [Ephemeral values in Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/gestion-donnees-sensibles/ephemeral-values/)
