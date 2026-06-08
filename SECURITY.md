# Security policy

`repro-evidence-kit` is security-adjacent tooling for reviewing generated artifacts and evidence metadata. Its security policy is intentionally conservative: do not publish private samples, credentials, forensic data, or sensitive logs in public project spaces.

## Supported versions

The current early release line is `0.4.x`. Security fixes are handled on a best-effort basis for the current release line. Older pre-`0.4.x` releases should be treated as unsupported unless a maintainer explicitly says otherwise.

## Reporting a vulnerability

Use a GitHub private security advisory when possible. If that is not available, contact the maintainer through GitHub without including sensitive artifacts in the initial public message.

Do not attach or paste any of the following in public issues, pull requests, comments, or logs:

- private binaries,
- credentials, tokens, API keys, signing keys, or other secrets,
- forensic datasets,
- sensitive logs,
- client or user data,
- proprietary samples,
- target-specific reverse-engineering artifacts,
- evidence bundles that disclose private paths, private inputs, or private outputs.

Use minimized synthetic reproductions whenever possible.

## Security-relevant bug classes

Please report issues that could cause or hide sensitive disclosure, including:

- unsafe path handling or path disclosure in manifests, diffs, evidence bundles, or reports,
- hash or evidence-bundle mishandling that causes misleading review output,
- generated reports that accidentally include private data,
- signature-sidecar validation mistakes,
- schema validation behavior that accepts unsafe or misleading metadata,
- packaging or release workflow problems that could affect published artifacts,
- CI/reporting adapters that misrepresent failed verification as success.

## Signed sidecar limitations

The signed-bundle sidecar workflow is a local HMAC tamper-detection prototype for exact evidence-bundle bytes.

It does not provide:

- signer identity,
- a public trust chain,
- certificate validation,
- command-execution proof,
- artifact semantic proof,
- proof that generated outputs are safe or correct.

Treat sidecars as local review aids, not public authenticity guarantees.

## Handling fixes

Security fixes should preserve the repository's boundaries:

- examples must remain synthetic or clearly redistributable,
- private data must not be committed as a reproduction,
- trust and security claims must remain limited to documented behavior,
- release and publishing changes require human maintainer review.

Maintainer response is best effort. If a report requires private context to reproduce, provide the smallest safe synthetic reproduction or describe the issue without disclosing the sensitive material.
