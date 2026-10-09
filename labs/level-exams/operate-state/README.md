# Level B exam: operating the state

This exam closes level B of the Terraform course. It is not a lesson: on a new
scenario, it measures four skills worked in the State, Environments and
Automate modules.

| Skill | What is checked |
| --- | --- |
| `state` | another run's lock is waited for, never forced; a backup precedes every write |
| `refactor` | the incident is repaired without recreating any machine, production plan at 0 |
| `environment` | `dev` and `prod` have distinct states; a change on dev leaves prod untouched |
| `automate` | `chaine.sh` returns 0, 2 or 1, never prompts, applies the reviewed plan |

Workstation prerequisites: Terraform 1.16, libvirt (`qemu:///system`) and Incus,
as for the First infrastructures labs. The preparation downloads the cloud image
and the S3 store the first time, with verified checksums.

This exam also requires a `dsoxlab` that plays the `setup.yaml` of a
`shell` lab: that is what builds the ground (dsoxlab issue #298). With an
earlier version, `dsoxlab run` leaves an empty working directory, and
nothing says why.

The mission is in `dsoxlab challenge`.
