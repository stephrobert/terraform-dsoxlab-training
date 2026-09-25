# Scenario: permissions add up, they do not override

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
