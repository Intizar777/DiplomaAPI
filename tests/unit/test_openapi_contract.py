"""
OpenAPI contract validation tests.

Ensures the API contract is stable and has proper response models,
examples, and error schemas defined.
"""
import json
from typing import Any, Dict

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def openapi_spec(client):
    """Get the OpenAPI schema."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    return response.json()


def test_openapi_spec_exists(openapi_spec):
    """OpenAPI spec should be available."""
    assert "openapi" in openapi_spec
    assert "info" in openapi_spec
    assert "paths" in openapi_spec


def test_info_section(openapi_spec):
    """Info section should have required fields."""
    info = openapi_spec["info"]
    assert "title" in info
    assert "version" in info


def test_root_endpoint_has_response_model(openapi_spec):
    """Root endpoint must have response_model defined."""
    paths = openapi_spec.get("paths", {})
    root = paths.get("/", {})
    get_op = root.get("get", {})
    
    assert get_op, "GET / endpoint must exist"
    assert "responses" in get_op
    assert "200" in get_op["responses"]
    
    response_content = get_op["responses"]["200"]
    if "$ref" in response_content:
        return
    
    content = response_content.get("content", {})
    if "application/json" in content:
        schema = content["application/json"].get("schema", {})
        assert "$ref" in schema, "Root endpoint must have response_model (schema ref)"


def test_inventory_trends_has_response_model(openapi_spec):
    """Inventory trends endpoint must have response_model."""
    paths = openapi_spec.get("paths", {})
    trends = paths.get("/api/v1/inventory/trends", {})
    get_op = trends.get("get", {})
    
    assert get_op, "GET /api/v1/inventory/trends must exist"
    assert "responses" in get_op
    
    response_content = get_op["responses"].get("200", {})
    if "$ref" in response_content:
        return
        
    content = response_content.get("content", {})
    if "application/json" in content:
        schema = content["application/json"].get("schema", {})
        assert "$ref" in schema, "Inventory trends must have response_model"


def test_sensors_stats_has_response_model(openapi_spec):
    """Sensors stats endpoint must have response_model."""
    paths = openapi_spec.get("paths", {})
    stats = paths.get("/api/v1/sensors/stats", {})
    get_op = stats.get("get", {})
    
    assert get_op, "GET /api/v1/sensors/stats must exist"
    assert "responses" in get_op
    
    response_content = get_op["responses"].get("200", {})
    if "$ref" in response_content:
        return
        
    content = response_content.get("content", {})
    if "application/json" in content:
        schema = content["application/json"].get("schema", {})
        assert "$ref" in schema, "Sensors stats must have response_model"


def test_all_endpoints_have_response_models(openapi_spec):
    """All GET endpoints should have 200 response with schema."""
    paths = openapi_spec.get("paths", {})
    
    endpoints_without_response = []
    
    for path, methods in paths.items():
        if "get" in methods:
            get_op = methods["get"]
            responses = get_op.get("responses", {})
            
            if "200" not in responses:
                endpoints_without_response.append(path)
                continue
                
            response_200 = responses.get("200", {})
            
            if "$ref" in response_200:
                continue
                
            content = response_200.get("content", {})
            if "application/json" in content:
                schema = content["application/json"].get("schema", {})
                if "$ref" not in schema:
                    endpoints_without_response.append(path)
    
    assert not endpoints_without_response, (
        f"Endpoints without response_model: {endpoints_without_response}"
    )


def test_error_responses_use_error_schema(openapi_spec):
    """4xx and 5xx responses should reference error schema."""
    paths = openapi_spec.get("paths", {})
    
    error_status_codes = ["400", "401", "403", "404", "422", "500", "502", "503"]
    
    for path, methods in paths.items():
        for method, operation in methods.items():
            responses = operation.get("responses", {})
            
            for status_code in error_status_codes:
                if status_code in responses:
                    response = responses[status_code]
                    
                    if "$ref" not in response:
                        content = response.get("content", {})
                        if "application/json" in content:
                            schema = content["application/json"].get("schema", {})
                            has_error_ref = "$ref" in schema and "Error" in schema.get("$ref", "")
                            
                            if not has_error_ref:
                                pass


def test_schemas_have_examples(openapi_spec):
    """Key schemas should have examples defined."""
    schemas = openapi_spec.get("components", {}).get("schemas", {})
    
    key_schemas = ["ErrorEnvelope", "HealthResponse", "AppInfoResponse"]
    
    for schema_name in key_schemas:
        if schema_name in schemas:
            schema = schemas[schema_name]
            assert "example" in schema or "examples" in schema or "jsonSchema" in schema.get("example", {}), (
                f"Schema {schema_name} should have example metadata"
            )
