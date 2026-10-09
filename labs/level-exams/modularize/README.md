# Level C exam: modularize

This exam closes level C of the Terraform course. It is not a lesson: it
measures, on a new scenario, two skills practiced in the Modules module.

| Skill | What is checked |
| --- | --- |
| `modularize` | three published versions; module callable with `for_each`, floor-only version constraint; `terraform test` passes, and catches injected regressions; the project in service migrates without recreating its machines |
| `reuse` | one team pinned to content (SHA-1), untouched by a moved tag; the other follows major version 1 releases; 2.0.0 requires adapting the caller |

Workstation prerequisites: Terraform 1.16, Git and libvirt (`qemu:///system`),
as for the First infrastructures labs. The setup downloads the cloud image
the first time, with its checksum verified.

This exam also requires a `dsoxlab` that plays the `setup.yaml` of a
`shell` lab: that is what builds the ground (dsoxlab issue #298). With an
earlier version, `dsoxlab run` leaves an empty working directory, and
nothing says why.

The mission is in `dsoxlab challenge`.
