# Scenario: Pro · Objective 4, create, maintain and use modules

**Exam objective targeted: 4** (4a create a module, 4b use it, 4c refactor and version it,
**4d refactor an existing configuration into modules**).

## Capability targeted

Turn a flat, repetitive configuration into a **reusable module**, then reorganise it
**without destroying or recreating** the resources already in place. That is where the
Professional level is decided: a refactor that destroys production is a failed refactor.

## Where the learner starts

In `challenge/work`, a flat configuration that **duplicates the same set of resources three
times**, with only a few values changing. It is **already applied**: a state exists, the
resources are created, and their identifiers are frozen in the supplied fixture.

## The state to reach

1. A local module exposes a clean interface: typed and documented input variables, useful
   outputs, and **no hard-coded value**.
2. The root calls that module **three times** (or once with `for_each`), and the
   duplication is gone.
3. The module carries its **own version requirements**: a `required_providers` block with a
   constraint, and **no provider configuration**, those being inherited from the caller.

   Mind the trap the lab has you observe: a `module` block's `version` argument **only
   applies to registry modules**. On a local source, Terraform refuses at `init` time:

   ```text
   Error: Invalid registry module source address
   you also set the argument "version", which applies only to registry modules.
   ```

   Measured on 2026-09-25. Versioning a local module therefore goes through the repository
   carrying it, not through that argument.

4. **The decisive point**: after the refactor, `terraform plan` announces **zero changes**.
   The resources changed address in state (they now live under `module.*`) but were not
   recreated. That means moving the addresses properly rather than letting Terraform
   destroy and recreate.

## How it is proven

- `terraform state list` shows addresses prefixed with `module.`, and **no** resource left
  at the old root address.
- The identifiers in state are **identical** to those before the refactor: the proof they
  were not recreated. That is what an empty plan does NOT say, since a configuration that
  destroyed and recreated everything would have converged too.
- `terraform plan -detailed-exitcode` exits **0** right after the refactor.
- The plan's `configuration` section is read to check the module's interface: every
  variable has a description, and outputs exist. It also confirms no provider configuration
  lives inside the module.
- The produced files are read back: their content must be unchanged, which also catches a
  module writing with `path.module` instead of `path.root` and thus moving them.

Three of these tests carry a guard refusing to measure while the resources do not live
under a module: without it, the supplied starting state made them green before any work.
