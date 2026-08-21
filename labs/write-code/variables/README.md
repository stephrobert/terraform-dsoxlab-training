# Variables: typing, validation, nullable, sensitive and precedence

Declaring a variable and setting a `default` never fails anyone. What fails are
four rarely taught traps: the **default type** that lets anything through, the
explicit `null` that **overwrites** a `default`, the `sensitive` mistaken for a
protection when it only masks display, and the **precedence order** of value
sources. This tutorial shows them on a throwaway catalog example; the challenge
makes you chain them on a different case.

## A variable is more than a default

The `variable` block accepts far more than `description`, `type` and `default`.
The arguments that matter are `validation`, `sensitive`, `nullable` (default
`true`) and, since Terraform 1.10, `ephemeral`. Without a `type` constraint, a
variable is **`any`**: it accepts anything, and the bug only shows up in use.

```hcl
variable "region" {
  type    = string
  default = "eu-west-3"
}
```

Some names are **reserved** and cannot name a variable: `source`, `version`,
`providers`, `count`, `for_each`, `lifecycle`, `depends_on`, `locals`.

## Complex types, and optional()

The topic goes beyond `list(string)`. The most useful type in practice is
**`object({...})`**, often inside a `map`, with **`optional()`** attributes
carrying a default:

```hcl
variable "servers" {
  type = map(object({
    cpu    = number
    memory = optional(number, 512)
    expose = optional(bool, false)
  }))
}
```

Provide an incomplete entry, and Terraform **fills it** with the `optional()`
defaults:

```hcl
servers = {
  api = { cpu = 2 }   # memory = 512, expose = false added by Terraform
}
```

`set(...)`, `tuple([...])` and nested objects follow the same logic. An
`optional(x)` with no second argument defaults to `null`; with one, it defaults
to that value.

## Validation rejects before any provider

A **`validation`** block checks a condition on the variable and **fails at plan
time**, before any provider call. It is the cheapest barrier against a nonsense
value:

```hcl
variable "size" {
  type = string

  validation {
    condition     = contains(["S", "M", "L"], var.size)
    error_message = "size must be S, M or L."
  }
}
```

```bash
terraform plan -var size=XXL
```

```text
Error: Invalid value for variable
```

## The null trap: nullable

Here is the most valuable trap of the topic. A variable has a `default`, so you
think you are safe. But passing **`null` explicitly** (often from a generated
value file) **overwrites** the default and propagates `null`:

```hcl
variable "retries" {
  type    = number
  default = 3
}
```

With `retries = null` in a `terraform.tfvars`, the variable is **`null`**, not
`3`. To force the fallback to the default, set **`nullable = false`**:

```hcl
variable "retries" {
  type     = number
  default  = 3
  nullable = false
}
```

Now an explicit `null` **falls back to `3`**.

## sensitive masks display, not the state

The last and most dangerous misunderstanding. **`sensitive = true` does not
protect the secret.** It masks the value in the human output of `plan`, `apply`
and `terraform output`, nothing more. The documentation is explicit: "Terraform
still records sensitive values in the state, so anyone who can access your state
data can access your sensitive values."

Concretely, `terraform show -json` and `terraform output -json` return the value
**in cleartext**, and the state file stores it as is. To truly exclude a value
from the plan and state, use **`ephemeral = true`** (Terraform 1.10+), not
`sensitive`.

## The precedence order of sources

When several sources give a value to the same variable, Terraform applies them
in a **fixed order**, weakest to strongest:

1. the block `default`;
2. the environment variable **`TF_VAR_<name>`**;
3. the **`terraform.tfvars`** file;
4. the **`terraform.tfvars.json`** file;
5. the **`*.auto.tfvars`** files (and `.json`), loaded in **lexical order**: the
   last name alphabetically wins;
6. the **`-var`** and **`-var-file`** command-line options, in the order given.

Two frequent surprises: a `*.auto.tfvars` beats an exported `TF_VAR_`, and
between two `*.auto.tfvars` the alphabetical order decides, not the write order.
The command line always wins.

## Your turn

```bash
dsoxlab run write-code-variables
dsoxlab check write-code-variables
dsoxlab hint write-code-variables
```

Exam objectives: **2e** (variables and complex types) and **2f** (sensitive
data).

Reference: [Variables in Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/variables-terraform/)
