# Scenario: the stream a run sends back, and the three ways to start one

**Exam objective targeted: 6a, analyze the HCP Terraform run workflow.**

Objective 6 is assessed by multiple choice, and needs no account. But what a CLI receives
from a remote run — "Running plan in HCP Terraform. Output will stream here" — is the very
same structured stream `terraform apply -json` produces locally. So this lab records a real
one, and reads it.

A run went through last night. Two resources exist, a third does not, and the summary the
stream carries says three additions. Someone has to work out what actually happened.

## Capability targeted

Read the stream of a run rather than its final message: tell what was announced from what
took place, find the resources that failed, and know which of the three workflows allows
what.

## Where the learner starts

`challenge/work` holds three directories:

1. `flux/`, a supplied configuration with three `local_file` resources. The third one
   **fails on purpose**: it writes below a path whose parent is a file. The apply therefore
   ends with a non-zero status, and that is the expected outcome.
2. `analyse/`, a configuration holed with five `???`, which must read the recorded stream
   and draw its conclusions.
3. `questionnaire/`, five answers to place in `reponses.auto.tfvars`, on the three
   workflows.

## The state to reach

1. The run is played in `flux/` with its stream recorded:
   `terraform apply -auto-approve -json > run.jsonl`. Two files are created, the third is
   not.
2. `par_type` counts the stream's messages by type, read from the stream rather than
   written out by hand.
3. `resume_annonce` gives the `changes` object of the only `change_summary` the stream
   carries.
4. `adresses_abouties` and `adresses_en_echec` separate the resources that completed from
   the one that errored.
5. `ecart_entre_annonce_et_abouti` gives the difference between the two, which is the point
   of the whole exercise.
6. The five answers establish which workflow forbids a remote apply, what a CLI run
   uploads, where its variable values come from, which workflow is recommended for
   non-interactive use, and which file excludes content from the upload.

## Why the run fails, and why that is the subject

Measured on 2026-09-25 with Terraform 1.16.1, on the same configuration depending on
whether it completes:

| Run | `change_summary` messages |
| --- | --- |
| completes | two, `plan` then `apply` |
| fails midway | **one**, `plan` alone |

On an interrupted run, the only summary the stream carries is the one the plan
**announced**. It says `add: 3` where two resources were created, and nothing in that
message says otherwise. What took place is only readable from the `apply_complete`
messages.

A run that completes could not measure that: everything planned completes, and both halves
of the stream tell the same story.

## How it is proven

The tests re-read `flux/run.jsonl` and recompute what the analysis should have returned, so
what is compared is the learner's analysis against the truth of their own stream, never
against a frozen number. A hand-written stream would not pass either: the tests require the
system to agree, two files present, the impossible one absent, and exactly two resources in
the state.

Checked by degrading the solution: filtering on `operation == "apply"`, which is the right
reflex on a run that completes, drops the score to 8/12; reading the addresses from
`planned_change` instead of `apply_complete` drops it to 10/12.
