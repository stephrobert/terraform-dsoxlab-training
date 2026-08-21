# 🎯 Challenge: pick count or for_each, and prove it

## Starting point

`challenge/work` holds a small project. `versions.tf` and `variables.tf` are
**complete, do not touch them**. Three variables drive everything: `services` (a
`list(string)`, `["web", "api", "cache"]`), `workers` (a number, `3`) and
`rapport` (a bool, `false`).

`main.tf` ships the **working count version** of `local_file.service`, on
purpose. `workers.tf`, `rapport.tf` and `outputs.tf` come with `???` holes.

## ✅ Objective

**First run `init` then `apply`** on the count version: you now have
`service[0]`, `[1]`, `[2]` in the state. A `plan -var 'services=["web","cache"]'`
shows the trap: removing one service recreates another.

Then:

1. **Migrate `local_file.service`** to `for_each` keyed by name, and add the
   `moved` blocks so the migration destroys nothing.
2. **`random_pet.worker`**: interchangeable copies, so `count = var.workers`.
3. **`local_file.rapport`**: optional, so `count = var.rapport ? 1 : 0`.
4. **Outputs**: `noms_workers` (splat over the workers), `chemins_services` (a
   `for` expression over the service map, since splat does not apply to
   `for_each`), `rapport` (`one()` over the 0-or-1 rapport).

After your final apply, a second `terraform plan` must propose nothing.

## 🧭 The trap to avoid

- **`count` indexes by integer, `for_each` by key.** Removing an element from the
  middle of a `count` list shifts all the following ones.
- **A block never carries both**: `count` and `for_each` together raise
  `Invalid combination of "count" and "for_each"`.
- **Migrating without `moved`** destroys and recreates every instance.

## 🔍 Validation

```bash
dsoxlab check write-code-count
```

Eight tests reading `terraform show -json` and `output -json`: the index type of
the `service` instances, the plan actions on removal, the non-destructive
migration (a `moved` proof rebuilt from `challenge/reference/`), the count
reduction, the conditional rapport, and idempotence. None reads your `.tf`.
