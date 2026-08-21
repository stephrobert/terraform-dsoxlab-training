# Version constraints and the lock file

A **version constraint** bounds what Terraform accepts: its version, providers,
modules. Two things trip people up, and this lab tackles them: the **meaning of
the operators** (especially `~>` and the exact pin), and the fact that the
`terraform` block only accepts **literals**. This tutorial shows them on a
throwaway example; the challenge makes you apply them on `local` and `random`.

## The operators

| Operator | Meaning |
|---|---|
| `= 1.2.0` | **exactly** this version; cannot combine with any other |
| `>= 1.2.0` | **lower** bound |
| `< 2.0.0` | **upper** bound (excludes newer versions) |
| `~> 5.0` | pessimistic: `5.x`, but **not** `6.0` |
| `~> 5.0.2` | pessimistic: `5.0.x`, but **not** `5.1.0` |

`<` and `<=` bound **upward**, not downward: that is the most common inversion.
And `= 1.2.0` fixes a single version, to combine with nothing.

## The pessimistic ~>

`~> 5.0` allows the whole `5.x` series (up to `5.99`) without ever reaching
`6.0`. `~> 5.0.2` is stricter: it locks the `5.0.x` minor. The classic mistake is
writing `~> 1.0.0` thinking it allows patches, when it freezes the minor.

```hcl
terraform {
  required_version = ">= 1.15.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

## The terraform block only accepts constants

The `terraform` block is evaluated very early: it **cannot reference any named
value**. A variable, local or function in `required_version` fails `init` with
`Error: Variables not allowed`. The constraint must be a **literal**.

## The lock file

`.terraform.lock.hcl` locks **provider** versions (not modules), and **is
committed**. For each provider it records the selected version, the constraints
considered, and **hashes** under two schemes: `h1:` (preferred, computed on the
content) and `zh:` (legacy). Read the actual selection with:

```bash
terraform version -json | jq '.provider_selections'
```

The lock does **not** track modules: Terraform always selects the newest module
version satisfying the constraint, which can vary from machine to machine.

## Your turn

```bash
dsoxlab run write-code-version-constraints
dsoxlab check write-code-version-constraints
dsoxlab hint write-code-version-constraints
```

Exam objective: **3a** (version constraints, lock file).

Reference: [Version constraints in Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/version-constraints-terraform/)
