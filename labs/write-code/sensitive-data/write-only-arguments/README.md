# Write-only arguments: a secret that never lands in the state

A **write-only** argument passes a value to the provider **during the
operation**, but Terraform **never** writes it to the state or the plan. It fills
the gap `sensitive` leaves open: `sensitive` hides the value in logs but keeps it
**in clear text in the state**. This tutorial shows the idea on a throwaway
database-password example; the challenge makes you prove it on another case.

Write-only arguments arrived in **Terraform 1.11** and need a provider that
exposes them. They are recognizable by their **`_wo` suffix**, always paired with
a **`_wo_version`**.

## The problem: `sensitive` does not protect the state

An ordinary argument persists its value in the state, even when `sensitive`:

```hcl
resource "aws_db_instance" "example" {
  # ...
  password = var.db_password   # written in clear text into terraform.tfstate
}
```

`sensitive` prevents display in `terraform plan`, but anyone who reads
`terraform.tfstate` (or a poorly protected remote backend) sees the password. The
state is not a vault: the secret must **not enter it** in the first place.

## The fix: the `_wo` argument and its `_wo_version`

The same provider exposes a write-only variant of the argument. It forms a
**mandatory pair**: the value, and an **integer version number**.

```hcl
resource "aws_db_instance" "example" {
  # ...
  password_wo         = var.db_password
  password_wo_version = 1
}
```

- **`password_wo`** is sent to the provider during apply, then **forgotten**:
  after the operation it is `null` in the state. The secret never appears there.
- **`password_wo_version`** is the **only** one of the two that gets persisted. It
  acts as a clock: Terraform re-sends the value to the service only when this
  number **changes**. While it stays at `1`, later applies touch nothing and the
  plan is empty (idempotence).

To rotate a secret, bump `_wo_version` (1 to 2) together with the new value.
Without a version change, a new value in `password_wo` alone would be **ignored**.

## The rule that trips up the careless

`_wo` and `_wo_version` **always go together**. Supplying the value without the
version number (or the reverse) raises a validation error at apply: the provider
demands the complete pair. Likewise, an ordinary argument and its write-only
variant are **mutually exclusive** on the same resource: pick `password` **or**
`password_wo`, never both.

## Write-only and ephemeral values: the duo

A write-only argument is one of the few **allowed contexts** for an **ephemeral**
value (see the sibling ephemeral lab). You generate an ephemeral secret, which
never touches the state, and feed it to a write-only argument, which does not
persist it either: the secret leaves **no trace on disk**, end to end.

## Your turn

You know that a `_wo` argument passes a value without persisting it, that its
`_wo_version` is the only one stored and drives the re-send, that the two are a
mandatory pair, and that `sensitive` alone would leak the secret into the state.
The challenge makes you store a secret in a parameter, prove it appears
**nowhere** in the state, and stay idempotent. The tests prove it on the JSON and
on the state file itself.

```bash
dsoxlab run write-code-sensitive-data-write-only-arguments
dsoxlab check write-code-sensitive-data-write-only-arguments
dsoxlab hint write-code-sensitive-data-write-only-arguments
```

The lab starts a local AWS emulator (Floci) on its own: no Docker command to
type, no cloud account, no bill.

Target exam objective: **2f** (manage sensitive data), Professional level.

Reference: [Write-only arguments in Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/gestion-donnees-sensibles/write-only-arguments/)
