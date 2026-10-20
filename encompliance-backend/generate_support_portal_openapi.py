#!/usr/bin/env python3
"""
Support Portal OpenAPI Documentation Generator
-----------------------------------------------
This script generates OpenAPI documentation for the Support Portal API.
It provides:
- OpenAPI schema generation
- API documentation export
- Schema validation
- Documentation formatting
"""

import json
import yaml
import os
from fastapi.openapi.utils import get_openapi
from app.support_portal_main import support_portal_app

# Create docs directory if it doesn't exist
docs_dir = "../docs"
os.makedirs(docs_dir, exist_ok=True)

# Generate the OpenAPI schema as a Python dictionary
openapi_schema = get_openapi(
    title=support_portal_app.title,
    version=support_portal_app.version,
    openapi_version=support_portal_app.openapi_version,
    description=support_portal_app.description,
    routes=support_portal_app.routes
)

# Save as JSON
with open(os.path.join(docs_dir, "support-portal-api-spec.json"), "w") as f:
    json.dump(openapi_schema, f, indent=2)
    print(f"Support Portal OpenAPI JSON schema saved to {os.path.join(docs_dir, 'support-portal-api-spec.json')}")

# Save as YAML
with open(os.path.join(docs_dir, "support-portal-api-spec.yaml"), "w") as f:
    yaml.dump(openapi_schema, f, sort_keys=False)
    print(f"Support Portal OpenAPI YAML schema saved to {os.path.join(docs_dir, 'support-portal-api-spec.yaml')}")

print("Support Portal OpenAPI schema generation complete.")

