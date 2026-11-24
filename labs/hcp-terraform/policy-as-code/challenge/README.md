# Policy as code, what blocks a run and who can override it

## The situation

**Exam objective targeted: 6d.**

Objective 6 is assessed by multiple choice: no HCP Terraform account, no remote run. The
trap covered here catches candidates out: believing a `hard-mandatory` cannot be bypassed,
when it is the policy set's override setting that decides, not the enforcement level alone.

## Capability targeted

Determine, for a given run, whether a failing policy lets the run continue, blocks it with
a way out, or blocks it with no recourse, depending on the framework (Sentinel, OPA,
Terraform policy), the policy set's override setting and the **Manage Policy Overrides**
permission. And write a compliance rule that actually refuses a non-compliant plan.

## Where the learner starts

`challenge/work` holds a configuration with no provider at all, nothing to create:

1. `situations.auto.tfvars.json`, not modifiable, typed in `variables.tf`: seven run cases
   described by framework, enforcement level, policy failure, override allowed or not by
   the policy set, and whether the user holds **Manage Policy Overrides**.
2. `verdicts.tf` (one verdict per case) and `connaissances.tf` (levels per framework, the
   only framework running in policy checks and its maximum version, where policies sit
   relative to cost estimation, the Free edition), holed with `???`.
3. `plans/plan-conforme.json` and `plans/plan-non-conforme.json`, two real
   `terraform show -json` outputs captured with the `local` provider (the second creates a
   file at `0777`), and `evaluation.tf`, the compliance rule holed with `???`, which must
   read them through `jsondecode(file(...))`.

## The state to reach

1. The `verdicts` output maps each case to one of `poursuit`, `bloque_surchargeable` and
   `bloque`.
2. The failing `advisory` case is `poursuit`: an advisory never interrupts a run.
3. The `hard-mandatory` case whose policy set allows overrides, with a user holding the
   permission, is `bloque_surchargeable`, not `bloque`.
4. The `soft-mandatory` case with a user lacking the permission is `bloque`: the level
   alone is not enough, the right is needed too.
5. `niveaux_par_framework` gives three levels for Sentinel (`advisory`, `soft-mandatory`,
   `hard-mandatory`), two for OPA (`advisory`, `mandatory`), three for Terraform policy
   (`advisory`, `mandatory overridable`, `mandatory`).
6. `policy_checks` states that only Sentinel runs there and that they cap at Sentinel
   `0.40.x`; `free_tier` gives one policy set, five policies, no VCS.
7. `violations` is empty for the compliant plan and holds the offending resource's address
   for the non-compliant one.

## How it is proven

The tests run `terraform init` then `terraform apply -auto-approve` and read
`terraform output -json`: no `.tf` is read back. Each case is asserted separately, so the
message says which one is wrong, and the seven are built so that no constant answer passes
(`bloque` everywhere fails on the advisory cases, `bloque_surchargeable` everywhere fails
on the cases without the right). The evaluation is checked in both directions, empty
violations for the compliant plan and the expected address for the other: a rule refusing
everything would pass half of it otherwise.

All the figures were read at their source on 2026-09-25, on the official HCP Terraform
documentation, and the tests carry that link in their failure messages.

## 🎯 Challenge: what blocks a run, and who can override it

### 📦 Starting point

`challenge/work` holds a configuration with **no provider at all**: this lab
creates nothing, it reasons and it reads.

| File | State |
| --- | --- |
| `situations.auto.tfvars.json` | **supplied**, seven runs described |
| `variables.tf`, `versions.tf` | **supplied** |
| `verdicts.tf` | one `???`: each run's verdict |
| `connaissances.tf` | three `???`: facts to establish |
| `evaluation.tf` | one `???`: the compliance rule |
| `plans/` | two **real** `terraform show -json` outputs |

### ✅ Objective

1. **Qualify the seven runs**, with three values and no more:
   `poursuit`, `bloque_surchargeable`, `bloque`.
2. **Establish three facts**: each framework's levels, what tells policy checks
   from policy evaluations, and what the Free edition allows.
3. **Write the compliance rule**: no file created with a right granted to the
   rest of the world. It returns the offending **addresses**, not a boolean.

### 🧭 The trap, and it catches candidates out

A `hard-mandatory` **is not unbypassable**. What decides an override is the
**policy set setting**, crossed with the user's **permission**:

> Override capability is controlled by the policy set setting, not individual
> enforcement levels.

The level decides one thing only: an `advisory` never blocks. For everything
else you need **both**: the policy set allowing it, and the user holding
*Manage Policy Overrides*.

Each situation carries those three pieces of information. Use them.

### ⚠️ No constant answer passes

The seven cases are built for that:

| Uniform answer | Fails on |
| --- | --- |
| `bloque` everywhere | the two `advisory` cases |
| `bloque_surchargeable` everywhere | the three cases without the right |
| `poursuit` everywhere | the other five |

### 🔍 Validation

```bash
dsoxlab check hcp-terraform-policy-as-code
```

Thirteen tests, all read from `terraform output -json`: what your configuration
**computes**, never what it contains.

The seven cases are asserted one by one, so the message says which one is wrong.
And the compliance rule is tested in **both directions**: a rule refusing
everything fails on the compliant plan.

Stuck? `dsoxlab hint hcp-terraform-policy-as-code`.
