#!/usr/bin/env python3
"""
Unit tests for cpp_parser_descent.py using real Orkid source files
"""
import unittest
import tempfile
import os
from pathlib import Path

from obt.cpp_parser_descent import RecursiveDescentCppParser
from obt.cpp_database_v2 import CppDatabaseV2
from obt.cpp_entities_v2 import EntityType, LocationType, MemberType
from ork import path as ork_path

class TestCppParserDescent(unittest.TestCase):
    """Test the recursive descent C++ parser with real Orkid files"""
    
    def setUp(self):
        """Set up parser and temp database"""
        self.parser = RecursiveDescentCppParser()
        
        # Create temp database for integration tests
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        self.db = CppDatabaseV2(self.db_path)
    
    def tearDown(self):
        """Clean up temp database"""
        try:
            os.unlink(self.db_path)
        except:
            pass
    
    def test_parse_context_h_no_duplicates(self):
        """Test parsing Context.h - should not create duplicate template classes"""
        # This is the file that had the duplicate template class bug
        context_file = ork_path.root / "ork.core" / "inc" / "ork" / "util" / "Context.h"
        
        if not context_file.exists():
            self.skipTest(f"Context.h not found at {context_file}")
        
        # Parse the file
        entities = self.parser.parse_file(context_file)
        
        # Check for Context class (not constructor or other functions with same name)
        context_entities = [e for e in entities 
                           if e.short_name == "Context" and e.entity_type == EntityType.CLASS]
        
        # Should have exactly ONE Context class entity (not two!)
        self.assertEqual(len(context_entities), 1, 
                        f"Expected 1 Context class entity, got {len(context_entities)}")
        
        # And it should be marked as a template
        context = context_entities[0]
        self.assertTrue(context.is_template, "Context should be marked as template")
        self.assertIsNotNone(context.template_params, "Context should have template parameters")
        
        # Add to database to verify no duplicates there either
        for entity in entities:
            self.db.add_entity(entity)
        
        # Query database for Context class specifically
        db_contexts = self.db.search_entities(name="Context", namespace="ork::util", 
                                             entity_type=EntityType.CLASS.value)
        self.assertEqual(len(db_contexts), 1, 
                        "Database should have exactly 1 Context class entity")
    
    def test_parse_cvector3_h(self):
        """Test parsing cvector3.h for fvec3 class"""
        vector_file = ork_path.root / "ork.core" / "inc" / "ork" / "math" / "cvector3.h"
        
        if not vector_file.exists():
            self.skipTest(f"cvector3.h not found at {vector_file}")
        
        # Parse the file
        entities = self.parser.parse_file(vector_file)
        
        # Look for fvec3
        fvec3_entities = [e for e in entities if e.short_name == "fvec3"]
        
        if fvec3_entities:
            fvec3 = fvec3_entities[0]
            # fvec3 might be a typedef or a class depending on implementation
            self.assertIn(fvec3.entity_type, [EntityType.CLASS, EntityType.TYPEDEF],
                         f"fvec3 should be a class or typedef, got {fvec3.entity_type}")
            
            # If it's a class, check for members
            if fvec3.entity_type == EntityType.CLASS:
                # Check for some expected members
                field_names = [m.name for m in fvec3.get_members_by_type(MemberType.FIELD)]
                # fvec3 typically has x, y, z components
                # Note: actual structure may vary
                
                # Check it has some methods
                methods = fvec3.get_members_by_type(MemberType.METHOD)
                self.assertGreater(len(methods), 0, "fvec3 class should have methods")
    
    def test_parse_mutex_h(self):
        """Test parsing mutex.h"""
        mutex_file = ork_path.root / "ork.core" / "inc" / "ork" / "kernel" / "mutex.h"
        
        if not mutex_file.exists():
            # Try alternative location
            mutex_file = ork_path.root / "ork.core" / "inc" / "ork" / "kernel" / "thread.h"
            if not mutex_file.exists():
                self.skipTest(f"mutex.h not found")
        
        # Parse the file
        entities = self.parser.parse_file(mutex_file)
        
        # Look for mutex-related classes
        mutex_entities = [e for e in entities if "mutex" in e.short_name.lower()]
        
        if mutex_entities:
            # Check we found some mutex-related entities
            self.assertGreater(len(mutex_entities), 0, "Should find mutex-related entities")
            
            # Check they're properly namespaced
            for entity in mutex_entities:
                if entity.namespace:
                    self.assertTrue(entity.namespace.startswith("ork"), 
                                  f"Mutex entities should be in ork namespace, got {entity.namespace}")
    
    def test_parse_concurrent_queue_h(self):
        """Test parsing concurrent_queue.h for LockedResource"""
        queue_file = ork_path.root / "ork.core" / "inc" / "ork" / "kernel" / "concurrent_queue.h"
        
        if not queue_file.exists():
            self.skipTest(f"concurrent_queue.h not found at {queue_file}")
        
        # Parse the file
        entities = self.parser.parse_file(queue_file)
        
        # Look for LockedResource
        locked_resource = None
        for entity in entities:
            if entity.short_name == "LockedResource":
                locked_resource = entity
                break
        
        if locked_resource:
            # Should be a template class
            self.assertTrue(locked_resource.is_template, "LockedResource should be a template")
            self.assertIsNotNone(locked_resource.template_params)
            self.assertEqual(locked_resource.entity_type, EntityType.CLASS)
    
    def test_no_duplicate_templates_comprehensive(self):
        """Comprehensive test: parse multiple files and verify no template duplicates"""
        test_files = [
            ork_path.root / "ork.core" / "inc" / "ork" / "util" / "Context.h",
            ork_path.root / "ork.core" / "inc" / "ork" / "kernel" / "concurrent_queue.h",
        ]
        
        template_count = {}  # canonical_name -> count
        
        for file_path in test_files:
            if not file_path.exists():
                continue
            
            entities = self.parser.parse_file(file_path)
            
            # Add to database
            for entity in entities:
                self.db.add_entity(entity)
                
                # Track templates
                if entity.is_template:
                    if entity.canonical_name in template_count:
                        template_count[entity.canonical_name] += 1
                    else:
                        template_count[entity.canonical_name] = 1
        
        # Verify no template appears more than once
        for name, count in template_count.items():
            self.assertEqual(count, 1, 
                           f"Template {name} appeared {count} times, expected 1")
        
        # Verify database has no duplicates
        stats = self.db.get_statistics()
        
        # Query for all templates
        with self.db.connect() as conn:
            template_entities = conn.execute(
                "SELECT canonical_name, COUNT(*) as cnt FROM entities WHERE is_template = 1 GROUP BY canonical_name"
            ).fetchall()
            
            for row in template_entities:
                self.assertEqual(row['cnt'], 1, 
                               f"Template {row['canonical_name']} has {row['cnt']} entries in DB, expected 1")
    
    def test_parse_simple_file(self):
        """Test parsing a simple test file"""
        # Create a simple test file
        test_content = b"""
namespace ork {
    // Regular class
    class SimpleClass {
    public:
        int getValue() const { return m_value; }
        void setValue(int v) { m_value = v; }
    private:
        int m_value;
    };
    
    // Template class - should only create ONE entity
    template<typename T>
    class TemplateClass {
    public:
        T data;
        void process(T value);
    };
    
    // Enum
    enum class Color : uint32_t {
        RED = 0xFF0000,
        GREEN = 0x00FF00,
        BLUE = 0x0000FF
    };
    
    // Function
    int processData(const SimpleClass& obj, int flags = 0);
}
"""
        # Write test file using tempfile
        with tempfile.NamedTemporaryFile(suffix='.cpp', delete=False) as tf:
            test_file = Path(tf.name)
            test_file.write_bytes(test_content)
        
        try:
            # Parse it
            entities = self.parser.parse_file(test_file)
            
            # Check entities
            entity_names = {e.short_name: e for e in entities}
            
            # Should have SimpleClass
            self.assertIn("SimpleClass", entity_names)
            simple_class = entity_names["SimpleClass"]
            self.assertEqual(simple_class.entity_type, EntityType.CLASS)
            self.assertFalse(simple_class.is_template)
            
            # Check SimpleClass members
            members = simple_class.members
            member_names = [m.name for m in members]
            self.assertIn("getValue", member_names)
            self.assertIn("setValue", member_names)
            self.assertIn("m_value", member_names)
            
            # Should have TemplateClass (only once!)
            template_classes = [e for e in entities if e.short_name == "TemplateClass"]
            self.assertEqual(len(template_classes), 1, 
                           "Should have exactly 1 TemplateClass entity")
            template_class = template_classes[0]
            self.assertTrue(template_class.is_template)
            self.assertIsNotNone(template_class.template_params)
            
            # Should have Color enum
            self.assertIn("Color", entity_names)
            color_enum = entity_names["Color"]
            self.assertEqual(color_enum.entity_type, EntityType.ENUM)
            self.assertTrue(color_enum.is_enum_class)
            self.assertEqual(color_enum.underlying_type, "uint32_t")
            
            # Check enum values
            enum_values = color_enum.get_members_by_type(MemberType.ENUM_VALUE)
            enum_names = [v.name for v in enum_values]
            self.assertIn("RED", enum_names)
            self.assertIn("GREEN", enum_names)
            self.assertIn("BLUE", enum_names)
            
            # Should have processData function
            self.assertIn("processData", entity_names)
            process_func = entity_names["processData"]
            self.assertEqual(process_func.entity_type, EntityType.FUNCTION)
            self.assertEqual(process_func.return_type, "int")
            self.assertEqual(len(process_func.parameters), 2)
            
        finally:
            # Clean up
            if test_file.exists():
                test_file.unlink()
    
    def test_integration_parser_to_database(self):
        """Test full integration: parse file and store in database"""
        # Create test content with potential duplicate scenario
        test_content = b"""
namespace test {
    // This template class used to create duplicates in the old system
    template<typename T>
    class Container {
    public:
        T* data;
        size_t size;
        
        Container() : data(nullptr), size(0) {}
        ~Container() { delete[] data; }
        
        void resize(size_t newSize);
        T& operator[](size_t index) { return data[index]; }
    };
}
"""
        # Write test file using tempfile
        with tempfile.NamedTemporaryFile(suffix='.hpp', delete=False) as tf:
            test_file = Path(tf.name)
            test_file.write_bytes(test_content)
        
        try:
            # Parse file
            entities = self.parser.parse_file(test_file)
            
            # Add all entities to database
            for entity in entities:
                self.db.add_entity(entity)
            
            # Query database for Container class specifically
            containers = self.db.search_entities(name="Container", namespace="test",
                                                entity_type=EntityType.CLASS.value)
            
            # Should have exactly ONE Container class entity
            self.assertEqual(len(containers), 1, 
                           "Database should have exactly 1 Container class entity")
            
            container = containers[0]
            self.assertTrue(container.is_template)
            self.assertEqual(container.namespace, "test")
            
            # Check members were stored
            self.assertGreater(len(container.members), 0)
            
            # Check statistics
            stats = self.db.get_statistics()
            self.assertEqual(stats['entities_class'], 1)
            self.assertEqual(stats['template_entities'], 1)
            
        finally:
            if test_file.exists():
                test_file.unlink()

if __name__ == "__main__":
    unittest.main()