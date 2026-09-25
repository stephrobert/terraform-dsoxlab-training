# Read a replacement in the plan, before it happens

Two received ideas are expensive on an auto-scaling group, and both pass code
review without trouble:

- `version = "$Latest"` on an ASG's launch template **never** triggers an
  instance refresh;
- a `create_before_destroy` placed on the **launch template** protects nothing at
  all.

This lab has you read both in the plan converted to JSON, **without ever calling
AWS**: no `apply`, no account, not even the emulator. State is supplied, every
plan runs with `-refresh=false`, and only the first `init` needs the network.

## What is known at plan time triggers nothing

That is the heart of the first trap, and it fits in one sentence: **a value known
at plan time produces no change**.

`"$Latest"` is a string literal. It is `"$Latest"` before the apply, and still
afterwards. From Terraform's point of view nothing moved: the ASG stays a
`no-op`, the group is never refreshed, and nobody notices for a long time.

Omitting the argument is no better: it falls back to `"$Default"`, with the same
effect.

You need a value **computed at apply time**, that is, a reference to the
template's attribute:

```hcl
launch_template {
  id      = aws_launch_template.socle.id
  version = aws_launch_template.socle.latest_version
}
```

That can be verified in the plan, in a place people rarely read:

```console
$ terraform show -json plan.tfplan | jq '.resource_changes[]
    | select(.type=="aws_autoscaling_group") | .change.after_unknown'
```

`after_unknown` carries `true` on whatever Terraform will only know at apply
time. That is the proof the value is computed rather than frozen.

## Updating a template does not replace it

Changing `image_id` on an `aws_launch_template` **creates a version**. The
template is not replaced: its plan carries `["update"]`.

That is what makes the second trap so natural. You want to avoid an outage, you
put `create_before_destroy` on the resource you just changed, and you feel you
have handled it. But the resource being replaced is the **group**, not the
template.

```console
$ terraform show -json plan.tfplan | jq '.resource_changes[].change.actions'
["update"]              # the template
["create","delete"]     # the group
```

The **order** of those two values is exactly what tells `create_before_destroy`
from the default behaviour:

| Actions | What happens |
| --- | --- |
| `["delete", "create"]` | the old one leaves first: **a window at zero instances** |
| `["create", "delete"]` | the new one arrives first: no dip |

And `replace_paths` names the attribute that forced the replacement.

## The two requirements are linked

`create_before_destroy` makes two groups **coexist** for the duration of the
switch. And AWS refuses two groups bearing the same name.

Applying the rule without changing the name therefore produces a collision, and
handling the name without the rule leaves the capacity dip. The two requirements
cannot be handled separately, and that is the kind of link a tutorial does not
mention because it only shows up at runtime.

Hence the `random_integer`'s `keepers`: it is what makes the suffix change when
the template changes, therefore what makes the new name **unknown at plan time**,
therefore necessarily different from the old one.

## `instance_refresh` has a default ceiling that blocks

Two preferences, and you need both:

- the **floor**: never drop below the target capacity;
- the **ceiling**: explicitly allow going above it.

The second surprises people. The ceiling's default value **refuses** to exceed
the target capacity; without raising it there is no room to create an instance
before removing one, and the requested floor becomes impossible to hold.

## Over to you

```bash
dsoxlab run aws-launch-template-autoscaling
dsoxlab check aws-launch-template-autoscaling
dsoxlab hint aws-launch-template-autoscaling
```

Eight tests, all read from a plan written in binary then converted to JSON. The
last one requires the plan **not to be empty**: here an exit code of 2 is the
success, because a lab neutralised to make the tests pass would exit 0.

Exam objective targeted: **1b**.

Reference: [launch template and autoscaling](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/aws/launch-template-autoscaling/)
