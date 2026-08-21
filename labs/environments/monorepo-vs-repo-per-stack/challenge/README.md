# 🎯 Challenge: two stacks that talk to each other

## 📦 Starting point

A monorepo **already split** but **not wired**. Nothing is initialised, no state
exists.

| Path | What it is |
| --- | --- |
| `modules/reseau/` | **complete** local module, leave it alone |
| `stacks/plateforme/` | calls the module, empty `outputs.tf`, one secret declared |
| `stacks/applicatif/` | consumes the platform, **stubbed** `data` block |
| `CIBLE.md` | the state to reach and the three deciding facts |

## ✅ What you must achieve

1. `stacks/plateforme` initialises.
2. Its state holds the module resources, including `random_password.db`.
3. Its root outputs expose `network_name` and `network_cidr`.
4. **No** root output carries the password.
5. `stacks/applicatif` has a `mode: data` entry of type
   `terraform_remote_state`.
6. Its `network_cidr` matches the platform's **exactly**, and the file it
   produces contains it.
7. Both stacks are **idempotent**.

## ⚠️ The heart of the matter

Three measured facts decide the whole exercise.

**A local module does not accept `version`.** `init` fails, and the message says
exactly why. Read it before deleting the line.

**Only ROOT outputs cross.** An output from a nested module stays invisible from
another configuration: whatever must cross the boundary is re-exported
explicitly.

**Publishing an output publishes the whole state.** "any user or server which has
enough access to read the root module output values will also always have access
to the full state snapshot data". The password therefore has no place in a root
output, even marked `sensitive`.

## 🔍 Validation

`dsoxlab check environments-monorepo-vs-repo-per-stack` proves, by execution:

- that the platform tracks both the module **and** its secret;
- that it **re-exports** its two outputs at the root;
- that **none** of its outputs carries the password, compared **value by value**
  rather than on raw text;
- that the application really reads the upstream **state**;
- that the CIDR is **identical** on both sides. It is drawn at random on apply:
  copying it will not hold;
- that both stacks have converged.

Stuck? `dsoxlab hint environments-monorepo-vs-repo-per-stack`.
