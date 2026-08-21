# 🎯 Challenge: split a monolith, and prove a file name matters

## 📦 Starting point

`challenge/work` holds **a single file**, `tout.tf`: the `terraform` block, three
variables, two resources and one output, piled up out of order. Nothing has been
applied.

Two `???` even prevent parsing: the **type** of the `environnements` variable,
and the **description** of the `chemins` output. Start there.

## ✅ Objective

Refactor this configuration into the **Standard Module Structure**, add a
**nested module** and a **standalone example**, then demonstrate that a file named
`override.tf` really changes the outcome.

## 📋 What you must obtain

1. `tout.tf` is gone, replaced by `main.tf`, `variables.tf`, `outputs.tf`,
   `README.md` and `LICENSE`. The `terraform` block lives **alone** in
   `terraform.tf`, the name the official style guide uses.
2. A nested module exists under `modules/fiche/`, with its own `main.tf`,
   `variables.tf`, `outputs.tf` and a **`README.md`** marking it usable from
   outside. It creates one `random_pet` and one `local_file` per call.
3. The root calls it by the **relative** path `./modules/fiche`.
4. The module is instantiated **once per environment**: `module.fiche["dev"]` and
   `module.fiche["prod"]`.
5. Every variable and every output, at the root and in the module, carries a
   **`type`** and a **`description`**. The `chemins` output is a `map(string)`
   aggregating the path each instance exposes.
6. `examples/minimal/` holds a standalone configuration calling the module, which
   `terraform validate` accepts.
7. An **`override.tf`** brings `local_file.index`'s `file_permission` from `0644`
   down to `0600`. `main.tf` still declares `0644`: it is the **applied state**
   that must read `0600`.
8. The configuration is applied and stable: `plan -detailed-exitcode` exits **0**.

## ⚠️ The heart of the matter

It is often said that Terraform file names are purely cosmetic. True, **except
for one family**: `override.tf` and `*_override.tf`, which Terraform loads
**last** and **merges** over the rest.

The same content in a file with an ordinary name overrides nothing, it **breaks
the configuration**:

```text
Error: Duplicate resource "local_file" configuration
Resource names must be unique per type in each module.
```

That is the only exception, and it is the one the test checks.

## 🔍 Validation

`dsoxlab check modules-module-structure` proves, by execution:

- the standard structure files exist, `LICENSE` and both `README` included;
- `module_calls.fiche.source` is exactly `./modules/fiche`, and the module does
  expose an output;
- the state holds both indexed instances, each with its two resources;
- `local_file.index` carries `file_permission = "0600"` in the state, which no
  other file name can achieve;
- the `chemins` output comes back with type `["map","string"]` and one key per
  environment;
- `examples/minimal` validates on its own, `valid: true` and `error_count: 0`;
- `plan -detailed-exitcode` returns **0**.

No test reads your `.tf` files.

Stuck? `dsoxlab hint modules-module-structure`.
