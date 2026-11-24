# Pro · Objective 5, configure and use providers

## The situation

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

## 🎯 Challenge: two configurations of one provider

### 📦 Starting point

`challenge/work` holds a `main.tf` that **does not apply**, and a `CIBLE.md`.
Floci provides the emulator.

Three things are missing, and they do not show at the same time:

1. **no version constraint** on the provider;
2. **the provider looks for an identity that does not exist**: run a `plan` and
   read the error, it names what it did not find;
3. **a new requirement**: the archives must live in a second region, which a
   single configuration cannot do.

The first two are **diagnosed**. The third is **built**.

### ✅ Objective

1. **A version constraint**, reflected in the lock file.
2. **The default provider** reaches the emulator without checking a
   non-existent identity: **non-empty** fake credentials, and the three options
   sparing it the search.
3. **A second configuration**, aliased, for `us-east-1`. It carries its own
   options: nothing is inherited from one configuration to another.
4. **`aws_instance.archives`** created by that second configuration,
   `aws_instance.principal` by the default one.

### 🧭 The omission that does not show

Without the `provider` argument, a resource uses the **default** configuration.
It is created in the wrong place, and **nothing flags it**: two instances look
alike, and state does not say which produced them.

The only place that says so is the `provider_config_key` field of the JSON
plan's `configuration` section.

### ⚠️ The lock file does not update itself

`constraints` is only written to `.terraform.lock.hcl` when the entry is
**created**. If you add the constraint after a first `init`, delete the lock and
run it again: neither `init` nor `init -upgrade` fixes it.

### 🔍 Validation

```bash
dsoxlab check certifications-professional-capstone5-providers
```

Six tests, in an environment with **no AWS credentials at all**: no `AWS_*`
variable, no `~/.aws`. That is what makes the error to diagnose appear, and what
guarantees the lab measures your work rather than your machine.

One proof leaves Terraform: Floci **isolates by region**, so each instance must
be seen in its own and absent from the other.

Stuck? `dsoxlab hint certifications-professional-capstone5-providers`.
