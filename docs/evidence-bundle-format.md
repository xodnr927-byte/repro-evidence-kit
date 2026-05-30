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
