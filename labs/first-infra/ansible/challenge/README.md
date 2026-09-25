# 🎯 Challenge: produce an Ansible inventory from the state

## Starting point

`challenge/work` holds an incomplete configuration. **No cloud, no hypervisor**:
the fleet is simulated by resources whose attributes are only known **after
creation**, like an address allocated by a scheduler.

That is deliberate: a guessable value would prove nothing.

## ✅ Objective

1. **The fleet type**, as an explicit structure. Never `any`.
2. **The addresses**, computed from the base CIDR and each server index, **by an
   HCL function**.
3. **The resource** from the `local` provider writing `inventaire.json`,
   serialised **by a function**.
4. **The output**, exposing the inventory as a **structure**.

## 🧭 Four choices separating a reliable bridge from one that merely stands

**An explicit type refuses at plan time.** `map(object({ role = string, index =
number }))` rejects an entry without `index` **before any provider call**. With
`any`, the same mistake passes the plan and breaks further on, with a message
naming neither the variable nor the offending entry.

**An address is computed.** `cidrhost(var.cidr_de_base, serveur.index)` follows
the network. Copied by hand, it is right today and wrong at the first change,
**with nothing to flag it**.

**`jsonencode` rather than concatenation.** A hand-built string produces
*almost* valid JSON: one comma too many, a quote forgotten in a name, and
Ansible returns a parsing error that does not say where.

**A managed file disappears with the fleet.** An inventory surviving the
destruction points at machines that no longer exist. Ansible will connect, fail,
and the message will talk about the network.

## 🔍 Validation

```bash
dsoxlab check first-infra-ansible
```

Seven tests. Addresses are not compared to a list written in the test: they are
**recomputed** from the CIDR, two independent computations being worth more than
a constant. And the file must carry the identifiers **drawn at creation**:
addresses can be guessed, those cannot.
