# A security group whose rules prove themselves

## The situation

**Exam objective targeted: 2d, meta-arguments.**

Two copy-pasted rules pass the apply. This lab covers what only shows
afterwards: mixing inline rules with dedicated rule resources, and forgetting
that Terraform removes the egress rule AWS adds by default.

## Capability targeted

Build a security group whose rules are all dedicated resources, the ingress rules
coming from a single block driven by `for_each`, and attach an instance to a
subnet designated deterministically.

## Where the learner starts

**Floci is started by the lab itself**, declared under `runtime.services` and
published on `http://localhost:14566`. No AWS account, no bill, no real endpoint.
The Docker socket and `-u root` are not optional: without them the instance stays
stuck in `pending`. Floci also ignores the requested AMI: its value is a stub, no
test inspects it.

`challenge/work` is bare: no `.terraform/`, no lock file, no state. `versions.tf`
is complete (`hashicorp/aws` provider at `~> 6.0`, an `endpoints` block towards
`http://localhost:14566`, the three `skip_*`, non-empty fake credentials): the
provider configuration is supplied, it is not the subject of the lab. So is
`reseau.tf`: a VPC and **two** subnets tagged `Tier = "public"` and
`Tier = "private"`, so that a draw by lot cannot pass for a choice.
`variables.tf` carries a `flux_entrants` map of three entries, name to port.
`main.tf` and `outputs.tf` are holed with `???`: the chosen subnet, the security
group, the single ingress rule block, the egress rule, the instance attachment
and the exposed outputs.

## The state to reach

1. The directory is initialised and the lock file exists.
2. The VPC and both subnets are in `mode: managed`. The chosen subnet is
   designated by a data source filtered on the `Tier = "public"` tag, never by an
   index: the documentation guarantees no ordering on the ids returned.
3. The security group belongs to the created VPC and **carries no inline rule**:
   its `ingress` and `egress` attributes are empty in state. Mixing the two
   styles produces perpetual diffs and overwritten rules.
4. The three ingress rules come from a **single**
   `aws_vpc_security_group_ingress_rule` block driven by `for_each` over
   `flux_entrants`: one port range and a single CIDR per rule.
5. An explicit egress rule exists (`aws_vpc_security_group_egress_rule`,
   `ip_protocol = "-1"`, **neither** `from_port` **nor** `to_port`): without it
   the instance has no egress at all, because Terraform deletes the "allow
   everything" rule AWS creates when the group is born.
6. The instance lives in the chosen subnet and references the group through
   `vpc_security_group_ids`, never through `security_groups`, which expects names
   and only applies in the default VPC.
7. Replaying a plan announces nothing, and state after destruction is empty.

## How it is proven

No test reads back a learner's `.tf`, and none parses human output.

- `terraform show -json` sorts each address in state by `mode`, which rules out
  passing a managed subnet off as a data source, and the security group's
  `ingress` and `egress` attributes are checked to be empty there.
- The ingress rule's instances are counted in `values.root_module.resources`:
  three entries of the same `type` and the same `name`, whose `index` field is a
  **string**. A `count` would give integers, and copy-paste three distinct `name`
  values. The egress rule is found by its `type`, with `from_port` and `to_port`
  expected to be null.
- `terraform output -json`: the exposed `subnet_id` equals the `id` of the subnet
  tagged `public`, and the instance's `subnet_id` in state equals it too.
- `terraform plan -detailed-exitcode` exits 0 after the apply, and the
  destruction plan converted to JSON holds no `mode: data` entry. On the Floci
  side, `describe-security-group-rules` returns three ingress rules and one
  egress rule for that group.

## 🎯 Challenge: rules that prove themselves, a subnet that is not drawn by lot

### Starting point

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

### ✅ Objective

1. **Name the public subnet** through a data source filtered on its tag, never
   through an index.
2. **A security group** in the created VPC, with **no inline rule**.
3. **A single block** of ingress rules, driven by `for_each` over
   `flux_entrants`.
4. **An explicit egress rule**.
5. **The instance** in the chosen subnet, attached to the group.
6. **The outputs** exposing the chosen subnet's id and the group's id.

### 🧭 Four traps, three of which only show after the apply

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

### 🔍 Validation

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
