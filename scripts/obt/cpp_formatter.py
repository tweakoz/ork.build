"""
C++ Entity Display Formatter
Provides clean formatting for C++ entities in search results
"""

import json
from typing import Dict, List, Optional, Set, Tuple, Any
from pathlib import Path

class TaggedString:
    """A string with associated formatting tags - pure data structure"""
    def __init__(self):
        self.parts = []  # List of (text, tag) tuples
    
    def add(self, text: str, tag: str = None):
        """Add text with optional tag"""
        self.parts.append((text, tag))
    
    def plain_text(self) -> str:
        """Get plain text without formatting"""
        return ''.join(text for text, tag in self.parts)

class CppFormatter:
    """Formats C++ entities for readable display"""
    
    def __init__(self, deco=None):
        self.typedef_cache = {}  # Cache for typedef/alias resolution
        self.namespace_context = ""  # Current namespace context
        self.deco = deco  # Decorator for colors (optional)
        
    def format_function_signature(self, entity) -> TaggedString:
        """
        Format a function signature for display
        
        Args:
            entity: Function entity with return_type and parameters
        
        Returns:
            TaggedString with formatted signature
        """
        result = TaggedString()
        
        # Get basic function name
        func_name = entity.name
        
        # Get return type
        return_type = getattr(entity, 'return_type', '')
        
        # Add virtual/static prefix if present
        if hasattr(entity, 'is_virtual') and entity.is_virtual:
            result.add("virtual ", None)
        elif hasattr(entity, 'is_static') and entity.is_static:
            result.add("static ", None)
            
        # Clean up and add return type
        if return_type:
            return_type = self._simplify_type(return_type, entity.namespace)
            result.add(return_type, 'return_type')
            result.add(" ", None)
            
        # Add function name
        result.add(func_name, 'function_name')
        
        # Parse and add parameters
        result.add("(", None)
        if hasattr(entity, 'parameters') and entity.parameters:
            try:
                if isinstance(entity.parameters, str):
                    params = json.loads(entity.parameters)
                else:
                    params = entity.parameters
                    
                # Calculate indent for wrapped params (align with first param)
                # This is the length of everything before the opening paren + 1
                indent_len = len(result.plain_text())
                indent = " " * indent_len
                
                # Format each parameter - first on same line, rest on new lines
                for i, param in enumerate(params):
                    if i > 0:
                        # New line with proper indent for subsequent params
                        result.add("\n" + indent, None)
                    self._add_parameter_to_result(result, param, entity.namespace)
                    # Add comma after each param except the last
                    if i < len(params) - 1:
                        result.add(",", None)
                    
            except (json.JSONDecodeError, TypeError):
                # Fallback to raw string if not valid JSON
                result.add(entity.parameters if entity.parameters else "", None)
        result.add(")", None)
        
        # Add const qualifier if present
        if hasattr(entity, 'is_const') and entity.is_const:
            result.add(" const", None)
            
        return result
    
    def _add_parameter_to_result(self, result: TaggedString, param: Dict, func_namespace: str):
        """Add a single parameter to the TaggedString result"""
        param_type = param.get('type', '')
        param_name = param.get('name', '')
        param_default = param.get('default', '')
        
        # Simplify the type
        param_type = self._simplify_type(param_type, func_namespace)
        
        # Add parameter type
        result.add(param_type, 'param_type')
        
        # Add parameter name if present
        if param_name:
            result.add(" ", None)
            result.add(param_name, 'param_name')
            
        # Add default value if present
        if param_default:
            result.add(" = ", None)
            result.add(param_default, None)
    
    def _simplify_type(self, type_str: str, current_namespace: str) -> str:
        """
        Simplify a type name based on context
        
        - Remove redundant namespace prefixes
        - Use typedef/alias names when available
        - Clean up template syntax
        """
        if not type_str:
            return type_str
            
        # First, check typedef cache
        if type_str in self.typedef_cache:
            type_str = self.typedef_cache[type_str]
            
        # Handle namespace-relative names
        if current_namespace:
            # Remove current namespace prefix if present
            ns_prefix = current_namespace + "::"
            if type_str.startswith(ns_prefix):
                type_str = type_str[len(ns_prefix):]
                
            # Also handle nested namespaces
            # e.g., if we're in ork::lev2 and type is ork::lev2::gfx::Buffer
            # we can simplify to gfx::Buffer
            parts = current_namespace.split("::")
            for i in range(len(parts), 0, -1):
                prefix = "::".join(parts[:i]) + "::"
                if type_str.startswith(prefix):
                    type_str = type_str[len(prefix):]
                    break
        
        # Clean up common patterns
        type_str = self._apply_common_simplifications(type_str)
        
        return type_str
    
    def _apply_common_simplifications(self, type_str: str) -> str:
        """Apply common type simplifications"""
        
        # Common typedef replacements (can be extended based on project conventions)
        common_typedefs = {
            # Orkid common typedefs
            "std::shared_ptr<Context>": "context_ptr_t",
            "std::shared_ptr<const Context>": "const_context_ptr_t",
            "std::shared_ptr<Buffer>": "buffer_ptr_t",
            "std::unique_ptr<Buffer>": "buffer_uptr_t",
            "std::shared_ptr<RenderContextFrameData>": "rcfd_ptr_t",
            "std::shared_ptr<FxShaderMaterial>": "fxmaterial_ptr_t",
            "std::shared_ptr<FxShaderParam>": "fxparam_ptr_t",
            "std::shared_ptr<GfxMaterial>": "material_ptr_t",
            "std::shared_ptr<Texture>": "texture_ptr_t",
            "std::shared_ptr<RenderTarget>": "rtbuffer_ptr_t",
            "std::shared_ptr<VertexBuffer>": "vtxbuf_ptr_t",
            "std::shared_ptr<IndexBuffer>": "idxbuf_ptr_t",
            "std::shared_ptr<DrawableBuffer>": "drawbuffer_ptr_t",
            # Common STL typedefs
            "std::vector<std::string>": "string_vector_t",
            "std::unordered_map<std::string, std::string>": "string_map_t",
            "std::unordered_map<std::string, int>": "string_int_map_t",
        }
        
        # Apply known typedefs
        for full_type, typedef in common_typedefs.items():
            if full_type in type_str:
                type_str = type_str.replace(full_type, typedef)
        
        # Simplify std:: types when unambiguous
        std_simplifications = {
            "std::string": "string",
            "std::vector": "vector",
            "std::shared_ptr": "shared_ptr",
            "std::unique_ptr": "unique_ptr",
            "std::map": "map",
            "std::unordered_map": "unordered_map",
        }
        
        # Only apply std:: simplifications if not ambiguous
        # (this is a conservative approach, can be made more aggressive)
        
        return type_str
    
    def set_typedef_cache(self, typedef_map: Dict[str, str]):
        """Set the typedef cache for type resolution"""
        self.typedef_cache = typedef_map
        
    def set_namespace_context(self, namespace: str):
        """Set the current namespace context for relative naming"""
        self.namespace_context = namespace

def format_entity_for_display(entity, formatter: Optional[CppFormatter] = None) -> str:
    """
    Main entry point for formatting any C++ entity for display
    """
    if formatter is None:
        formatter = CppFormatter()
        
    # Set namespace context
    if hasattr(entity, 'namespace'):
        formatter.set_namespace_context(entity.namespace)
    
    # Format based on entity type
    if entity.entity_type == "function" or \
       (hasattr(entity, 'member_type') and entity.member_type == 'method'):
        return formatter.format_function_signature(entity)
    elif entity.entity_type == "typedef":
        # Format typedef
        if hasattr(entity, 'target_type') and entity.target_type:
            return f"typedef {entity.target_type} {entity.name}"
        return entity.name
    elif entity.entity_type == "alias":
        # Format type alias
        if hasattr(entity, 'target_type') and entity.target_type:
            return f"using {entity.name} = {entity.target_type}"
        return entity.name
    else:
        # Default: just return the name
        return entity.name