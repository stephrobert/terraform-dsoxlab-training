# What blocks a run, and what lets you override it

The Professional's objective 6 is the only one assessed **by multiple choice**:
HashiCorp asks for no hands-on work in HCP Terraform. This lab therefore starts
no remote run and needs **no account**. It has you reason, and evaluate real
plans.

The trap it covers catches candidates out: believing a `hard-mandatory` cannot
be bypassed.

## The level does not decide the override

The **policy set setting** does, crossed with the user's **permission**. The
documentation is unambiguous:

> Override capability is controlled by the **policy set setting**, not
> individual enforcement levels.

The level decides one thing only: an `advisory` never blocks. For everything
else, two conditions must hold together:

| Policy set allows override | User has *Manage Policy Overrides* | Verdict |
| --- | --- | --- |
| yes | yes | blocked, **overridable** |
| yes | no | **blocked** |
| no | yes | **blocked** |
| no | no | **blocked** |

A `hard-mandatory` in an open policy set, with a user holding the right, is
therefore overridable. A `soft-mandatory` without the right is not.

## Three frameworks, three vocabularies

That is the other source of confusion, and it is read rather than guessed:

| Framework | Levels |
| --- | --- |
| **Sentinel** | `advisory`, `soft-mandatory`, `hard-mandatory` |
| **OPA** | `advisory`, `mandatory` |
| **Terraform policy** | `advisory`, `mandatory overridable`, `mandatory` |

Three levels on one side, two on another, and a label naming the override
without guaranteeing it: the policy set always has the last word.

## Policy checks or policy evaluations: the order decides what you see

| | When | Framework | Sees cost |
| --- | --- | --- | --- |
| **policy checks** | after cost estimation | Sentinel only, ≤ **0.40.x** | **yes** |
| **policy evaluations** | just before estimation | all | no |

That is not an implementation detail: if your rule is about **cost**, it must
live in a policy check, the legacy mode. An evaluation will never see the
estimate, since it runs before it.

## What the Free edition allows

> HCP Terraform **Free** edition includes one policy set of up to five policies.

One policy set, five policies, and no repository connection: wiring a VCS or
creating versions through the API is reserved for higher editions.

## A rule says where, not just no

The lab's second half evaluates two **real** `terraform show -json` outputs,
captured with the `local` provider: one creates a file at `0640`, the other at
`0777`.

The rule must return the **offending addresses**, not a boolean:

```hcl
violations = {
  for nom, plan in local.plans : nom => [
    for c in plan.resource_changes : c.address
    if can(c.change.after.file_permission)
    && tonumber(substr(c.change.after.file_permission, 3, 1)) > 0
  ]
}
```

A policy that says "no" without saying "where" forces whoever suffers it to go
looking. And the `can()` is not decorative: not every resource has that
attribute, and an expression assuming otherwise falls over on the first plan
carrying something other than a file.

## The token, and why you do not need one

This lab needs **no HCP Terraform account**, and nothing runs remotely. If you
come across

```
Error: Required token could not be found
```

your configuration was accepted: Terraform has reached the authentication step,
and the lab deliberately stops there.

To go beyond it, a token takes three minutes to create and place, and
[`docs/hcp-token.md`](../../../docs/hcp-token.md) says where to put it and which
location wins when several are filled:

```bash
python3 scripts/diagnostic-jeton-hcp.py --verifier
```

## Over to you

```bash
dsoxlab run hcp-terraform-policy-as-code
dsoxlab check hcp-terraform-policy-as-code
dsoxlab hint hcp-terraform-policy-as-code
```

It runs **offline**, with no provider at all: this lab creates nothing, it
reasons and it reads.

Thirteen tests. The seven cases are asserted **one by one**, so the message says
which is wrong, and they are built so that no constant answer passes. The
compliance rule is tested in **both directions**: a rule refusing everything
fails on the compliant plan.

Exam objective targeted: **6d**.

Reference: [managing policy sets in HCP Terraform](https://developer.hashicorp.com/terraform/cloud-docs/policy-enforcement/manage-policy-sets)
