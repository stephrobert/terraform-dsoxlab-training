# 🎯 Challenge: read a replacement in the plan

## Starting point

A base is **already in service**, described by the provided
`terraform.tfstate`: an `aws_launch_template.socle` at version 1 on
`ami-0000000000000a1`, and an `aws_autoscaling_group.grappe` named
`grappe-app-742`, min 2, max 4, target 2.

`challenge/work` holds `versions.tf` (**provided**, neutralised provider),
`terraform.tfstate` (**provided**), `CONSIGNES.md` and `main.tf` (**full of
holes**).

**No `apply`, no AWS account, no emulator.** Everything is read from the plan,
and every plan runs with `-refresh=false`. Only the first `terraform init` needs
the network.

## ✅ Objective

The AMI has already moved to `ami-0000000000000b7`: that is the business
request. Five `???` remain, and each decides a behaviour the plan will reveal.

1. The `keepers` of the `random_integer`.
2. The argument giving the group its **name**.
3. The `version` argument of the ASG's `launch_template` block.
4. The ASG's `lifecycle` block.
5. **Both** `instance_refresh` preferences.

## 🧭 The two traps, and why they stay invisible

**`version = "$Latest"` never triggers anything.** It is the reflex, and it is
wrong: that string is **known** at plan time, so the ASG stays `no-op`. The
group will never be refreshed, and nobody will notice for a long time. Omitting
the argument is no better: it falls back to `"$Default"`, same effect. You need
a value **computed at apply time**.

**A `create_before_destroy` placed on the launch template protects nothing.**
It is the group that gets replaced, not the template — that one is merely
updated. Putting the rule in the wrong place gives the illusion of having dealt
with the matter.

And the two business requirements are **linked**: `create_before_destroy` makes
two groups coexist during the switch, and AWS refuses two groups with the same
name. That is why the name must change. Handling one without the other does not
work.

## 🔍 Validation

```bash
dsoxlab check aws-launch-template-autoscaling
```

Eight tests. The plan is written in binary then converted to JSON. The order of
actions, `["create", "delete"]` and not the reverse, is exactly what tells
`create_before_destroy` from the default behaviour. Unknown values are read from
`after_unknown`, the replacement trigger from `replace_paths`. The last test
requires the plan **not to be empty**: here, exit code 2 is the success. No test
opens a `.tf`.
