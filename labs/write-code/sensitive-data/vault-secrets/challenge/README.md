# 🎯 Challenge: the secret comes from Vault, without touching the state

## ✅ Objective

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

## 🔍 Validation

`dsoxlab check write-code-sensitive-data-vault-secrets` proves, on JSON and via the
Vault API:

- no `mode: data` entry; the replica has `data_json_wo`, `data_json` at `null` and
  `data` empty, `data_json_wo_version` at `1`;
- the source password appears **nowhere** in `show -json` or the state;
- `kvv2/app/db-replique` in Vault holds the **same** password as the source;
- idempotence, and rotation: `copie_version=2` pushes the new password.

Stuck? `dsoxlab hint write-code-sensitive-data-vault-secrets`.
