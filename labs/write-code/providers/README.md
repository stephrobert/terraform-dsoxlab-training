# Providers: explicit source and alias

A **provider** translates your resources into API calls. You declare it in
`required_providers` and configure it in a `provider` block. Two confusions
trip people up, and this lab tackles them: the **source address** (the implicit
`hashicorp/` prefix is actually discouraged) and the difference between **local
name** and **alias**. This tutorial shows them on a throwaway AWS example; the
challenge makes you apply them on a different case.

## The source address: always explicit

Since Terraform 0.13, **`source` is required**. Writing it implicitly for
HashiCorp providers is only **backward compatibility**; the docs recommend the
opposite, "use explicit source addresses for all providers":

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

The full address is **`[HOSTNAME/]NAMESPACE/TYPE`**. `hashicorp/aws` is really
`registry.terraform.io/hashicorp/aws`: the **hostname**, often omitted, is the
gateway to **private registries** and **mirrors**.

## Local name and alias: do not confuse them

These are **two distinct mechanisms**:

- The **local name** (the key in `required_providers`) identifies the provider in
  the module, and attaches a resource type by its prefix: `aws_instance` goes to
  the provider with local name `aws`.
- The **alias** creates an **additional configuration** of the **same** provider,
  to target two regions for example.

```hcl
provider "aws" {
  region = "eu-west-3"
}

provider "aws" {
  alias  = "us"
  region = "us-east-1"
}

resource "aws_instance" "paris" {
  # default config
}

resource "aws_instance" "virginie" {
  provider = aws.us
}
```

Without an alias, a second `provider "aws" {}` block would be a **rejected
duplicate** (`Duplicate provider configuration`). And `virginie` only picks the
`us` config because it carries `provider = aws.us`.

## The proof is in the JSON

`terraform version -json` exposes `provider_selections`, the full address to each
provider's selected version. And the **plan JSON** lists each configuration in
`configuration.provider_config` (with its `full_name` and `alias`), and each
resource carries a `provider_config_key` (`aws` or `aws.us`):

```bash
terraform plan -out=tfplan
terraform show -json tfplan | jq '.configuration.provider_config'
```

## A word on modules

A **module intended to be called contains no `provider` block**: the config
lives in the root module and crosses the boundary via `configuration_aliases` (on
the child) and `providers = { ... }` (on the caller). A module that inherits a
`provider` block becomes incompatible with `count`, `for_each` and `depends_on`.

## Your turn

```bash
dsoxlab run write-code-providers
dsoxlab check write-code-providers
dsoxlab hint write-code-providers
```

Exam objective: **5b** (provider configuration, aliases).

Reference: [Providers in Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/providers-terraform/)
