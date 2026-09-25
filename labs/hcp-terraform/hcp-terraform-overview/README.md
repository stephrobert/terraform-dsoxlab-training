# A run is a plan, then an apply of that plan

The Professional's objective 6 is the only one assessed **by multiple choice**.
But a run is not a piece of trivia: it is a discipline, and that discipline can
be played locally. This lab therefore needs **no account**, and it still has you
run something.

## The saved plan is the local counterpart of a run

HCP Terraform "enforces Terraform's division between plan and apply operations.
It always plans first, then uses that plan's output for the apply." A saved plan
does exactly that:

```bash
terraform plan -out=run1.tfplan
terraform apply run1.tfplan        # no confirmation prompt: the plan decided
```

Three refusals give that division its meaning, and all three were measured on
2026-09-25 with Terraform 1.16.1.

**Replaying an applied plan is refused.**

```
Error: Saved plan is stale

The given plan file can no longer be applied because the state was changed by
another operation after the plan was created.
```

That is the local counterpart of a workspace's run queue: "if there's already a
run in progress, the new run won't start until the current one has completely
finished — HCP Terraform won't even plan the run yet, because the current run
might change what a future run would do."

**Changing a variable at apply time is refused.**

```
Error: Can't change variable when applying a saved plan
```

Same property as a run, which is locked to a configuration version and a set of
variable values: "if you change variables or commit new code before the run
finishes, it will only affect future runs."

**A plan with no changes is not applyable.** `terraform show -json` says so in a
field, `applyable: false`, and HCP Terraform says the same thing with a run
state: **Planned and finished**. The `allow empty apply` run mode is the only way
round it.

## What decides whether a run applies on its own

Four things, and the auto-apply setting is only one of them:

| Situation | Outcome |
| --- | --- |
| pull request on a VCS workspace | **speculative plan**, can never apply |
| `terraform plan` through the CLI integration | **speculative plan** |
| plan with no changes | **planned and finished** |
| auto-apply on, commit on the tracked branch, author may apply | **applies on its own** |
| auto-apply on, run queued by a **run trigger** | **waits for confirmation** |
| execution mode `local` | **no remote run at all** |

The last two are what candidates get wrong. "Some plans can't be auto-applied,
like plans queued by run triggers or by users without permission to apply runs":
the setting is on, the trigger gives no right to it. And a workspace in `local`
execution mode "acts only as a remote backend for Terraform state", with no
Sentinel, no cost estimation and no notifications, since all three rely on remote
execution.

## The eleven stages, and the one that surprises

| # | Stage | | # | Stage |
| --- | --- | --- | --- | --- |
| 1 | pending | | 7 | **cost estimation** |
| 2 | fetching | | 8 | **sentinel policy check** |
| 3 | pre-plan | | 9 | pre-apply |
| 4 | plan | | 10 | apply |
| 5 | post-plan | | 11 | post-apply |
| 6 | **opa policy check** | | | |

The OPA check runs **before** cost estimation, Sentinel's **after**. That is not
trivia: it is why a Sentinel rule can read an estimated cost and an OPA rule
cannot.

One more asymmetry worth keeping: run tasks can run at several stages, and a
failing task halts the run at every one of them **except post-apply** — there is
nothing left to halt, the infrastructure is already provisioned.

## Over to you

```bash
dsoxlab run hcp-terraform-hcp-terraform-overview
dsoxlab check hcp-terraform-hcp-terraform-overview
dsoxlab hint hcp-terraform-hcp-terraform-overview
```

Fifteen tests. The first four play a real run and read the saved plans through
`terraform show -json`; the others read what the configuration computes, never
what it contains.

Exam objective targeted: **6a**.

References: [run states and stages](https://developer.hashicorp.com/terraform/cloud-docs/run/states)
and [remote operations](https://developer.hashicorp.com/terraform/cloud-docs/run/remote-operations)
