# Security policy

## Supported versions

Until the first tagged release, security fixes are applied to the default branch. No older release line is currently supported.

## Reporting a vulnerability

Please do not publish exploitable details, credentials, farmer information, private datasets, or precise farm locations in public issues.

Use GitHub's private vulnerability reporting for this repository when enabled. If the feature is not enabled or you cannot access it, contact the maintainer privately through a contact channel published on the maintainer's GitHub profile: https://github.com/mohammerd. Include the affected commit or version, impact, reproduction steps, and any suggested mitigation. Avoid attaching real farmer or partner data.

The maintainers will acknowledge reports when reasonably possible, investigate, and coordinate a fix and disclosure. Do not assume a report is resolved until the maintainer confirms it.

## Scope

Report vulnerabilities in code, provider adapters, data processing, configuration handling, dependency usage, secrets handling, and release workflows.

For agricultural model-output safety concerns, provide a minimal synthetic or fully de-identified example, exact model/data version, language, context needed to reproduce, and plausible harm. Do not include identifiable people, farms, or confidential records.

## Handling sensitive material

Never commit API keys, access tokens, passwords, private datasets, personal information, exact farm coordinates, private reviewer details, or partner-confidential material. Use environment variables or a dedicated secrets manager for credentials.
