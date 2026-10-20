import os, secrets, sys
from pathlib import Path
import pytest
os.chdir(Path(__file__).resolve().parents[1] / "encompliance-backend")
sys.path.insert(0, str(Path.cwd()))
for key in ("SECRET_KEY", "JWT_SECRET_KEY", "SUPPORT_PORTAL_SECRET_KEY"):
    os.environ[key] = secrets.token_urlsafe(48)
for key in ("OPENAI_API_KEY", "STRIPE_SECRET_KEY", "STRIPE_PUBLISHABLE_KEY"):
    os.environ[key] = "test-placeholder"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
raise SystemExit(pytest.main(["tests", "-q", "--maxfail=10", "-o", "addopts="] + sys.argv[1:]))
