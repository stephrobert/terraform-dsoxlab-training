# Scenario: constrain the Terraform version and lock the providers

**Exam objective targeted: 3a, manage the installation and versioning of Terraform and its providers.**

Installing a binary proves almost nothing. What matters is being able to impose a CLI version on a configuration and to freeze the providers it downloads, so that the same configuration behaves the same way on every machine in the team.

## Capability targeted

Declare a `required_version` constraint in the `terraform {}` block, make it fail deliberately in order to observe the refusal to run, pin the providers through `required_providers`, then make use of the `.terraform.lock.hcl` lock file that `terraform init` produces.

The official documentation is explicit about the boundary: `required_version` applies only to the CLI version, never to the providers'. These are two distinct mechanisms, and the lab forces you to handle both.

## Where the learner starts

Terraform is installed by one of the methods in the guide and `terraform version` answers. The learner knows how to pin a version at the tooling level (`mise.toml`, `.terraform-version`), but does not know the configuration itself carries its own constraint, and has never opened a lock file.

The `challenge/work` working directory holds only an empty `main.tf`. No `.terraform/`, no `.terraform.lock.hcl`, no downloaded provider. The lab is of type `shell`: it consumes no virtual machine and requires no cloud access.

## The state to reach

In `challenge/work`:

1. A `terraform {}` block carries a `required_version` satisfied by the installed CLI, and a `required_providers` declaring `hashicorp/local`, `hashicorp/null` and `hashicorp/random` with explicit version constraints.
2. The configuration creates one resource from each of those three providers, with no network access beyond downloading the providers.
3. `terraform init` succeeded and produced `.terraform.lock.hcl`, containing the three providers with their checksums.
4. `terraform providers lock` was re-run for at least two platforms, so that the lock covers heterogeneous machines.
5. The configuration was applied: state has converged.

In an `echec-version/` subdirectory:

6. A minimal configuration whose `required_version` cannot be satisfied by the installed CLI, serving as a counter-example.

## How it is proven

Validation never opens the `.tf` files written by the learner and parses no output meant for a human. It relies solely on structured output and exit codes:

- `terraform version -json` in `challenge/work`: the reported version satisfies the constraint, and `provider_selections` lists exactly the three expected providers.
- `terraform init` run in `echec-version/` returns a non-zero exit code, while the same call in `challenge/work` returns 0. What is proven is the refusal to run on an unsatisfied constraint, not the presence of some text.
- `.terraform.lock.hcl` is analysed as the machine file it is: three `provider` blocks, each with its resolved version, its `constraints` and at least one `h1:` checksum, for two platforms at minimum.
- The `.terraform/` directory is deleted, then `terraform init` is re-run: `provider_selections` must stay strictly identical. That is the proof the lock is authoritative and that nothing drifted towards a newer version.
- `terraform plan -detailed-exitcode` returns 0, which proves state is applied and converged. A code 2 would signal a configuration that was never applied.

All five proofs fail if the learner merely installed the binary.
