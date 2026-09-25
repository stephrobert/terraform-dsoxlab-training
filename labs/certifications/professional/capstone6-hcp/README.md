# When several rules apply at once

The Professional's objective 6 is assessed **by multiple choice**, and this
capstone needs **no account**. It does not replay the seven labs of the section:
it crosses them.

That is the difference between knowing a rule and knowing which one wins.

## Questions that answer in order

To qualify a run, the rules do not commute. Each makes the next one moot:

| Question | If yes |
| --- | --- |
| does the workspace run anything at all? | if not, nothing else matters |
| will this run ever be able to apply? | if not, no policy has any object |
| is there anything to apply? | if not, the run ends |
| does a policy object? | and can it be overridden? |
| does the apply start on its own? | setting **and** trigger |

## The three traps, and why they look alike

They all have the same shape: a true rule, applied to a question that does not
arise.

**A failing `mandatory` policy on a pull request blocks nothing.** The rule
"mandatory blocks" is correct. It does not apply here, because a speculative plan
cannot apply: there is nothing to block.

**A failing `advisory` does not prevent an auto-apply.** The rule "a failing
policy stops the run" is false for that level, and that is the only thing the
level decides.

**In `local` execution mode, the policy question does not arise.** The workspace
is only a state store: nothing runs at HCP Terraform, so nothing is evaluated
there.

## What the capstone also has you write

**An attachment** (6b), written out in full: a `cloud` block is resolved before
any expression is evaluated, so it accepts no named value. A correct
configuration reaches `Required token could not be found`, and that is the
capstone's boundary.

**A sheet with no secret** (6c). Two measurements from the section meet here:
`sensitive` protects the display and leaves the value in clear text in the state,
and sensitivity propagates through functions without Terraform looking at what
they do. A fingerprint is therefore still considered sensitive, and the output
publishing it must be annotated.

## Over to you

```bash
dsoxlab run   certifications-professional-capstone6-hcp
dsoxlab check certifications-professional-capstone6-hcp
dsoxlab hint  certifications-professional-capstone6-hcp
```

Eight tests. One of them checks that **all seven verdicts differ**: two situations
receiving the same outcome would signal a rule that confuses them.

Exam objective targeted: **6**, in full.

Reference: [the Professional exam review](https://developer.hashicorp.com/terraform/tutorials/pro-cert/pro-review)
