# Read secrets from Vault without freezing them in the state

The Professional exam names **Vault explicitly** in sub-objective **2f**. The
problem is not reading a Vault secret, it is reading it **without ending up in
clear text in the state**. This tutorial shows the trap of the historical way,
then the right combination: an **ephemeral** read and a **write-only** write. The
challenge makes you prove it on a replicated secret.

## The trap: the data source copies the secret in clear text

The oldest way to read a KV v2 secret is a **data source**:

```hcl
data "vault_kv_secret_v2" "source" {
  mount = "kvv2"
  name  = "app/db"
}
```

It works, but it **copies the value into the state**. Worse: `sensitive_values`
marks it `true` while hiding nothing, the value stays readable in `terraform show
-json` and in `terraform.tfstate`. The provider even emits a **deprecation
warning** on this data source. An external secret read this way leaks exactly like
a hardcoded one.

## The ephemeral read: `ephemeral`

The `hashicorp/vault` provider in **5.x** exposes the same read as an
**ephemeral** block. An `ephemeral` block produces a value available **during** the
operation, but **never written** to the state or the plan:

```hcl
ephemeral "vault_kv_secret_v2" "source" {
  mount = "kvv2"
  name  = "app/db"
}
```

You reference its result with `ephemeral.vault_kv_secret_v2.source.data["password"]`.
This value can only go into an **ephemeral context**: a provider configuration, a
provisioner, or a **write-only argument**. That last one is what we want.

## The write-only write: `data_json_wo`

The `vault_kv_secret_v2` resource has two ways to write its content: the ordinary
argument **`data_json`**, which **persists** in the state (marked sensitive, but
present), and its **write-only** variant **`data_json_wo`**, which passes the value
to the provider **without ever persisting it**. Like any write-only argument, it
forms a mandatory pair with a version number:

```hcl
resource "vault_kv_secret_v2" "target" {
  mount = "kvv2"
  name  = "app/copy"

  data_json_wo         = jsonencode({ password = ephemeral.vault_kv_secret_v2.source.data["password"] })
  data_json_wo_version = 1
}
```

After apply, in the state: `data_json_wo` is `null`, `data_json` is `null`, `data`
is an empty object; only **`data_json_wo_version`** remains. To rotate the secret,
you **bump** that number. Changing it from `1` to `2` re-triggers the send; without
that change, a new value in the source is **not** picked up (Terraform does not
track what it does not store).

## The ephemeral + write-only duo

End to end, the secret **never touches disk on the Terraform side**: read by an
`ephemeral` (no state), written by a `data_json_wo` (no state). It transits in
memory during the operation, from the source KV to the target KV. That is the
complete answer to sub-objective 2f, and the only one that leaves no trace.

## Your turn

You know that the `vault_kv_secret_v2` data source **leaks** (and is deprecated),
that an `ephemeral` block reads without persisting, that `data_json_wo` writes
without persisting, and that only `data_json_wo_version` remains and drives
rotation. The challenge makes you replicate a secret from one Vault path to
another, leaving **no trace** in the state. A Vault dev server is started on its
own by dsoxlab.

```bash
dsoxlab run write-code-sensitive-data-vault-secrets
dsoxlab check write-code-sensitive-data-vault-secrets
dsoxlab hint write-code-sensitive-data-vault-secrets
```

Target exam objective: **2f** (manage sensitive data), Professional level.

Reference: [Vault provider](https://registry.terraform.io/providers/hashicorp/vault/latest/docs)
