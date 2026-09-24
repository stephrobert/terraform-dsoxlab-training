# 🎯 Challenge: a chain of locals crossing three traps

## Starting point

`challenge/work` declares a project where **only `locals.tf` is holed**.
`versions.tf`, `variables.tf`, `main.tf` and `outputs.tf` are **complete, not to
be modified**. The supplied variables are `project` (`Atelier_Locaux`),
`environment` (`prod`), `node_count`, `memory_mb` and `db_password` (sensitive).

`locals.tf` arrives with **three separate `locals` blocks**, deliberately:
Terraform merges them, so a local in one block can reference another. Every
value is a `???`, and `terraform init` fails as it stands.

## ✅ Objective

Write the nine locals, spread across three blocks:

**Naming**
1. `slug`: `project` lowercased, underscores turned into dashes.
2. `base_name`: `slug` and `environment` joined by a dash. Expected:
   `atelier-locaux-prod`.

**Computation**
3. `is_production`: true only if `environment` is `prod`.
4. `effective_ram`: memory **doubled** in prod, otherwise its value. **It must
   stay a number**: mixing a number and a string in the ternary would silently
   convert it to a string.
5. `node_names`: a list of `node_count` strings `base_name-001`,
   `base_name-002`, ... A `for` expression and `format("%s-%03d", ...)`.

**Derived from a resource** (hence unknown at plan time)
6. `build_digest`: the first 8 characters of `random_id.build.hex`.
7. `manifest_name`: `base_name`, a dash, `build_digest`, `.json` extension.
8. `db_dsn`: a postgres DSN for user `app` on `localhost`, using
   `db_password` and `base_name` as the database name. It inherits
   `db_password`'s sensitivity.

After your `apply`, `terraform plan` must propose nothing.

## 🧭 The three traps

- **The ternary converts types.** `4096 : "2048"` is valid and returns a
  string. `effective_ram` must come out as a **number**.
- **A local derived from a resource is unknown at plan time.** `manifest_name`
  shows up as `(known after apply)`, unlike `base_name`.
- **Sensitivity propagates.** `db_dsn` derives from the sensitive
  `db_password`: the matching output is already marked `sensitive`, do not
  remove it.

## 🔍 Validation

```bash
dsoxlab check write-code-locals
```

Nine tests. They read `terraform show -json` (plan and state) and
`output -json`: `after_unknown` for the plan/apply boundary, the **JSON type**
of `effective_ram`, the `sensitive` flag of `db_dsn`, and the resource's real
hex. None reads your `.tf`.
