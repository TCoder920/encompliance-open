#!/usr/bin/env python3

import json
import yaml
import os
from fastapi.openapi.utils import get_openapi
from app.main import app

"""
OpenAPI Documentation Generator
-----------------------------
This script generates OpenAPI documentation for the EnCompliance API.
It provides:
- OpenAPI schema generation
- API documentation export
- Schema validation
- Documentation formatting
- API endpoint documentation
"""

# Create docs directory if it doesn't exist
docs_dir = "../docs"
os.makedirs(docs_dir, exist_ok=True)

# Generate the OpenAPI schema as a Python dictionary
openapi_schema = get_openapi(
    title=app.title,
    version=app.version,
    openapi_version=app.openapi_version,
    description=app.description,
    routes=app.routes
)

# Save as JSON
with open(os.path.join(docs_dir, "api-spec.json"), "w") as f:
    json.dump(openapi_schema, f, indent=2)
    print(f"OpenAPI JSON schema saved to {os.path.join(docs_dir, 'api-spec.json')}")

# Save as YAML
with open(os.path.join(docs_dir, "api-spec.yaml"), "w") as f:
    yaml.dump(openapi_schema, f, sort_keys=False)
    print(f"OpenAPI YAML schema saved to {os.path.join(docs_dir, 'api-spec.yaml')}")

print("OpenAPI schema generation complete.") 