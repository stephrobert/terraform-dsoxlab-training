# Changelog

**Language:** [English](./CHANGELOG.md) · [Français](./CHANGELOG.fr.md)

All notable changes to this project are recorded in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/).

This repository is a **content catalog**, not a library: it is not versioned and
publishes no releases. The entries below date changes to the catalog, and the
unit that matters is the lab.

## [Unreleased]

### Added

- **The `hcp-terraform` section is complete**: seven labs playable with no
  account, plus an eighth, optional one that crosses the boundary. Each was
  proven in both directions and deliberately degraded to check that it
  discriminates.
  - `hcp-terraform-overview` plays a run in two steps with saved plans, which
    reproduces a remote run's plan/apply split locally. Three measured refusals
    give it its meaning: a replayed plan is stale, a variable cannot be changed
    at apply time, and a plan with no changes is not applyable.
  - `hcp-workspaces` establishes that `terraform validate` answers "Success" on
    two faults that make `init` fail.
  - `remote-runs` has you analyse the JSON stream of a run that **failed
    midway**: the only summary the stream then carries is the plan's, which
    announces more than actually happened.
  - `shared-credentials` measures that `sensitive` protects the display and
    leaves the value in clear text in the state.
  - `projects-teams` has you write the permission rule, which keeps the most
    permissive level rather than the most specific one.
  - `premier-run-distant` provisions HCP Terraform with the `tfe` provider, then
    has a real remote run execute. It is the only lab requiring an account;
    without a token its tests skip instead of failing.
- **A guide to the HCP Terraform token**, `docs/hcp-token.md` and its
  translation: creating the token, the three possible locations with their
  measured priority, and the mix-up with the GitHub App OAuth token, which sits
  on the same page and yields a `401` indistinguishable from a revocation.
- **`scripts/diagnostic-jeton-hcp.py`**, which says which location wins, flags
  ignored tokens, checks the token's shape before calling the API, and never
  prints a token's value.
- **`tests/test_aucun_jeton_versionne.py`**, which rejects an API token, an AWS
  key or a filled-in `credentials` block entering the repository. It reads file
  contents, where a `.gitignore` only protects the paths someone thought to
  name.
- **Repository governance**: `LICENSE` (CC BY 4.0), `CONTRIBUTING`,
  `CODE_OF_CONDUCT`, `SECURITY` and this changelog, in English and French.

### Changed

- **Local steering files are excluded by the repository itself.** `.claude/` and
  `todo/` were only ignored by the author's machine-wide `.gitignore`: on
  another machine, a `git add -A` would have published them.

## 2026-09-20

### Added

- The first labs of the `getting-started` section, written one by one from
  scenarios that had no tests.
- Pre-commit hooks, green across the whole repository: hard stop on secrets and
  private keys, and a check that solutions stay encrypted.
- An issue form, so that `dsoxlab support --issue` arrives pre-filled.

### Fixed

- `runtime.fixtures`, forgotten twice: without that list the work directory
  stays empty and the lab measures nothing.
- A false negative caught by the full cycle, on `terraform-vs-opentofu`.

## 2026-08-21

### Added

- First commit: 87 labs, their scenarios and their order in `meta.yml`.
