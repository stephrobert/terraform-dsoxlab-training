# Scenario: the run workflow, played in two steps then qualified

**Exam objective targeted: 6a, analyze the HCP Terraform run workflow.**

Objective 6 is assessed by multiple choice: no HCP Terraform account, no remote run. But a
run is above all a **strict division between a plan and an apply**, where the apply reuses
the plan already computed instead of computing another one. That division can be played
locally, with saved plans, and that is what this lab starts with.

A team has just moved to HCP Terraform. Its runs sometimes apply on their own, sometimes
wait, sometimes end without applying anything, and nobody can say in advance which will
happen.

## Capability targeted

Play a run in two steps and see what the saved plan refuses, then determine, for a
described run, whether it applies automatically, waits for confirmation, ends with no
apply, or does not even exist. And place the eleven stages of a run in the order the
documentation gives.

## Where the learner starts

`challenge/work` holds two directories:

1. `run/`, with a supplied configuration: one `local_file` resource whose content comes
   from a variable. Nothing to change there, everything to play.
2. `analyse/`, six runs described in `situations.auto.tfvars.json` (trigger, auto-apply
   setting, execution mode, whether the plan holds changes, whether the author may apply),
   with `verdicts.tf`, `etapes.tf` and `faits.tf` holed with `???`.

## The state to reach

1. A first run is played in `run/`: its plan is saved as `run1.tfplan`, and applying **that
   plan** creates `rapport.txt` holding `premier-run`.
2. A second run is planned into `run2.tfplan` with `second-run`, and it **stays pending**:
   the file on disk still holds the first run's value.
3. The `verdicts` output qualifies the six runs with five words and no more:
   `plan_speculatif`, `planned_and_finished`, `apply_automatique`, `attend_confirmation`,
   `aucun_run_distant`. A pull request is speculative whatever the auto-apply setting says;
   a plan with no changes ends the run; a run trigger gives no right to auto-apply.
4. `etapes_du_run` gives the eleven stages in order, OPA policy check **before** cost
   estimation and Sentinel policy check **after**.
5. `faits` states the two operations that do not block the run queue, the one stage where a
   failing run task no longer halts the run, and what a `local` execution mode workspace
   still provides.

## How it is proven

The run half reads the disk and the saved plans, through `terraform show -json`: the state
of the system, never the commands typed. Three properties measured on 2026-09-25 with
Terraform 1.16.1 carry it:

- applying a saved plan opens no confirmation prompt, because the plan has already decided;
- replaying the same plan after the apply is refused with `Saved plan is stale`, the local
  counterpart of a workspace's run queue;
- passing `-var` to the apply of a saved plan is refused with `Can't change variable when
  applying a saved plan`, the counterpart of a run locked to its configuration version and
  set of variable values.

Those last two tests cannot be green before the work: with no apply the first plan is not
stale, and with no saved plan there is nothing to replay. Checked by degrading the
solution: applying the second plan instead of leaving it pending drops the score to 12/15,
and an `apply` that never goes through a saved plan drops it to 12/15 as well.

The analysis half reads `terraform output -json` only. The six cases are built so that no
constant answer passes, and each is asserted separately so the message says which one is
wrong. Every figure and every rule comes from the official documentation, read on
2026-09-25, and the tests carry those links in their failure messages.
