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
        self._schemas_cache = {}
    
    def _format_schema(self, schema: Dict[str, Any], lines: List[str], indent: str = ""):
        """
        Format schema details recursively.
        
        Args:
            schema: Schema dictionary
            lines: List to append formatted lines to
            indent: Current indentation level
        """
        # Handle $ref
        if ref := schema.get("$ref"):
            ref_name = ref.replace("#/components/schemas/", "")
            lines.append(f"{indent}Ref: {ref_name}")
            if ref_name in self._schemas_cache:
                self._format_schema(self._schemas_cache[ref_name], lines, indent + "  ")
            return
        
        # Type
        schema_type = schema.get("type", "any")
        lines.append(f"{indent}Type: {schema_type}")
        
        # Description
        if description := schema.get("description"):
            lines.append(f"{indent}Description: {description}")
        
        # Properties (for objects)
        if properties := schema.get("properties"):
            lines.append(f"{indent}Properties:")
            required_fields = schema.get("required", [])
            
            for prop_name, prop_details in properties.items():
                lines.append(f"{indent}  - {prop_name}:")
                if prop_name in required_fields:
                    lines.append(f"{indent}    Required: Yes")
                self._format_schema(prop_details, lines, indent + "    ")
        
        # Items (for arrays)
        if items := schema.get("items"):
            lines.append(f"{indent}Items:")
            self._format_schema(items, lines, indent + "  ")
        
        # Enum values
        if enum := schema.get("enum"):
            lines.append(f"{indent}Enum: {', '.join(map(str, enum))}")
        
        # Format (string formats like date-time, email, etc.)
        if format_type := schema.get("format"):
            lines.append(f"{indent}Format: {format_type}")
        
        # Example
        if self.include_examples and (example := schema.get("example")):
            lines.append(f"{indent}Example: {example}")
    
    def format(self, spec: Dict[str, Any]) -> str:
        """
        Format OpenAPI spec to LLM-friendly text.
        
        Args:
            spec: OpenAPI specification dictionary
            
        Returns:
            Formatted documentation string
        """
        lines = []
        
        # Store schemas for $ref resolution
        self._schemas_cache = spec.get("components", {}).get("schemas", {})
        
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
                            self._format_schema(schema, lines, indent="  ")
                        if self.include_examples and (example := param.get("example")):
                            lines.append(f"  Example: {example}")
                
                # Request Body
                if request_body := details.get("requestBody"):
                    lines.append("Request Body:")
                    content = request_body.get("content", {})
                    for content_type, content_details in content.items():
                        lines.append(f"  Content-Type: {content_type}")
                        if schema := content_details.get("schema"):
                            lines.append("  Schema:")
                            self._format_schema(schema, lines, indent="    ")
                
                # Responses
                responses = details.get("responses", {})
                if responses:
                    lines.append("Responses:")
                    for status_code, response_details in responses.items():
                        lines.append(f"- {status_code}:")
                        if desc := response_details.get("description"):
                            lines.append(f"  Description: {desc}")
                        content = response_details.get("content", {})
                        for content_type, content_details in content.items():
                            lines.append(f"  Content-Type: {content_type}")
                            if schema := content_details.get("schema"):
                                lines.append("  Schema:")
                                self._format_schema(schema, lines, indent="    ")
                
                lines.append("")
        
        # Schemas
        lines.append("=== Schemas ===")
        lines.append("")
        
        for schema_name, schema_details in self._schemas_cache.items():
            if self.require_description and not schema_details.get("description"):
                continue
            
            lines.append(f"Schema: {schema_name}")
            self._format_schema(schema_details, lines, indent="")
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
