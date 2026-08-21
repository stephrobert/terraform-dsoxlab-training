# The four Terraform validation levels

Terraform has **four** mechanisms to validate a configuration. They look alike on
paper, but only one **does not stop** the operation. Knowing which to put where,
and which one blocks, is exam objective **2a**. This tutorial lays them on a
throwaway sizing example; the challenge makes you have them coexist and prove it.

## 1. `validation`: reject an input before the plan

In a `variable` block, a `validation` block rejects an input value **before any
plan**. Since Terraform **1.9**, its `condition` can reference **another
variable** (cross-validation):

```hcl
variable "replicas" {
  type = number
  validation {
    condition     = var.replicas <= var.replicas_max
    error_message = "replicas cannot exceed replicas_max."
  }
}
```

## 2. `precondition`: reject an assumption before creation

In `lifecycle`, a `precondition` checks an **assumption** at plan time, before the
resource is created. Beware: on a resource with `count = 0` there is **no
instance**, so the precondition is **not evaluated**.

```hcl
resource "aws_instance" "web" {
  # ...
  lifecycle {
    precondition {
      condition     = var.instance_type != "t2.nano"
      error_message = "t2.nano is too small for this role."
    }
  }
}
```

## 3. `postcondition`: reject a result after creation

Still in `lifecycle`, a `postcondition` checks the **result** after creation. It
is the **only** one with **`self`**, the created object:

```hcl
    postcondition {
      condition     = self.private_ip != ""
      error_message = "The instance did not receive a private IP."
    }
```

## 4. `check`: watch without blocking

A root-level `check` block **watches** an invariant. Unlike the three above, a
failing `assert` **does not stop** apply: it produces a **warning**, not an
error. It is meant for service-continuity checks you do not want to be blocking.

```hcl
check "http_health" {
  data "http" "home" {
    url = "https://${aws_instance.web.public_ip}/"
  }
  assert {
    condition     = data.http.home.status_code == 200
    error_message = "The home page does not return 200."
  }
}
```

A `check` may contain a **scoped data source**, as here. Worth knowing: this data
source is **re-read on every plan**, so it always shows up as action `read` in the
plan. Consequence: **`terraform plan -detailed-exitcode` returns `2`** ("changes
present"), even on a converged configuration. A CI that decides on that code will
always believe changes remain.

## Read the verdict of all four: the `checks` array

`terraform show -json` exposes a top-level **`checks`** array. Each entry carries
an `address.kind` (`var`, `resource`, `output_value`, `check`) and a `status`
(`pass` / `fail`). A failing `check` carries its message in
`instances[].problems[].message`. This is **the** machine proof of the four
levels, without ever reading human output.

One last trap: **`terraform validate` does not run these conditions**. It does not
know the variable values, so it returns `valid: true` on an input the **plan**
will refuse. `validate` checks the shape, the plan checks the values.

## Your turn

You know that `validation`, `precondition` and `postcondition` **block**, that the
`check` block only **warns**, that `postcondition` alone has `self`, that a
`check`'s data source makes `plan -detailed-exitcode` return 2, and that the
`checks` array of `show -json` gives the verdict of all four. The challenge makes
you fill the four levels and prove it.

```bash
dsoxlab run write-code-validation-check-preconditions
dsoxlab check write-code-validation-check-preconditions
dsoxlab hint write-code-validation-check-preconditions
```

Target exam objective: **2a** (validate the configuration), Professional level.

Reference: [Custom conditions](https://developer.hashicorp.com/terraform/language/expressions/custom-conditions)
