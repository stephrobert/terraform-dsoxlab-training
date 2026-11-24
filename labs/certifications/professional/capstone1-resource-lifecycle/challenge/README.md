# Pro · Objective 1, resource lifecycle, import and drift reconciliation

## The situation

**Exam objective targeted: 1** (1a `init`, 1b `plan`, 1c `apply`, 1d `destroy`,
and above all **1e: manage resource state, import resources, reconcile drift**).

It is the only objective for which HashiCorp publishes official practice labs,
and the most discriminating one: taking over infrastructure you did not create is
the daily reality of a Professional profile.

## Capability targeted

Bring under Terraform's control a resource **created outside it**, without
destroying it, then **detect and reconcile a discrepancy** that appeared outside
the code.

## Where the learner starts

Floci runs locally (Docker socket mounted, `-u root`). Two resources were created
**outside Terraform**, directly through the AWS CLI: an EC2 instance and an S3
bucket. They carry precise tags.

In `challenge/work`, a `main.tf` declares the `aws` provider aiming at Floci, and
the two resources holed: the blocks exist, but the arguments are `???`. No state
exists yet.

## The state to reach

1. Both resources appear in state, **without having been recreated**: the
   imported instance's identifier is the same as before.
2. The configuration is **faithful** to reality: right after the import, a
   `terraform plan` proposes **no change**. That is an import's real success
   criterion, and the classic trap: an import that "works" but whose plan then
   wants to modify the resource is a failed import.
3. A **drift** is then caused outside Terraform (a tag changed through the AWS
   CLI). The learner must detect it, then choose and apply the reconciliation.
4. The final `destroy` leaves an empty state and no resource left on the Floci
   side.

## How it is proven

The tests query state, never the learner's file:

- `terraform show -json`: both addresses are present, and the `instance_id`
  matches the one created outside Terraform (proof of an import, not of a
  recreation).
- `terraform plan -detailed-exitcode` exits **0** after the import: the
  configuration is faithful.
- The `Owner` tag carries its manual value on the Floci side **and** in state:
  the drift was accepted rather than overwritten. Doing nothing would leave the
  original value, overwriting would restore it, and both fail.
- `terraform plan -refresh-only -detailed-exitcode` exits **0** as well. The
  ordinary plan alone is not enough: it can exit 0 on a stale state.
- After `destroy`: state holds nothing, and the AWS CLI pointed at Floci no
  longer finds the instance. That test runs even if the preceding ones failed.

## 🎯 Challenge: take over, without destroying, what Terraform knows nothing about

### 📦 Starting point

Two objects **already exist** at the provider, created by hand:

| Object | What it carries |
| --- | --- |
| an EC2 instance | the tags `Name = capstone-facturation`, `Owner = finops`, `Env = prod` |
| an S3 bucket | the name `capstone-archives-legacy` |

`challenge/work` holds `providers.tf` (**supplied**, aiming at Floci) and
`main.tf` (**holed**). No state.

**Nobody hands you the identifiers.** Finding them is step one.

```bash
aws --endpoint-url http://localhost:14566 ec2 describe-instances \
    --filters 'Name=tag:Name,Values=capstone-facturation' \
    --query 'Reservations[].Instances[].InstanceId' --output text
```

The instance is created as the lab starts, in parallel: if the command returns
nothing, wait a few seconds and run it again.

### ✅ Objective

1. **Import both objects** under the addresses `aws_instance.facturation` and
   `aws_s3_bucket.archives`, without recreating them.
2. **Make the configuration faithful**: an ordinary `plan` proposes nothing.
3. **Cause a drift** outside Terraform, setting the `Owner` tag to `plateforme`:

   ```bash
   aws --endpoint-url http://localhost:14566 ec2 create-tags \
       --resources <id> --tags 'Key=Owner,Value=plateforme'
   ```

4. **Accept it**: align the code with reality, not the other way round.

### 🧭 The two criteria that matter

**An import is not finished when the resource is in state.** While an ordinary
`plan` proposes anything, your code describes something other than the real
object, and the next `apply` will modify that object. Record its real values
before writing the configuration.

**Two exit codes must fall together** at the end:

```bash
terraform plan -detailed-exitcode                 # 0: reality matches the code
terraform plan -refresh-only -detailed-exitcode   # 0: state matches reality
```

The first alone is not enough: it can exit 0 on a stale state.

### ⚠️ Overwriting drift is a reflex, not a decision

An `apply` "puts things back in order" and erases a change somebody made for a
reason you do not know. That colleague will never learn why their tag
disappeared.

Accepting drift means deciding reality is right, and saying so in the code.

### 🔍 Validation

```bash
dsoxlab check certifications-professional-capstone1-resource-lifecycle
```

Five tests. None reads your `.tf`: they compare the state's identifier with the
one Floci knows, check the tag **on both sides**, and require both exit codes.

The last test **destroys**, and it runs even if the others failed: a failed lab
leaving an instance behind makes the next lab pay for it.

Stuck? `dsoxlab hint certifications-professional-capstone1-resource-lifecycle`.
