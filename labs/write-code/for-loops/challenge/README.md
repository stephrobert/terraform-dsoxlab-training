# 🎯 Challenge: transform a server catalogue

## Starting point

`challenge/work` holds a `var.serveurs` map of six entries, already written and
**not to be modified**. `outputs.tf` is complete as well. Two files are holed
with `???`:

- `locals.tf`: four `locals` whose body is to be written.
- `main.tf`: the `for_each` of `local_file.fiche`.

While the `???` are there, the configuration does not parse. Every hole carries
above it a comment stating what is expected.

The catalogue is built to catch shortcuts: two servers share a role, one `prod`
server is **inactive** (`web2`), one server has an **empty** tag list (`db`).

## ✅ Objective

Produce, from the `var.serveurs` map alone, these five results:

1. **`noms_prod`**: a **tuple** of the names of servers whose `env` is `prod`.
   Brackets, and let Terraform sort the keys.

2. **`par_role`**: an **object** where each key is a role and each value the
   **list** of names carrying that role. Two servers share a role: you have to
   **group**, not overwrite the key.

3. **`memoires`**: a **tuple** of the memory figures, **one entry per server**.
   Six, not one. A tuple of length 1 would betray a splat applied to the map.

4. **`tags_plats`**: a **tuple** of `"<server>:<tag>"` strings, one per existing
   pair. Cross two levels, then flatten. The tagless server must disappear **on
   its own**, with no `if` clause.

5. **`local_file.fiche`**: a record for every server that is both `prod` **and**
   active, and for no other. Filter the resource's `for_each`.

After your `apply`, `terraform plan` must propose nothing.

## 🧭 The trap to know

The **`[*]` splat on a map raises no error**: it wraps the whole map in a
single-element tuple. `var.serveurs[*]` has a length of 1, not 6. On a map, an
explicit `for` expression is the only reliable form.

## 🔍 Validation

```bash
dsoxlab check write-code-for-loops
```

Nine tests. They decode `terraform output -json` and `terraform show -json`: each
root's type, the exact length, the expected content, and the set of
`local_file.fiche` instances. No test reads your `.tf`: it is the **shape of the
result** that proves the right expression.
