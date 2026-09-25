# Scenario: making the plan say what a launch template change really does

**Exam objective targeted: 1b.**

An ASG referencing `version = "$Latest"` never triggers an instance refresh, and a
`create_before_destroy` placed on the launch template protects nothing at all. This lab has both
truths read from the plan converted to JSON, without ever calling AWS.

## Capability targeted

Make a plan say, on already applied infrastructure, which resource is updated, which is replaced and
in what order the replacement will happen, then fix the configuration so that replacing the group
goes neither through a window at zero instances nor through a name collision.

## Where the learner starts

Execution note: no AWS account, no `apply`, and the Floci emulator is not required. Its coverage of
`CreateLaunchTemplate` and of instance refresh could not be verified, so the lab rests on no API
call: the provider is configured with fake credentials and its checks disabled, and every plan runs
with `-refresh=false`. Only the first `terraform init` needs the network. `challenge/work` holds:

- `versions.tf`: supplied, not to be modified. Terraform `>= 1.11.0`, `hashicorp/aws` and
  `hashicorp/random` pinned to an exact version, `provider "aws"` block already neutralised.
- `terraform.tfstate`: supplied. A platform already in service: a `random_integer.suffixe`, an
  `aws_launch_template.socle` at version 1 on `ami-0000000000000a1`, and an
  `aws_autoscaling_group.grappe` named `grappe-app-742`, min 2, max 4, target 2, pointing at version
  `"1"` of the template.
- `main.tf`: the target configuration, holed. The template's AMI has already moved to
  `ami-0000000000000b7`, that is the business request. Set to `"???"`: the `version` argument of the
  ASG's `launch_template` block, the argument giving the group its name, the `random_integer`'s
  `keepers` block, the ASG's `lifecycle` block and two `instance_refresh` preferences.
- `CONSIGNES.md`: deploy the new AMI without ever dropping below the target capacity, and apply the
  new naming convention to the group.

## The state to reach

1. `aws_launch_template.socle` carries the `update` action alone: changing `image_id` creates a
   version, it does not replace the template.
2. `aws_autoscaling_group.grappe` is not a `no-op`: the template version it references is unknown at
   plan time, because computed at apply time. A literal `"$Latest"`, like omitting the argument which
   would then be `"$Default"`, would produce the opposite.
3. That same ASG carries the `create` then `delete` actions, in that order, and not the reverse.
4. The replacement path declared by the plan names the group's name.
5. The new group's name is itself unknown at plan time, hence necessarily different from
   `grappe-app-742`: the two generations cannot collide during the switch.
6. `random_integer.suffixe` is replaced in that same plan.
7. The `instance_refresh` preferences forbid any drop below the target capacity and explicitly allow
   going above it, which the ceiling's default value refuses.
8. The plan does report pending changes: nothing was neutralised to make the tests pass.

## How it is proven

No test opens a `.tf` file. The plan is written in binary then converted to JSON. Points 1 and 3 are
read from `resource_changes[].change.actions`: `["update"]` for the template, `["create", "delete"]`
for the group, the order of those two values being exactly what tells `create_before_destroy` from
the default behaviour. Point 4 is read from `resource_changes[].change.replace_paths`. Points 2 and 5
are read from `change.after_unknown`, where the template version and the group name are true although
they would be known strings in a frozen configuration. Point 6 is a third `resource_changes` entry
being replaced, point 7 is read from `planned_values` on the ASG's nested preferences, and point 8
comes from the exit code of `terraform plan -refresh=false -detailed-exitcode`, whose value of 2 is
the expected one here. An empty `challenge/work` produces no `resource_changes` and fails everywhere;
copying `"$Latest"` fails point 2; keeping a frozen name fails points 5 and 6; removing the
`lifecycle` block fails point 3.
