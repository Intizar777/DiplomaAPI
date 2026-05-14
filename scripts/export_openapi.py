#!/usr/bin/env python3
"""
OpenAPI contract export and validation script.

Usage:
    python scripts/export_openapi.py export    - Export OpenAPI JSON to file
    python scripts/export_openapi.py check     - Validate contract has required elements
    python scripts/export_openapi.py diff      - Compare current spec with baseline
"""
import argparse
import json
import sys
from pathlib import Path

import httpx


def get_openapi_spec(base_url: str = "http://localhost:8000") -> dict:
    """Fetch OpenAPI spec from running server."""
    response = httpx.get(f"{base_url}/openapi.json", timeout=30)
    response.raise_for_status()
    return response.json()


def export_spec(output_path: Path, base_url: str):
    """Export OpenAPI spec to file."""
    spec = get_openapi_spec(base_url)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(spec, f, indent=2)
    
    print(f"✓ Exported OpenAPI spec to {output_path}")
    return spec


def check_contract(spec: dict) -> bool:
    """Validate contract has required elements."""
    errors = []
    
    if "openapi" not in spec:
        errors.append("Missing 'openapi' version")
    
    if "info" not in spec:
        errors.append("Missing 'info' section")
    else:
        info = spec["info"]
        if "title" not in info:
            errors.append("Missing info.title")
        if "version" not in info:
            errors.append("Missing info.version")
    
    if "paths" not in spec:
        errors.append("Missing 'paths' section")
    else:
        paths = spec["paths"]
        
        if "/" not in paths:
            errors.append("Missing root endpoint '/'")
        
        if "/health" not in paths:
            errors.append("Missing health endpoint '/health'")
        
        for path, methods in paths.items():
            for method, operation in methods.items():
                responses = operation.get("responses", {})
                
                if "200" not in responses:
                    errors.append(f"{method.upper()} {path} missing 200 response")
                    continue
                
                response_200 = responses["200"]
                if "$ref" in response_200:
                    continue
                    
                content = response_200.get("content", {})
                if "application/json" in content:
                    schema = content["application/json"].get("schema", {})
                    if "$ref" not in schema:
                        errors.append(f"{method.upper()} {path} missing response_model")
    
    if errors:
        print("✗ Contract validation failed:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print("✓ Contract validation passed")
    return True


def diff_specs(baseline_path: Path, current_spec: dict) -> bool:
    """Compare current spec with baseline."""
    if not baseline_path.exists():
        print(f"✗ Baseline file not found: {baseline_path}")
        return False
    
    with open(baseline_path) as f:
        baseline = json.load(f)
    
    breaking_changes = []
    
    baseline_paths = set(baseline.get("paths", {}).keys())
    current_paths = set(current_spec.get("paths", {}).keys())
    removed_paths = baseline_paths - current_paths
    
    if removed_paths:
        breaking_changes.append(f"Removed paths: {removed_paths}")
    
    for path in baseline_paths & current_paths:
        baseline_methods = set(baseline["paths"][path].keys())
        current_methods = set(current_spec["paths"][path].keys())
        removed_methods = baseline_methods - current_methods
        
        if removed_methods:
            breaking_changes.append(f"Removed methods on {path}: {removed_methods}")
    
    if breaking_changes:
        print("✗ Breaking changes detected:")
        for change in breaking_changes:
            print(f"  - {change}")
        return False
    
    print("✓ No breaking changes detected")
    return True


def main():
    parser = argparse.ArgumentParser(description="OpenAPI contract tools")
    parser.add_argument("command", choices=["export", "check", "diff"],
                        help="Command to run")
    parser.add_argument("--output", "-o", type=Path, 
                        default=Path("docs/openapi.json"),
                        help="Output path for export")
    parser.add_argument("--baseline", "-b", type=Path,
                        default=Path("docs/openapi_baseline.json"),
                        help="Baseline file for diff")
    parser.add_argument("--base-url", default="http://localhost:8000",
                        help="Base URL for running server")
    
    args = parser.parse_args()
    
    if args.command == "export":
        export_spec(args.output, args.base_url)
    elif args.command == "check":
        spec = get_openapi_spec(args.base_url)
        success = check_contract(spec)
        sys.exit(0 if success else 1)
    elif args.command == "diff":
        current = get_openapi_spec(args.base_url)
        success = diff_specs(args.baseline, current)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
