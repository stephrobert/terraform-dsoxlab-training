# 🎯 Challenge: what blocks a run, and who can override it

## 📦 Starting point

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

## ✅ Objective

1. **Qualify the seven runs**, with three values and no more:
   `poursuit`, `bloque_surchargeable`, `bloque`.
2. **Establish three facts**: each framework's levels, what tells policy checks
   from policy evaluations, and what the Free edition allows.
3. **Write the compliance rule**: no file created with a right granted to the
   rest of the world. It returns the offending **addresses**, not a boolean.

## 🧭 The trap, and it catches candidates out

A `hard-mandatory` **is not unbypassable**. What decides an override is the
**policy set setting**, crossed with the user's **permission**:

> Override capability is controlled by the policy set setting, not individual
> enforcement levels.

The level decides one thing only: an `advisory` never blocks. For everything
else you need **both**: the policy set allowing it, and the user holding
*Manage Policy Overrides*.

Each situation carries those three pieces of information. Use them.

## ⚠️ No constant answer passes

The seven cases are built for that:

| Uniform answer | Fails on |
| --- | --- |
| `bloque` everywhere | the two `advisory` cases |
| `bloque_surchargeable` everywhere | the three cases without the right |
| `poursuit` everywhere | the other five |

## 🔍 Validation

```bash
dsoxlab check hcp-terraform-policy-as-code
```

Thirteen tests, all read from `terraform output -json`: what your configuration
**computes**, never what it contains.

The seven cases are asserted one by one, so the message says which one is wrong.
And the compliance rule is tested in **both directions**: a rule refusing
everything fails on the compliant plan.

Stuck? `dsoxlab hint hcp-terraform-policy-as-code`.
