# Scenario: Pro · Objective 5, configure and use providers

**Exam objective targeted: 5** (5a plugin architecture, 5b configuration with aliasing,
versioning, sourcing and upgrades, 5c authentication, 5d diagnosing provider errors).

## Capability targeted

Have **several configurations of the same provider** coexist in one configuration, master
the version constraint and the lock file, and **diagnose a provider error** instead of
suffering it.

## Where the learner starts

Floci runs locally. In `challenge/work`, a configuration declares only **one** `aws`
provider aiming at the emulator, and a new requirement lands: some resources must be
created through a **second provider configuration** (another region, other settings).

The configuration also carries two deliberate problems: a missing version constraint, and
an **authentication error** caused by missing options on the provider. The exact diagnosis
is part of the exercise:

```text
Error: No valid credential sources found
failed to refresh cached credentials, no EC2 IMDS role found
```

The provider looks for credentials in order: the environment, then `~/.aws`, then EC2
instance metadata. The tests run in an environment stripped of every `AWS_*` variable and
with a `HOME` holding no `.aws`, without which the starting configuration would pass on a
machine that has credentials, and the lab would measure nothing.

## The state to reach

1. Two `aws` provider configurations coexist, one default and one **aliased**, and each
   resource is explicitly attached to the right one.
2. The provider version is **constrained** in `required_providers`, and the lock file
   reflects that constraint.
3. The authentication error is fixed: the provider aims at Floci with the options that
   disable identity checks pointless locally, and non-empty fake credentials.
4. `terraform init` then `apply` succeed, and the resources are created on the Floci side.

## How it is proven

- The JSON plan's `configuration.provider_config` holds both configurations, one carrying
  `alias = archives`, and each with its own region.
- **The central proof**: `provider_config_key` on each resource says which configuration
  produced it. Without the `provider` argument a resource silently takes the default one,
  and nothing else in state would show it: two EC2 instances look alike.
- A proof leaving Terraform: Floci **isolates by region**, measured on 2026-09-25. Each
  instance must be visible in its own region and absent from the other, which no single
  configuration could achieve.
- The lock file carries a `constraints` field for `hashicorp/aws`.
- The final test destroys both instances whatever happens: each one is a real container on
  Floci, holding a port that the next lab would fail on.
