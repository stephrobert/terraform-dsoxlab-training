# 🎯 Challenge: explicit source and alias

## Starting point

`challenge/work` holds an incomplete project, `versions.tf` and `main.tf`, both
holed (`???`). Only `hashicorp/random` is used. `terraform apply` fails as-is.

## ✅ Objective

1. **`versions.tf`, `source`**: write the **explicit** source address of the
   random provider (`hashicorp/random`), even though the prefix is implicit for
   HashiCorp providers.
2. **`main.tf`, second provider block**: add an **`alias = "secondaire"`**.
   Without it, this is a rejected duplicate (`Duplicate provider configuration`).
3. **`main.tf`, `random_pet.autre`**: attach this resource to the aliased config
   with **`provider = random.secondaire`**. Do not touch `random_pet.defaut`,
   which stays on the default config.

After `apply`, a second `terraform plan` must propose nothing.

## 🧭 What the lab makes you observe

- **The explicit source resolves** to `registry.terraform.io/hashicorp/random`.
- **The alias** creates a second configuration of the same provider; a resource
  only picks it if it carries `provider =`.
- **The wiring is read in the plan JSON** (`provider_config`,
  `provider_config_key`), never in your `.tf`.

## 🔍 Validation

```bash
dsoxlab check write-code-providers
```

Five tests reading `terraform version -json`, the plan JSON and `show -json`: the
resolved source, the declared aliased configuration, the wiring of both
resources, their presence, and idempotence. None reads your `.tf`.
