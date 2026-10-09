# Level C exam: turn copy-pasted code into a versioned module

Two teams copy-pasted the same libvirt machine configuration, and the two
copies drifted apart. `equipe-web/` is **in service**: its two machines are
running. `equipe-data/` is not deployed yet. The address of the Git
repository where the module is published, the base image and the prefix are
in `contexte.txt`.

Indicative duration: **2 hours**. No hints are offered.

## The module contract

One machine: a 6 GiB copy-on-write disk of the base image, and a domain that
boots, with 1 vCPU, on the requested libvirt network.

| Version | Inputs | What changes |
|---|---|---|
| `v1.0.0` | `nom`, `taille`, `image_de_base`, `reseau` | `taille` is `petite` (512 MiB) or `moyenne` (768 MiB), any other value is rejected |
| `v1.1.0` | + optional `vcpu` | the number of vCPUs; without it, nothing changes for the caller |
| `v2.0.0` | `memoire_mib` **replaces** `taille` | memory is given in MiB: a v1 caller must adapt |

The module is published in the repository, each version under its tag. It is
**tested** with `terraform test`, and its tests cover the contract: the
grader will break the module (size values, rejection of an unknown size) and
expects your tests to notice.

## What is expected

Results, checked on the real state, never on the shape of your code:

- **The module is reusable as is.** It can be called with `for_each`, and it
  only constrains the **minimum** version of the libvirt provider.
- **The project in service moves to the module without recreating its
  machines.** The `equipe-web` machines keep their identity, and its plan has
  nothing left to do.
- **Two ways to consume.** `equipe-data` is **pinned to the content** of
  version 1.0.0: nothing done to the repository can change what it gets. It
  deploys its two machines, at the sizes of its copy. `equipe-web` **follows
  the published releases** of major version 1: it gets 1.1.0 without anyone
  touching its code, and will never get 2.0.0 by surprise.

## How it is graded

The report gives a verdict per skill: `modularize`, `reuse`. A failed skill
points to the lessons that teach it.

To get graded: `dsoxlab check`.
