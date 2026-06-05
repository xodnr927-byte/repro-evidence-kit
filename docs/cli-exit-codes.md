# CLI exit codes

All commands use the same top-level exit-code contract.

| Code | Meaning | Examples |
| --- | --- | --- |
| `0` | The command completed and the checked predicate passed. | Manifest written, manifests diffed, evidence bundle valid, signature verified. |
| `1` | The command completed and found an expected validation or verification failure. | Invalid evidence bundle, unexpected sandbox outputs, signature mismatch, unsupported signature sidecar metadata. |
| `2` | The command could not complete because of an input, parsing, filesystem, dependency, or runtime error. | Missing JSON file, malformed sidecar JSON, unreadable evidence file, schema validation without `jsonschema`. |

Use `1` as a CI policy failure and `2` as an infrastructure or invocation failure.
