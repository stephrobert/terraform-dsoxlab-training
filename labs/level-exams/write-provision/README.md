# Level A exam: write and provision

This exam closes level A of the Terraform course. It is not a lesson: it
measures, on a new scenario, six skills practiced in the Discover, Write code
and First infrastructures modules.

| Skill | What is checked |
| --- | --- |
| `workflow` | after deployment, a plan has nothing left to do |
| `resource` | every catalog machine exists, at its size, on an isolated network, and boots; providers are locked |
| `parameterize` | an invalid catalog is rejected before any plan |
| `expression` | removing a catalog entry destroys that machine only |
| `guard` | the critical machine refuses destruction and replacement; another machine is recreated before being destroyed |
| `sensitive` | the application secret reaches the machine, and appears neither in the state nor in the plan |

Workstation prerequisites: Terraform 1.16 and libvirt (`qemu:///system`), as
for the First infrastructures labs. The setup downloads the cloud image the
first time, with its checksum verified.

The mission is in `dsoxlab challenge`.
