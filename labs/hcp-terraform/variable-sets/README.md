# Fifteen precedence levels, and one inversion

HCP Terraform stacks **fifteen** value sources for a single variable. The list
reads in a minute and sticks badly, because it contains an inversion almost
nobody notices.

This lab needs **no HCP Terraform account**: objective 6 is assessed by multiple
choice, and everything is simulated locally.

## The table, strongest to weakest

| Rank | Source |
| --- | --- |
| 1 | `-var` on the command line |
| 2 | `TF_VAR_` in the environment |
| 3 | **priority** variable set, global |
| 4 | **priority** variable set, org-owned, project scope |
| 5 | **priority** variable set, org-owned, workspace scope |
| 6 | **priority** variable set, project-owned, project scope |
| 7 | **priority** variable set, project-owned, workspace scope |
| 8 | **workspace** variable |
| 9 | normal variable set, project-owned, workspace scope |
| 10 | normal variable set, project-owned, project scope |
| 11 | normal variable set, org-owned, workspace scope |
| 12 | normal variable set, org-owned, project scope |
| 13 | normal variable set, **global** |
| 14 | `*.auto.tfvars` |
| 15 | `terraform.tfvars` |

## The inversion

Look at ranks 3 to 7, then 9 to 13. They descend in opposite directions.

Among **normal** variable sets, the **narrowest** scope wins: workspace beats
project, which beats global. That is the intuition, and it is right.

Among **priority** sets it is the **other way round**: global beats project,
which beats workspace.

> When a variable set is priority, the values take precedence over any variables
> with the same key set at a more specific scope.

It makes sense once read: "priority" exists precisely to impose a value from
above, against whatever a rung closer to the ground had set. But anyone learning
the table without reading that sentence will remember it backwards for half the
cases.

## Two more surprises

**The files are at the bottom.** `terraform.tfvars` beats nothing at all, and
`*.auto.tfvars` barely more. The smallest global variable set overrides them.
That is the opposite of local Terraform, where those files dominate `default`
values.

**An HCL map has no order.** When two variable sets share the **same** scope and
the **same** owner, nothing in the precedence separates them: the
**lexicographic order of their names** decides, by Unicode code points. Digits
come before uppercase, which comes before lowercase.

## The check that stops you writing the answer out

The six supplied cases can be resolved by hand in ten minutes, and a resolution
naming them one by one would pass.

So the tests replay the configuration with **eight cases they generate
themselves**, which you have never seen, two of them aimed at the inversion and
one empty. A resolution that **walks the table** handles them all; one written
case by case handles none.

Hence the brief's constraint: name no case explicitly.

## The empty case, and why it matters

A case with no source set must resolve to a **sentinel**, not to `null` and
certainly not to an error.

It is a writing detail that costs dearly: indexing `[0]` on an empty list brings
down the **whole plan**, and every other case with it. A `try()` returns the
sentinel and lets the rest work.

## Over to you

```bash
dsoxlab run hcp-terraform-variable-sets
dsoxlab check hcp-terraform-variable-sets
dsoxlab hint hcp-terraform-variable-sets
```

Twelve tests, offline. The table is compared **position by position**: a single
inversion fails, and the message names the offending rank rather than printing
fifteen unreadable lines.

Exam objective targeted: **6b**.

Reference: [variables in HCP Terraform](https://developer.hashicorp.com/terraform/cloud-docs/workspaces/variables)
