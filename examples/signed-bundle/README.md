# Signed bundle example

This example demonstrates local tamper detection for exact evidence-bundle bytes.
It uses only synthetic data and writes temporary key/signature files outside git.

```bash
printf 'synthetic local test key only\n' > /tmp/repro-evidence-local.key
repro-evidence evidence sign examples/evidence-bundle.yaml \
  --key /tmp/repro-evidence-local.key \
  --key-hint local-synthetic \
  -o /tmp/evidence-bundle.yaml.sig.json
repro-evidence evidence verify-signature examples/evidence-bundle.yaml \
  --signature /tmp/evidence-bundle.yaml.sig.json \
  --key /tmp/repro-evidence-local.key \
  --format text
```

A passing signature proves only that the exact bundle bytes match the local key
material used by the verifier. It does not prove command execution, output
semantics, signer identity, or a public trust chain.
