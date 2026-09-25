# 🎯 Challenge: rules that prove themselves, a subnet that is not drawn by lot

## Starting point

`challenge/work` is bare: no `.terraform/`, no lock file, no state.

**Floci is started by the lab**, on `http://localhost:14566`: no AWS account, no
bill.

| File | What it has |
| --- | --- |
| `versions.tf` | **supplied**. Provider `~> 6.0`, `endpoints`, the three `skip_*`, fake credentials |
| `reseau.tf` | **supplied**. One VPC and **two** subnets, tagged `Tier = "public"` and `Tier = "private"` |
| `variables.tf` | **supplied**. A `flux_entrants` map of three entries, name to port |
| `main.tf` | **holed**: the chosen subnet, the group, the rules, the instance |
| `outputs.tf` | **holed** |

There are **two** subnets, deliberately: with only one, a draw by lot would pass
for a choice.

## ✅ Objective

1. **Name the public subnet** through a data source filtered on its tag, never
   through an index.
2. **A security group** in the created VPC, with **no inline rule**.
3. **A single block** of ingress rules, driven by `for_each` over
   `flux_entrants`.
4. **An explicit egress rule**.
5. **The instance** in the chosen subnet, attached to the group.
6. **The outputs** exposing the chosen subnet's id and the group's id.

## 🧭 Four traps, three of which only show after the apply

**An index is not a choice.** `data.aws_subnets.tous.ids[0]` works today. The
documentation guarantees **no ordering** on the ids returned: tomorrow the `[0]`
names the other subnet, and the instance changes network without a line of code
moving. Filter on the tag.

**Never mix inline rules and dedicated resources.** The two styles fight over the
same object: the group's `ingress` blocks describe the complete set of rules, so
Terraform deletes on the next apply whatever the dedicated resources added. The
symptom is a perpetual diff nobody manages to converge.

**AWS places an "allow all" egress rule when the group is created, and Terraform
deletes it.** That is intended, and it is the source of a classic incident: the
group looks right, ingress works, and nothing goes out. If you want egress,
**declare it**.

**`security_groups` is not `vpc_security_group_ids`.** The first expects
**names** and only applies in the default VPC. In a VPC of your own it is the
second, and it expects **ids**.

## 🔍 Validation

```bash
dsoxlab check aws-sg-subnet-instance
```

No test opens a `.tf`. The three ingress rules are counted in state, and their
`index` field must be a **string**: a `count` would give integers, and
copy-paste would give three distinct `name` values. That is how a `for_each` is
proven without reading the code.

A cross-check leaves Terraform: `describe-security-group-rules` on the Floci side
must return three ingress rules and **one** egress rule.

Stuck? `dsoxlab hint aws-sg-subnet-instance`.
