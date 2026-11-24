# Objective 6, where the sub-objectives cross

## The situation

**Exam objective targeted: the whole of 6** (6a the run workflow, 6b workspaces and access,
6c credentials, 6d policy as code).

Objective 6 is the only one assessed **by multiple choice**: HashiCorp asks for no hands-on
work in HCP Terraform. This capstone therefore needs **no account**, like the seven labs of
the section.

## What a capstone adds to the seven labs

Each of the seven labs covers one sub-objective. Here, every situation crosses **two**, and
that is the whole exercise: taken separately, each field is handled by a reflex you already
have; together they reinforce or cancel one another, and the order in which you look at
them decides the outcome.

A team is preparing a compliance audit. It has to say, for six described runs, what actually
happened, attach its audit directory to the right workspace, and publish a sheet the auditor
can verify without the service token ever leaving.

## Capability targeted

Settle a situation where several rules of objective 6 apply at once, without confusing what
each of them decides.

## Where the learner starts

`challenge/work` holds three directories:

1. `audit/`, seven situations described in `situations.auto.tfvars.json`, each carrying a
   trigger, an auto-apply setting, an execution mode, whether the plan holds changes, and
   the state of a policy with both conditions of its override. Two files holed with `???`;
2. `rattachement/`, missing its `cloud` block;
3. `secret/`, where a service sheet must be written without the token entering it.

## The state to reach

1. `verdicts` qualifies the seven situations, with seven possible words and **six different
   outcomes**: no constant answer passes, and there is no majority to play.
2. `gouvernance` establishes what allows an override, what becomes of policies in `local`
   execution mode, and where a run's credentials live.
3. `rattachement/` attaches **by name** to the `audit-conformite` workspace of the
   `atelier-dsoxlab` organization, and its `init` reaches the authentication step.
4. `secret/` writes a sheet carrying the token's fingerprint and never the token, and the
   state holds the token's value nowhere.

## The three crossings that cost

**A failing `mandatory` policy on a pull request blocks nothing.** There is nothing to
block: a speculative plan cannot apply. The "mandatory therefore blocked" reflex answers the
wrong question.

**A failing `advisory` does not prevent an auto-apply.** The enforcement level decides one
thing only, and that is not it.

**A `local` execution mode makes the policy question moot.** Nothing runs at HCP Terraform,
so no policy is evaluated there, whatever its level.

## How it is proven

The tests read `terraform output -json` for the audit, the initialization output for the
attachment, and the state for the secret. One test also checks that **all seven verdicts
differ**: two cases receiving the same outcome would signal a rule that confuses them.

For the attachment, two conditions are required together, because a measurement from
2026-09-25 demands it: a configuration holding both `backend` and `cloud` prints "Required
token could not be found" **next to** its fault. The boundary marker alone would therefore
declare a broken configuration correct.

For the secret, the whole state file is swept rather than the one expected attribute: a
secret moved elsewhere would be just as exposed. The last test exercises both sides, since a
sheet emptied of everything would satisfy the prohibition while serving no purpose.

## 🎯 Challenge: the compliance audit

### 📦 Starting point

`challenge/work` holds three directories. **No HCP Terraform account.**

| File | State |
| --- | --- |
| `audit/situations.auto.tfvars.json` | **supplied**, seven runs described |
| `audit/variables.tf`, `audit/versions.tf` | **supplied** |
| `audit/verdicts.tf` | one `???`: each situation's verdict |
| `audit/gouvernance.tf` | three `???`: facts to establish |
| `rattachement/versions.tf` | the `cloud` block is missing |
| `secret/main.tf` | two `???`: the sheet and its fingerprint |
| `secret/variables.tf`, `jeton.auto.tfvars` | **supplied**, do not change |

### ✅ Objective

1. **Qualify the seven situations.** Seven words are possible; six are enough, and
   each is used exactly once.
2. **Establish three governance facts.**
3. **Attach `rattachement/`** to the `audit-conformite` workspace of the
   `atelier-dsoxlab` organization, by name.
4. **Write the service sheet** without the token entering the state.

Write a **rule**, not a list of answers: no situation key should appear in your
expression.

### 🧭 The rules do not commute

Every situation crosses two sub-objectives. The order in which you ask the
questions decides the outcome, because each one makes the next moot: a workspace
that runs nothing evaluates no policy; a run that can never apply has nothing to
block; a plan with no changes applies nothing.

### ⚠️ Six different outcomes

That is how the capstone is built, and a test checks it. Two situations receiving
the same verdict would signal a rule that confuses them, not two cases that
happen to look alike.

### 🔍 Validation

```bash
dsoxlab check certifications-professional-capstone6-hcp
```

Eight tests. The audit is read from `terraform output -json`, the attachment from
the initialization output, and the secret from the state, swept in full.

Stuck? `dsoxlab hint certifications-professional-capstone6-hcp`.
