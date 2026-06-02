# Evidence bundle format

An evidence bundle records the minimal public facts needed to review an experiment or artifact transformation.

Required top-level fields:

- `schema_version`
- `title`
- `inputs`
- `commands`
- `outputs`

Artifacts in `inputs` and `outputs` require:

- `path`
- `sha256`

Commands require either:

- `argv`, or
- `command`

The format is intentionally small. It is not a provenance database and does not store private source material.

## Validation modes

`repro-evidence evidence validate BUNDLE` uses the lightweight validator. It is intended for base installs and checks the stable required fields without requiring optional packages.

`repro-evidence evidence validate BUNDLE --schema` uses `schemas/evidence-bundle.schema.json` through the optional `jsonschema` dependency. Use schema-backed validation in CI when maintainers want stricter contract checks such as SHA-256 hex formatting and numeric bounds.

The schema path can be overridden for local experiments with `--schema-path`, but repository CI should use the checked-in schema by default.
