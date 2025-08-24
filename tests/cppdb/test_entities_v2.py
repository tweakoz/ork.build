#!/usr/bin/env python3
"""
Unit tests for cpp_entities_v2.py data models
"""
import unittest
from obt.cpp_entities_v2 import (
    Entity, Location, Member, Parameter,
    EntityType, LocationType, AccessLevel, MemberType
)

class TestLocation(unittest.TestCase):
    """Test Location data model"""
    
    def test_location_creation(self):
        """Test creating a location"""
        loc = Location(
            file_path="/path/to/file.cpp",
            line_number=42,
            column_number=10,
            location_type=LocationType.DEFINITION,
            has_body=True
        )
        
        self.assertEqual(loc.file_path, "/path/to/file.cpp")
        self.assertEqual(loc.line_number, 42)
        self.assertEqual(loc.column_number, 10)
        self.assertEqual(loc.location_type, LocationType.DEFINITION)
        self.assertTrue(loc.has_body)
    
    def test_location_equality(self):
        """Test location equality based on file and line"""
        loc1 = Location("/path/file.cpp", 42, column_number=10)
        loc2 = Location("/path/file.cpp", 42, column_number=20)  # Different column
        loc3 = Location("/path/file.cpp", 43)  # Different line
        
        self.assertEqual(loc1, loc2)  # Same file and line
        self.assertNotEqual(loc1, loc3)  # Different line
    
    def test_location_hash(self):
        """Test location hashing for use in sets"""
        loc1 = Location("/path/file.cpp", 42)
        loc2 = Location("/path/file.cpp", 42)
        loc3 = Location("/path/file.cpp", 43)
        
        locations = {loc1, loc2, loc3}
        self.assertEqual(len(locations), 2)  # loc1 and loc2 are same

class TestMember(unittest.TestCase):
    """Test Member data model"""
    
    def test_member_creation(self):
        """Test creating a member"""
        member = Member(
            name="m_data",
            member_type=MemberType.FIELD,
            data_type="int",
            access_level=AccessLevel.PRIVATE,
            is_static=False,
            line_number=10
        )
        
        self.assertEqual(member.name, "m_data")
        self.assertEqual(member.member_type, MemberType.FIELD)
        self.assertEqual(member.data_type, "int")
        self.assertEqual(member.access_level, AccessLevel.PRIVATE)
        self.assertFalse(member.is_static)
    
    def test_member_equality(self):
        """Test member equality based on name and type"""
        m1 = Member("foo", MemberType.METHOD)
        m2 = Member("foo", MemberType.METHOD)  # Same
        m3 = Member("foo", MemberType.FIELD)   # Different type
        m4 = Member("bar", MemberType.METHOD)  # Different name
        
        self.assertEqual(m1, m2)
        self.assertNotEqual(m1, m3)
        self.assertNotEqual(m1, m4)
    
    def test_method_member(self):
        """Test creating a method member"""
        method = Member(
            name="process",
            member_type=MemberType.METHOD,
            data_type="void",
            access_level=AccessLevel.PUBLIC,
            is_virtual=True,
            is_const=True,
            signature="void process() const"
        )
        
        self.assertEqual(method.member_type, MemberType.METHOD)
        self.assertTrue(method.is_virtual)
        self.assertTrue(method.is_const)
        self.assertEqual(method.signature, "void process() const")

