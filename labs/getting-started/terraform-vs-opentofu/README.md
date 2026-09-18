# Terraform and OpenTofu: how far compatibility goes

OpenTofu is a fork of Terraform, born from the 2023 licence change. The sentence
you hear everywhere is "the two tools are compatible". It is true, and it is
incomplete. This tutorial shows what really travels from one binary to the
other, and the exact point where it stops.

## Implicit sourcing, or the bet nobody sees

Write a `random_pet` resource without declaring anything. Terraform guesses:
`hashicorp/random`, on `registry.terraform.io`. OpenTofu guesses too:
`hashicorp/random`, but on `registry.opentofu.org`.

As long as both registries publish the same thing, nobody notices. The day they
diverge, your configuration resolves two different providers depending on which
binary reads it, and nothing in the code said so.

```hcl
terraform {
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}
```

**Declaring removes the guess.** `source` names the organisation, the constraint
bounds the version, and the lock file records what was selected.

## The pessimistic constraint

`~> 3.6` is the form to know. It accepts `3.6.0`, `3.9.1`, and refuses `4.0.0`:
the major component is locked, patches stay available.

| Form | Effect |
|---|---|
| `= 3.6.0` | pinned: no patch, ever |
| `>= 3.6` | floating: `4.0` will pass, and break |
| `~> 3.6` | pessimistic: `3.x` yes, `4.0` no |

A floating version is exactly what implicit sourcing allows: each binary
resolves whatever it wants.

## What travels: the state

That is the good news, and it is solid. Apply with `terraform`, then run `tofu`
in the same directory:

```bash
terraform apply -auto-approve
tofu init
tofu plan -detailed-exitcode ; echo $?   # 0
tofu output nom_animal                   # the same value
```

**No destruction, no recreation.** The state is read as is, the same provider
versions are selected, and the plan is empty. The announced compatibility does
exist, right there.

## What does not travel: the lock

Now look at `.terraform.lock.hcl` after `tofu` has run:

```text
provider "registry.opentofu.org/hashicorp/local" {
provider "registry.opentofu.org/hashicorp/null" {
provider "registry.opentofu.org/hashicorp/random" {
```

The `registry.terraform.io` addresses are **gone**. And `terraform` stops dead:

```text
Error: Inconsistent dependency lock file

  - provider registry.terraform.io/hashicorp/local: required by this
    configuration but no version is selected
```

The fix is simple, `terraform init -upgrade`, and the plan returns to `0`: the
round trip changed neither the state nor the infrastructure. But it is not
automatic, and in a team where everyone picks their own binary, the lock flips
on every commit.

<Aside type="caution" title="The lock records its constraints only once">
`constraints` is written into `.terraform.lock.hcl` only when the entry is
**created**. If you run `init` before writing your constraints, the lock stays
without them, and nothing will add them later, not even `init -upgrade`. To
start clean, delete the file and run `init` again.
</Aside>

## Over to you

You now know that implicit sourcing is a silent bet, that a pessimistic
constraint bounds the major without forbidding patches, that the state really
does travel between the tools, and that the lock file is the exact point where
compatibility stops.

The challenge has you make a configuration portable, then produce those proofs.

```bash
dsoxlab run getting-started-terraform-vs-opentofu
dsoxlab check getting-started-terraform-vs-opentofu
dsoxlab hint getting-started-terraform-vs-opentofu
```

Exam sub-objective covered: **5b** (provider configuration: sourcing and
versioning), leaning on **3a**.

Reference: [Terraform or OpenTofu](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/terraform-vs-opentofu/)
