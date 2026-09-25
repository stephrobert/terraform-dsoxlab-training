# Six objectives, six directories, one sitting

The six capstones of the Professional section each prove one objective, which is
what learning requires. The exam does not announce which objective the next task
belongs to, and it leaves no time to settle back in.

This lab is the dress rehearsal: six tasks, one per objective, to be played in
one go once the capstones are done.

## What it changes compared with the capstones

**Nothing is announced at the convenient moment.** Each directory carries its
instructions as comments, the way an inherited repository does, and the
difficulty lies as much in the reading as in the writing. Three tasks also
require a **stable** plan afterwards: a solution that rebuilds on every run
produces the right file and still fails, which is exactly what the exam
penalises.

| Task | Objective | What is measured |
| --- | --- | --- |
| `t1-derive` | 1 | the hand-corrected file is adopted, not overwritten |
| `t2-dynamique` | 2 | three faults fixed, three resources become one, a port refused at plan time |
| `t3-etats` | 3 | the value crosses two states, and follows when the base changes |
| `t4-module` | 4 | three environments go through a module, nothing recreated |
| `t5-providers` | 5 | the private file is rendered by another configuration, with closed permissions |
| `t6-hcp` | 6 | twelve questions, a global threshold, four sub-objectives covered |

## Two traps that cannot be guessed

**The first is the content.** Task 1 lays down a file that someone corrected by
hand. A configuration that describes it approximately yields a state that looks
right, a plan that looks stable, and a rewritten file: the correction is lost.
Only reading the content tells the two apart, and that is what the test does.

**The second is where permissions belong.** The `local` provider accepts no
argument at all: its configuration schema is empty, measured on 2026-09-25.
Putting `directory_permission` there fails the apply on

```
An argument named "directory_permission" is not expected here.
```

Permissions belong to the resource, and there are two of them: one for the file,
one for the directory Terraform creates along the way.

## Task 6 marks itself

Twelve questions, a supplied marking scheme that holds **no answer in clear
text**, only the salted `sha256` fingerprint of each. Terraform returns the
score, the score per sub-objective and the list of unanswered questions:

```console
$ terraform output score
83
$ terraform output score_par_sous_objectif
{ "6a" = 100, "6b" = 75, "6c" = 66, "6d" = 100 }
```

You must reach the global threshold **and** have answered across all four
sub-objectives. A flattering score obtained by skipping a slice of the syllabus
does not pass: the same requirement as in `mock-004`, and for the same reason.

What the scheme protects, stated plainly: it prevents **reading** the answers by
opening a file. It does not prevent **recovering** them, since the salt is there
and a single-choice question has only four possible answers. No local marking
scheme can do better.

## What it does not cover

Local providers cannot import: `local` and `null` both answer
`Resource Import Not Implemented`. Import remains proven by
`capstone1-resource-lifecycle` and `aws-import-moved-drift`, which have a real
provider; here task 1 proves the other half of the same sub-objective, drift
reconciliation.

That is the price of a mock exam that starts in one command, with no emulator
and no account, and can therefore be replayed as often as needed.

## Over to you

```bash
dsoxlab run certifications-professional-mock-pro
dsoxlab check certifications-professional-mock-pro
dsoxlab hint certifications-professional-mock-pro
```

Objective targeted: all **six** of the Professional syllabus.

Reference: [preparing for the Terraform Professional certification](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/certifications/professional/)
