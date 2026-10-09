# Level A exam: write and provision a demo environment

A product team needs a demo environment on the team's libvirt host: an
isolated network and a few machines, described by a **catalog**. Nothing
exists yet: you write the Terraform code, at the root of your working
directory, and you deploy it.

Indicative duration: **45 minutes**. No hints are offered.

## What you receive

- `entrees.auto.tfvars.json`: the prefix of everything you create, the
  network range, the base cloud image and the path of the operations team's
  public key;
- `catalogue.auto.tfvars.json`: the catalog, under the `machines` variable.
  Each machine has a `role` (`front`, `app` or `db`), a `taille` (size:
  `petite` is 512 MiB, `moyenne` is 768 MiB) and a `generation`;
- `acces/`: the operations team's key.

Do not modify these files: the grader will give you other catalogs and
observe what your code does with them.

## What is expected

Results, checked on the real state of the machines and the plans, never on
the shape of your code:

- **The environment exists.** An **isolated** network whose name starts with
  the prefix, and, for each catalog entry, a machine whose name starts with
  `<prefix>-<name>`, at the requested size, connected to that network, that
  really **boots**. Each machine accepts the `exploit` account with the key
  from `acces/`, with passwordless sudo.
- **The configuration converges.** After your deployment, a new plan has
  nothing left to do.
- **The catalog drives everything.** An invalid catalog (unknown size or role,
  missing field) is **rejected before any plan**. Removing an entry from the
  catalog destroys **that machine only**, without touching the others.
- **A new generation replaces the machine.** When an entry's `generation`
  changes, its machine is replaced.
- **The `db` machine is critical.** No plan may destroy or replace it. Any
  other machine that is replaced is **created before** the old one is
  destroyed.
- **The application secret reaches its destination, and nowhere else.**
  Each `app` machine receives a secret of at least 16 characters in
  `/etc/app/secret`, owned by root, mode 600. That secret appears **neither in
  the state nor in any plan**.
- **Provider versions are locked**, and the lock is kept in the working
  directory.

## How it is graded

The report gives a verdict per skill: `workflow`, `resource`, `parameterize`,
`expression`, `guard`, `sensitive`. A failed skill points to the lessons that
teach it.

To get graded: `dsoxlab check`.
