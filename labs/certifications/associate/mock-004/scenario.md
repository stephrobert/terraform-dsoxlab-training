# Scenario: a mock exam whose answers are proven

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
