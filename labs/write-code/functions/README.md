# Compose values with HCL functions

**Exam objective targeted: 2c**, compute and interpolate data with HCL functions.

Functions look like the easy part of the exam, until the day an out-of-range
index, a missing key or a badly escaped template makes a plan fail. This lab
chains those traps, then adds what almost no tutorial covers: the functions a
provider exposes.

Reference guide:
[Terraform functions](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/fonctions-terraform/)

## Prerequisites

- `terraform` on the PATH, version **1.8 or later** (provider functions do not
  exist before that).
- Network access for the first `terraform init` only, long enough to download the
  `hashicorp/local` provider.

Check your version:

```bash
terraform version
```

## 1. The console, before writing anything

`terraform console` works **in an empty directory, with no `terraform init`**.
That is the reflex to acquire: test the expression, then write it.

```bash
echo 'upper("lab")' | terraform console
```

```
"LAB"
```

Initialisation only becomes necessary when the expression touches a provider, a
module or a data source. A provider function is one of those.

## 2. Splitting, deduplicating, and why it matters

A CSV string often comes from a CI variable. `split()` turns it into a list:

```bash
echo 'split(",", "prod,dev,prod,staging")' | terraform console
```

```
tolist([
  "prod",
  "dev",
  "prod",
  "staging",
])
```

That list holds a duplicate. Passing it as-is to a `for_each` fails, because
`for_each` requires a **set** or a **map**. `toset()` does the conversion and
removes the duplicate along the way:

```bash
echo 'toset(split(",", "prod,dev,prod,staging"))' | terraform console
```

```
toset([
  "dev",
  "prod",
  "staging",
])
```

The stake is not cosmetic. With a set, each instance is addressed in state by
**its value** (`["dev"]`), and not by a position (`[0]`). Inserting an
environment later therefore shifts nothing.

## 3. element: modulo wrap-around

This is the first trap. `element()` does not behave like a classic index access.

```bash
echo 'element(["dev","staging","prod"], 5)' | terraform console
```

```
"prod"
```

Index 5 over three elements gives `5 % 3 = 2`, hence the third element.
**`element()` does not fall back on the first element**, it computes a modulo.
Two more behaviours to remember: `element(list, -1)` returns the last element,
and `element([], 0)` raises an error.

For a strict access that fails out of range, use `list[index]`.

## 4. lookup: the fallback value is not optional

Second trap. Many tutorials claim `lookup()` returns `null` when the key is
missing. It does not:

```bash
echo 'lookup({dev = "small"}, "qa")' | terraform console
```

```
Error: Invalid function argument
  the given object has no attribute "qa"
```

The two-argument form is moreover **deprecated since Terraform 0.7**. Always pass
the third argument:

```bash
echo 'lookup({dev = "small"}, "qa", "small")' | terraform console
```

```
"small"
```

## 5. merge: the last map wins

```bash
echo 'merge({projet = "demo"}, {env = "qa"})' | terraform console
```

```
{
  "env" = "qa"
  "projet" = "demo"
}
```

When a key is present on both sides, the **last** one prevails. That is what lets
you define a base of common tags and override one value at the last moment.

## 6. ceil: rounding the right way

Terraform only knows one `number` type, which accepts decimals. A division
therefore returns a float:

```bash
echo '1536 / 1024' | terraform console        # 1.5
echo 'ceil(1536 / 1024)' | terraform console
```

```
2
```

For sizing memory or disk, `floor()` would produce a resource that is too small.
`ceil()` guarantees it stays sufficient.

## 7. templatefile: only escape `${`

Third trap, and the most expensive. In a template, **only the `${` sequence has
to be escaped as `$${`**. A literal `$` followed by anything else passes through
untouched.

The lab's `node.yaml.tftpl` file holds all four cases:

```
hostname: ${hostname}
litteral: $${AUTRE}
script: |
  echo "home=$HOME"
  echo "date=$(date)"
```

After rendering, `${hostname}` is substituted, `$${AUTRE}` becomes the text
`${AUTRE}`, and `$HOME` as well as `$(date)` stay intact so that bash interprets
them at runtime.

Systematically escaping every `$` as `$$`, as many tutorials recommend,
**corrupts the script**: bash reads `$$` as the process PID, and `$$HOME` prints
as `786103HOME`.

## 8. Provider functions

You cannot define your own functions in HCL, but a provider can expose some.
Since **Terraform 1.8**, they are called like this:

```
provider::<local_name>::<function>(...)
```

The catch: `<local_name>` is the name declared in `required_providers`, not the
provider's name. The **built-in** `terraform` provider lets you try without
downloading anything:

```hcl
terraform {
  required_providers {
    terraform = { source = "terraform.io/builtin/terraform" }
  }
}
```

It exposes `encode_tfvars`, `decode_tfvars` and `encode_expr`:

```hcl
provider::terraform::encode_tfvars({ env = "qa", gib = 2 })
# returns the string: env = "qa"\ngib = 2\n
```

After adding a provider to `required_providers`, you must **re-run
`terraform init`**, otherwise the call fails with `Unknown provider`.

## 9. When is a function evaluated?

Not every function error falls at plan time. A function applied to a value
**unknown at plan time**, because it comes from a resource not yet created, is
only evaluated at `apply` time. The error then arises **after** resources have
been created, and you have to reconcile the partial state afterwards.

That is why an explicit validation beats a function that may fail too late.

## Over to you

The challenge awaits in `challenge/README.md`. The supplied configuration does not
validate: seven `locals` and two resource attributes are to be completed.

```bash
dsoxlab run write-code-functions
dsoxlab check write-code-functions
```

If you get stuck, three hints of increasing cost are available:

```bash
dsoxlab hint write-code-functions
```
