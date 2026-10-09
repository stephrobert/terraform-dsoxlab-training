# Releasing terraform-dsoxlab-training

**Language:** [English](./RELEASING.md) · [Français](./RELEASING.fr.md)

This repository ships **lab content**, not a Python package. A release publishes
a **`tar.gz` bundle** of the Terraform lab catalogue as GitHub Release assets: no PyPI, no
wheel, no external artifact registry.

## What a release contains

`release.yml` builds `terraform-dsoxlab-training-<version>.tar.gz` with:

- `labs/`, `meta.yml`, `meta.fr.yml`, `conftest.py`, `curriculums.yml`
- the tooling that replays the catalogue: `scripts/`, `tests/`, `docs/`
- `validation-labs.json`, the verdict of the two-way validation campaign
- the governance documents (`README`, `LICENSE`, `CONTRIBUTING`,
  `CODE_OF_CONDUCT`, `SECURITY`, `CHANGELOG`), in both languages

It **excludes** local steering (`.claude/`, `CLAUDE.md`), generated files
(`.venv/`, caches), the learner's scratch space (`challenge/work/`), and
everything that carries a secret — the vault password and any private key.

Four assets are attached to each release:

| Asset | What it is for |
| --- | --- |
| `terraform-dsoxlab-training-<version>.tar.gz` | the catalogue itself |
| `….tar.gz.sha256` | integrity, checkable offline |
| `….tar.gz.cosign.bundle` | keyless Cosign signature |
| `provenance.intoto.jsonl` | SLSA provenance, the asset OpenSSF Scorecard's Signed-Releases check looks for |

## Why three jobs, and not one

The workflow is split into **build**, **attest**, **publish**, and that split is
the only thing separating SLSA Build Level 2 from Level 3.

GitHub's documentation puts it in two sentences: "Artifact attestations by
itself provides SLSA v1.0 Build Level 2", and "Reusable workflows can provide
isolation between the build process and the calling workflow, to meet SLSA v1.0
Build Level 3". As long as the job that builds the archive is also the one that
signs its provenance, nothing technically stops the build process from
producing provenance that lies. Level 3 requires the signing to happen out of
its reach.

Hence `.github/workflows/attester.yml`, called as a reusable workflow:

- it is the **only workflow in the repository** granted `attestations: write`;
- it receives **a name and a digest**, never the archive nor the repository: it
  performs no `checkout`;
- the publish job can write the release but **cannot attest**, lacking that
  permission;
- the archive is re-checked against its digest **before** publication, so that
  an artifact altered between two jobs is not published with provenance that
  does not describe it.

## Cutting a release

1. Move the `[Unreleased]` entries under a new version in `CHANGELOG.md` **and**
   `CHANGELOG.fr.md`, and add the two link definitions.
2. Check the catalogue locally: `dsoxlab validate-structure`, `pytest tests/ -q`,
   and `python3 scripts/valider-labs.py --check` (no lab must be ROUGE).
3. Open a pull request for that change, and let the CI go green.
4. Once merged, tag the **merged commit** and push the tag, which triggers
   `release.yml`:

   ```bash
   git switch main && git pull
   git tag -a vX.Y.Z -m "terraform-dsoxlab-training X.Y.Z"
   git push origin vX.Y.Z
   ```

5. Watch the run. The three jobs must all be green: a failed `provenance` job
   leaves the release unpublished rather than publishing it unattested.

## Verifying a release

Integrity and contents:

```bash
sha256sum -c terraform-dsoxlab-training-<version>.tar.gz.sha256
tar tzf terraform-dsoxlab-training-<version>.tar.gz | head
```

Build provenance. Proves the archive really was produced by this repository's
workflow, and not rebuilt by someone else:

```bash
gh attestation verify terraform-dsoxlab-training-<version>.tar.gz --repo stephrobert/terraform-dsoxlab-training
```

**The check that establishes Build Level 3** names the signing workflow. It
fails if the provenance was produced anywhere other than the isolated attester
workflow, and it is the one to run on the first release to confirm the chain
holds:

```bash
gh attestation verify terraform-dsoxlab-training-<version>.tar.gz \
  --repo stephrobert/terraform-dsoxlab-training \
  --signer-workflow stephrobert/terraform-dsoxlab-training/.github/workflows/attester.yml
```

Keyless Cosign signature. **Both** certificate flags are mandatory: without
them, `cosign verify-blob` accepts any identity, which empties the verification
of its meaning.

```bash
cosign verify-blob \
  --bundle terraform-dsoxlab-training-<version>.tar.gz.cosign.bundle \
  --certificate-identity-regexp "https://github.com/stephrobert/terraform-dsoxlab-training/.github/workflows/release.yml@.*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  terraform-dsoxlab-training-<version>.tar.gz
```

> **Cosign version trap.** The CI installs **Cosign 3.x**, which writes a new
> bundle format. A local **Cosign 2.x** answers `no signatures found` on a
> perfectly signed archive: the release is not broken, the local tool cannot
> read the format. Check `cosign version` and align it before concluding
> anything.

> Commits and tags are created by a human, never by an assistant.
