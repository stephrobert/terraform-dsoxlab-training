# Scenario: the function that is not in the language

**Target exam objective: 5a (plugin architecture), with direct support on 2c (HCL functions).**

Since Terraform 1.8, a provider can expose its own functions, called through a qualified prefix. The trap is not the syntax: it is that this prefix reuses the **local name** from the `required_providers` block, and that the function only exists once the plugin is loaded, in a version that contains it.

## Target capability

Make a plugin-provided function callable: declare the provider source under an imposed local name, constrain its version to the minimum that exposes the function, call that function with the `provider::<local-name>::<function>` syntax, and demonstrate, with proof, that these functions are not part of the language.

## Where the learner starts

`challenge/work` holds a configuration that refuses to validate. No VM, no remote account, and no download for the built-in provider.

- `versions.tf`: `required_version = ???`, and a `required_providers` block declaring `hashicorp/local` with a `version = ???`. The built-in provider is absent. A comment imposes the local name to give it: **`tfcore`**, not `terraform`.
- `amont.tfvars.txt`: a supplied, non-editable fixture in `.tfvars` format. It carries `region = "eu-west-3"`, `node_count = 3`, `enable_debug = true` and `zones = ["a", "b", "c"]`.
- `locals.tf`: five locals whose value is replaced by `???`. The first reads the fixture with `file()` and must decode it; the second re-encodes the result after adding `environment = "prod"`; the third produces the expression-syntax representation of the zones list; the fourth and fifth test directory existence, one present, one absent.
- `main.tf`: a `local_file` resource writing `aval.tfvars`, whose `content` has a hole.
- `outputs.tf`: complete and non-editable. It exposes `region`, `node_count`, `aval`, `zones_expr`, `dir_present` and `dir_absent`.
- No `.terraform/`, no `.terraform.lock.hcl`, no state.

## The target state

1. The built-in provider is declared under the source `terraform.io/builtin/terraform`, with the local name `tfcore`. The three matching calls are therefore written `provider::tfcore::...`. No `provider::terraform::` can work here, for lack of a local name carrying that name.
2. `required_version` admits Terraform 1.8 and refuses anything earlier: before that version the qualified syntax does not exist.
3. The constraint on `hashicorp/local` admits 2.5.0 or newer. The `direxists` function was added in that exact version: a constraint like `~> 2.4.0` produces a successful `init` and a failing call.
4. The `node_count` output is `3` as a JSON **number**, not a string: decoding `.tfvars` content restores the types, unlike a text read.
5. The `aval` output is exactly `enable_debug = true`, `environment = "prod"`, `node_count = 3`, `region = "eu-west-3"` then `zones = ["a", "b", "c"]`, one declaration per line, in alphabetical key order and with the `=` signs aligned. This layout is not chosen by the learner: it is imposed by the encoding function, and that is precisely what proves the value comes out of it.
6. The `zones_expr` output is `["a", "b", "c"]` in Terraform expression syntax, not the compact JSON `jsonencode` would have produced.
7. `dir_present` is true for an existing directory, `dir_absent` is false for a nonexistent path.
8. `aval.tfvars` is written to disk with the same content as the `aval` output.
9. A plan re-run right after apply announces nothing.

## How it is proven

No test opens a learner `.tf` file, none parses human output.

- `terraform providers schema -json` is the architecture proof: `provider_schemas["terraform.io/builtin/terraform"].functions` contains exactly `decode_tfvars`, `encode_expr` and `encode_tfvars`, and `provider_schemas["registry.terraform.io/hashicorp/local"].functions` contains `direxists`. The functions are thus described by the plugin schema, just like its resources.
- `terraform metadata functions -json` is the proof by absence: this document lists only the language functions, about two hundred and forty. The test checks that none of the four functions used appears there. A function absent here but present in a provider schema comes from the plugin, unambiguously.
- `terraform version -json`: `provider_selections["registry.terraform.io/hashicorp/local"]` is greater than or equal to 2.5.0. A too-low constraint fails this test before apply.
- `terraform output -json`: the test checks the JSON **type** of `node_count` before its value, then compares `aval` and `zones_expr` to the expected strings, and checks that `dir_present` and `dir_absent` are respectively true and false.
- `terraform show -json`: the `content` attribute of the `mode: managed`, `local_file` resource is compared to the `aval` output, in the same document.
- `terraform plan -detailed-exitcode` returns 0 after apply.
- A `challenge/work` left as is produces neither state nor output: the qualified call fails with `Unknown provider function`, and nothing passes.

Reference: https://developer.hashicorp.com/terraform/language/functions
