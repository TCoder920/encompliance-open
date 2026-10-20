# EnCompliance Open

Childcare compliance management with regulatory documents, facility records, task workflows, and support portals.

Collaborative development is welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Local development

Use Python 3.12 and Node.js 22.21 or newer. Start from a fresh clone with no production credentials.

```sh
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r encompliance-backend/requirements.txt -r requirements-dev.txt
python scripts/create_local_env.py
cd encompliance-backend
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Local SQLite is suitable for synthetic development only; use PostgreSQL for migration validation. Background jobs are disabled unless explicitly enabled. AI, email, calendar, and payment features need sandbox adapters or credentials.

In another terminal, install and start the web interface:

```sh
cd encompliance-frontend
npm ci --ignore-scripts
npm run dev -- --host 127.0.0.1
```

## Validation

```sh
python scripts/run_tests.py
(cd encompliance-frontend && npm ci --ignore-scripts && npm run build)
```

See [VALIDATION.md](VALIDATION.md) for actual results, security findings, and unsupported integration tests.
CI uses synthetic settings and never deploys an application.

## License and source

AGPL-3.0-only. See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).
Third-party components retain their own licenses. Modified deployments must preserve applicable
license notices and source-access obligations. The source is https://github.com/TCoder920/encompliance-open.

## Security

See [SECURITY.md](SECURITY.md). Do not commit secrets, databases, logs, exports, or real user records.
