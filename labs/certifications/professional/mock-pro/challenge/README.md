# 🎯 Challenge: Pro, integrative mock exam

## 📦 The starting point

`challenge/work` holds **six directories**, one per objective. Each carries its
instructions as comments at the top of `main.tf`, and every `???` marks what is
left to write.

| Directory | What it holds |
| --- | --- |
| `t1-derive/` | an `existant.txt` laid down outside Terraform, and a configuration to write around it |
| `t2-dynamique/` | a configuration that **does not validate**, and three twin resources |
| `t3-etats/` | two root modules, `socle/` and `app/`, still ignoring each other |
| `t4-module/` | three environments written three times, already applied |
| `t5-providers/` | a single provider configuration where two are needed |
| `t6-hcp/` | `questions.md` (twelve questions), `reponses.auto.tfvars` to fill in, `bareme.tf` and `versions.tf` **supplied, not to be modified** |

The order is yours: each task is marked independently of the others. Start with
what you know how to do, which is also how the exam is played.

## ✅ What you must reach

### `t1-derive/`, objective 1

1. `local_file.inventaire` manages `existant.txt`, and **its content is
   unchanged**.
2. `terraform plan -detailed-exitcode` returns **0** after the apply.

### `t2-dynamique/`, objective 2

3. The three faults are fixed: `terraform validate` passes.
4. The three files come from **a single** resource, driven by `for_each`.
5. Each file carries its port, and the variable **refuses at plan time** a port
   outside 1024-65535.

### `t3-etats/`, objective 3

6. The base module publishes its identifier and its zone as outputs.
7. The application reads them through a data source, **copying nothing**.
8. Replaying the base with another zone makes the application follow.

### `t4-module/`, objective 4

9. The three environments go through a local module.
10. **No resource is recreated**: the state identifiers are the ones from
    before, and the plan is stable.

### `t5-providers/`, objective 5

11. A second provider configuration, **aliased**, renders `prive/`.
12. `prive/` is 700 and `prive/note.txt` is 600; `public/` keeps the default.
13. The provider constraint accepts the 2 series from 2.5 onwards and refuses
    3.0.

### `t6-hcp/`, objective 6

14. The **twelve** answers in `reponses.auto.tfvars`, with no `???` left.
15. **A global score of at least 75 %**, and **no sub-objective below 50 %**.

## 🧭 The answer format

| Type | What is expected | Example |
| --- | --- | --- |
| single choice | one letter | `b` |
| multiple choice | the letters **sorted**, joined | `ac`, never `ca` |

Case and surrounding spaces are ignored. An entry left at `???` counts as
missing, and the tests require that none remain.

```bash
cd t6-hcp
terraform output corrige                   # which questions are wrong
terraform output score_par_sous_objectif   # which sub-objective is weak
terraform output sans_reponse              # what is left to fill in
```

## ⚠️ Three traps, all of them measured

**The content of `existant.txt`.** Describing it approximately gives a correct
state, a stable plan, and a rewritten file: the hand-made correction is lost.
Reproduce the content **exactly**, trailing newline included.

**Permissions, in task 5.** The `local` provider accepts no argument.
`directory_permission` inside a `provider` block fails the apply on
`An argument named "directory_permission" is not expected here.` Permissions
belong to the resource, and there are two of them.

**The marking scheme, in task 6.** It holds only salted `sha256` fingerprints.
Replacing them with fingerprints of your own answers scores 100, and the test
refuses that: it first checks that the twelve fingerprints are intact.

## 🔍 Validation

```bash
dsoxlab check certifications-professional-mock-pro
```

Sixteen tests, grouped by task. They read `terraform show -json`, the state, the
lock file and the real permissions on disk, never your `.tf` files. Three tasks
require a stable plan: a solution that rebuilds on every run fails, even when
the file it produces is right.

Stuck? `dsoxlab hint certifications-professional-mock-pro`.
