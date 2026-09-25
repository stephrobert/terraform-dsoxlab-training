# 🎯 Challenge: extract a module without recreating anything

## 📦 Starting point

`challenge/work` holds a **flat** configuration, duplicating the same set three
times, and it is **already applied**: a `terraform.tfstate` is there, the nine
objects exist, the files in `out/` are on disk.

| Service | Replicas |
| --- | --- |
| `api` | 3 |
| `web` | 2 |
| `batch` | 1 |

## ✅ Objective

1. **Extract a local module** into `modules/service/`, with typed and
   **documented** variables, and useful outputs.
2. **Call it once per service**, indexed by the service **name**.
3. **Recreate nothing.** The nine identifiers of the starting state must be found
   again, at the new addresses.
4. The module **configures no provider**, but keeps its own
   `required_providers`.

After your work, `terraform plan` must propose nothing.

## 🧭 What decides between a successful and a failed refactor

Changing address is not changing object. Without `moved`, Terraform sees nine
addresses disappear and nine appear: it destroys and recreates everything.

```hcl
moved {
  from = random_pet.api_nom
  to   = module.service["api"].random_pet.nom
}
```

**An empty plan does not prove nothing was destroyed**: a configuration that had
recreated everything converges too. The **identifiers** settle it, and that is
what the tests compare.

## ⚠️ Three traps, each one measured

**`version` only applies to registry modules.** On `./modules/service`, Terraform
refuses at `init` time: "applies only to registry modules".

**A block with several arguments is written over several lines.** The compact
form `moved { from = X  to = Y }` answers "The argument \"to\" is required", a
message that says nothing about layout.

**Write with `path.root`, not `path.module`.** Otherwise the files end up in the
module's subdirectory, and Terraform recreates them.

## 🔍 Validation

```bash
dsoxlab check certifications-professional-capstone4-modules
```

Six tests. They read state and the JSON plan, never your `.tf`. The central proof
compares the identifiers before and after.

Stuck? `dsoxlab hint certifications-professional-capstone4-modules`.
