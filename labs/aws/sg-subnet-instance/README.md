# Security group: dedicated rules, for_each and a deterministic subnet

Two copy-pasted rules pass the apply, and the group looks right. This lab is
about what only shows **afterwards**: a diff that never converges, outbound
traffic that does not go out, and an instance that changes subnet without a line
of code moving.

It runs on **Floci**, started by the lab on `http://localhost:14566`: no AWS
account, no bill.

## Never mix the two rule styles

AWS offers two ways to describe a security group's rules, and they are
**incompatible**:

```hcl
# style 1: inline rules, inside the group
resource "aws_security_group" "app" {
  ingress { ... }
}

# style 2: dedicated resources, outside the group
resource "aws_vpc_security_group_ingress_rule" "http" { ... }
```

Inline blocks describe the group's **complete set** of rules. Terraform therefore
considers anything not listed there to be surplus, and deletes on the next apply
whatever the dedicated resources added. Those will recreate them, and so on.

The symptom is a **perpetual diff** nobody manages to converge, whose cause
appears nowhere in the message.

The rule is simple: **pick one style, and one only**. Dedicated resources are
preferable, because they can be added and removed one at a time.

## AWS adds an egress rule, Terraform removes it

When a security group is created, AWS adds an "allow all" egress rule as a
matter of course. Terraform **deletes** it, because it is not in your
configuration.

That is consistent, and it is the source of a classic incident: ingress works,
the group looks complete, and nothing goes out. People look at routing, the NAT
gateway, DNS, and the defect is a rule nobody wrote because they believed it came
by default.

```hcl
resource "aws_vpc_security_group_egress_rule" "tout" {
  security_group_id = aws_security_group.app.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"   # neither from_port nor to_port with -1
}
```

## An index is not a choice

```hcl
subnet_id = data.aws_subnets.tous.ids[0]   # works today
```

The documentation guarantees **no ordering** on the ids returned. The `[0]` names
one subnet today and may name another tomorrow, without a line of code moving.

The lab creates **two** subnets on purpose, so that a draw by lot cannot pass for
a choice. The deterministic form filters on what carries the meaning:

```hcl
data "aws_subnets" "publics" {
  filter {
    name   = "tag:Tier"
    values = ["public"]
  }
}
```

## `for_each` is proven in state

Three rules can come from three copy-pasted blocks, from a `count`, or from a
`for_each`. The result is the same on the AWS side, but not in state:

| Written as | What state carries |
| --- | --- |
| three blocks | three distinct `name` values |
| `count` | an **integer** `index`: 0, 1, 2 |
| `for_each` | a **string** `index`: the map key |

That is what lets the lab prove the `for_each` **without opening a `.tf`**.

And it is not a testing subtlety: the difference matters in practice. Removing
the second entry of a `count` shifts the following ones and **destroys then
recreates** everything after it. With `for_each`, each rule is identified by its
key, and removing an entry touches only that one.

## `security_groups` is not `vpc_security_group_ids`

Two arguments that look alike and do not do the same thing:

- `security_groups` expects **names**, and only applies in the default VPC;
- `vpc_security_group_ids` expects **ids**, and is the one to use in a VPC of
  your own.

## Over to you

```bash
dsoxlab run aws-sg-subnet-instance
dsoxlab check aws-sg-subnet-instance
dsoxlab hint aws-sg-subnet-instance
```

No test opens a `.tf`. A cross-check leaves Terraform:
`describe-security-group-rules` on the Floci side must return three ingress rules
and **one** egress rule.

Exam objective targeted: **2d**, meta-arguments.

Reference: [security group, subnet and instance](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/aws/sg-subnet-instance/)
