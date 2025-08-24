"""
Entity data models for normalized C++ database
Clean room implementation - no legacy code dependencies
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

class EntityType(Enum):
    """Types of C++ entities we track"""
    CLASS = "class"
    STRUCT = "struct" 
    FUNCTION = "function"
    ENUM = "enum"
    TYPEDEF = "typedef"
    NAMESPACE = "namespace"
    VARIABLE = "variable"
    UNION = "union"

class LocationType(Enum):
    """Types of entity locations in code"""
    DECLARATION = "declaration"
    DEFINITION = "definition"
    FORWARD_DECLARATION = "forward_declaration"

class AccessLevel(Enum):
    """Access levels for class members"""
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"

class MemberType(Enum):
    """Types of class/struct members"""
    FIELD = "field"
    METHOD = "method"
    CONSTRUCTOR = "constructor"
    DESTRUCTOR = "destructor"
    NESTED_TYPE = "nested_type"
    ENUM_VALUE = "enum_value"
    TYPEDEF = "typedef"
    FRIEND = "friend"

@dataclass
class Location:
    """Where an entity appears in code"""
    file_path: str
    line_number: int
    column_number: int = 0
    location_type: LocationType = LocationType.DEFINITION
    has_body: bool = False
    context: Optional[str] = None  # Code snippet around the location
    
    def __eq__(self, other):
        """Locations are equal if file and line match"""
        if not isinstance(other, Location):
            return False
        return (self.file_path == other.file_path and 
                self.line_number == other.line_number)
    
    def __hash__(self):
        """Hash based on file and line"""
        return hash((self.file_path, self.line_number))

@dataclass
class Member:
    """Class/struct member (field, method, etc.)"""
    name: str
    member_type: MemberType
    data_type: Optional[str] = None
    access_level: AccessLevel = AccessLevel.PRIVATE
    is_static: bool = False
    is_virtual: bool = False
    is_const: bool = False
    is_constexpr: bool = False  # For constexpr keyword  
    is_mutable: bool = False  # For mutable keyword
    is_inline: bool = False
    is_explicit: bool = False  # For constructors
    is_override: bool = False  # For virtual methods
    is_final: bool = False     # For virtual methods
    is_deleted: bool = False   # For deleted functions
    is_default: bool = False   # For defaulted functions
    is_pure_virtual: bool = False  # For pure virtual (= 0)
    is_noexcept: bool = False      # For noexcept methods
    array_dimensions: Optional[str] = None  # For arrays: "[10][20]"
    pointer_depth: int = 0          # Number of * indirections
    line_number: int = 0
    signature: Optional[str] = None  # Full signature for methods
    value: Optional[str] = None      # For enum values or default values
    implementation_locations: List['Location'] = field(default_factory=list)  # Member function implementations, static member instantiations, explicit template instantiations
    
    # UNIFIED TYPE SYSTEM FIELDS
    base_type_id: Optional[int] = None  # Reference to canonical_types.id
    is_reference: bool = False          # T& reference type
    is_rvalue_reference: bool = False   # T&& rvalue reference  
    is_volatile: bool = False           # volatile qualifier
    return_const: bool = False          # const return type (for methods)
    
    def __eq__(self, other):
        """Members are equal if they represent the same entity"""
        if not isinstance(other, Member):
            return False
        
        # For methods/constructors/destructors: name + signature must match
        if self.member_type in [MemberType.METHOD, MemberType.CONSTRUCTOR, MemberType.DESTRUCTOR]:
            return (self.name == other.name and 
                   self.member_type == other.member_type and
                   self.signature == other.signature)
        
        # For fields: name + type + array dimensions must match
        elif self.member_type == MemberType.FIELD:
            return (self.name == other.name and 
                   self.member_type == other.member_type and
                   self.data_type == other.data_type and
                   self.array_dimensions == other.array_dimensions)
        
        # For others: name + type
        else:
            return self.name == other.name and self.member_type == other.member_type
    
    def __hash__(self):
        """Hash based on name, type, and signature for methods"""
        if self.member_type == MemberType.METHOD:
            return hash((self.name, self.member_type, self.signature))
        else:
            return hash((self.name, self.member_type))
    
    def get_type_modifiers(self) -> Dict[str, Any]:
        """Get type modifiers for unified type composition"""
        return {
            'is_const': self.is_const if not self.return_const else False,  # Member const vs return const
            'return_const': self.return_const,
            'is_volatile': self.is_volatile,
            'is_constexpr': self.is_constexpr,
            'is_mutable': self.is_mutable,
            'pointer_depth': self.pointer_depth,
            'is_reference': self.is_reference,
            'is_rvalue_reference': self.is_rvalue_reference,
            'array_dimensions': self.array_dimensions.strip('[]').split('][') if self.array_dimensions else []
        }
    
    def add_implementation_location(self, location: 'Location') -> bool:
        """
        Add an implementation location for this member.
        For methods: function body implementations
        For static members: instantiation locations
        For templates: explicit instantiation locations
        Returns True if location was added.
        """
        # Check if we already have this location
        for existing in self.implementation_locations:
            if existing == location:  # Uses Location.__eq__
                return False  # Already have this location
        
        # Add new location
        self.implementation_locations.append(location)
        return True

@dataclass
class Parameter:
    """Function/method parameter"""
    name: Optional[str]  # Can be unnamed
    param_type: str
    default_value: Optional[str] = None
    is_const: bool = False
    is_reference: bool = False
    is_pointer: bool = False
    is_rvalue_ref: bool = False

@dataclass
class Entity:
    """Canonical entity representation"""
    canonical_name: str  # Full qualified name, e.g., "ork::util::Context"
    short_name: str      # Just the name, e.g., "Context"
    entity_type: EntityType
    namespace: Optional[str] = None
    
    # Template information
    is_template: bool = False
    template_params: Optional[str] = None  # e.g., "<typename T, int N>"
    is_template_specialization: bool = False
    specialized_from: Optional[str] = None  # Parent template if specialization
    
    # Storage
    locations: List[Location] = field(default_factory=list)
    members: List[Member] = field(default_factory=list)
    
    # Class/struct specific
    base_classes: List[str] = field(default_factory=list)
    is_abstract: bool = False
    is_final: bool = False
    is_pod: bool = False  # Plain old data
    
    # Function specific
    return_type: Optional[str] = None
    parameters: List[Parameter] = field(default_factory=list)
    is_method: bool = False
    is_virtual: bool = False
    is_static: bool = False
    is_const: bool = False
    is_inline: bool = False
    is_constexpr: bool = False
    is_noexcept: bool = False
    is_deleted: bool = False
    is_default: bool = False
    is_override: bool = False
    is_final_method: bool = False
    
    # Enum specific
    underlying_type: Optional[str] = None  # e.g., "uint32_t" for enum class
    is_enum_class: bool = False
    
    # Typedef/alias specific
    aliased_type: Optional[str] = None
    is_using_alias: bool = False  # using vs typedef
    
    def add_location(self, location: Location) -> bool:
        """
        Add a location, avoiding duplicates and preferring definitions.
        Returns True if location was added or updated.
        """
        # Check if we already have this location
        for i, existing in enumerate(self.locations):
            if existing == location:  # Uses Location.__eq__
                # Update if new location has more information
                if location.location_type == LocationType.DEFINITION and \
                   existing.location_type != LocationType.DEFINITION:
                    # Replace with definition
                    self.locations[i] = location
                    return True
                elif location.has_body and not existing.has_body:
                    # Update body flag
                    existing.has_body = True
                    return True
                return False  # Already have this location
        
        # New location
        self.locations.append(location)
        return True
    
    def add_member(self, member: Member) -> bool:
        """
        Add a member, avoiding duplicates.
        Returns True if member was added.
        """
        if member not in self.members:  # Uses Member.__eq__
            self.members.append(member)
            return True
        return False
    
    def get_primary_location(self) -> Optional[Location]:
        """Get the primary (definition) location if available"""
        # Prefer definitions over declarations
        for loc in self.locations:
            if loc.location_type == LocationType.DEFINITION:
                return loc
        # Fall back to first declaration
        for loc in self.locations:
            if loc.location_type == LocationType.DECLARATION:
                return loc
        # Fall back to any location
        return self.locations[0] if self.locations else None
    
    def get_members_by_access(self, access_level: AccessLevel) -> List[Member]:
        """Get all members with specified access level"""
        return [m for m in self.members if m.access_level == access_level]
    
    def get_members_by_type(self, member_type: MemberType) -> List[Member]:
        """Get all members of specified type"""
        return [m for m in self.members if m.member_type == member_type]
    
    def is_derived(self) -> bool:
        """Check if this class/struct derives from others"""
        return bool(self.base_classes)
    
    def merge_with(self, other: 'Entity') -> bool:
        """
        Merge another entity's information into this one.
        Used when same entity found in multiple files.
        Returns True if merge was successful.
        """
        if self.canonical_name != other.canonical_name:
            return False  # Can't merge different entities
        
        # Merge locations
        for loc in other.locations:
            self.add_location(loc)
        
        # Merge members
        for member in other.members:
            self.add_member(member)
        
        # Update missing information
        if not self.return_type and other.return_type:
            self.return_type = other.return_type
        
        if not self.parameters and other.parameters:
            self.parameters = other.parameters
        
        if not self.template_params and other.template_params:
            self.template_params = other.template_params
            self.is_template = True
        
        if not self.base_classes and other.base_classes:
            self.base_classes = other.base_classes
        
        if not self.underlying_type and other.underlying_type:
            self.underlying_type = other.underlying_type
        
        if not self.aliased_type and other.aliased_type:
            self.aliased_type = other.aliased_type
        
        # Update flags (prefer True values)
        self.is_abstract = self.is_abstract or other.is_abstract
        self.is_final = self.is_final or other.is_final
        self.is_virtual = self.is_virtual or other.is_virtual
        self.is_static = self.is_static or other.is_static
        self.is_const = self.is_const or other.is_const
        self.is_inline = self.is_inline or other.is_inline
        self.is_constexpr = self.is_constexpr or other.is_constexpr
        self.is_noexcept = self.is_noexcept or other.is_noexcept
        
        return True
    
    def __str__(self):
        """String representation for debugging"""
        loc = self.get_primary_location()
        loc_str = f"{loc.file_path}:{loc.line_number}" if loc else "unknown"
        return f"{self.entity_type.value} {self.canonical_name} at {loc_str}"
    
    def __repr__(self):
        """Detailed representation for debugging"""
        return (f"Entity(canonical_name='{self.canonical_name}', "
                f"type={self.entity_type.value}, "
                f"locations={len(self.locations)}, "
                f"members={len(self.members)})")