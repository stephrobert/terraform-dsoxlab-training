# Permissions add up, they do not override

## The situation

**Exam objective targeted: 6b, workspaces and their configuration options, access
management included.**

Objective 6 is assessed by multiple choice, and needs no account. This lab therefore has
you **write the rule** rather than recite it: a wrong rule shows up on six cases, a
memorised sentence does not.

An organization grants rights at three levels, and two teams disagree about what they may
do on the same workspace. One holds an organization-wide permission and a modest role on
the workspace; the other the opposite. Both believe the closest right wins.

## Capability targeted

Work out a team's effective access on a workspace from what it holds at organization,
project and workspace level, and know the two role scales, which are not the same one.

## Where the learner starts

`challenge/work` holds two directories:

1. `acces/`, six teams described in `equipes.auto.tfvars.json` by what they hold at each of
   the three levels, with the scale and the equivalences supplied, and two `???` to fill.
2. `questionnaire/`, five answers to place in `reponses.auto.tfvars`.

## The state to reach

1. `acces_effectif` maps each team to its effective access, computed by a rule that names
   no team: a seventh one would be handled without rewriting anything.
2. That rule returns the **most permissive** of the three levels, never the most specific.
3. `equipes_qui_peuvent_appliquer` lists the teams that can launch an apply, which takes at
   least write access: the `plan` role proposes, it does not apply.
4. The five answers establish what decides between two levels, who can in practice start a
   plan on a VCS-backed workspace, how long a run task's access token lives, and the role
   that sits between read and write on a workspace, then between write and admin on a
   project.

## The trap, and where it comes from

Everywhere else, the permission set at the most specific level wins. Here it does not:

> Each permission is additive, granting a user the highest level of permissions possible,
> regardless of which scope set that permission.

The documentation's two examples bracket the rule exactly, and the lab uses them as case 1
and case 2: `Manage all workspaces` at the organization beats a workspace `Read`, while
`View all workspaces` does **not** beat a workspace `Write`. Additive does not mean the
organization wins; it means the widest right wins.

## Two scales that are not the same

Read at their source on 2026-09-25:

| Scope | Roles, least to most permissive |
| --- | --- |
| workspace | `Read` < `Plan` < `Write` < `Admin` |
| project | `Read` < `Write` < `Maintain` < `Admin` |

`Plan` exists only on workspaces, `Maintain` only on projects, and they do not land in the
same place. That is what rules out comparing two levels by eye.

## How it is proven

The tests read `terraform output -json` only: what the configuration computes, never what
it contains. Each of the six cases is asserted separately, so the message says which one is
wrong, and the last test makes the ranking **decide** something rather than merely classify:
a team stuck at `plan` must be excluded from those that can apply, and the three that write
or better must be included.

Checked by degrading the solution: the ordinary intuition, where the most specific level
wins, gives 10/13, and counting `plan` among those that can apply gives 12/13.

## 🎯 Challenge: work out what six teams may actually do

### 📦 Starting point

`challenge/work` holds two directories. **No account needed.**

| File | State |
| --- | --- |
| `acces/equipes.auto.tfvars.json` | **supplied**, six teams described |
| `acces/variables.tf`, `acces/versions.tf` | **supplied** |
| `acces/acces.tf` | two `???`, with the scale and equivalences supplied |
| `questionnaire/questionnaire.tf` | **supplied**, do not change |
| `questionnaire/reponses.auto.tfvars` | five `???` to answer |

### ✅ Objective

1. **Compute each team's effective access** on the workspace, from what it holds
   at organization, project and workspace level.
2. **List the teams that can apply.** Applying takes at least write access.
3. **Answer the five questions.**

Write a **rule**, not a list of answers: no team key should appear in your
expression, and a seventh team must be handled without rewriting anything.

### 🧭 The trap, and it is a solid habit

Everywhere else, the permission set at the most specific level wins. Here,
permissions **add up**, and the effective access is the **most permissive** of
the three levels — whoever granted it.

Two cases in the file are the documentation's own examples, one in each
direction. If your rule gets both right, it is almost certainly the right rule.

Careful with the other over-correction: nothing accumulates. Two read-level
grants do not make a write.

### ⚠️ The two scales are not the same one

| Scope | Roles |
| --- | --- |
| workspace | `Read` < `Plan` < `Write` < `Admin` |
| project | `Read` < `Write` < `Maintain` < `Admin` |

`plan` exists only on workspaces, `maintenance` only on projects, and it sits
above write. The supplied scale already merges both; use it rather than
comparing by eye.

### 🔍 Validation

```bash
dsoxlab check hcp-terraform-projects-teams
```

Thirteen tests, all reading `terraform output -json`: what your configuration
**computes**, never what it contains.

Stuck? `dsoxlab hint hcp-terraform-projects-teams`.
