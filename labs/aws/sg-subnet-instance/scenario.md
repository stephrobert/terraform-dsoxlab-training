# Scenario: a security group whose rules prove themselves

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
