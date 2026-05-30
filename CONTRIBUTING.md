# Contributing

Contributions are welcome if they keep the project general-purpose and reviewable.

Do not submit proprietary binaries, copyrighted samples, private case data, credentials, or target-specific reverse-engineering artifacts. Use synthetic fixtures generated from source code whenever possible.

Before opening a pull request, run:

```bash
python -m unittest discover -s tests
python -m repro_evidence_kit evidence validate examples/evidence-bundle.yaml
```
