"""Create local-only development settings without overwriting an existing file."""
from pathlib import Path
import secrets
p = Path(__file__).resolve().parents[1] / "encompliance-backend" / ".env"
with p.open("x") as out:
    for key in ("SECRET_KEY", "JWT_SECRET_KEY", "SUPPORT_PORTAL_SECRET_KEY"):
        out.write(f"{key}={secrets.token_urlsafe(48)}\n")
    out.write("DATABASE_URL=sqlite:///./local.db\nOPENAI_API_KEY=test-placeholder\nSTRIPE_SECRET_KEY=test-placeholder\nSTRIPE_PUBLISHABLE_KEY=test-placeholder\nENABLE_BACKGROUND_JOBS=false\n")
print("Created local settings. No external integration credentials were configured.")
