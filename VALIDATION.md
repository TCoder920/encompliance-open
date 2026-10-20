# Experimental public release validation — 2026-10-20

**Published as an unfinished prototype with the owner’s explicit acceptance of broken workflows on 2026-10-20.** Security and licensing checks remain required; application completeness is not a publication gate.

- Source selection: approved development branch; clean source copy with fresh history.
- Python install: passed; vulnerable document/multipart/web-server dependencies updated.
- Frontend builds: both interfaces compile; the support build previously erased the user build. Separate output directories repair that defect.
- API lifespan startup and `/health`: passed.
- Synthetic authentication regression check: JSON and form login passed; inactive accounts
  rejected through JSON, form, and legacy email endpoints.
- Broad backend run: **123 passed, 21 failed, 75 setup errors**, interrupted after 278 seconds
  because a reminder-scheduler test did not terminate. This is an incomplete run.
- Failures included duplicate/shared test-data constraints, outdated authentication expectations,
  and age-assignment tests. The initial frontend test setup referenced missing files.
- Frontend tests after harness repair: **16 passed, 5 failed; 9 suites failed**, including missing accessibility helpers and ESM configuration errors.
- Built frontend loopback HTTP startup: passed.
- GitHub CI: secret scanning passed; core backend job stopped after 10 failures (10 tests passed).
- Gitleaks: zero findings in the sanitized export.

## Scope and safeguards

Gitleaks 8.30.1 was installed from the official release and its SHA-256 checked.
Source history and the sanitized export were scanned. Fresh Git history excludes old secrets.
Private exports, logs, local databases, deployment evidence, and generated artifacts are excluded.
Bandit found no high-severity findings in the audited application Python directories.
This is a migration audit, not a claim that the entire upstream framework is vulnerability-free.
No production services, customer data, deployments, banking transactions, or brokerage orders were used.

## Resolved security issues

Removed stored development exports, deleted-user records, token-bearing logs, and test uploads.
Required locally generated signing/encryption secrets and removed default shared secrets.
Removed authentication-header/token logging. Legacy login handlers now delegate to the same
active-account and OTP policy as the current login route; previously they bypassed these checks.
Background integration jobs are disabled by default for local development.
Training HTML is rendered in a sandboxed iframe without same-origin access.

## Known defects and rebuilding scope

The broad test suite does not establish reliable onboarding, authorization, and core record
workflows from a fresh database. Test isolation, frontend tests, and the remaining
failures require substantial rework before this application can be considered useful or reliable.
External-service tests and regulator-document fetching were not exercised.
Third-party regulatory documents retain their original rights; AGPLv3 applies to authorized code.

## Prototype CI policy

Required `test` checks install dependencies, build both web interfaces, start the API, and exercise synthetic login/inactive-account safeguards. Required `secrets` checks scan the full fresh history with Gitleaks. The separate `legacy-tests` job retains the broad backend suite and may fail; its result remains visible and is not a required merge check. No failing tests were converted into passing assertions or removed.

## Remaining dependency advisories and use restrictions

The frontend audit reports **35 high and 8 moderate findings**, primarily through legacy development/test tooling: braces, extract-zip/Cypress, qs, sprintf-js/Jest, and uuid. A compatible `npm audit fix --ignore-scripts` did not resolve these chains. Broad major-version toolchain migrations are deferred to the rebuild. Do not run optional Cypress/download/archive workflows, process untrusted archives/glob patterns through affected tools, or provide credentials to CI. The documented install disables lifecycle scripts.

Python retains python-jose 3.5.0 (`PYSEC-2026-4298`) and ecdsa 0.19.2 (`PYSEC-2026-1325`), with no fixes listed in the audit. Authentication constrains the accepted algorithm; vulnerable pure-Python ECDSA signing is not used. These are disclosed residual advisories, not a clean dependency audit.

Use only synthetic local data on loopback. The incomplete application has not established safe operation with real records, public hosting, cloud integrations, or regulatory decisions. No deployment is provided by this release.
