# Taking over what you did not create

This is the Professional's first objective, the only one for which HashiCorp
publishes official practice labs, and the most discriminating. Writing a fresh
configuration can be learned in an afternoon. Taking over infrastructure that
already exists, that nobody documented and that Terraform knows nothing about,
is the daily reality of the job.

The lab runs on **Floci**, a local AWS emulator: no account, no bill. Two objects
were created **outside Terraform**, by hand: an EC2 instance and an S3 bucket.

## An import is not finished when the resource is in state

That is the most expensive misconception, and the lab makes it its central
criterion.

```console
$ terraform state list
aws_instance.facturation      # it is there
$ terraform plan -detailed-exitcode
  ~ instance_type = "t3.micro" -> "t3.small"
$ echo $?
2
```

The resource is in state, and yet the import **failed**: your configuration
describes something other than the real object. The next `apply` will modify that
object, in production, without anybody asking.

The success criterion is therefore:

```console
$ terraform plan -detailed-exitcode
No changes.
$ echo $?
0
```

Which means **recording the real values** before writing the configuration,
rather than writing what you would have chosen.

## Two object types, two ways of naming them

An import's identifier is not a Terraform convention, it is the **provider's**,
and it changes with the type:

| Resource | Import identifier |
| --- | --- |
| `aws_instance` | the instance id, `i-0abc...` |
| `aws_s3_bucket` | the bucket **name** |

And nobody hands them to you: finding them is step one.

```bash
aws --endpoint-url http://localhost:14566 ec2 describe-instances \
    --filters 'Name=tag:Name,Values=capstone-facturation' \
    --query 'Reservations[].Instances[].InstanceId' --output text
```

## Drift is information, not a fault

Somebody changed a tag by hand. The plan proposes to put it back. The reflex is
to apply, because "the code is the source of truth".

But drift says **somebody did something**, for a reason you do not know.
Overwriting it erases both the change and the reason. The lab therefore asks you
to **accept** it: align the code with reality.

Two exit codes then fall together, and you need both:

```console
$ terraform plan -detailed-exitcode                 # 0: reality matches the code
$ terraform plan -refresh-only -detailed-exitcode   # 0: state matches reality
```

The first alone is not enough: it can exit **0** on a stale state, because it
compares the code with what state believes, not with what is.

## What happened while writing this lab

Two measurements that hold beyond it.

**The inherited object does not exist right away.** It is created when the
service starts, in parallel with the lab. The reference solution, launched right
after `dsoxlab run`, found nothing and exited in error, while it passed when
re-run by hand ten seconds later. A step that waits for an effect waits for that
effect, within a bounded budget.

**A forgotten container blocks the next creation.** Floci starts a real container
behind every instance and gives it an SSH port. Containers left by an interrupted
session hold those ports, and the next instance fails with
`Bind for 0.0.0.0:2201 failed: port is already allocated`, a message mentioning
neither instance nor lab. That is why the last test destroys **whatever
happens**.

## Over to you

```bash
dsoxlab run certifications-professional-capstone1-resource-lifecycle
dsoxlab check certifications-professional-capstone1-resource-lifecycle
dsoxlab hint certifications-professional-capstone1-resource-lifecycle
```

Five tests. None reads your `.tf`: they query state, the plan, and Floci
directly. The last one destroys and requires that **nothing survives**, in state
or at the provider.

Exam objective targeted: **1**, and above all **1e**.

Reference: [Professional exercises](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/certifications/professional/exercices/)
