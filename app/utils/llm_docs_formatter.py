"""
OpenAPI to LLM-friendly documentation formatter.

Converts OpenAPI specifications into a clear, consistent format
optimized for Large Language Models (LLMs) to process and understand.
"""
from typing import Any, Dict, List, Optional
from fastapi.openapi.utils import get_openapi


class OpenAPILLMFormatter:
    """Format OpenAPI spec for LLM consumption."""
    
    def __init__(
        self,
        include_examples: bool = True,
        include_deprecated: bool = False,
        require_description: bool = True,
    ):
        """
        Initialize formatter.
        
        Args:
            include_examples: Include example values in output
            include_deprecated: Include deprecated endpoints
            require_description: Only include items with descriptions
        """
        self.include_examples = include_examples
        self.include_deprecated = include_deprecated
        self.require_description = require_description
    
    def format(self, spec: Dict[str, Any]) -> str:
        """
        Format OpenAPI spec to LLM-friendly text.
        
        Args:
            spec: OpenAPI specification dictionary
            
        Returns:
            Formatted documentation string
        """
        lines = []
        
        # API Info
        info = spec.get("info", {})
        lines.append("API Documentation")
        lines.append("")
        if title := info.get("title"):
            lines.append(f"Title: {title}")
        if version := info.get("version"):
            lines.append(f"Version: {version}")
        if description := info.get("description"):
            lines.append(f"Description: {description}")
        lines.append("")
        
        # Endpoints
        lines.append("=== Endpoints ===")
        lines.append("")
        
        paths = spec.get("paths", {})
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.lower() not in ["get", "post", "put", "delete", "patch"]:
                    continue
                    
                if not self.include_deprecated and details.get("deprecated"):
                    continue
                    
                if self.require_description and not details.get("summary") and not details.get("description"):
                    continue
                
                lines.append(f"Endpoint: {path}")
                lines.append(f"Method: {method.upper()}")
                
                if summary := details.get("summary"):
                    lines.append(f"Summary: {summary}")
                
                if description := details.get("description"):
                    lines.append(f"Description: {description}")
                
                # Parameters
                parameters = details.get("parameters", [])
                if parameters:
                    lines.append("Parameters:")
                    for param in parameters:
                        if self.require_description and not param.get("description"):
                            continue
                        lines.append(f"- {param.get('name')} ({param.get('in')}):")
                        if desc := param.get("description"):
                            lines.append(f"  Description: {desc}")
                        lines.append(f"  Required: {'Yes' if param.get('required') else 'No'}")
                        if schema := param.get("schema"):
                            if param_type := schema.get("type"):
                                lines.append(f"  Type: {param_type}")
                        if self.include_examples and (example := param.get("example")):
                            lines.append(f"  Example: {example}")
                
                # Request Body
                if request_body := details.get("requestBody"):
                    lines.append("Request Body:")
                    content = request_body.get("content", {})
                    for content_type, content_details in content.items():
                        lines.append(f"  Content-Type: {content_type}")
                        if schema := content_details.get("schema"):
                            lines.append(f"  Schema: {schema.get('$ref', 'inline')}")
                
                # Responses
                responses = details.get("responses", {})
                if responses:
                    lines.append("Responses:")
                    for status_code, response_details in responses.items():
                        lines.append(f"- {status_code}:")
                        if desc := response_details.get("description"):
                            lines.append(f"  Description: {desc}")
                
                lines.append("")
        
        # Schemas
        lines.append("=== Schemas ===")
        lines.append("")
        
        components = spec.get("components", {})
        schemas = components.get("schemas", {})
        
        for schema_name, schema_details in schemas.items():
            if self.require_description and not schema_details.get("description"):
                continue
            
            lines.append(f"Schema: {schema_name}")
            lines.append(f"Type: {schema_details.get('type', 'object')}")
            
            if description := schema_details.get("description"):
                lines.append(f"Description: {description}")
            
            # Properties
            properties = schema_details.get("properties", {})
            if properties:
                lines.append("Properties:")
                required_fields = schema_details.get("required", [])
                
                for prop_name, prop_details in properties.items():
                    if self.require_description and not prop_details.get("description"):
                        continue
                    
                    lines.append(f"- {prop_name}:")
                    lines.append(f"  Type: {prop_details.get('type', 'any')}")
                    
                    if description := prop_details.get("description"):
                        lines.append(f"  Description: {description}")
                    
                    lines.append(f"  Required: {'Yes' if prop_name in required_fields else 'No'}")
                    
                    if self.include_examples and (example := prop_details.get("example")):
                        lines.append(f"  Example: {example}")
                    
                    if enum := prop_details.get("enum"):
                        lines.append(f"  Enum: {', '.join(map(str, enum))}")
            
            lines.append("")
        
        return "\n".join(lines)


def get_llm_docs(app, **formatter_options) -> str:
    """
    Get LLM-friendly documentation from FastAPI app.
    
    Args:
        app: FastAPI application instance
        **formatter_options: Options for OpenAPILLMFormatter
        
    Returns:
        Formatted documentation string
    """
    spec = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    formatter = OpenAPILLMFormatter(**formatter_options)
    return formatter.format(spec)
