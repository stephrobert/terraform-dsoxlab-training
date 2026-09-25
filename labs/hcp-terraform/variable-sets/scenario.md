# Scenario: HCP Terraform's fifteen-level precedence, simulated locally

**Exam objective targeted: 6b (HCP Terraform workspaces and their configuration options),
an objective assessed by multiple-choice questions only.**

Fifteen levels, and one inversion almost nobody notices: among **priority** variable sets,
the **broadest** scope wins, whereas among normal sets it is the **narrowest**. This lab
has the complete table built in HCL, then judged by Terraform on cases the learner does not
see before the correction. No HCP Terraform account is required.

## Capability targeted

Rank any HCP Terraform value source in the official fifteen-level order, and predict the
retained value when several sources define the same key, including between two sets of
identical scope and ownership.

## Where the learner starts

`challenge/work` holds a configuration that already applies, with no remote infrastructure
(`local` provider), `terraform init` already run:

- `VOCABULAIRE.md`: the fifteen imposed source identifiers, shuffled, from the five
  `priority_*` to `auto_tfvars` and `terraform_tfvars`, through `cli_var`, `tf_var_env`,
  `workspace`, the four normal `set_*` and `set_global`.
- `variables.tf` and `cas.auto.tfvars`, not to be modified: `variable "cas"` as a
  `map(map(string))` maps, for each case, a source to its value; `variable "duel_lexical"`
  pits two sets of identical scope and owner against each other.
- `precedence.tf` holed: `local.ordre`, a list of fifteen entries of which eleven are
  `"???"`. The four already in place (`cli_var`, `tf_var_env`, `workspace`,
  `terraform_tfvars`) are anchors: they prevent guessing the table by rotating it one notch.
- `resolution.tf` to be written, which must walk `local.ordre` without ever naming a case
  explicitly, and `qcm.tf` holed: five statements to settle as booleans.

## The state to reach

1. `ordre_precedence` exposes the fifteen identifiers in the exact official order, most to
   least prioritary.
2. `resolutions` carries, for each case, the retained source **and** its value.
3. A case with no source resolves to the `default_hcl` sentinel, never to `null` nor to a
   plan error.
4. `gagnant_lexical` separates by Unicode code points, not by order of appearance in the
   map, which does not exist.
5. `reponses` carries the five expected booleans, and the apply is idempotent.

## How it is proven

The tests never read a `.tf` or a `.tfvars` of the learner's.

- `terraform apply` then `terraform output -json`: `ordre_precedence` is compared position
  by position with the official list, and a single inversion fails the assertion, the
  message naming the offending rank.
- **The anti-copy check**: a second plan replaces `cas` entirely with eight cases the tests
  generate, then `terraform show -json` is queried on
  `.planned_values.outputs.resolutions.value`. A resolution written case by case then gives
  wrong winners. Two cases aim at the inversion: `priority_org_workspace_scoped` beats
  `priority_project_project_scoped`, and `set_project_project_scoped` beats
  `set_org_workspace_scoped`.
- A third plan injects an empty case and requires the sentinel: indexing `[0]` on an empty
  list would bring down the whole plan, not just that case.
- A `-var` on `duel_lexical` mixes uppercase and digits, which match no natural writing
  order, so that only a sort by code points passes.
- `terraform plan -detailed-exitcode` exits 0. An empty `challenge/work` exposes no output
  and fails on the first assertion.

Every figure was read at its source on 2026-09-25, and the tests carry that link in their
failure messages.
