# A module interface: four mechanisms beyond `type` and `default`

A module is judged by what it **accepts** as input and what it **guarantees** as
output. Declaring a `type` and a `default` covers the simple case, and lets four
situations through that break in practice: an optional **object attribute**, an
**explicitly passed `null`**, an output that should **refuse** to publish itself,
and a **secret** crossing the module boundary.

This tutorial shows all four, measured on a throwaway configuration.

## The playground

A module producing a token for a broadcast channel:

```hcl
# modules/bulletin/main.tf
resource "random_password" "jeton" {
  length = var.taille_jeton
}
```

Called as briefly as possible, with a single attribute:

```hcl
module "bulletin" {
  source = "./modules/bulletin"

  canal = { nom = "interne" }
}
```

## `optional()`: making an object attribute optional

`default` applies to the **whole variable**, never to the **fields** of an
object. Declare `object({ nom = string, frequence = string })` and the call above
fails: an attribute is missing.

The official mechanism is **`optional(type, default)`**, available since **1.3**:

```hcl
variable "canal" {
  type = object({
    nom       = string
    frequence = optional(string, "hebdomadaire")
    actif     = optional(bool, true)
  })
}
```

The second argument is the value substituted when the attribute is **absent**.
The module therefore fills in what the caller did not provide:

```json
{
  "actif": true,
  "frequence": "hebdomadaire",
  "nom": "interne"
}
```

Without that second argument, `optional(string)` would yield `null`: the variable
would be optional, but with no fallback value.

## `nullable`: an explicit `null` is not an absence

Here is the trap you never see coming. A caller writes `libelle = null` thinking
"pass nothing". With a variable that does have a `default`:

```hcl
variable "libelle" {
  type    = string
  default = "bulletin"
}
```

The value received is **`null`**, not `"bulletin"`:

```text
libelle = null
```

Because **`nullable` defaults to `true`**: an explicit null is a value like any
other, and it overrides the default. The fix is one line:

```hcl
variable "libelle" {
  type     = string
  default  = "bulletin"
  nullable = false
}
```

The same call then returns `"bulletin"`. A reusable module therefore sets
`nullable = false` on every variable whose default must **always** apply.

## `validation`: refusing a value, and saying where to fix it

A `validation` block rejects a value with a message you write:

```hcl
variable "taille_jeton" {
  type    = number
  default = 16

  validation {
    condition     = var.taille_jeton >= 12 && var.taille_jeton <= 64
    error_message = "taille_jeton doit etre comprise entre 12 et 64."
  }
}
```

The refusal is explicit, and the last line matters when several modules declare
the same variable:

```text
Error: Invalid value for variable

  on main.tf line 6, in module "bulletin":
   6:   taille_jeton = 8
    ├────────────────
    │ var.taille_jeton is 8

taille_jeton doit etre comprise entre 12 et 64.

This was checked by the validation rule at
modules/bulletin/variables.tf:19,3-13.
```

Terraform names **two** places: where the offending value was passed, and where
the rule that refused it is written.

## Outputs carry more than `value`

An `output` block accepts, among others, **`description`**, **`sensitive`**,
**`precondition`**, **`type`** and **`depends_on`**. Two of them change observable
behaviour.

**`sensitive`** prevents the value from being displayed, and its necessity
**propagates**:

```hcl
output "jeton" {
  description = "Jeton d'acces du canal."
  sensitive   = true
  value       = random_password.jeton.result
}
```

Republish that value at the root without marking it, and the plan **fails**:

```text
Error: Output refers to sensitive values

To reduce the risk of accidentally exporting sensitive data that was intended
to be only internal, Terraform requires that any root module output
containing sensitive data be explicitly marked as sensitive, to confirm your
intent.
```

The child module does not even need to have marked its own output: the
**contamination** comes from the value itself. Chaining modules without knowing
this leads straight to that refusal.

**`precondition`** lets an output **refuse to publish itself**:

```hcl
output "emplacement" {
  value = local_file.this.filename

  precondition {
    condition     = var.canal.actif
    error_message = "L'emplacement n'est publie que pour un canal actif."
  }
}
```

The condition is evaluated **at plan time**, and its failure stops it dead:

```text
Error: Module output value precondition failed
```

This is how you express a **guarantee**: the module does not publish a value that
would make no sense in the state it is called in.

## Your turn

You can make an object attribute optional with `optional()`, protect a default
from an explicit `null` with `nullable = false`, refuse an out-of-range value
with a message that says where to fix it, gate an output behind a
`precondition`, and let a secret cross the boundary without breaking the plan.
The challenge hands you a module called **twice**, whose entire interface is
yours to write: the minimal call is what puts it to the test.

```bash
dsoxlab run modules-module-variables-outputs
dsoxlab check modules-module-variables-outputs
dsoxlab hint modules-module-variables-outputs
```

Target exam sub-objective: **2e** (variables and outputs, complex types),
supporting **4a** and **2f**.

Reference: [module variables and outputs](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/variables-outputs-module/)
