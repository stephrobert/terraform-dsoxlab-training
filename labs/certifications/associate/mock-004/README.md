# A mock exam whose answers are proven

A multiple-choice test marked by hand proves nothing, and cheats itself. You
tick, you look at the key, you tell yourself you knew. On exam day the question
is about what a command **refuses** to do, and the illusion collapses.

This lab fixes two defects of an ordinary mock exam, and they are what justify
its existence.

## The answers travel in a variables file

You do not tick, you **declare**:

```hcl
reponses = {
  q01 = "b"
  q02 = "ac"
  ...
}
```

Terraform marks it itself, and returns the result as JSON:

```console
$ terraform output score
87
$ terraform output score_par_objectif
{ "1" = 100, "2" = 75, "3" = 85, ... }
```

The marking scheme carries **no answer in clear text**, only the salted `sha256`
fingerprint of each one.

Let us say straight away what that is worth: it prevents **reading** the answers
by opening a file, which is the real case. It does not prevent **recovering**
them, since the salt is in the scheme and a single-choice question has only four
possible answers. No local marking scheme can do better, and it is better
written down than left to suggest some inviolability.

## Four questions have no answer until you have built something

That is the real guard rail, and what sets this lab apart from a questionnaire.

The last four questions are about the **state** of a Terraform workshop you have
to put together: how many objects in `mode: managed`, what is the address of the
only `mode: data` block, what code `plan -detailed-exitcode` returns after the
apply, and whether the sensitive value can be read in clear text in state.

The tests **recompute** those four values from your own state, then compare them
with the fingerprints. Two consequences:

- answering without building fails on the state;
- building without answering fails on the score.

Both halves of the lab hold each other up.

## The workshop picks up what the syllabus is least able to recite

It fits in four resources and one `data` block, and yet it has you place side by
side five mechanisms people confuse:

| What you must write | What it makes you observe |
| --- | --- |
| `create_before_destroy` | the replacement order, readable in the plan |
| `precondition` | a refusal **at plan time**, before any action |
| `postcondition` | reading the result back through `self`, the only one that has it |
| `check` block | the only one of the five that **warns without blocking** |
| `depends_on` | the only dependency no reference can express |

And a sensitive output, which makes you observe that `sensitive` masks a display
without encrypting anything: the value is in clear text in `terraform.tfstate`.

## The threshold, and why there are two

The lab requires **80 % overall** and **50 % per objective**.

The second is not gratuitous severity. Forty questions allow compensation: you
can miss a whole objective and still be at 82 % by being good everywhere else. A
flattering overall score then hides a part of the syllabus never revised, which
will come up on exam day. The per-objective floor forbids that gamble.

```console
$ terraform output score_par_objectif
{ "1" = 100, "2" = 75, "3" = 85, "4" = 90, "5" = 25, "6" = 80, "7" = 100, "8" = 100 }
```

Here the overall passes, the lab fails, and it says where to revise.

## Over to you

```bash
dsoxlab run certifications-associate-mock-004
dsoxlab check certifications-associate-mock-004
dsoxlab hint certifications-associate-mock-004
```

It runs **offline**, on the `local`, `null` and `random` providers: no VM, no
cloud account.

The forty questions are labelled by **official sub-objective**, read on
2026-09-24 from the grid HashiCorp publishes and kept in the repository's
`curriculums.yml`.

A word on coverage: objective **4h** is about secrets management, and `local`,
`null` and `random` offer no *write-only* argument. That sub-objective is
therefore tested otherwise, through a knowledge question and through a workshop
question that has you observe the sensitive value in clear text in state.

Objectives targeted: all **eight** of the Associate 004 syllabus.

Reference: [Associate exercises](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/certifications/associate/exercices/)
