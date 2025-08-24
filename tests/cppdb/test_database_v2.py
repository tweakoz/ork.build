#!/usr/bin/env python3
"""
Unit tests for cpp_database_v2.py normalized database
"""
import unittest
import tempfile
import os
from pathlib import Path

from obt.cpp_database_v2 import CppDatabaseV2
from obt.cpp_entities_v2 import (
    Entity, Location, Member, Parameter,
    EntityType, LocationType, AccessLevel, MemberType
)
from ork import path as ork_path

class TestCppDatabaseV2(unittest.TestCase):
    """Test normalized C++ database"""
    
    def setUp(self):
        """Create temporary database for each test"""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        self.db = CppDatabaseV2(self.db_path)
    
    def tearDown(self):
        """Clean up temporary database"""
        try:
            os.unlink(self.db_path)
        except:
            pass
    
    def test_database_creation(self):
        """Test database schema is created correctly"""
        # Check tables exist
        with self.db.connect() as conn:
            cursor = conn.execute(
                """SELECT name FROM sqlite_master 
                   WHERE type='table' 
                   ORDER BY name"""
            )
            tables = [row[0] for row in cursor]
            
            expected_tables = [
                'entities',
                'entity_locations', 
                'entity_members',
                'entity_references',
                'files'
            ]
            
            for table in expected_tables:
                self.assertIn(table, tables)
    
    def test_add_simple_entity(self):
        """Test adding a simple class entity"""
        entity = Entity(
            canonical_name="MyClass",
            short_name="MyClass",
            entity_type=EntityType.CLASS
        )
        
        # Add location
        entity.add_location(Location("/path/file.cpp", 42))
        
        # Add to database
        entity_id = self.db.add_entity(entity)
        self.assertIsNotNone(entity_id)
        self.assertGreater(entity_id, 0)
        
        # Retrieve and verify
        retrieved = self.db.get_entity("MyClass")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.canonical_name, "MyClass")
        self.assertEqual(retrieved.entity_type, EntityType.CLASS)
        self.assertEqual(len(retrieved.locations), 1)
        self.assertEqual(retrieved.locations[0].line_number, 42)
    
    def test_no_duplicate_entities(self):
        """Test that adding same entity twice doesn't create duplicates"""
        entity1 = Entity("MyClass", "MyClass", EntityType.CLASS)
        entity1.add_location(Location("/path/file.h", 10))
        
        entity2 = Entity("MyClass", "MyClass", EntityType.CLASS)
        entity2.add_location(Location("/path/file.cpp", 50))
        
        # Add both
        id1 = self.db.add_entity(entity1)
        id2 = self.db.add_entity(entity2)
        
        # Should be same ID (updated, not duplicated)
        self.assertEqual(id1, id2)
        
        # Should have both locations
        retrieved = self.db.get_entity("MyClass")
        self.assertEqual(len(retrieved.locations), 2)
        
        # Check no duplicates in database
        with self.db.connect() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM entities WHERE canonical_name = ?",
                ("MyClass",)
            ).fetchone()[0]
            self.assertEqual(count, 1)
    
    def test_no_duplicate_template_classes(self):
        """Test that template classes aren't duplicated (the original bug)"""
        # Regular class version
        regular = Entity(
            canonical_name="ork::util::Context",
            short_name="Context",
            entity_type=EntityType.CLASS,
            namespace="ork::util"
        )
        regular.add_location(Location("/inc/Context.h", 42))
        
        # Template version (same location!)
        template = Entity(
            canonical_name="ork::util::Context",
            short_name="Context",
            entity_type=EntityType.CLASS,
            namespace="ork::util",
            is_template=True,
            template_params="<typename T>"
        )
        template.add_location(Location("/inc/Context.h", 42))
        
        # Add both
        self.db.add_entity(regular)
        self.db.add_entity(template)
        
        # Should only have ONE entity
        entities = self.db.search_entities(name="Context", namespace="ork::util")
        self.assertEqual(len(entities), 1)
        
        # And it should be marked as template
        entity = entities[0]
        self.assertTrue(entity.is_template)
        self.assertEqual(entity.template_params, "<typename T>")
    
    def test_entity_with_members(self):
        """Test adding entity with members"""
        entity = Entity("MyClass", "MyClass", EntityType.CLASS)
        
        # Add members
        field = Member("m_data", MemberType.FIELD, data_type="int",
                      access_level=AccessLevel.PRIVATE)
        method = Member("process", MemberType.METHOD, data_type="void",
                       access_level=AccessLevel.PUBLIC, is_virtual=True)
        
        entity.add_member(field)
        entity.add_member(method)
        
        # Add to database
        self.db.add_entity(entity)
        
        # Retrieve and verify
        retrieved = self.db.get_entity("MyClass")
        self.assertEqual(len(retrieved.members), 2)
        
        # Check members
        fields = retrieved.get_members_by_type(MemberType.FIELD)
        self.assertEqual(len(fields), 1)
        self.assertEqual(fields[0].name, "m_data")
        self.assertEqual(fields[0].data_type, "int")
        
        methods = retrieved.get_members_by_type(MemberType.METHOD)
        self.assertEqual(len(methods), 1)
        self.assertEqual(methods[0].name, "process")
        self.assertTrue(methods[0].is_virtual)
    
    def test_no_duplicate_members(self):
        """Test that duplicate members aren't added"""
        entity = Entity("MyClass", "MyClass", EntityType.CLASS)
        
        # Add member
        member1 = Member("foo", MemberType.METHOD)
        entity.add_member(member1)
        self.db.add_entity(entity)
        
        # Try to add duplicate member
        entity2 = Entity("MyClass", "MyClass", EntityType.CLASS)
        member2 = Member("foo", MemberType.METHOD, is_virtual=True)
        entity2.add_member(member2)
        self.db.add_entity(entity2)
        
        # Should still have only one member
        retrieved = self.db.get_entity("MyClass")
        methods = retrieved.get_members_by_type(MemberType.METHOD)
        self.assertEqual(len(methods), 1)
        
        # But it should be updated
        self.assertTrue(methods[0].is_virtual)
    
    def test_function_entity(self):
        """Test adding function entity with parameters"""
        entity = Entity(
            canonical_name="ork::process",
            short_name="process",
            entity_type=EntityType.FUNCTION,
            namespace="ork",
            return_type="int"
        )
        
        # Add parameters
        param1 = Parameter("input", "const std::string&", is_const=True, is_reference=True)
        param2 = Parameter("flags", "int", default_value="0")
        entity.parameters = [param1, param2]
        
        # Add to database
        self.db.add_entity(entity)
        
        # Retrieve and verify
        retrieved = self.db.get_entity("ork::process")
        self.assertEqual(retrieved.return_type, "int")
        self.assertEqual(len(retrieved.parameters), 2)
        self.assertEqual(retrieved.parameters[0].name, "input")
        self.assertTrue(retrieved.parameters[0].is_const)
        self.assertTrue(retrieved.parameters[0].is_reference)
        self.assertEqual(retrieved.parameters[1].default_value, "0")
    
    def test_enum_entity(self):
        """Test adding enum entity with values"""
        entity = Entity(
            canonical_name="Color",
            short_name="Color",
            entity_type=EntityType.ENUM,
            is_enum_class=True,
            underlying_type="uint32_t"
        )
        
        # Add enum values
        entity.add_member(Member("RED", MemberType.ENUM_VALUE, value="0"))
        entity.add_member(Member("GREEN", MemberType.ENUM_VALUE, value="1"))
        entity.add_member(Member("BLUE", MemberType.ENUM_VALUE, value="2"))
        
        # Add to database
        self.db.add_entity(entity)
        
        # Retrieve and verify
        retrieved = self.db.get_entity("Color")
        self.assertTrue(retrieved.is_enum_class)
        self.assertEqual(retrieved.underlying_type, "uint32_t")
        
        enum_values = retrieved.get_members_by_type(MemberType.ENUM_VALUE)
        self.assertEqual(len(enum_values), 3)
        self.assertEqual(enum_values[0].name, "RED")
        self.assertEqual(enum_values[0].value, "0")
    
    def test_search_entities(self):
        """Test searching for entities"""
        # Add various entities
        entities = [
            Entity("MyClass", "MyClass", EntityType.CLASS),
            Entity("YourClass", "YourClass", EntityType.CLASS),
            Entity("MyStruct", "MyStruct", EntityType.STRUCT),
            Entity("process", "process", EntityType.FUNCTION),
            Entity("std::vector", "vector", EntityType.CLASS, namespace="std"),
            Entity("std::string", "string", EntityType.CLASS, namespace="std"),
        ]
        
        for entity in entities:
            self.db.add_entity(entity)
        
        # Search by type
        classes = self.db.search_entities(entity_type="class")
        self.assertEqual(len(classes), 4)  # MyClass, YourClass, std::vector, std::string
        
        # Search by multiple types
        class_struct = self.db.search_entities(entity_type="class,struct")
        self.assertEqual(len(class_struct), 5)  # All classes + MyStruct
        
        # Search by name
        my_class = self.db.search_entities(name="MyClass")
        self.assertEqual(len(my_class), 1)
        self.assertEqual(my_class[0].short_name, "MyClass")
        
        # Search by pattern
        my_entities = self.db.search_entities(pattern="My")
        self.assertEqual(len(my_entities), 2)  # MyClass, MyStruct
        
        # Search by namespace
        std_entities = self.db.search_entities(namespace="std")
        self.assertEqual(len(std_entities), 2)
        
        # Combined search
        std_classes = self.db.search_entities(entity_type="class", namespace="std")
        self.assertEqual(len(std_classes), 2)
    
    def test_delete_entity(self):
        """Test deleting an entity"""
        entity = Entity("MyClass", "MyClass", EntityType.CLASS)
        entity.add_member(Member("foo", MemberType.METHOD))
        entity.add_location(Location("/path/file.cpp", 42))
        
        self.db.add_entity(entity)
        
        # Verify it exists
        self.assertIsNotNone(self.db.get_entity("MyClass"))
        
        # Delete it
        self.assertTrue(self.db.delete_entity("MyClass"))
        
        # Verify it's gone
        self.assertIsNone(self.db.get_entity("MyClass"))
        
        # Verify cascading delete (members and locations should be gone)
        with self.db.connect() as conn:
            members = conn.execute(
                "SELECT COUNT(*) FROM entity_members"
            ).fetchone()[0]
            self.assertEqual(members, 0)
            
            locations = conn.execute(
                "SELECT COUNT(*) FROM entity_locations"
            ).fetchone()[0]
            self.assertEqual(locations, 0)
    
    def test_clear_database(self):
        """Test clearing all data"""
        # Add some entities
        for i in range(5):
            entity = Entity(f"Class{i}", f"Class{i}", EntityType.CLASS)
            entity.add_location(Location(f"/path/file{i}.cpp", i))
            self.db.add_entity(entity)
        
        # Clear database
        self.db.clear_database()
        
        # Verify everything is gone
        stats = self.db.get_statistics()
        self.assertEqual(stats['total_entities'], 0)
        self.assertEqual(stats['total_locations'], 0)
        self.assertEqual(stats['total_members'], 0)
    
    def test_statistics(self):
        """Test getting database statistics"""
        # Add various entity types
        self.db.add_entity(Entity("Class1", "Class1", EntityType.CLASS))
        self.db.add_entity(Entity("Class2", "Class2", EntityType.CLASS))
        self.db.add_entity(Entity("Struct1", "Struct1", EntityType.STRUCT))
        self.db.add_entity(Entity("func1", "func1", EntityType.FUNCTION))
        self.db.add_entity(Entity("Enum1", "Enum1", EntityType.ENUM))
        
        # Add template
        template = Entity("TClass", "TClass", EntityType.CLASS,
                         is_template=True, template_params="<typename T>")
        self.db.add_entity(template)
        
        stats = self.db.get_statistics()
        
        self.assertEqual(stats['total_entities'], 6)
        self.assertEqual(stats['entities_class'], 3)
        self.assertEqual(stats['entities_struct'], 1)
        self.assertEqual(stats['entities_function'], 1)
        self.assertEqual(stats['entities_enum'], 1)
        self.assertEqual(stats['template_entities'], 1)
    
    def test_file_tracking(self):
        """Test file modification tracking"""
        file_path = "/path/to/file.cpp"
        mtime1 = 1000.0
        
        # First update
        hash1 = self.db.update_file_record(file_path, mtime1)
        self.assertIsNotNone(hash1)
        
        # Check not modified (same time)
        self.assertFalse(self.db.is_file_modified(file_path, mtime1))
        
        # Check modified (newer time)
        self.assertTrue(self.db.is_file_modified(file_path, mtime1 + 1))
        
        # Update with new time
        mtime2 = 2000.0
        hash2 = self.db.update_file_record(file_path, mtime2)
        
        # Now old time should show as not modified
        self.assertFalse(self.db.is_file_modified(file_path, mtime1))
        self.assertFalse(self.db.is_file_modified(file_path, mtime2))
    
    def test_complex_entity(self):
        """Test a complex entity with all features"""
        # Create a complex template class
        entity = Entity(
            canonical_name="ork::util::SmartPtr",
            short_name="SmartPtr",
            entity_type=EntityType.CLASS,
            namespace="ork::util",
            is_template=True,
            template_params="<typename T>",
            is_final=True
        )
        
        # Add base classes
        entity.base_classes = ["BasePtr", "Countable"]
        
        # Add multiple locations
        entity.add_location(Location("/inc/SmartPtr.h", 10, 
                                    location_type=LocationType.DECLARATION))
        entity.add_location(Location("/inc/SmartPtr.hpp", 100,
                                    location_type=LocationType.DEFINITION,
                                    has_body=True))
        
        # Add various members
        entity.add_member(Member("m_ptr", MemberType.FIELD, 
                               data_type="T*",
                               access_level=AccessLevel.PRIVATE))
        entity.add_member(Member("m_count", MemberType.FIELD,
                               data_type="std::atomic<int>",
                               access_level=AccessLevel.PRIVATE,
                               is_static=True))
        entity.add_member(Member("SmartPtr", MemberType.CONSTRUCTOR,
                               access_level=AccessLevel.PUBLIC,
                               is_explicit=True))
        entity.add_member(Member("~SmartPtr", MemberType.DESTRUCTOR,
                               access_level=AccessLevel.PUBLIC,
                               is_virtual=True))
        entity.add_member(Member("get", MemberType.METHOD,
                               data_type="T*",
                               access_level=AccessLevel.PUBLIC,
                               is_const=True,
                               is_inline=True))
        entity.add_member(Member("reset", MemberType.METHOD,
                               data_type="void",
                               access_level=AccessLevel.PUBLIC))
        
        # Add to database
        self.db.add_entity(entity)
        
        # Retrieve and verify everything
        retrieved = self.db.get_entity("ork::util::SmartPtr")
        
        self.assertEqual(retrieved.canonical_name, "ork::util::SmartPtr")
        self.assertEqual(retrieved.namespace, "ork::util")
        self.assertTrue(retrieved.is_template)
        self.assertEqual(retrieved.template_params, "<typename T>")
        self.assertTrue(retrieved.is_final)
        self.assertEqual(retrieved.base_classes, ["BasePtr", "Countable"])
        
        # Check locations
        self.assertEqual(len(retrieved.locations), 2)
        primary = retrieved.get_primary_location()
        self.assertEqual(primary.location_type, LocationType.DEFINITION)
        self.assertTrue(primary.has_body)
        
        # Check members
        self.assertEqual(len(retrieved.members), 6)
        
        fields = retrieved.get_members_by_type(MemberType.FIELD)
        self.assertEqual(len(fields), 2)
        
        constructors = retrieved.get_members_by_type(MemberType.CONSTRUCTOR)
        self.assertEqual(len(constructors), 1)
        self.assertTrue(constructors[0].is_explicit)
        
        destructors = retrieved.get_members_by_type(MemberType.DESTRUCTOR)
        self.assertEqual(len(destructors), 1)
        self.assertTrue(destructors[0].is_virtual)
        
        public_members = retrieved.get_members_by_access(AccessLevel.PUBLIC)
        self.assertEqual(len(public_members), 4)  # ctor, dtor, get, reset
    
    def test_real_orkid_classes(self):
        """Test with real Orkid classes that are stable"""
        # Test LockedResource - a template class for thread-safe resources
        locked_resource = Entity(
            canonical_name="ork::LockedResource",
            short_name="LockedResource",
            entity_type=EntityType.CLASS,
            namespace="ork",
            is_template=True,
            template_params="<typename T>"
        )
        locked_resource.add_location(Location(
            str(ork_path.root / "ork.core" / "inc" / "ork" / "kernel" / "concurrent_queue.h"),
            100  # Approximate line number
        ))
        
        # Test mutex - standard synchronization primitive
        mutex = Entity(
            canonical_name="ork::mutex",
            short_name="mutex",
            entity_type=EntityType.CLASS,
            namespace="ork"
        )
        mutex.add_location(Location(
            str(ork_path.root / "ork.core" / "inc" / "ork" / "kernel" / "mutex.h"),
            50  # Approximate line number
        ))
        
        # Test fvec3 - 3D float vector
        fvec3 = Entity(
            canonical_name="ork::fvec3",
            short_name="fvec3",
            entity_type=EntityType.CLASS,
            namespace="ork"
        )
        fvec3.add_location(Location(
            str(ork_path.root / "ork.core" / "inc" / "ork" / "math" / "cvector3.h"),
            200,  # Approximate line number
            location_type=LocationType.DEFINITION,
            has_body=True
        ))
        # Add some typical fvec3 members
        fvec3.add_member(Member("x", MemberType.FIELD, data_type="float", 
                               access_level=AccessLevel.PUBLIC))
        fvec3.add_member(Member("y", MemberType.FIELD, data_type="float",
                               access_level=AccessLevel.PUBLIC))
        fvec3.add_member(Member("z", MemberType.FIELD, data_type="float",
                               access_level=AccessLevel.PUBLIC))
        fvec3.add_member(Member("normalize", MemberType.METHOD, data_type="void",
                               access_level=AccessLevel.PUBLIC))
        fvec3.add_member(Member("length", MemberType.METHOD, data_type="float",
                               access_level=AccessLevel.PUBLIC, is_const=True))
        
        # Add all to database
        self.db.add_entity(locked_resource)
        self.db.add_entity(mutex)
        self.db.add_entity(fvec3)
        
        # Test searching for them
        all_classes = self.db.search_entities(entity_type="class")
        self.assertEqual(len(all_classes), 3)
        
        # Test template search
        templates = []
        for entity in all_classes:
            if entity.is_template:
                templates.append(entity)
        self.assertEqual(len(templates), 1)
        self.assertEqual(templates[0].short_name, "LockedResource")
        
        # Test fvec3 members
        fvec3_retrieved = self.db.get_entity("ork::fvec3")
        self.assertIsNotNone(fvec3_retrieved)
        self.assertEqual(len(fvec3_retrieved.members), 5)
        
        # Check fields
        fields = fvec3_retrieved.get_members_by_type(MemberType.FIELD)
        self.assertEqual(len(fields), 3)
        field_names = [f.name for f in fields]
        self.assertIn("x", field_names)
        self.assertIn("y", field_names)
        self.assertIn("z", field_names)
        
        # Check methods
        methods = fvec3_retrieved.get_members_by_type(MemberType.METHOD)
        self.assertEqual(len(methods), 2)
        
        # Test that paths are correct
        for entity in [locked_resource, mutex, fvec3]:
            loc = entity.get_primary_location()
            self.assertTrue(loc.file_path.startswith(str(ork_path.root)))
    
    def test_orkid_template_specialization(self):
        """Test handling of template specializations like Context<T>"""
        # Base template
        context_template = Entity(
            canonical_name="ork::util::Context",
            short_name="Context",
            entity_type=EntityType.CLASS,
            namespace="ork::util",
            is_template=True,
            template_params="<typename T>"
        )
        context_template.add_location(Location(
            str(ork_path.root / "ork.core" / "inc" / "ork" / "util" / "Context.h"),
            42,
            location_type=LocationType.DEFINITION
        ))
        
        # Specialization
        context_int = Entity(
            canonical_name="ork::util::Context<int>",
            short_name="Context<int>",
            entity_type=EntityType.CLASS,
            namespace="ork::util",
            is_template_specialization=True,
            specialized_from="ork::util::Context"
        )
        context_int.add_location(Location(
            str(ork_path.root / "ork.core" / "inc" / "ork" / "util" / "Context.h"),
            100,
            location_type=LocationType.DEFINITION
        ))
        
        # Add both
        self.db.add_entity(context_template)
        self.db.add_entity(context_int)
        
        # Should have two separate entities
        contexts = self.db.search_entities(pattern="Context", namespace="ork::util")
        self.assertEqual(len(contexts), 2)
        
        # Check specialization relationship
        spec = self.db.get_entity("ork::util::Context<int>")
        self.assertIsNotNone(spec)
        self.assertTrue(spec.is_template_specialization)
        self.assertEqual(spec.specialized_from, "ork::util::Context")

    def test_typedef_resolution(self):
        """Test resolving typedefs to their underlying types"""
        # Create a template class
        vector3 = Entity(
            canonical_name="Vector3",
            short_name="Vector3",
            entity_type=EntityType.STRUCT,
            is_template=True,
            template_params="<typename T>"
        )
        
        # Add some members to Vector3
        vector3.add_member(Member(
            name="x",
            member_type=MemberType.FIELD,
            data_type="T"
        ))
        vector3.add_member(Member(
            name="y", 
            member_type=MemberType.FIELD,
            data_type="T"
        ))
        vector3.add_member(Member(
            name="length",
            member_type=MemberType.METHOD,
            data_type="T"
        ))
        
        # Create a typedef
        fvec3 = Entity(
            canonical_name="fvec3",
            short_name="fvec3",
            entity_type=EntityType.TYPEDEF,
            aliased_type="Vector3<float>",
            is_using_alias=True
        )
        
        # Add both to database
        self.db.add_entity(vector3)
        self.db.add_entity(fvec3)
        
        # Test resolution
        resolved = self.db.resolve_typedef(fvec3)
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.short_name, "Vector3")
        self.assertEqual(resolved.entity_type, EntityType.STRUCT)
        self.assertTrue(resolved.is_template)
        
        # Test effective members
        fvec3_members = self.db.get_effective_members(fvec3)
        self.assertEqual(len(fvec3_members), 3)
        member_names = [m.name for m in fvec3_members]
        self.assertIn("x", member_names)
        self.assertIn("y", member_names)
        self.assertIn("length", member_names)
        
        # Test that non-typedef returns itself
        resolved_vector = self.db.resolve_typedef(vector3)
        self.assertEqual(resolved_vector, vector3)

    def test_file_tracking(self):
        """Test file tracking for incremental updates"""
        import tempfile
        import time
        
        # Create a test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
            test_file = f.name
            f.write("class TestClass {};")
        
        try:
            # Add file to database
            file_hash1 = self.db.add_file(test_file)
            self.assertIsNotNone(file_hash1)
            
            # Check file is tracked
            stats = self.db.get_statistics()
            self.assertEqual(stats['total_files'], 1)
            
            # Check if file is considered modified (should not be)
            mtime = os.path.getmtime(test_file)
            self.assertFalse(self.db.is_file_modified(test_file, mtime))
            
            # Simulate file modification
            time.sleep(0.01)  # Small delay to ensure different mtime
            with open(test_file, 'w') as f:
                f.write("class TestClass { int x; };")
            
            # Check if file is now considered modified
            new_mtime = os.path.getmtime(test_file)
            self.assertTrue(self.db.is_file_modified(test_file, new_mtime))
            
            # Update file record
            file_hash2 = self.db.update_file_record(test_file, new_mtime)
            self.assertIsNotNone(file_hash2)
            self.assertNotEqual(file_hash1, file_hash2)  # Hash should change
            
            # Now file should not be considered modified
            self.assertFalse(self.db.is_file_modified(test_file, new_mtime))
            
        finally:
            # Clean up
            os.unlink(test_file)
    
    def test_incremental_parsing(self):
        """Test that only modified files are reparsed"""
        import tempfile
        import time
        from obt.cpp_parser_v2 import CppParserV2
        
        parser = CppParserV2()
        
        # Create two test files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.hpp', delete=False) as f1:
            file1 = Path(f1.name)
            f1.write("class Class1 {};")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.hpp', delete=False) as f2:
            file2 = Path(f2.name)
            f2.write("class Class2 {};")
        
        try:
            # Initial parse of both files
            entities1 = parser.parse_file(file1)
            for entity in entities1:
                self.db.add_entity(entity)
            self.db.add_file(file1)
            
            entities2 = parser.parse_file(file2)
            for entity in entities2:
                self.db.add_entity(entity)
            self.db.add_file(file2)
            
            # Check both files are tracked
            stats = self.db.get_statistics()
            self.assertEqual(stats['total_files'], 2)
            
            # Check which files need reparsing (none should)
            mtime1 = os.path.getmtime(str(file1))
            mtime2 = os.path.getmtime(str(file2))
            self.assertFalse(self.db.is_file_modified(str(file1), mtime1))
            self.assertFalse(self.db.is_file_modified(str(file2), mtime2))
            
            # Modify file1
            time.sleep(0.01)
            file1.write_text("class Class1 { int member; };")
            new_mtime1 = os.path.getmtime(str(file1))
            
            # Check which files need reparsing (only file1)
            self.assertTrue(self.db.is_file_modified(str(file1), new_mtime1))
            self.assertFalse(self.db.is_file_modified(str(file2), mtime2))
            
        finally:
            # Clean up
            file1.unlink()
            file2.unlink()

if __name__ == "__main__":
    unittest.main()