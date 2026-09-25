# 🎯 Challenge: a mock exam whose answers are proven

## 📦 Starting point

`challenge/work` holds **two directories**, and the order in which you tackle
them is not indifferent.

| Directory | What it holds |
| --- | --- |
| `examen/` | `questions.fr.md` (40 questions), `reponses.auto.tfvars` (to fill in), `bareme.tf` and `versions.tf` **supplied, not to be modified** |
| `atelier/` | `versions.tf` and `variables.tf` **supplied**, `main.tf` and `outputs.tf` **holed** |

**Start with the workshop.** The last four questions have no answer until it is
built: they are about the state it produces.

## ✅ What you must reach

### In `atelier/`

1. **Four managed resources**, and a **single** `data` block.
2. The `lifecycle` block of `local_file.modele_source` carries **three** things:
   the rule that creates before destroying, a `precondition` refusing at plan
   time a fingerprint that is too short, and a `postcondition` reading the
   written file back through `self`.
3. The data source reads the file **produced** by that resource, by referencing
   its attribute.
4. `null_resource.garde` waits for the data source although it uses **none** of
   its data.
5. A `check` block named `modele_lisible`, at **root** level.
6. Two outputs, one of them **sensitive**.

### In `examen/`

7. The **40 answers** in `reponses.auto.tfvars`, with no `???` left.
8. **An overall score of at least 80 %**, and **no objective below 50 %**.

## 🧭 The answer format

| Type | What is expected | Example |
| --- | --- | --- |
| single choice | one letter | `b` |
| true / false | `v` or `f` | `v` |
| multiple choice | the letters **sorted**, stuck together | `ac`, never `ca` |
| workshop | the value observed, lowercase | `4` |

Case and surrounding spaces are ignored: `B` and ` b ` both pass. An entry left
at `???` counts as **unanswered**, and the tests require none to remain.

Three outputs help you make progress:

```bash
cd examen
terraform output corrige              # which questions are wrong
terraform output score_par_objectif   # which objective is weak
terraform output sans_reponse         # what is left to fill in
```

## ⚠️ What the marking scheme protects, and what it does not

No answer exists in clear text in what you receive: `bareme.tf` carries only
salted `sha256` fingerprints. That prevents **reading** the answers by opening a
file.

It does not prevent **recovering** them: the salt is in the scheme, and a
single-choice question has only four possible answers. No local marking scheme
can do better, and this lab prefers to say so rather than suggest otherwise.

The real guard rail is elsewhere: the last four questions are about **your**
workshop, and the tests recompute their answers from **your** state before
comparing. Answering without building fails on the state; building without
answering fails on the score.

## 🔍 Validation

```bash
dsoxlab check certifications-associate-mock-004
```

Ten tests. They read `terraform show -json` and `terraform output -json` of both
directories, never your `.tf`. The last one requires **both** directories to be
stable: a `check` block querying data re-read on every plan would bring back a
code 2 and fail that check.

Stuck? `dsoxlab hint certifications-associate-mock-004`.
