# Variables, locals and the real precedence order

A Terraform variable can take its value from five different places. As long as
only one speaks, all is well. The day two contradict each other you need to know
which wins, and intuition is wrong at one precise spot that costs an evening.

This lab runs **offline**, on the `local` and `random` providers: no VM, no
account, and yet everything that matters can be observed.

## The five rungs, in order

```text
default  <  TF_VAR_  <  terraform.tfvars  <  *.auto.tfvars  <  -var
```

The **decisive** rung is the second: a plain values file **beats** the
environment variable. `TF_VAR_` sits just above the `default`, and below
**every** file.

That is the rank almost everybody places too high, because everywhere else an
environment variable is a way to override configuration. In Terraform it is the
opposite: it is what you supply when no file speaks.

The most **discreet** is the third. A `*.auto.tfvars` file is loaded
automatically, after `terraform.tfvars`. Its name does not say so, no command
mentions it, and the colleague who drops one into the repository changes
everybody's behaviour without a line of code moving.

## A variable with no `default` is not a missing variable

`region` has no `default`, and that does not make the configuration invalid: it
makes the value **required**. Terraform will ask for it interactively, or take
it from `TF_VAR_region`, or from a `-var`.

That is the right way to declare what has no sensible default. A `default = ""`
added to silence the tool turns a clean error into a silently wrong
configuration.

## `validation` judges a value, not a typo

```hcl
variable "replicas" {
  type    = number
  default = 2

  validation {
    condition     = var.replicas >= 1 && var.replicas <= 9
    error_message = "replicas doit rester entre 1 et 9."
  }
}
```

Two things to know:

- **`error_message` is mandatory.** A `validation` block without one does not
  compile;
- **the refusal happens at plan time**, not at apply time. That is what makes it
  a useful guard rail: the absurd value is rejected before anything exists.

The lab's tests judge these validations on the **exit code only**. A message is
a string its author chooses; making it a criterion would amount to grading the
prose. And a counter-check verifies that an **accepted** value passes, without
which a condition rejecting everything would make the test pass for the wrong
reason.

## A complex type is proven by consuming it

```hcl
variable "sizing" {
  type = object({
    cpu       = number
    memory_mb = number
  })
  default = { cpu = 2, memory_mb = 2048 }
}
```

Declaring the object proves nothing: an `any` would pass too. What proves the
type is actually held is an output that **computes** with its fields:

```hcl
output "sizing_total_mb" {
  value = var.sizing.memory_mb * var.replicas
}
```

Were the field missing, or not a number, the expression would fall over.

## A local is not a variable

`local.stack_name` is `app-<env>-<region>`. The difference fits in one sentence:
a **variable** is an input to the project, a **local** is an internal
computation. Nobody can supply a local from outside, and that is exactly what
you want for a derived value: it cannot diverge from what it derives from.

## Over to you

```bash
dsoxlab run first-infra-variables-outputs
dsoxlab check first-infra-variables-outputs
dsoxlab hint first-infra-variables-outputs
```

Eight tests. The four rungs are checked **in order**, by actually manipulating
the environment and the files, never by reading back your HCL.

Exam objective targeted: **2e**.

Reference: [variables and outputs](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/premieres-infras/variables-outputs/)
