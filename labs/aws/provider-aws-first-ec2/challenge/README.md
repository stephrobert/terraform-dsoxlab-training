# Challenge: make the AWS provider talk to a local API

`challenge/work` holds five files. Two have holes in them, a third is cut down
to the bare minimum.

| File | State |
| --- | --- |
| `terraform.tf` | provider `source` and `version` are `???` |
| `providers.tf` | the block carries only `region` |
| `outputs.tf` | all three `value` are `???` |
| `variables.tf` | complete, leave it alone |
| `main.tf` | complete, leave it alone |

## What to reach

1. Provider `hashicorp/aws` on **6.x**, under a constraint bounded both ways.
2. Static dummy credentials in the configuration.
3. The three validations that would query the real AWS switched off.
4. `endpoints` redirecting the `ec2` service to `var.floci_endpoint`.
5. `var.common_tags` applied through `default_tags`, not by the resource.
6. The instance reaches the `running` state.
7. The three outputs return the id, the state and the private IP.
8. A plan re-run after apply announces no change.

## Two measured traps

- `terraform validate` **passes** on a half-configured provider. It proves
  nothing here: the `plan` is what fails.
- A tag set on the resource and a tag of the same name set by `default_tags`
  produce **neither error nor warning**: the resource value wins silently.

## Scoring

100 points, minus the cost of any hint requested (10, 15 and 20).

```bash
dsoxlab check aws-provider-aws-first-ec2
```
