# Import, moved and drift: the three traps a tutorial never shows

Taking over an existing resource, renaming it, absorbing a change made by hand:
three common gestures, and three ways to get it wrong **with no message saying
so**. That is what makes them expensive: they do not break, they lie.

The lab runs on **Floci**, a local AWS emulator: no account, no bill.

## An import is not finished when the resource is in state

That is the first misconception. The success criterion for an import is not "the
resource shows up in `terraform state list`", it is:

```console
$ terraform plan -detailed-exitcode
No changes.
$ echo $?
0
```

While an ordinary plan proposes anything at all, the import is not finished:
your code describes something other than the real object, and the next `apply`
will modify that object.

The trap is amplified by `-generate-config-out`, which is helpful and also
produces arguments the API returns and the configuration has no business
carrying. Removing them is part of the work.

And before any of that: **nobody hands you the id**. Finding it is step one.

```bash
aws --endpoint-url http://localhost:14566 ec2 describe-instances \
    --filters 'Name=tag:Name,Values=legacy-billing-api' \
              'Name=instance-state-name,Values=running' \
    --query 'Reservations[].Instances[].InstanceId' --output text
```

## A `plan` alone writes nothing to state

A `moved` block changes a resource's logical address without touching the real
object:

```hcl
moved {
  from = aws_instance.legacy
  to   = aws_instance.billing_api
}
```

You plan it, you see the rename announced, and you move on. But **a plan writes
nothing**: until it is applied, state still carries the old address.

And the block **stays in place** afterwards. Removing it is a breaking change
for anyone still starting from the old address, an unmerged branch or an older
state, for instance.

## A `moved` with a wrong `from` is ignored in silence

That one is the worst of the set. If the `from` address matches nothing,
Terraform **says nothing**: it finds nothing to move, carries on, and **creates**
the target resource.

The result: the real object ends up **duplicated**, once outside state and once
inside. No error, no warning, and a plan that looks normal.

Which is why the lab's test does not settle for seeing the right address: it
copies your directory, puts the old address back into the copied state, and
demands that the plan carry a `previous_address` entry as `no-op`. A deleted or
misspelled `moved` would produce a `create` there.

## Overwriting drift is a reflex, not a decision

Somebody changed a tag by hand. The plan proposes to put it back. The reflex is
to apply, because "the code is the source of truth".

But drift is **information**: somebody did something, for a reason you do not
know. Overwriting it erases both the change and the reason, and the colleague
who made it will never learn why their tag disappeared.

Accepting drift means aligning the **code with reality**. Two exit codes then
fall together, and you need both:

```console
$ terraform plan -detailed-exitcode                 # 0: reality matches the code
$ terraform plan -refresh-only -detailed-exitcode   # 0: state matches reality
```

The first alone is not enough: it can exit 0 on a stale state.

## Over to you

```bash
dsoxlab run aws-import-moved-drift
dsoxlab check aws-import-moved-drift
dsoxlab hint aws-import-moved-drift
```

Six tests. The `moved` is proven **without opening a `.tf`**, and a counter-check
verifies on the Floci side that no extra instance exists: no destroy, no create.

Exam objective targeted: **1e**.

Reference: [import, moved and drift](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/aws/import-moved-drift/)
