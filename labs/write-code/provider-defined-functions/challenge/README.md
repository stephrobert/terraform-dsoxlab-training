# 🎯 Challenge: provider-defined functions

## ✅ Objective

In `challenge/work`, make the configuration valid using **four provider
functions** called with the `provider::<local_name>::<function>` syntax.

Three files have holes:

1. **`versions.tf`**: set `required_version` (the version that introduces the
   qualified syntax), declare the **built-in** provider under the local name
   **`tfcore`** (source `terraform.io/builtin/terraform`), and constrain
   `hashicorp/local` to a version that exposes `direxists`.
2. **`locals.tf`**: five locals to fill.
   - decode `amont.tfvars.txt` into an object (types are restored);
   - re-encode it as tfvars after adding `environment = "prod"`;
   - produce the expression syntax of `config.zones`;
   - test the existence of a present directory, then an absent one.
3. **`main.tf`**: the `local_file` `content` is the re-encoded tfvars.

Reminders:

- a provider function only exists if the provider is **declared** in
  `required_providers` (even `tfcore`), otherwise `Unknown provider function`;
- `direxists` was **added in a specific version** of `hashicorp/local`: a
  too-low constraint compiles but fails at the call;
- the namespace name is the provider's **local name**, not its type: here
  `provider::tfcore::…`, not `provider::terraform::…`.

## 🔍 Validation

`dsoxlab check write-code-provider-defined-functions` proves, on Terraform's JSON
outputs:

- `providers schema -json`: the functions are described by each provider;
- `metadata functions -json`: none is a language function;
- `version -json`: `hashicorp/local` is 2.5.0 or newer;
- `output -json`: `node_count` is a **number**, `aval` is the sorted tfvars,
  `zones_expr` is in expression syntax, `dir_present`/`dir_absent` are true/false;
- `show -json`: the written file indeed contains the re-encoded tfvars.

Stuck? `dsoxlab hint write-code-provider-defined-functions`.
