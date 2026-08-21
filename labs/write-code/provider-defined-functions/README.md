# Provider-defined functions

Since **Terraform 1.8**, a provider brings more than resources and data sources:
it can also expose its own **functions**. You call them through a dedicated
namespace, **`provider::<local_name>::<function>`**, which tells them apart
unambiguously from the language's built-in functions (`max`, `jsonencode`…). This
tutorial shows the mechanism on the **built-in `terraform` provider**, usable
**offline**; the challenge makes you practice on two of its other functions.

## Declare the provider, even the built-in one

A provider function is only available if the provider is **declared** in
`required_providers`, including the built-in `terraform` provider:

```hcl
terraform {
  required_providers {
    terraform = {
      source = "terraform.io/builtin/terraform"
    }
  }
}
```

Without this declaration the call fails with **`Unknown provider function`**,
which precisely reminds you to add the provider to `required_providers`. The
local name chosen here (`terraform`) is the one that appears in the call
namespace.

## Call a provider function

The built-in `terraform` provider exposes three functions, all offline. The
easiest to observe is **`encode_expr`**, which serializes any value into
**Terraform expression syntax**:

```hcl
output "expr" {
  value = provider::terraform::encode_expr([1, "deux", true, null])
}
```

The output is the string `[1, "deux", true, null]`. This is handy to **generate**
Terraform code or a configuration fragment from computed data, without assembling
the string by hand.

## What the namespace guarantees

The `provider::` prefix is not decorative: it **removes any ambiguity** between a
language function and a provider function, and makes explicit **which provider**
the function comes from. Two providers can expose a function with the same name
without clashing, since the local name separates them
(`provider::terraform::…` versus `provider::other::…`).

A provider function is a **pure function**: it takes arguments, returns a value,
touches nothing. It evaluates at plan time, creates no resource, and does not
appear in the state.

## A function may require a specific provider version

A function only exists from the **provider version** that introduced it. A
too-low constraint in `required_providers` **passes `init`** but fails the
**call**: the function simply is not in the installed plugin. Setting the right
version bound is therefore part of the exercise, just like the call itself.

Two commands prove where a function comes from, unambiguously:

- **`terraform providers schema -json`** describes each provider's functions, in
  `provider_schemas[<address>].functions`;
- **`terraform metadata functions -json`** lists **only** the ~238 language
  functions. A function absent here but present in a provider schema comes from
  the plugin.

## Your turn

You know that a provider function is called via
`provider::<local_name>::<function>`, that the provider must be declared in
`required_providers` (even the built-in one, here under the name `tfcore`), that a
function may require a minimum provider version, and that these functions are
pure. The challenge makes you **serialize** an object into tfvars, do the
**reverse**, produce an **expression syntax**, and test a directory's existence
with a third-party provider's function. The tests prove it on the JSON outputs.

```bash
dsoxlab run write-code-provider-defined-functions
dsoxlab check write-code-provider-defined-functions
dsoxlab hint write-code-provider-defined-functions
```

Target exam objective: **2c** (functions), supporting **5a** (providers),
Professional level.

Reference: [Provider-defined functions](https://developer.hashicorp.com/terraform/language/functions)
