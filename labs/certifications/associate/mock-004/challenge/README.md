# A mock exam whose answers are proven

## The situation

**Exam objectives targeted: Terraform Associate 004, 4c (use variables and outputs) as the
main one, with 4d, 4f, 4g and 7b mobilised by the workshop questions.**

A multiple-choice test marked by hand proves nothing and cheats itself: here the answers
travel in a variables file, Terraform marks them itself, and four questions have no answer
until infrastructure has been built. The trap covered is that of stale question banks: the
novelties of the 004 are neither the lock file nor `moved`, they are 4f (`depends_on`,
`create_before_destroy`), 4g, 4h and 8c.

## Capability targeted

Answer the eight objectives of the Associate 004 syllabus in a machine format, and prove
every answer through the state of a configuration actually initialised, applied and
inspected: knowing the answer, and being able to show it with the CLI. Assert nothing
without proof.

## Where the learner starts

`challenge/work` holds two directories. In `examen/`: a `questions.fr.md` of 40 questions
`q01` to `q40`, labelled by official objective, mixing single choice, true/false and
multiple answers (marked by sorted letters, for instance `ac`); a `reponses.auto.tfvars`
where every entry is `"???"`; and a supplied marking scheme, not to be modified, which
declares `variable "reponses"` as a `map(string)` and compares the salted `sha256`
fingerprint of each answer with a table of fingerprints, no answer existing in clear text.
In `atelier/`: a configuration holed with `???` on `local`, `null` and `random`, with no
`.terraform/`, no state and no lock file.

## The state to reach

1. `atelier` is initialised, the three providers constrained with `~>`, the lock present.
2. `atelier` is applied and holds managed objects and exactly one `data` block, a
   dependency declared through `depends_on`, and a resource replaced under
   `create_before_destroy`.
3. A `precondition`, a `postcondition` and a `check` block all pass, and a `sensitive`
   variable has its value in clear text in state while its output is masked.
4. Right after the apply, `atelier` is stable: no pending change.
5. `reponses.auto.tfvars` holds no `???` any more and supplies the 40 answers, among them
   `q37` to `q40` which are about the real state of `atelier`: the number of objects in
   `mode: managed`, the address of the `mode: data` block, the exit code of the stability
   plan, and whether the sensitive value is present in clear text in state.
6. The overall score reaches at least 80 %, no objective is below 50 %, and the scheme's
   fingerprint table is intact.

## How it is proven

- In `examen`, `terraform output -json` exposes `corrige` (one boolean per question),
  `score`, `score_par_objectif` and `sans_reponse`: the tests require `sans_reponse` to be
  empty, a number of wrong entries under the tolerated quota, and `score` above 80.
- Nothing can be hard-coded, those outputs being computed by the scheme from
  `var.reponses`. The tests hold no answer: they check the `empreintes` table does have
  forty entries and that each is a `sha256`, which detects a truncated or rewritten scheme
  without ever serving as an answer key.
- In `atelier`, `terraform show -json` is the single source: objects counted by `mode`, the
  address of the `data` block, the sensitive value in clear text in state; the plan
  converted to JSON confirms `create_before_destroy` and the `depends_on`.
  `plan -detailed-exitcode` exits 0 right after the apply.
- Final cross-check: the tests recompute the four control values from `atelier`'s state and
  require them to match the answers supplied. Guessing `q37` to `q40` without building the
  workshop fails on the state, building without answering fails on the score. No learner
  `.tf` is read back. Lacking any write-only argument in `local`, `null` and `random`, 4h
  cannot be tested through an argument never written to state: it is tested otherwise, by a
  knowledge question and by a workshop question that has the learner observe the sensitive
  value in clear text in `terraform.tfstate`.

## 🎯 Challenge: a mock exam whose answers are proven

### 📦 Starting point

`challenge/work` holds **two directories**, and the order in which you tackle
them is not indifferent.

| Directory | What it holds |
| --- | --- |
| `examen/` | `questions.fr.md` (40 questions), `reponses.auto.tfvars` (to fill in), `bareme.tf` and `versions.tf` **supplied, not to be modified** |
| `atelier/` | `versions.tf` and `variables.tf` **supplied**, `main.tf` and `outputs.tf` **holed** |

**Start with the workshop.** The last four questions have no answer until it is
built: they are about the state it produces.

### ✅ What you must reach

#### In `atelier/`

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

#### In `examen/`

7. The **40 answers** in `reponses.auto.tfvars`, with no `???` left.
8. **An overall score of at least 80 %**, and **no objective below 50 %**.

### 🧭 The answer format

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

### ⚠️ What the marking scheme protects, and what it does not

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

### 🔍 Validation

```bash
dsoxlab check certifications-associate-mock-004
```

Ten tests. They read `terraform show -json` and `terraform output -json` of both
directories, never your `.tf`. The last one requires **both** directories to be
stable: a `check` block querying data re-read on every plan would bring back a
code 2 and fail that check.

Stuck? `dsoxlab hint certifications-associate-mock-004`.
