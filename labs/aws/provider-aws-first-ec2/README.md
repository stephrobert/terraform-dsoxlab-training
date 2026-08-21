# AWS provider: authentication, endpoints and default tags

The first failure on AWS is almost never the HCL: it is the provider
configuration. Where does it call, with which identity, and what does it
validate before it even plans?

This lab answers those three questions without an AWS account. The provider
targets a local emulator of the EC2 API, and every command runs in an
environment stripped of all `AWS_*` variables, with a `HOME` that has no `.aws`:
whatever is not written in the configuration does not exist.

## What you will be able to do

- Pin a provider to a major version, **bounded on both sides**, and check the
  version actually installed rather than the one you assume you have.
- Give the provider a static identity, switch off the three validations that
  would go and query the real AWS, and redirect a service through `endpoints`.
- Apply tags to every resource of a root through `default_tags`, and know where
  they surface — and where they never do.
- Prove an instance is running, from structured state rather than a message.

## Duration

About 40 minutes.

## Running the lab

```bash
dsoxlab run aws-provider-aws-first-ec2
```

The emulator starts on its own. Work happens in `challenge/work`.

```bash
dsoxlab check aws-provider-aws-first-ec2
```
