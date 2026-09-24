# 🎯 Challenge: take over, without destroying, what Terraform knows nothing about

## 📦 Starting point

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

## ✅ Objective

1. **Import both objects** under the addresses `aws_instance.facturation` and
   `aws_s3_bucket.archives`, without recreating them.
2. **Make the configuration faithful**: an ordinary `plan` proposes nothing.
3. **Cause a drift** outside Terraform, setting the `Owner` tag to `plateforme`:

   ```bash
   aws --endpoint-url http://localhost:14566 ec2 create-tags \
       --resources <id> --tags 'Key=Owner,Value=plateforme'
   ```

4. **Accept it**: align the code with reality, not the other way round.

## 🧭 The two criteria that matter

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

## ⚠️ Overwriting drift is a reflex, not a decision

An `apply` "puts things back in order" and erases a change somebody made for a
reason you do not know. That colleague will never learn why their tag
disappeared.

Accepting drift means deciding reality is right, and saying so in the code.

## 🔍 Validation

```bash
dsoxlab check certifications-professional-capstone1-resource-lifecycle
```

Five tests. None reads your `.tf`: they compare the state's identifier with the
one Floci knows, check the tag **on both sides**, and require both exit codes.

The last test **destroys**, and it runs even if the others failed: a failed lab
leaving an instance behind makes the next lab pay for it.

Stuck? `dsoxlab hint certifications-professional-capstone1-resource-lifecycle`.