class TestEntity(unittest.TestCase):
    """Test Entity data model"""
    
    def test_entity_creation(self):
        """Test creating an entity"""
        entity = Entity(
            canonical_name="ork::util::Context",
            short_name="Context",
            entity_type=EntityType.CLASS,
            namespace="ork::util"
        )
        
        self.assertEqual(entity.canonical_name, "ork::util::Context")
        self.assertEqual(entity.short_name, "Context")
        self.assertEqual(entity.entity_type, EntityType.CLASS)
        self.assertEqual(entity.namespace, "ork::util")
        self.assertFalse(entity.is_template)
        self.assertEqual(len(entity.locations), 0)
        self.assertEqual(len(entity.members), 0)
    
    def test_template_entity(self):
        """Test creating a template entity"""
        entity = Entity(
            canonical_name="std::vector",
            short_name="vector",
            entity_type=EntityType.CLASS,
            namespace="std",
            is_template=True,
            template_params="<typename T, typename Allocator>"
        )
        
        self.assertTrue(entity.is_template)
        self.assertEqual(entity.template_params, "<typename T, typename Allocator>")
    
    def test_add_location(self):
        """Test adding locations to entity"""
        entity = Entity("MyClass", "MyClass", EntityType.CLASS)
        
        # Add declaration
        loc1 = Location("/path/file.h", 10, location_type=LocationType.DECLARATION)
        self.assertTrue(entity.add_location(loc1))
        self.assertEqual(len(entity.locations), 1)
        
        # Add definition
        loc2 = Location("/path/file.cpp", 50, location_type=LocationType.DEFINITION)
        self.assertTrue(entity.add_location(loc2))
        self.assertEqual(len(entity.locations), 2)
        
        # Try to add duplicate location
        loc3 = Location("/path/file.h", 10, location_type=LocationType.DECLARATION)
        self.assertFalse(entity.add_location(loc3))
        self.assertEqual(len(entity.locations), 2)
        
        # Update existing location with definition
        loc4 = Location("/path/file.h", 10, location_type=LocationType.DEFINITION)
        self.assertTrue(entity.add_location(loc4))
        self.assertEqual(len(entity.locations), 2)
        # Check it was updated
        self.assertEqual(entity.locations[0].location_type, LocationType.DEFINITION)
    
    def test_get_primary_location(self):
        """Test getting primary location (prefer definition)"""
        entity = Entity("MyClass", "MyClass", EntityType.CLASS)
        
        # Add declaration first
        decl = Location("/path/file.h", 10, location_type=LocationType.DECLARATION)
        entity.add_location(decl)
        
        # Primary should be declaration (only one available)
        self.assertEqual(entity.get_primary_location(), decl)
        
        # Add definition
        defn = Location("/path/file.cpp", 50, location_type=LocationType.DEFINITION)
        entity.add_location(defn)
        
        # Primary should now be definition
        self.assertEqual(entity.get_primary_location(), defn)
    
    def test_add_member(self):
        """Test adding members to entity"""
        entity = Entity("MyClass", "MyClass", EntityType.CLASS)
        
        # Add field
        field = Member("m_data", MemberType.FIELD, data_type="int")
        self.assertTrue(entity.add_member(field))
        self.assertEqual(len(entity.members), 1)
        
        # Add method
        method = Member("process", MemberType.METHOD, data_type="void")
        self.assertTrue(entity.add_member(method))
        self.assertEqual(len(entity.members), 2)
        
        # Try to add duplicate
        dup_field = Member("m_data", MemberType.FIELD, data_type="double")
        self.assertFalse(entity.add_member(dup_field))
        self.assertEqual(len(entity.members), 2)
    
    def test_get_members_by_access(self):
        """Test filtering members by access level"""
        entity = Entity("MyClass", "MyClass", EntityType.CLASS)
        
        # Add members with different access levels
        pub_method = Member("publicMethod", MemberType.METHOD, 
                           access_level=AccessLevel.PUBLIC)
        priv_field = Member("m_data", MemberType.FIELD,
                           access_level=AccessLevel.PRIVATE)
        prot_method = Member("protectedMethod", MemberType.METHOD,
                            access_level=AccessLevel.PROTECTED)
        
        entity.add_member(pub_method)
        entity.add_member(priv_field)
        entity.add_member(prot_method)
        
        # Test filtering
        public_members = entity.get_members_by_access(AccessLevel.PUBLIC)
        self.assertEqual(len(public_members), 1)
        self.assertEqual(public_members[0].name, "publicMethod")
        
        private_members = entity.get_members_by_access(AccessLevel.PRIVATE)
        self.assertEqual(len(private_members), 1)
        self.assertEqual(private_members[0].name, "m_data")
    
    def test_get_members_by_type(self):
        """Test filtering members by type"""
        entity = Entity("MyClass", "MyClass", EntityType.CLASS)
        
        # Add different member types
        field1 = Member("m_data", MemberType.FIELD)
        field2 = Member("m_count", MemberType.FIELD)
        method = Member("process", MemberType.METHOD)
        
        entity.add_member(field1)
        entity.add_member(field2)
        entity.add_member(method)
        
        # Test filtering
        fields = entity.get_members_by_type(MemberType.FIELD)
        self.assertEqual(len(fields), 2)
        
        methods = entity.get_members_by_type(MemberType.METHOD)
        self.assertEqual(len(methods), 1)
        self.assertEqual(methods[0].name, "process")
    
    def test_is_derived(self):
        """Test checking if class is derived"""
        base_class = Entity("Base", "Base", EntityType.CLASS)
        self.assertFalse(base_class.is_derived())
        
        derived_class = Entity("Derived", "Derived", EntityType.CLASS)
        derived_class.base_classes = ["Base"]
        self.assertTrue(derived_class.is_derived())
    
    def test_merge_entities(self):
        """Test merging two entities"""
        # Create entity with partial info
        entity1 = Entity("MyClass", "MyClass", EntityType.CLASS)
        entity1.add_location(Location("/path/file.h", 10))
        entity1.add_member(Member("method1", MemberType.METHOD))
        
        # Create another entity with more info
        entity2 = Entity("MyClass", "MyClass", EntityType.CLASS)
        entity2.add_location(Location("/path/file.cpp", 50))
        entity2.add_member(Member("method2", MemberType.METHOD))
        entity2.return_type = "void"
        entity2.is_virtual = True
        
        # Merge
        self.assertTrue(entity1.merge_with(entity2))
        
        # Check merged data
        self.assertEqual(len(entity1.locations), 2)
        self.assertEqual(len(entity1.members), 2)
        self.assertEqual(entity1.return_type, "void")
        self.assertTrue(entity1.is_virtual)
        
        # Can't merge different entities
        entity3 = Entity("OtherClass", "OtherClass", EntityType.CLASS)
        self.assertFalse(entity1.merge_with(entity3))
    
    def test_function_entity(self):
        """Test creating a function entity"""
        entity = Entity(
            canonical_name="process",
            short_name="process",
            entity_type=EntityType.FUNCTION,
            return_type="int",
            is_const=True,
            is_noexcept=True
        )
        
        # Add parameters
        param1 = Parameter("input", "const std::string&", is_const=True, is_reference=True)
        param2 = Parameter("flags", "int", default_value="0")
        entity.parameters = [param1, param2]
        
        self.assertEqual(entity.entity_type, EntityType.FUNCTION)
        self.assertEqual(entity.return_type, "int")
        self.assertTrue(entity.is_const)
        self.assertTrue(entity.is_noexcept)
        self.assertEqual(len(entity.parameters), 2)
        self.assertEqual(entity.parameters[0].name, "input")
        self.assertEqual(entity.parameters[1].default_value, "0")
    
    def test_enum_entity(self):
        """Test creating an enum entity"""
        entity = Entity(
            canonical_name="Color",
            short_name="Color",
            entity_type=EntityType.ENUM,
            is_enum_class=True,
            underlying_type="uint32_t"
        )
        
        # Add enum values
        red = Member("RED", MemberType.ENUM_VALUE, value="0xFF0000")
        green = Member("GREEN", MemberType.ENUM_VALUE, value="0x00FF00")
        blue = Member("BLUE", MemberType.ENUM_VALUE, value="0x0000FF")
        
        entity.add_member(red)
        entity.add_member(green)
        entity.add_member(blue)
        
        self.assertEqual(entity.entity_type, EntityType.ENUM)
        self.assertTrue(entity.is_enum_class)
        self.assertEqual(entity.underlying_type, "uint32_t")
        self.assertEqual(len(entity.members), 3)
        
        # Check enum values
        enum_values = entity.get_members_by_type(MemberType.ENUM_VALUE)
        self.assertEqual(len(enum_values), 3)
        self.assertEqual(enum_values[0].value, "0xFF0000")
    
    def test_typedef_entity(self):
        """Test creating a typedef/alias entity"""
        entity = Entity(
            canonical_name="StringList",
            short_name="StringList",
            entity_type=EntityType.TYPEDEF,
            aliased_type="std::vector<std::string>",
            is_using_alias=True
        )
        
        self.assertEqual(entity.entity_type, EntityType.TYPEDEF)
        self.assertEqual(entity.aliased_type, "std::vector<std::string>")
        self.assertTrue(entity.is_using_alias)

class TestParameter(unittest.TestCase):
    """Test Parameter data model"""
    
    def test_parameter_creation(self):
        """Test creating function parameters"""
        # Simple parameter
        param1 = Parameter("count", "int")
        self.assertEqual(param1.name, "count")
        self.assertEqual(param1.param_type, "int")
        self.assertFalse(param1.is_const)
        self.assertFalse(param1.is_reference)
        
        # Const reference parameter
        param2 = Parameter(
            name="input",
            param_type="std::string",
            is_const=True,
            is_reference=True
        )
        self.assertTrue(param2.is_const)
        self.assertTrue(param2.is_reference)
        
        # Parameter with default value
        param3 = Parameter(
            name="flags",
            param_type="int",
            default_value="0"
        )
        self.assertEqual(param3.default_value, "0")
        
        # Unnamed parameter
        param4 = Parameter(None, "void*", is_pointer=True)
        self.assertIsNone(param4.name)
        self.assertTrue(param4.is_pointer)
        
        # Rvalue reference
        param5 = Parameter(
            name="data",
            param_type="std::vector<int>",
            is_rvalue_ref=True
        )
        self.assertTrue(param5.is_rvalue_ref)

if __name__ == "__main__":
    unittest.main()