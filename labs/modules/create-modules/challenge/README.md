# 🎯 Challenge: make an inherited module reusable again

## 📦 Starting point

`challenge/work` holds a two-level project: a root and a local module,
`modules/livrable/`. The root wants to deliver **three environments** with a
single `module` block carrying `for_each`.

Start with the observation, before any change:

```bash
terraform init
```

The `init` **fails**, and its message names both the problem and the fix. That is
the starting point of this lab: read it in full.

| File | What it is |
| --- | --- |
| `versions.tf`, `variables.tf` (root) | complete, **do not touch** |
| `main.tf` (root) | the module call, one argument is missing |
| `outputs.tf` (root) | two outputs to write, shipped commented out |
| `modules/livrable/main.tf` | the module, with **an inherited flaw** |
| `modules/livrable/versions.tf` | its requirements, one line to add |
| `modules/livrable/variables.tf` | three variables, undocumented |
| `modules/livrable/outputs.tf` | two outputs to complete |

## ✅ Objective

Make this module **callable several times**, by removing what prevents it, then
by properly handing it the provider configuration it needs.

## 📋 What you must obtain

1. **No provider configuration** lives in `modules/livrable/` any more. They stay
   at the root, and the module keeps its `required_providers`: configurations are
   inherited, source and version requirements never are.
2. The module **declares** the aliased configuration it expects, under its
   `local` requirement.
3. The root call **hands it over**, under the name the child expects.
4. Inside the module, `local_file.archive` stays on the aliased configuration,
   `local_file.manifeste` on the default one.
5. The `for_each` produces **three instances**, `module.livrable["dev"]`,
   `["preprod"]` and `["prod"]`.
6. Every module variable carries a non-empty **`description`**, and **none** has
   a `default`: they stay mandatory.
7. Both module outputs are completed, and the root ones **aggregate** the three
   instances into an object indexed by environment.
8. `terraform apply` succeeds, the six files under `livraisons/` exist, and
   `terraform plan -detailed-exitcode` exits **0**.

## ⚠️ The heart of the matter

The official rule fits in one sentence: **"a module intended to be called by one
or more other modules must not contain any `provider` blocks"**. Terraform does
not enforce it on principle, it enforces it because it cannot do otherwise: a
module configuring its own providers can only be instantiated once.

Three errors await you, in this order, and each points at the next step:

| Message | What it asks for |
| --- | --- |
| `Module is incompatible with count, for_each, and depends_on` | remove the provider configuration from the child |
| `Provider configuration not present` | declare the expected alias in the module |
| `Missing required provider configuration` | pass that configuration from the caller |

Removing the `for_each` would make the first error disappear. That is not the
solution: the tests require the three instances.

## 🔍 Validation

`dsoxlab check modules-create-modules` proves, by execution:

- no `provider_config` entry carries a `module_address`, and the `archive` alias
  is still declared at the root;
- the `module` block does carry a `for_each`, and the state holds the three
  indexed addresses;
- each child resource's `provider_config_key` points at the right configuration,
  which proves the `providers` argument was wired;
- every module variable has a `description` and no `default`;
- both root outputs have three keys, and the announced paths match real files;
- `plan -detailed-exitcode` returns **0**.

No test opens your `.tf` files.

Stuck? `dsoxlab hint modules-create-modules`.
