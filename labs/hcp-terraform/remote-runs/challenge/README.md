# The stream a run sends back, and the three ways to start one

## The situation

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

## 🎯 Challenge: read the stream of a run that failed midway

### 📦 Starting point

`challenge/work` holds three directories. **No account needed.**

| File | State |
| --- | --- |
| `flux/main.tf` | **supplied**, do not change: its third resource fails on purpose |
| `analyse/analyse.tf` | five `???`: read the stream and draw conclusions |
| `questionnaire/questionnaire.tf` | **supplied**, do not change |
| `questionnaire/reponses.auto.tfvars` | five `???` to answer |

### ✅ Objective

1. **Play the run and record its stream** in `flux/`:

   ```bash
   terraform apply -auto-approve -json > run.jsonl
   ```

   It will end with a non-zero status. **That is the expected outcome**: the
   third resource writes below a path whose parent is a file.

2. **Analyse the stream**: messages by type, the summary it carries, the
   addresses that completed, the one that errored, and the difference between
   what was announced and what took place.

3. **Answer the five questions** on the three workflows.

### 🧭 The trap, and it closes on a sensible habit

The stream of a run that **completes** carries two `change_summary` messages, one
for the plan and one for the apply. Filtering on the apply is then the right
thing to do.

The stream of a run that **fails midway** carries only one, the plan's. Filtering
on the apply returns nothing, and the summary you are left with announces more
than actually happened.

That difference is the whole point of the exercise. Count, do not trust.

### ⚠️ The stream cannot be written by hand

The tests require the system to agree with it: two files present, the impossible
one absent, and exactly two resources in the state.

### 🔍 Validation

```bash
dsoxlab check hcp-terraform-remote-runs
```

Twelve tests. They re-read `flux/run.jsonl` and recompute what your analysis
should have returned, so nothing is compared against a frozen number: a different
stream gives different expectations.

Stuck? `dsoxlab hint hcp-terraform-remote-runs`.
