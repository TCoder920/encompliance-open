# Private staging validation — 2026-10-20

**Publication gate is not satisfied. Keep this repository private.**

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

## Remaining publication blocker

The broad test suite does not establish reliable onboarding, authorization, and core record
workflows from a fresh database. Test isolation, frontend tests, and the remaining
failures need validation before this copy can be made public under the requested gate.
External-service tests and regulator-document fetching were not exercised.
Third-party regulatory documents retain their original rights; AGPLv3 applies to authorized code.
