# The secret comes from Vault, the state will know nothing about it

## The situation

**Target exam objective: 2f (manage sensitive data), the only sub-objective that names Vault explicitly.**

The sibling labs deal with a secret you build or type. This one deals with a secret you **fetch elsewhere**. The trap is that the historical way, the `vault_kv_secret_v2` data source, copies the value in clear text into the state, and `sensitive_values` marks it `true` while hiding nothing: the password stays readable in `terraform show -json`. We want the opposite: it must leave **no trace**.

## Target capability

Consume a pre-existing secret from Vault in Terraform, passing it to its destination without leaving any trace in the state or the plan. Read the source with an **`ephemeral`** block (never persisted), write the destination with a **write-only** argument (`data_json_wo`), and drive rotation with a version integer, the only thing that remains.

## Where the learner starts

`challenge/work` targets a **Vault dev** server that dsoxlab starts automatically (`runtime.services`): no install, no account, root token `root` on `http://127.0.0.1:8200`. The source secret `kvv2/app/db` (keys `password` and `username`) is **seeded** into Vault before the tests; under `dsoxlab run`, the learner seeds it with the `vault` CLI (see the challenge). The secret **pre-exists**: Terraform does not create it, it consumes it.

Complete already: `versions.tf` (`hashicorp/vault` provider `>= 5.0`, `required_version >= 1.11`), `providers.tf` (the Vault dev address and token), `variables.tf` (`copie_version`, default 1). Only `main.tf` has holes:

```hcl
??? "vault_kv_secret_v2" "source" {   # read the source WITHOUT persisting it
  mount = ???
  name  = ???
}
resource "vault_kv_secret_v2" "replique" {
  mount = "kvv2"
  name  = "app/db-replique"
  ???   = jsonencode({ password = ??? })   # write WITHOUT persisting (write-only)
  ???   = var.copie_version                # the write-only version integer
}
output "chemin" { value = ??? }
```

## The target state

1. The source secret is read by an `ephemeral` block, which produces **no** state entry, neither `mode: managed` nor `mode: data`.
2. The replica is a `mode: managed` resource whose `data_json_wo` is `null`, `data_json` is `null`, `data` is an empty object, and `data_json_wo_version` carries a number.
3. The source password appears **nowhere** in `terraform show -json` or in `terraform.tfstate`.
4. The secret did transit though: `kvv2/app/db-replique` exists in Vault and holds the same password as `kvv2/app/db`.
5. Right after apply, a new plan proposes nothing. Changing the source password in Vault **without** touching `copie_version` still produces no plan.
6. Bumping `copie_version` to 2 produces a non-empty plan, and the matching apply pushes the new password into the replica.

## How it is proven

The tests never open a learner `.tf` file. They drive Terraform in `challenge/work` and use only JSON, the raw state file, return codes, and the real state of Vault queried through its API.

1. Entry guard: if Vault is unreachable, the suite is skipped (or fails under `LAB_WORKDIR`). Then the source secret is seeded through the API.
2. `show -json` after apply: no `mode: data`, a single `mode: managed` entry of type `vault_kv_secret_v2`, with `data == {}`, `data_json is None`, `data_json_wo is None`, `data_json_wo_version == 1`.
3. The source password, read via the API, is searched in `show -json` **and** in the raw state: zero occurrences.
4. `GET /v1/kvv2/data/app/db-replique` returns the same `password` as the source.
5. `plan -detailed-exitcode` returns 0 after apply, and still 0 after a source-secret change without a version bump.
6. `plan -detailed-exitcode -var copie_version=2` returns 2; after `apply -var copie_version=2`, the Vault API gives the new password in the replica.

Reference: https://registry.terraform.io/providers/hashicorp/vault/latest/docs

## 🎯 Challenge: the secret comes from Vault, without touching the state

### ✅ Objective

In `challenge/work`, complete `main.tf` to **replicate** the secret `kvv2/app/db`
to `kvv2/app/db-replique`, without the password ever touching the Terraform state.

A **Vault dev** server is started on its own by dsoxlab (`runtime.services`). For a
manual `dsoxlab run`, first seed the source secret:

```bash
export VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root
vault secrets enable -path=kvv2 kv-v2
vault kv put kvv2/app/db username=app password=change-me
```

(`dsoxlab check` seeds it automatically before its tests.)

Then fill the `???` in `main.tf`:

1. the **ephemeral read** block of the source secret (`mount = "kvv2"`,
   `name = "app/db"`);
2. the **write-only** argument that writes the password into the replica, reusing
   the ephemerally-read value;
3. the write-only **version number** (`= var.copie_version`);
4. the value of the `chemin` output (the replica's `mount/name`).

### 🔍 Validation

`dsoxlab check write-code-sensitive-data-vault-secrets` proves, on JSON and via the
Vault API:

- no `mode: data` entry; the replica has `data_json_wo`, `data_json` at `null` and
  `data` empty, `data_json_wo_version` at `1`;
- the source password appears **nowhere** in `show -json` or the state;
- `kvv2/app/db-replique` in Vault holds the **same** password as the source;
- idempotence, and rotation: `copie_version=2` pushes the new password.

Stuck? `dsoxlab hint write-code-sensitive-data-vault-secrets`.
