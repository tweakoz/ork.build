#!/usr/bin/env python3
"""
Test that validates C++ class parsing by comparing database entities 
against Clang AST parsing of preprocessed source code. 
This provides ground truth validation using Clang's authoritative C++ parser.
"""

import sys
import os
from pathlib import Path
from collections import defaultdict
import json
import clang.cindex
from clang.cindex import CursorKind, AccessSpecifier

# Add obt to path
import obt.path
import obt.deco
from obt.cpp_database_v2 import CppDatabaseV2
from obt.cpp_entities_v2 import EntityType, MemberType

deco = obt.deco.Deco()

class ClangClassValidator:
    def __init__(self, db_path):
        self.db = CppDatabaseV2(db_path)
        self.clang_index = clang.cindex.Index.create()
        self.errors = []
        self.warnings = []
        self.stats = {
            'classes_checked': 0,
            'methods_found': 0,
            'methods_missing': 0,
            'methods_extra': 0,
            'fields_found': 0,
            'fields_missing': 0,
            'fields_extra': 0,
            'overloads_detected': 0,
            'access_mismatches': 0,
        }
        
    def get_access_string(self, access_spec):
        """Convert Clang AccessSpecifier to string."""
        if access_spec == AccessSpecifier.PUBLIC:
            return 'public'
        elif access_spec == AccessSpecifier.PROTECTED:
            return 'protected'
        elif access_spec == AccessSpecifier.PRIVATE:
            return 'private'
        return 'private'  # Default for classes
    
    def get_method_signature(self, cursor):
        """Extract method signature from cursor."""
        # Get parameter types
        params = []
        for child in cursor.get_children():
            if child.kind == CursorKind.PARM_DECL:
                param_type = child.type.spelling
                param_name = child.spelling or ""
                params.append(param_type)
        
        param_str = ", ".join(params)
        signature = f"{cursor.spelling}({param_str})"
        
        # Add const qualifier if present
        if cursor.is_const_method():
            signature += " const"
            
        return signature
    
    def find_class_cursor(self, root_cursor, class_name):
        """Find class cursor by name in AST."""
        for cursor in root_cursor.walk_preorder():
            if cursor.kind in [CursorKind.CLASS_DECL, CursorKind.STRUCT_DECL]:
                if cursor.spelling == class_name:
                    # Make sure it's a definition, not just declaration
                    if cursor.is_definition():
                        return cursor
        return None
    
    def extract_class_members_with_clang(self, class_name, preprocessed_source):
        """Use Clang AST to extract ground truth class members."""
        members = {
            'methods': [],
            'fields': [],
            'static_fields': [],
            'constructors': [],
            'destructor': None,
            'all_members': []  # For debugging
        }
        
        # Parse the preprocessed source with Clang
        try:
            tu = self.clang_index.parse(
                'tmp.cpp',
                args=['-std=c++17', '-x', 'c++'],
                unsaved_files=[('tmp.cpp', preprocessed_source)]
            )
            
            # Check for parse errors
            if tu.diagnostics:
                severe_errors = [d for d in tu.diagnostics if d.severity >= clang.cindex.Diagnostic.Error]
                if severe_errors:
                    print(f"  {deco.yellow('Clang parse warnings/errors:')}")
                    for diag in severe_errors[:3]:  # Show first 3
                        print(f"    {diag.spelling}")
            
            # Find the class
            class_cursor = self.find_class_cursor(tu.cursor, class_name)
            if not class_cursor:
                print(f"  {deco.red('Class not found by Clang')}: {class_name}")
                return members
            
            # Track current access level (default is private for class, public for struct)
            current_access = AccessSpecifier.PRIVATE
            if class_cursor.kind == CursorKind.STRUCT_DECL:
                current_access = AccessSpecifier.PUBLIC
            
            # Traverse class members
            for child in class_cursor.get_children():
                # Update access specifier
                if child.kind == CursorKind.CXX_ACCESS_SPEC_DECL:
                    current_access = child.access_specifier
                    continue
                
                # Skip base specifiers and other non-member items
                if child.kind == CursorKind.CXX_BASE_SPECIFIER:
                    continue
                    
                # Constructors
                if child.kind == CursorKind.CONSTRUCTOR:
                    members['constructors'].append({
                        'signature': self.get_method_signature(child),
                        'access': self.get_access_string(current_access)
                    })
                    members['all_members'].append(f"Constructor: {child.spelling}")
                    
                # Destructor
                elif child.kind == CursorKind.DESTRUCTOR:
                    members['destructor'] = {
                        'signature': child.spelling,
                        'access': self.get_access_string(current_access)
                    }
                    members['all_members'].append(f"Destructor: {child.spelling}")
                    
                # Regular methods
                elif child.kind == CursorKind.CXX_METHOD:
                    method_info = {
                        'name': child.spelling,
                        'signature': self.get_method_signature(child),
                        'access': self.get_access_string(current_access),
                        'is_virtual': child.is_virtual_method(),
                        'is_static': child.is_static_method(),
                        'is_const': child.is_const_method()
                    }
                    members['methods'].append(method_info)
                    members['all_members'].append(f"Method: {child.spelling}")
                    
                # Function declarations (might be static methods)
                elif child.kind == CursorKind.FUNCTION_DECL:
                    method_info = {
                        'name': child.spelling,
                        'signature': self.get_method_signature(child),
                        'access': self.get_access_string(current_access),
                        'is_static': True
                    }
                    members['methods'].append(method_info)
                    members['all_members'].append(f"Static Function: {child.spelling}")
                    
                # Member fields
                elif child.kind == CursorKind.FIELD_DECL:
                    field_type = child.type.spelling
                    field_info = {
                        'name': child.spelling,
                        'type': field_type,
                        'access': self.get_access_string(current_access),
                        'is_static': False
                    }
                    
                    # Check if it's an array
                    if child.type.kind == clang.cindex.TypeKind.CONSTANTARRAY:
                        field_info['is_array'] = True
                        field_info['array_size'] = child.type.element_count
                        
                    members['fields'].append(field_info)
                    members['all_members'].append(f"Field: {child.spelling} ({field_type})")
                    
                # Static member variables
                elif child.kind == CursorKind.VAR_DECL:
                    field_info = {
                        'name': child.spelling,
                        'type': child.type.spelling,
                        'access': self.get_access_string(current_access),
                        'is_static': True
                    }
                    members['static_fields'].append(field_info)
                    members['all_members'].append(f"Static Field: {child.spelling}")
                    
                # Type aliases and typedefs within the class
                elif child.kind in [CursorKind.TYPEDEF_DECL, CursorKind.TYPE_ALIAS_DECL]:
                    members['all_members'].append(f"Typedef: {child.spelling}")
                    
        except Exception as e:
            self.errors.append(f"Clang parsing error for {class_name}: {str(e)}")
            print(f"  {deco.red('Clang parsing error')}: {str(e)}")
            
        return members
    
    def compare_class_members(self, entity, clang_members):
        """Compare database members with Clang-extracted members."""
        class_name = entity.short_name
        db_members = entity.members
        
        # Group database members by type
        db_methods = []
        db_fields = []
        db_static_fields = []
        db_constructors = []
        db_destructor = None
        
        for member in db_members:
            member_type = member.member_type.value
            if member_type == 'method':
                # Check if it's constructor/destructor by name
                if member.name == class_name:
                    db_constructors.append(member)
                elif member.name == f'~{class_name}':
                    db_destructor = member
                else:
                    db_methods.append(member)
            elif member_type == 'field':
                if member.is_static:
                    db_static_fields.append(member)
                else:
                    db_fields.append(member)
            elif member_type == 'static_field':
                db_static_fields.append(member)
        
        # Compare methods
        clang_method_names = {m['name'] for m in clang_members['methods']}
        db_method_names = {m.name for m in db_methods}
        
        # Check for missing methods
        missing_methods = clang_method_names - db_method_names
        for method_name in missing_methods:
            self.errors.append(f"Missing method in DB: {class_name}::{method_name}")
            self.stats['methods_missing'] += 1
            print(f"  {deco.red('Missing method')}: {method_name}")
            
        # Check for extra methods in DB
        extra_methods = db_method_names - clang_method_names
        for method_name in extra_methods:
            self.warnings.append(f"Extra method in DB: {class_name}::{method_name}")
            self.stats['methods_extra'] += 1
            print(f"  {deco.yellow('Extra method in DB')}: {method_name}")
            
        self.stats['methods_found'] += len(clang_method_names & db_method_names)
        
        # Check for overloads
        clang_method_sigs = defaultdict(list)
        for method in clang_members['methods']:
            clang_method_sigs[method['name']].append(method['signature'])
            
        db_method_sigs = defaultdict(list)
        for method in db_methods:
            db_method_sigs[method.name].append(method.signature or '')
            
        # Find overloaded methods
        for method_name, sigs in clang_method_sigs.items():
            if len(sigs) > 1:
                self.stats['overloads_detected'] += 1
                db_sigs = db_method_sigs.get(method_name, [])
                if len(db_sigs) != len(sigs):
                    self.errors.append(f"Overload count mismatch: {class_name}::{method_name} - Clang: {len(sigs)}, DB: {len(db_sigs)}")
                    print(f"  {deco.red('Overload mismatch')}: {method_name} - Clang: {len(sigs)}, DB: {len(db_sigs)}")
                else:
                    print(f"  {deco.cyan('Overloaded method')}: {method_name} ({len(sigs)} overloads)")
        
        # Compare fields
        clang_field_names = {f['name'] for f in clang_members['fields']}
        db_field_names = {f.name for f in db_fields}
        
        missing_fields = clang_field_names - db_field_names
        for field_name in missing_fields:
            # Find the field info
            field_info = next((f for f in clang_members['fields'] if f['name'] == field_name), None)
            if field_info:
                self.errors.append(f"Missing field in DB: {class_name}::{field_name} ({field_info['type']})")
                self.stats['fields_missing'] += 1
                print(f"  {deco.red('Missing field')}: {field_name} ({field_info['type']})")
                
        extra_fields = db_field_names - clang_field_names
        for field_name in extra_fields:
            self.warnings.append(f"Extra field in DB: {class_name}::{field_name}")
            self.stats['fields_extra'] += 1
            print(f"  {deco.yellow('Extra field in DB')}: {field_name}")
            
        self.stats['fields_found'] += len(clang_field_names & db_field_names)
        
        # Compare static fields
        clang_static_names = {f['name'] for f in clang_members['static_fields']}
        db_static_names = {f.name for f in db_static_fields}
        
        missing_static = clang_static_names - db_static_names
        for field_name in missing_static:
            field_info = next((f for f in clang_members['static_fields'] if f['name'] == field_name), None)
            if field_info:
                self.errors.append(f"Missing static field in DB: {class_name}::{field_name}")
                print(f"  {deco.red('Missing static field')}: {field_name}")
                
        # Check access levels for matching members
        for db_method in db_methods:
            clang_method = next((m for m in clang_members['methods'] if m['name'] == db_method.name), None)
            if clang_method:
                db_access = db_method.access_level.value
                clang_access = clang_method['access']
                if db_access != clang_access:
                    self.warnings.append(f"Access mismatch for {class_name}::{db_method.name}: DB={db_access}, Clang={clang_access}")
                    self.stats['access_mismatches'] += 1
    
    def validate_class(self, entity):
        """Validate a single class entity using Clang."""
        class_name = entity.short_name
        canonical_name = entity.canonical_name
        
        print(f"\n{deco.cyan('Checking class')}: {canonical_name}")
        self.stats['classes_checked'] += 1
        
        # Get locations for this class
        locations = entity.locations
        if not locations:
            self.warnings.append(f"No locations found for class: {class_name}")
            return
            
        # Get preprocessed source for the file containing class definition
        definition_location = None
        for loc in locations:
            if loc.location_type.value == 'definition':
                definition_location = loc
                break
        
        if not definition_location:
            # Use first location if no definition found
            definition_location = locations[0]
            
        # Get preprocessed source
        source_file = self.db.get_source_file(definition_location.file_path)
        if not source_file:
            self.warnings.append(f"No source file found for: {definition_location.file_path}")
            return
            
        preprocessed_source = source_file.get('preprocessed_source')
        if not preprocessed_source:
            # Fall back to raw source
            preprocessed_source = source_file.get('raw_source', '')
            print(f"  {deco.yellow('Warning')}: Using raw source instead of preprocessed")
            
        # Extract members using Clang
        clang_members = self.extract_class_members_with_clang(class_name, preprocessed_source)
        
        # Debug output
        if clang_members['all_members']:
            print(f"  {deco.green('Clang found')} {len(clang_members['all_members'])} members")
        
        # Compare with database
        self.compare_class_members(entity, clang_members)
    
    def run_validation(self, limit=None, stable=False):
        """Run validation on all classes in database."""
        print(f"{deco.green('=== Clang-Based Class Parsing Validation ===')}") 
        print(f"Database: {self.db.db_path}")
        
        # Get all class and struct entities
        classes = []
        for entity_type in ['class', 'struct']:
            entities = self.db.search_entities(
                entity_type=entity_type,
                limit=limit or 10000
            )
            classes.extend(entities)
        
        print(f"Found {len(classes)} classes/structs to validate")
        
        if limit:
            if stable:
                print(f"Limiting validation to first {limit} classes (stable selection)")
                classes = classes[:limit]
            else:
                import random
                print(f"Limiting validation to {limit} random classes for better coverage")
                classes = random.sample(classes, min(limit, len(classes)))
        
        # Validate each class
        for entity in classes:
            try:
                self.validate_class(entity)
            except Exception as e:
                self.errors.append(f"Error validating {entity.short_name}: {str(e)}")
                print(f"  {deco.red('Error')}: {str(e)}")
        
        # Print summary
        print(f"\n{deco.green('=== Validation Summary ===')}") 
        print(f"Classes checked: {self.stats['classes_checked']}")
        print(f"Methods found: {self.stats['methods_found']}")
        print(f"Methods missing: {self.stats['methods_missing']}")
        print(f"Methods extra: {self.stats['methods_extra']}")
        print(f"Fields found: {self.stats['fields_found']}")
        print(f"Fields missing: {self.stats['fields_missing']}")
        print(f"Fields extra: {self.stats['fields_extra']}")
        print(f"Overloaded methods detected: {self.stats['overloads_detected']}")
        print(f"Access level mismatches: {self.stats['access_mismatches']}")
        
        if self.errors:
            print(f"\n{deco.red(f'Errors ({len(self.errors)}):')}") 
            for error in self.errors[:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more")
                
        if self.warnings:
            print(f"\n{deco.yellow(f'Warnings ({len(self.warnings)}):')}") 
            for warning in self.warnings[:10]:  # Show first 10 warnings
                print(f"  - {warning}")
            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more")
        
        # Write detailed report
        report_path = Path("/tmp/clang_validation_report.json")
        report = {
            'stats': self.stats,
            'errors': self.errors,
            'warnings': self.warnings
        }
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nDetailed report written to: {report_path}")
        
        return len(self.errors) == 0

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validate C++ class parsing using Clang AST as ground truth'
    )
    parser.add_argument('--limit', type=int, 
                       help='Limit number of classes to check')
    parser.add_argument('--class', dest='class_name',
                       help='Check specific class only')
    parser.add_argument('--stable', action='store_true',
                       help='Use stable (non-random) class selection for reproducible results')
    
    args = parser.parse_args()
    
    # Get database path
    db_path = obt.path.stage() / "cpp_db_v2_orkid.db"
    
    if not db_path.exists():
        print(f"{deco.red(f'Database not found: {db_path}')}")
        print("Run ork.cpp.db.build.py first to build the database")
        sys.exit(1)
    
    # Run validation
    validator = ClangClassValidator(db_path)
    
    if args.class_name:
        # Validate specific class
        entities = validator.db.search_entities(name=args.class_name)
        if not entities:
            print(f"{deco.red(f'Class not found: {args.class_name}')}")
            sys.exit(1)
        
        for entity in entities:
            if entity.entity_type.value in ['class', 'struct']:
                validator.validate_class(entity)
    else:
        # Validate all classes
        success = validator.run_validation(limit=args.limit, stable=args.stable)
        sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()