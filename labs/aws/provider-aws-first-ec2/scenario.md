# Scenario: making the AWS provider talk to a local emulator

**Exam objective targeted: 5c (provider authentication), 5b second (versioning and sourcing).**

The first failure on AWS is never the HCL, it is the provider configuration: where it calls, with which
identities, and what it validates before even planning. This lab tackles that trap by aiming at the local
emulator Floci, hence without an AWS account and without ever reading the machine's credentials.

## Capability targeted

Configure a `hashicorp/aws` provider pinned to the current major so that it authenticates and talks to a local
implementation of the API: fake static credentials, redirection through `endpoints`, disabling the validations
that call real AWS, tags applied by `default_tags`, then create an instance and prove it actually runs.

## Where the learner starts

Prerequisite: Floci listens on `http://localhost:14566` (`floci/floci:1.6.0`), started with `-u root` and
`/var/run/docker.sock` mounted. Without that, the instance stays stuck in `pending`, Floci creating a real
backing container behind every `RunInstances`.

`challenge/work` holds five files, two of them holed. `terraform.tf` declares the provider under the local name
`aws` but leaves `???` on `source` and on `version`. `providers.tf` is reduced to a `provider "aws"` block
carrying only `region = var.aws_region`: no credentials, no `endpoints`, no `skip_*` argument, no
`default_tags`. Complete are: `variables.tf` (`aws_region`, `ami_id`, `instance_type`, `floci_endpoint`,
`common_tags`) and `main.tf`, whose single `aws_instance "lab"` resource already consumes `var.ami_id` and
`var.instance_type`. `outputs.tf` has three `output` blocks whose `value` are `???`. No `.terraform/`, no state,
no `.terraform.lock.hcl`. The lab deliberately uses neither `data "aws_ami"` nor `data "aws_caller_identity"`:
Floci ignores the requested AMI and falls back on its base image.

## The state to reach

1. The installed provider is `registry.terraform.io/hashicorp/aws` at **6.x**, under a constraint bounded above
   and below, never the 5.x many examples still carry around.
2. The provider configuration carries non-empty fake static credentials, so that no `AWS_*` environment variable
   and no `~/.aws` file is needed.
3. The three validations that would query real AWS are disabled: credential validation through STS, querying the
   metadata API, and requesting the account id.
4. An `endpoints` block redirects the `ec2` service to Floci's address, carried by `var.floci_endpoint`.
5. The provider applies `var.common_tags` through `default_tags`, rather than the resource through a copied
   `tags`.
6. After the apply, state holds exactly one resource in `mode: managed`, of type `aws_instance`, which has
   reached the `running` state and not `pending`: proof that Floci could create its backing container, hence
   that the Docker socket is properly mounted.
7. The three outputs expose the instance id, its state and its private IP address, all non-empty.
8. A plan run right after the apply announces no change, and after the destroy state is empty.

## How it is proven

No test reads back a `.tf` file, everything goes through structured output.

- Plan saved then read back as JSON: `configuration.provider_config["aws"]` carries a `full_name` of
  `registry.terraform.io/hashicorp/aws`, a `version_constraint` bounding major 6, and `expressions` containing
  `endpoints`, the three `skip_*` at `true`, `default_tags`, and access keys with non-empty `constant_value`.
  The provider configuration is checked this way without depending on what Floci returns.
- `terraform version -json`: `provider_selections["registry.terraform.io/hashicorp/aws"]` is at least 6.0.0 and
  stays below 7.0.0. The commands run in an environment stripped of every `AWS_*` variable and with a `HOME`
  holding no `.aws`: if the credentials are not in the configuration, the plan fails.
- `terraform show -json` of state: a single entry, `"mode": "managed"`, `"type": "aws_instance"`. A
  configuration left holed produces nothing at all. A bounded loop of
  `terraform apply -refresh-only -auto-approve` until its `instance_state` is `running`, failing at the end of
  the budget: the transition is not instantaneous on Floci, and a permanent `pending` signs a missing Docker
  socket.
- `terraform output -json`: the three values are present and non-empty, and the state one is `running`.
- `terraform plan -detailed-exitcode` exits 0 right after the apply, then `terraform destroy -auto-approve`
  followed by rereading state leaves no resource, Floci indeed deleting the container on `terminate`.
