# 🎯 Challenge: two configurations of one provider

## 📦 Starting point

`challenge/work` holds a `main.tf` that **does not apply**, and a `CIBLE.md`.
Floci provides the emulator.

Three things are missing, and they do not show at the same time:

1. **no version constraint** on the provider;
2. **the provider looks for an identity that does not exist**: run a `plan` and
   read the error, it names what it did not find;
3. **a new requirement**: the archives must live in a second region, which a
   single configuration cannot do.

The first two are **diagnosed**. The third is **built**.

## ✅ Objective

1. **A version constraint**, reflected in the lock file.
2. **The default provider** reaches the emulator without checking a
   non-existent identity: **non-empty** fake credentials, and the three options
   sparing it the search.
3. **A second configuration**, aliased, for `us-east-1`. It carries its own
   options: nothing is inherited from one configuration to another.
4. **`aws_instance.archives`** created by that second configuration,
   `aws_instance.principal` by the default one.

## 🧭 The omission that does not show

Without the `provider` argument, a resource uses the **default** configuration.
It is created in the wrong place, and **nothing flags it**: two instances look
alike, and state does not say which produced them.

The only place that says so is the `provider_config_key` field of the JSON
plan's `configuration` section.

## ⚠️ The lock file does not update itself

`constraints` is only written to `.terraform.lock.hcl` when the entry is
**created**. If you add the constraint after a first `init`, delete the lock and
run it again: neither `init` nor `init -upgrade` fixes it.

## 🔍 Validation

```bash
dsoxlab check certifications-professional-capstone5-providers
```

Six tests, in an environment with **no AWS credentials at all**: no `AWS_*`
variable, no `~/.aws`. That is what makes the error to diagnose appear, and what
guarantees the lab measures your work rather than your machine.

One proof leaves Terraform: Floci **isolates by region**, so each instance must
be seen in its own and absent from the other.

Stuck? `dsoxlab hint certifications-professional-capstone5-providers`.
