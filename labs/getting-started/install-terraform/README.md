# Pin the CLI version and lock the providers

Installing the binary proves almost nothing. What matters is that one
configuration behaves **the same way on every machine in the team**, and that
rests on two distinct mechanisms people often conflate.

## Two constraints, two objects

```hcl
terraform {
  required_version = ">= 1.11.0, < 2.0.0"   # the CLI

  required_providers {                       # the providers
    local  = { source = "hashicorp/local",  version = "~> 2.5" }
    null   = { source = "hashicorp/null",   version = "~> 3.2" }
    random = { source = "hashicorp/random", version = "~> 3.6" }
  }
}
```

`required_version` applies **only** to the CLI version, never to the providers'.
That is explicit in the documentation, and it is the first thing to remember:
pinning Terraform pins nothing it downloads.

You also need to tell that constraint apart from the one your tooling sets. A
`mise.toml` or a `.terraform-version` says **which CLI to install** on your
machine. `required_version` says **which CLI is allowed to run this
configuration**, and it travels with it. The first is a local preference, the
second a contract of the repository.

## The refusal is clean, and that is the point

An unsatisfiable constraint does not produce a warning: it **prevents
execution**.

```console
$ terraform init
│ Error: Unsupported Terraform Core version
$ echo $?
1
```

That is exactly what you want: an immediate refusal beats an apply carried out by
a version that reads things differently. The lab has you trigger that refusal in
a dedicated subdirectory, because a safety mechanism you have never seen fire is
not a mechanism you know.

## The lock file is authoritative, and it is meant to be committed

`terraform init` produces `.terraform.lock.hcl`. It is not a cache: it is a
**machine file, to be versioned**, freezing the resolved versions and their
checksums.

```hcl
provider "registry.terraform.io/hashicorp/local" {
  version     = "2.9.1"
  constraints = "~> 2.5"
  hashes = [
    "h1:...",
  ]
}
```

The proof that it is authoritative takes three commands, and that is what the lab
requires:

```bash
terraform version -json | jq .provider_selections   # record
rm -rf .terraform/
terraform init
terraform version -json | jq .provider_selections   # strictly identical
```

Deleting `.terraform/` does not drift the versions towards the newest ones. If
they moved, the lock would be pointless.

## A single-platform lock breaks on a colleague's machine

This is the most expensive trap of the set, because it only shows elsewhere.
Checksums are **per platform**. A lock created on Linux holds no checksums for
macOS: the colleague using it will see their `init` fail on a file you did
commit.

```bash
terraform providers lock \
  -platform=linux_amd64 \
  -platform=darwin_arm64
```

That command has to be re-run **every time a constraint changes**, and it is what
the lab checks: at least two platforms in the lock.

## Over to you

```bash
dsoxlab run getting-started-install-terraform
dsoxlab check getting-started-install-terraform
dsoxlab hint getting-started-install-terraform
```

The lab is a `shell` lab: no VM, no cloud, and the network is only needed to
download the providers.

All five proofs fail if you merely installed the binary: that is deliberate.

Exam objective targeted: **3a**.

Reference: [installing Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/installer-terraform/)
