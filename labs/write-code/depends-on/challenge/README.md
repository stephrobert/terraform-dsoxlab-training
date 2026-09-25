# 🎯 Challenge: clean up a delivery's dependencies

## Starting point

`challenge/work` orchestrates a small delivery: a JSON manifest, a service
preparing a directory, a copy, a read. `versions.tf` and `variables.tf` are
**complete, not to be modified**. The rest deliberately mixes the two opposite
mistakes: a `depends_on` **too many**, and a **hidden** dependency that is
missing.

Three files need fixing:

- `main.tf`: a redundant `depends_on` on `local_file.manifeste`, and a
  `null_resource.publication` to wire to the platform (hard-coded path, no link
  at all).
- `data.tf`: the data source's `depends_on`, holed with `???`.
- `outputs.tf`: two values holed with `???`.

Run `terraform init` then `terraform apply`: you will first see syntax errors on
the `???`, then, once those are filled, the provisioner failure
`Error running command '... exit status 1'` while `publication` is not wired to
the platform.

## ✅ Objective

1. **Remove the redundant `depends_on`.** `local_file.manifeste` already
   references `random_pet.nom.id` in its `content`: the order is guaranteed
   without it.

2. **Make a dependency implicit.** `null_resource.publication`'s command
   hard-codes the manifest's path. Replace it with a reference to
   `local_file.manifeste.filename`.

3. **Add the only legitimate `depends_on`.** `null_resource.publication` needs
   the `.pret` marker placed by `null_resource.socle`, which exposes no data. No
   reference can express that link: add `depends_on = [null_resource.socle]`,
   and nothing else.

4. **Wire the data source and the outputs.** `data.local_file.publie` reads a
   literal path: add its `depends_on` towards `null_resource.publication`.
   `nom_livraison` is the `random_pet`'s `id`, `taille_publie` the length of the
   content read.

After your `apply`, `terraform plan` must propose nothing.

## 🧭 The rule that governs everything

> A block **never** declares in `depends_on` a resource it **already
> references** elsewhere.

The criterion: does the resource use any **data** from the upstream in its
arguments? If yes, a reference is enough. If no, and only then, `depends_on`.

## 🔍 Validation

```bash
dsoxlab check write-code-depends-on
```

Eight tests. They decode the JSON plan's `configuration` section, which exposes
for each block its `depends_on` and its expressions' `references`. The central
test refuses any `depends_on` duplicating a reference, wherever it is placed. No
test reads your `.tf`.
