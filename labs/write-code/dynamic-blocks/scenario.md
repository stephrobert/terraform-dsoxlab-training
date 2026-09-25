# Scenario: generate blocks, and know when not to

**Exam objective targeted: 2d.**

A `dynamic` block builds nested blocks wherever the provider's schema exposes them, and nowhere else: it cannot produce a meta-argument block such as `lifecycle`, because Terraform must process those blocks before it can safely evaluate any expression. The lab covers that wall, plus the reflex costing the most at review time: turning everything into a `dynamic`, including what never varies.

## Capability targeted

Produce a cloud-init document whose number, order and part names come from a variable, keeping literal the block that does not vary, filtering in the `for_each` rather than in the `content`, and writing by hand the `lifecycle` block no `dynamic` can generate.

## Where the learner starts

`challenge/work` holds a configuration neither initialised nor applied, limited to the `hashicorp/cloudinit` and `hashicorp/local` providers:

- `versions.tf`: complete, not to be touched. `required_version = ">= 1.15.0"`, both providers pinned.
- `variables.tf`: complete. `modules` is a `map(object({ contenu = string, actif = bool }))`, with three default entries, one of them carrying `actif = false`.
- `main.tf`: the `cloudinit_config.principal` data source exists. Its first part, the `#cloud-config` header common to every host, is already written as a literal `part` block. The `dynamic "part"` block that follows is holed with `???` on the iterated collection, on the filename and on the content.
- `main.tf` also holds `local_file.rendu`, which writes the rendering, and **a deliberately present `dynamic "lifecycle"`**: the configuration does not pass `terraform validate` as it stands. That is not a typo to fix, it is a dead end to understand.
- `outputs.tf`: `parties` and `nb_parties` are started, with `???` on the expression.

The brief requires running `terraform validate` before any modification. The starting observation is twofold, verified on Terraform 1.15.4: the `???` in the `dynamic "part"` block first raise syntax errors (`Invalid expression`), and once that block is written, the `dynamic "lifecycle"` hits `Blocks of type "lifecycle" are not expected here.` (the message names the **label** of the targeted block, never the word `dynamic`). Half the lab rests on that wall, `lifecycle` cannot be generated.

## The state to reach

1. The configuration validates: no `dynamic` placed on a meta-argument block any more, and `local_file.rendu` carries a literally written `lifecycle` block, with `create_before_destroy = true`.
2. After the default apply, `data.cloudinit_config.principal` carries exactly three parts: the literal header first, then the two active modules, sorted by key.
3. Each generated part's filename derives from the map's **key**, not from a rank: the module's key appears as such in the `filename`.
4. The module marked `actif = false` produced no part: the filter is in the `for_each`, never in the `content`.
5. With `-var 'modules={}'`, exactly **one** part remains, the header: the fixed part was not absorbed into the dynamic block.
6. With four active modules, five parts, in key order: the same configuration follows the variable without being touched.
7. `local_file.rendu` holds the data source's rendering, and a content change plans as a creation then a destruction, never the reverse.
8. The outputs are wired: `parties` is the ordered list of filenames, `nb_parties` their count.
9. A plan run right after the apply proposes nothing.

## How it is proven

The tests drive Terraform and never read the `.tf` files.

- `terraform validate -json`: `valid` is `true`. On the starting version the same call returns `false` (syntax errors on the `???`, then `Blocks of type "lifecycle" are not expected here.` once the `dynamic "part"` is completed).
- `terraform show -json`: in `values.root_module.resources`, the `data.cloudinit_config.principal` entry is in `mode: "data"` and its `values.part` is an **ordered list**. The tests compare its length, the sequence of `filename` values and each element's `content_type`. That is where, and nowhere else, the number of blocks actually generated can be read.
- Variants: the tests copy the workdir and its `.terraform` into a temporary directory, apply with `-var 'modules={}'` then with four active modules, and read `show -json` back. One part, then five. Hard-written blocks cannot follow both values at once, and a `dynamic` that had swallowed the header falls to zero on the first case.
- Filtering: the inactive module's key appears in no `filename`, and its content in no `content`.
- Key and not rank: every generated `filename` contains the corresponding map key. An iteration using only `.value` cannot produce those names.
- `lifecycle`: `terraform plan -out` with a module's content changed, then `terraform show -json` of the plan. `resource_changes` carries `local_file.rendu` with `actions == ["create", "delete"]`. The reverse order would prove `create_before_destroy` is missing, and no dynamic block could have placed that block.
- `terraform output -json`: `parties` is a list of strings of the same length as `part`, `nb_parties` a matching number.
- `terraform plan -detailed-exitcode`: code 0 right after the final apply.

None of these checks passes on an empty `challenge/work`: the first `show -json` finds no resource there.

Reference: https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/blocs-dynamiques/
