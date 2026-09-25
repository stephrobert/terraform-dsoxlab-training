# 🎯 Challenge: generate a cloud-init, and hit the wall

## Starting point

`challenge/work` builds a cloud-init document with
`data "cloudinit_config" "principal"`. `versions.tf`, `variables.tf` and
`outputs.tf` are **complete, not to be modified**. Everything happens in
`main.tf`, which holds two difficulties:

- a `dynamic "part"` block holed with `???` (the collection, the filename, the
  content);
- a **deliberately present** `dynamic "lifecycle"`. That is not a typo to repair
  as such: it is a dead end to understand.

Run `terraform validate` first. You will see syntax errors on the `???`, then,
once the `dynamic "part"` is written, this wall:
`Blocks of type "lifecycle" are not expected here.`

The `modules` variable is a map of three entries, one of which carries
`actif = false`.

## ✅ Objective

1. **Complete the `dynamic "part"`.** It generates one part per **active**
   module, sorted by key. The `actif` filter goes in the `for_each`, **never**
   in the `content`. The `filename` derives from the module's **key**
   (`part.key`), not from a rank.

2. **Keep the header literal.** The first part, `#cloud-config`, never varies:
   it stays a hand-written `part` block, outside the `dynamic`. Do not absorb it
   into the dynamic block.

3. **Dismantle the `lifecycle` trap.** A meta-argument block cannot be generated
   by `dynamic`. Replace the `dynamic "lifecycle"` with a **literal** `lifecycle`
   block carrying `create_before_destroy = true`.

After your `apply`, `terraform plan` must propose nothing.

## 🧭 What proves it is not literal

The configuration must **follow the variable**:

- with `-var 'modules={}'`, exactly **one** part remains, the header;
- with four active modules, **five** parts.

Hand-written blocks cannot satisfy both cases at once. And a `dynamic` that had
swallowed the header would fall to zero on the first.

## 🔍 Validation

```bash
dsoxlab check write-code-dynamic-blocks
```

Eight tests. They decode `terraform show -json` (the data source's ordered `part`
list), `output -json` and the JSON plan for `local_file.rendu`. None reads your
`.tf`: it is the number and order of the generated parts that prove the dynamic
block.
