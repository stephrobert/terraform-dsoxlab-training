# Scenario: giving an instance an identity without ever placing a key

**Exam objective targeted: 2b, use data sources.**

`aws_iam_policy_document` is a **local** data source: it queries nothing, it
builds JSON. The lab makes that obvious fact demonstrable and clears up the
vocabulary inversion around a role's two policies.

## Capability targeted

Compose the policy, role, instance profile, instance chain while steering the
IAM JSON from HCL, and prove in structured state that the trust policy and the
permissions take two distinct paths to the role.

## Where the learner starts

Floci runs on `localhost:14566`: no AWS account, no bill. The `challenge/work`
directory is bare, with no `.terraform/`, no lock file and no state. The supplied
`versions.tf` is complete: it pins `hashicorp/aws` at `~> 6.0` and aims at Floci
through an `endpoints` block and the three usual `skip_*`. The `main.tf` and
`outputs.tf` are holed with `???`: the block naming the service allowed to assume
the role, the argument turning the document into a real IAM object, the two S3
ARNs of the read statement, the profile's role, and the instance argument that
receives that profile. Two traps wait in the comments: the guide calls the
permissions policy a "resource policy", whereas the only resource-based policy
IAM knows is the **trust policy**; and it credits the profile with "one or more
roles", whereas AWS allows **exactly one**.

## The state to reach

1. The directory is initialised and the lock file exists.
2. Two `aws_iam_policy_document` entries appear in state as `mode: data`: the
   trust policy, with a `principals` block of type `Service` aiming at
   `ec2.amazonaws.com` and the `sts:AssumeRole` action; and the permissions
   policy, one statement of which carries the bucket ARN for `s3:ListBucket` and
   another the ARN suffixed with `/*` for `s3:GetObject`.
3. An `aws_iam_role` carries the first document in `assume_role_policy`, and
   nothing else: it holds no permission. An `aws_iam_policy` carries the second
   and exposes an `arn`. No `description` and no `tags`: Floci does not read them
   back.
4. An `aws_iam_role_policy_attachment` links the two, the role by its `name`, the
   policy by its `arn`; an `aws_instance` receives the profile's **name**, not
   its ARN. Replaying a plan after the apply announces no change.
5. Removing the attachment from the code leaves a single pending deletion: the
   role survives, and so does the policy.

## How it is proven

No test reads back the learner's `.tf`, and none parses human output.
`terraform show -json` sorts each address by `mode`: the two documents under
`data`, the five created objects under `managed`. Their JSON, read back through
`terraform output -json` then deserialised, yields the trust policy's `Principal`
and `Action` and the **two** distinct S3 ARNs of the second. On the Floci side,
`iam get-policy-version` confirms the document actually received,
`iam get-instance-profile` a `Roles` array with a single element, and
`ec2 describe-iam-instance-profile-associations` the `associated` state.
`terraform plan -detailed-exitcode` exits 0 after the apply, then 2 once the
attachment is removed, the JSON plan carrying a single entry whose `actions` are
`["delete"]`. The `description` the guide recommends stays **out of reach of an
apply on Floci**, which answers `UnsupportedOperation`: that point is validated
**at plan time only**.
