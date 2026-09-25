# The most permissive wins, not the most specific

The Professional's objective 6 is assessed **by multiple choice**, and needs no
account. This lab has you write the rule instead of reciting it, because a wrong
rule shows up on six cases and a memorised sentence does not.

It closes on a habit built by every other permission system you have used.

## Additive, and what that actually means

> Each permission is additive, granting a user the highest level of permissions
> possible, **regardless of which scope set that permission**.

Rights can be granted at three levels — organization, project, workspace — and a
team's effective permissions are the sum of all of them. Two examples from the
documentation bracket the rule:

| A team holds | Effective access |
| --- | --- |
| `Manage all workspaces` on the org **+** `Read` on the workspace | **Manage all workspaces** |
| `View all workspaces` on the org **+** `Write` on the workspace | **Write** |

The first surprises people who expect the workspace to have the final say. The
second corrects the over-correction: additive does not mean the organization
wins, it means **the widest right wins**, whoever granted it.

Note what it does not mean either: two `Read` grants do not add up to a `Write`.
Nothing is accumulated, the maximum is taken.

## Two scales, and they are not the same one

Read at their source on 2026-09-25:

| Scope | Roles, least to most permissive |
| --- | --- |
| **workspace** | `Read` < `Plan` < `Write` < `Admin` |
| **project** | `Read` < `Write` < `Maintain` < `Admin` |

`Plan` exists only on workspaces; `Maintain` only on projects, and it sits
**above** write. Comparing two levels by eye is therefore unsafe, and the rule
has to rank them explicitly.

`Plan` is worth a closer look: it lets a team propose a change without ever
applying it. That is what makes it useful — it opens review without opening
production — and it is why "can apply" starts at write, not at plan.

## Permissions you did not grant

Two cases where access leaks in through a system you connected:

- on a VCS-backed workspace, **anyone who can merge into the tracked branch** can
  indirectly queue plans there, "regardless of whether they have explicit
  permission to queue plans or are even a member of your HCP Terraform
  organization". With auto-apply on, merging starts runs;
- a run task receives an access token, and **all of them live for 10 minutes**.

"An integrated system is able to delegate any level of access that it has been
granted." Your permission matrix is only as tight as what you connected to it.

## Over to you

```bash
dsoxlab run hcp-terraform-projects-teams
dsoxlab check hcp-terraform-projects-teams
dsoxlab hint hcp-terraform-projects-teams
```

Thirteen tests, all reading `terraform output -json`. The six cases are asserted
one by one, so the message says which is wrong, and the last one makes the
ranking decide something rather than merely classify.

Exam objective targeted: **6b**.

Reference: [permissions overview](https://developer.hashicorp.com/terraform/cloud-docs/users-teams-organizations/permissions)
