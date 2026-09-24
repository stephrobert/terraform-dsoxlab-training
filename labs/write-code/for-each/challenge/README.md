# 🎯 Challenge: add a service without destroying anything

## ✅ Objective

`challenge/work` holds a configuration that is **correct and already applied**: a
`terraform.tfstate` is present, three services are running. Nothing is holed with
`???`.

The `DEMANDE.md` file carries the need: **add the `api` service between `web` and
`cache`**, without destroying or recreating the three existing services.

Applying the request naively destroys production. That is the whole point.

## 🚦 Start by measuring the damage

Before fixing anything, simply add `api` to the list and look at the plan. Do not
apply it.

```bash
cd challenge/work
terraform init
terraform plan
```

Note the number of resources destroyed. That is the figure you have to bring down
to zero.

## 🎯 The state to reach

| # | Requirement |
|---|---|
| 1 | No `count` any more: both resources are driven by `for_each` |
| 2 | The existing instances are re-addressed from `[0]`, `[1]`, `[2]` to `["web"]`, `["cache"]`, `["db"]` **through `moved` blocks** |
| 3 | The `random_pet` identities of the three original services are **unchanged** |
| 4 | `api` is added: **a single creation per resource type**, no destruction |
| 5 | The `identites` output is a **map** indexed by service name |
| 6 | `terraform plan -detailed-exitcode` returns **0** at the end |

## 🧩 The three traps

1. **`for_each` refuses a list.** It expects a map or a set of strings, and the
   keys must be known at plan time.
2. **Changing `count` to `for_each` changes the instances' address.** Without a
   `moved` block, Terraform destroys and recreates everything. The re-addressing
   must be **declarative**, not done by hand with `terraform state mv`.
3. **The `[*]` splat is invalid on a `for_each` resource.** It only applies to
   lists, sets and tuples. Use a `for` expression.

## 💡 The signature of a successful re-addressing

In the JSON plan, a correctly re-addressed instance carries
`"actions": ["no-op"]` **and** a `previous_address` field. If you read
`["delete", "create"]`, the resource is being replaced: that is a miss.

## 🔍 Validation

```bash
dsoxlab check write-code-for-each
```

The tests never read your `.tf` files. They compare the final identities with
those recorded in the starting state, and analyse the addition's plan to count
creations and destructions.
