# Expressions: references, types, conversion and null

An **expression** computes a value: an interpolation, an operator, a ternary, a
reference. It is the fabric of every configuration. The traps are the
**reference syntax** of a resource, **type conversion** (present for arithmetic,
absent for equality), and the **`null`** value wrongly replaced by an empty
string. This tutorial shows them in `terraform console` and on a throwaway
example; the challenge makes you apply them on a different case.

`terraform console` evaluates an expression without applying anything. It is
interactive, but also works **in a script**, by piping commands to its standard
input, which makes it a testing tool.

```bash
echo 'max(3, 7, 2)' | terraform console
```

```hcl
7
```

## Referencing a resource: no prefix

Named values each have a prefix: `var.name`, `local.name`,
`data.<type>.<name>.<attr>`, `module.<name>.<output>`, plus `each.key`,
`count.index`, `path.module` and `terraform.workspace`. But **a managed resource
is the exception: it is referenced WITH NO prefix**, as
`<type>.<name>.<attr>`:

```hcl
resource "random_string" "jeton" {
  length = 8
}

# correct: no "resource" keyword in the expression
output "valeur" {
  value = random_string.jeton.result
}
```

Writing `resource.random_string.jeton.result` is an **error**: the word
`resource` never appears in an expression. It is the only case in the list with
no prefix, and the most common beginner confusion.

## Types and automatic conversion

Terraform has three primitive types (`string`, `number`, `bool`) and complex
types (`list`, `set`, `tuple`, `map`, `object`). Between primitives it
**converts automatically** where it can, notably for arithmetic:

```hcl
> "5" + 3
8
```

The string `"5"` is converted to a number. **But equality does not convert.**
This is the rule that surprises the most:

```hcl
> 1 == "1"
false
```

The number `1` and the string `"1"` are **not** equal, for lack of conversion.
The documentation recommends using `==` and `!=` only between identical types,
or after an explicit conversion (`tostring()`, `tonumber()`). The same trap hits
the **ternary**, which does convert its two branches to a common type:
`true ? 12 : "hello"` returns a **string**, not a number.

## null: absence, not the empty string

**`null` represents the absence of a value.** Assigning `null` to a resource
argument is like **not writing it at all**: Terraform then applies the provider
default. The documentation says: "If you set an argument to `null`, Terraform
behaves as though you had completely omitted it."

```hcl
resource "local_file" "exemple" {
  filename        = "exemple.txt"
  content         = "x"
  file_permission = var.perm != "" ? var.perm : null
}
```

Here, when `var.perm` is empty, the argument is `null` and the permission falls
back to the provider default. Writing an **empty string** `""` instead would be
a real value, often invalid, not an omission. This is the standard way to make
an argument optional.

## Operators and precedence

Operators follow a classic precedence: unary (`!`, `-`), then `*` `/` `%`, then
`+` `-`, then comparisons, then `&&`, then `||`. Multiplication comes **before**
addition:

```hcl
> 1 + 2 * 3
7
```

`1 + 2 * 3` reads as `1 + (2 * 3)`, i.e. `7`, never `9`. When in doubt,
parentheses remove the ambiguity and document intent.

## A value can be unknown at plan time

Finally, an expression that depends on a not-yet-created attribute is
`(known after apply)`. This unknown **propagates**: a known value combined with
an unknown one yields an unknown. That is why a `count` cannot depend on a
resource attribute, and why some outputs only get their value after apply.

## Your turn

```bash
dsoxlab run write-code-expressions
dsoxlab check write-code-expressions
dsoxlab hint write-code-expressions
```

Exam objective: **2e** (expressions, types and values).

Reference: [Expressions in Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/expressions-terraform/)
