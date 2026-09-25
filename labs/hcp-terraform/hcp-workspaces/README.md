# One word, two meanings: the CLI workspace and the HCP one

The Professional's objective 6 is the only one assessed **by multiple choice**:
HashiCorp asks for no hands-on work in HCP Terraform. This lab therefore needs
**no account and no `terraform login`**, and it still proves something real,
because a `cloud` block is checked long before any authentication.

What it covers is a confusion the exam plays on: the same word names two very
different things.

## A CLI workspace is a state, and nothing else

```bash
terraform workspace new staging
```

That creates **one more state** in the same directory, from the same
configuration. No variables of its own, no permissions, no history, no run. It
is a way of holding several instances of one infrastructure, and it stops there.

## An HCP Terraform workspace is a unit of execution

It carries its own **input variables**, its own **permissions**, its own **run
history** and its own state. Two workspaces of one organization can run two
entirely different configurations.

Hence the consequence candidates get wrong: with HCP Terraform, a run's input
variables live **in the workspace**, not in a file in the repository.

| | CLI workspace | HCP Terraform workspace |
| --- | --- | --- |
| What it holds | one state | a state, variables, permissions, history |
| Where it lives | in the backend, next to the others | in an organization |
| Its variables | those of the directory | its own |
| Its permissions | those of the machine | teams, per workspace |

## Two attachment strategies, and they exclude one another

A directory attaches to HCP Terraform through the `cloud` block, and it does so
in one of two ways:

```hcl
cloud {
  organization = "atelier-dsoxlab"

  workspaces {
    name = "app-prod"          # one named workspace
  }
}
```

```hcl
cloud {
  organization = "atelier-dsoxlab"

  workspaces {
    project = "plateforme"     # restricts the selection to a project
    tags    = { env = "prod" } # every matching workspace
  }
}
```

`name` and `tags` cannot appear together: one names a single workspace, the
other selects a set of them. Terraform answers `Invalid workspaces
configuration`.

Measured on 2026-09-25 with Terraform 1.16.1: `tags` is accepted **both** as a
list of words and as a key-value map, and `project` alone is not enough. A
`workspaces` block holding only a `project`, or holding nothing, fails on a
message that names neither:

```
Error: failed to create backend alias to target "".
The hostname is not in the correct format.
```

## Where a `cloud` block is checked, and why `validate` misses it

This is the lab's real lesson, and it is measured rather than told.

A `cloud` block is resolved **before** any expression is evaluated, when
Terraform works out where the state lives. So it can reference no named value,
not even a variable with a default:

```hcl
cloud {
  organization = var.organisation   # Error: Variables not allowed
}
```

Which leads to a result worth remembering. Of three faults planted in the same
file:

| Fault | `terraform validate` | `terraform init` |
| --- | --- | --- |
| a `backend` block next to `cloud` | **catches it** | catches it |
| `organization = var.x` | `Success!` | `Variables not allowed` |
| `name` and `tags` together | `Success!` | `Invalid workspaces configuration` |

`terraform validate` answers "Success! The configuration is valid." on two
faults that make `init` fail. It checks the configuration's syntax and internal
consistency, not the attachment. A green `validate` therefore says nothing about
whether your `cloud` block is right.

## The boundary of a lab without an account

A correct `cloud` block goes as far as authentication and stops there:

```
Initializing HCP Terraform...

Error: Required token could not be found
```

That is what makes the lab verifiable with no account: a faulty configuration
never reaches that point. But that message alone proves nothing, and the
measurement says why: a configuration holding both a `backend` and a `cloud`
block prints it **as well**, right next to its fault. The tests therefore
require both the token message and the absence of every fault message.

## And if you wanted to cross that boundary

Nothing requires you to, and this lab scores 100 without an account. But if you
want to see what lies on the other side, a token takes three minutes to create
and place, and
[`docs/hcp-token.md`](../../../docs/hcp-token.md) says where to put it and which
location wins when several are filled:

```bash
python3 scripts/diagnostic-jeton-hcp.py --verifier
```

## Over to you

```bash
dsoxlab run hcp-terraform-hcp-workspaces
dsoxlab check hcp-terraform-hcp-workspaces
dsoxlab hint hcp-terraform-hcp-workspaces
```

Eight tests. Two directories to repair, five answers to establish, and no
account to create: the tests neutralize any token present on the machine, so the
measurement is the same everywhere.

Exam objective targeted: **6b**.

Reference: [connect to HCP Terraform](https://developer.hashicorp.com/terraform/cli/cloud/settings)
