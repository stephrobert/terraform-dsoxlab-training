# 🎯 Challenge: read the stream of a run that failed midway

## 📦 Starting point

`challenge/work` holds three directories. **No account needed.**

| File | State |
| --- | --- |
| `flux/main.tf` | **supplied**, do not change: its third resource fails on purpose |
| `analyse/analyse.tf` | five `???`: read the stream and draw conclusions |
| `questionnaire/questionnaire.tf` | **supplied**, do not change |
| `questionnaire/reponses.auto.tfvars` | five `???` to answer |

## ✅ Objective

1. **Play the run and record its stream** in `flux/`:

   ```bash
   terraform apply -auto-approve -json > run.jsonl
   ```

   It will end with a non-zero status. **That is the expected outcome**: the
   third resource writes below a path whose parent is a file.

2. **Analyse the stream**: messages by type, the summary it carries, the
   addresses that completed, the one that errored, and the difference between
   what was announced and what took place.

3. **Answer the five questions** on the three workflows.

## 🧭 The trap, and it closes on a sensible habit

The stream of a run that **completes** carries two `change_summary` messages, one
for the plan and one for the apply. Filtering on the apply is then the right
thing to do.

The stream of a run that **fails midway** carries only one, the plan's. Filtering
on the apply returns nothing, and the summary you are left with announces more
than actually happened.

That difference is the whole point of the exercise. Count, do not trust.

## ⚠️ The stream cannot be written by hand

The tests require the system to agree with it: two files present, the impossible
one absent, and exactly two resources in the state.

## 🔍 Validation

```bash
dsoxlab check hcp-terraform-remote-runs
```

Twelve tests. They re-read `flux/run.jsonl` and recompute what your analysis
should have returned, so nothing is compared against a frozen number: a different
stream gives different expectations.

Stuck? `dsoxlab hint hcp-terraform-remote-runs`.
