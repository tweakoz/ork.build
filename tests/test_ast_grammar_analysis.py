#!/usr/bin/env python3
"""
Test AST Grammar Analysis - Foundational test for tree-sitter-cpp AST pattern discovery
Analyze N unique random classes/structs from the C++ database
Build AST grammar incrementally while analyzing each class
Usage: python3 test_ast_grammar_analysis.py [count] (default: 50)
"""

import sys
import random
import subprocess
from pathlib import Path
from collections import defaultdict, Counter
import re
import argparse
import tempfile

# Add obt to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import obt.path
from obt.cpp_database_v2 import CppDatabaseV2

class ASTGrammarBuilder:
    def __init__(self):
        self.node_types = Counter()
        self.parent_child_rules = defaultdict(Counter)  # parent_type -> {child_type: count}
        self.field_list_children = Counter()  # what appears in field_declaration_list
        self.conditional_layouts = defaultdict(lambda: defaultdict(Counter))  # context -> parent -> child
        self.patterns = defaultdict(list)  # specific patterns found
        self.class_examples = {}  # node_type -> example class
        self.grammar_rules = defaultdict(set)  # structured grammar rules
        
    def analyze_ast_output(self, class_name, ast_text):
        """Parse AST output and build grammar incrementally with conditional layouts"""
        lines = ast_text.split('\n')
        
        # Build hierarchical structure
        node_stack = []  # [(node_type, indent_level), ...]
        
        for line in lines:
            # Skip non-AST lines (empty lines, headers, separators, class instance headers)
            if (not line.strip() or '=' in line or 'File:' in line or 'Source size:' in line or 
                'Found' in line or '(instance #' in line or 'AST Format:' in line or 'Coordinates:' in line):
                continue
            
            # Extract node type from the colored AST output (ANSI escape sequences)
            # Format: \x1b[38;5;51mnode_type\x1b[m with optional indentation
            if '\x1b[38;5;51m' in line and '\x1b[m' in line:
                # Extract node type between ANSI color codes
                match = re.search(r'\x1b\[38;5;51m(\w+)\x1b\[m', line)
                if not match:
                    continue
                    
                node_type = match.group(1).strip()
            else:
                continue
                
            if not node_type:
                continue
                
            # Count this node type
            self.node_types[node_type] += 1
            
            # Record first example
            if node_type not in self.class_examples:
                self.class_examples[node_type] = class_name
            
            # Calculate current indent level
            indent_level = (len(line) - len(line.lstrip())) // 2
            
            # Pop nodes that are no longer parents (same or less indent)
            while node_stack and node_stack[-1][1] >= indent_level:
                node_stack.pop()
            
            # If we have a parent, record the parent-child relationship
            if node_stack:
                parent_type = node_stack[-1][0]
                self.parent_child_rules[parent_type][node_type] += 1
                
                # Special context for field_declaration_list
                if parent_type == 'field_declaration_list':
                    self.field_list_children[node_type] += 1
                    
                    # Record conditional patterns within field_declaration_list
                    if node_type == 'function_definition' and ('= 0' in line or 'pure_virtual_clause' in ast_text):
                        self.patterns['pure_virtual_in_field_list'].append(class_name)
                    
            # Add current node to stack
            node_stack.append((node_type, indent_level))
                
    def _analyze_field_list_children(self, lines, class_name):
        """Analyze what appears inside field_declaration_list"""
        in_field_list = False
        field_list_indent = 0
        
        for line in lines:
            if 'field_declaration_list' in line:
                in_field_list = True
                field_list_indent = (len(line) - len(line.lstrip())) // 2
                continue
                
            if in_field_list:
                current_indent = (len(line) - len(line.lstrip())) // 2
                
                # If we've gone back to same level or less, we're out of field_list
                if current_indent <= field_list_indent and line.strip():
                    in_field_list = False
                    continue
                    
                # If this is a direct child of field_declaration_list
                if current_indent == field_list_indent + 1:
                    match = re.search(r'\[38;5;51m([^[]*?)\[m', line)
                    if match:
                        child_type = match.group(1).strip()
                        if child_type and child_type not in ['{', '}', ':']:
                            self.field_list_children[child_type] += 1
                            
                            # Record interesting patterns
                            if child_type == 'function_definition':
                                if '= 0' in ' '.join(lines):
                                    self.patterns['pure_virtual_methods'].append(class_name)
                                if 'delete' in ' '.join(lines):
                                    self.patterns['deleted_methods'].append(class_name)
                                    
    def print_summary(self):
        """Print comprehensive grammar summary"""
        print("\n" + "="*80)
        print("COMPREHENSIVE C++ AST GRAMMAR FROM RANDOM CLASSES")
        print("="*80)
        
        print(f"\n📊 GRAMMAR STATISTICS:")
        print(f"   Node types discovered: {len(self.node_types)}")
        print(f"   Total nodes analyzed: {sum(self.node_types.values())}")
        print(f"   Parent-child rules: {len(self.parent_child_rules)}")
        
        print(f"\n🏗️  FIELD_DECLARATION_LIST GRAMMAR (Critical for Parser):")
        print("   field_declaration_list can contain:")
        for child_type, count in self.field_list_children.most_common():
            if child_type not in ['{', '}']:  # Skip structural braces
                example = self.class_examples.get(child_type, "unknown")
                print(f"     {child_type:<25} ({count:>3}x) - e.g., {example}")
        
        print(f"\n🔍 TOP PARENT-CHILD GRAMMAR RULES:")
        for parent, children in list(self.parent_child_rules.items())[:10]:
            print(f"   {parent} →")
            for child, count in children.most_common(3):  # Top 3 children for each parent
                print(f"     ├─ {child} ({count}x)")
                
        print(f"\n⚡ CONDITIONAL PATTERNS:")
        for pattern_type, examples in self.patterns.items():
            if examples:
                print(f"   {pattern_type}: {', '.join(examples[:3])}")
                
        print(f"\n📋 PARSER IMPLEMENTATION REQUIREMENTS:")
        print("   ✅ Currently handled: field_declaration, access_specifier")
        print("   ❌ MISSING critical handlers:")
        
        critical_missing = []
        for child_type, count in self.field_list_children.most_common():
            if child_type not in ['field_declaration', 'access_specifier', '{', '}', ':']:
                critical_missing.append(f"      {child_type:<20} ({count:>3} occurrences)")
                
        for missing in critical_missing[:8]:  # Top 8 missing
            print(missing)
            
        print(f"\n🎯 GRAMMAR-BASED PARSER STRUCTURE NEEDED:")
        print("   def _extract_class_members(self, ...field_declaration_list...):")
        print("     for child in field_list.children:")
        for child_type, count in self.field_list_children.most_common(6):
            if child_type not in ['{', '}', ':', 'access_specifier']:
                print(f"       elif child.type == '{child_type}': # {count} occurrences")
                print(f"         member = self._extract_{child_type.replace('-', '_')}(child, ...)")
        print("         # ... etc")

def get_all_classes_structs(db_path):
    """Get all unique class and struct names from database"""
    db = CppDatabaseV2(db_path)
    
    with db.connect() as conn:
        cursor = conn.execute("""
            SELECT DISTINCT short_name, entity_type 
            FROM entities 
            WHERE entity_type IN ('class', 'struct')
            ORDER BY short_name
        """)
        results = cursor.fetchall()
    
    return [(row[0], row[1]) for row in results]

def run_ast_dump(class_name):
    """Run AST dump tool on a class and return the output"""
    # Use relative path from ork.build project root
    astdump_tool = Path(__file__).parent.parent / "obt.project" / "bin" / "ork.cpp.db.astdump.py"
    
    try:
        result = subprocess.run([
            str(astdump_tool),
            '--cls', class_name
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return result.stdout
        else:
            return f"ERROR: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "ERROR: Timeout"
    except Exception as e:
        return f"ERROR: {str(e)}"

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description='Analyze N random classes/structs for AST patterns')
    parser.add_argument('count', nargs='?', default=50, type=int, help='Number of classes to analyze (default: 50)')
    args = parser.parse_args()
    
    count = args.count
    
    # Get database path
    db_path = obt.path.stage() / "cpp_db_v2_orkid.db"
    
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        sys.exit(1)
    
    print("Getting all classes and structs from database...")
    all_classes = get_all_classes_structs(db_path)
    print(f"Found {len(all_classes)} total classes/structs")
    
    # Randomly select N unique classes
    if len(all_classes) < count:
        print(f"Warning: Only {len(all_classes)} classes available, using all of them")
        selected_classes = all_classes
    else:
        selected_classes = random.sample(all_classes, count)
    
    print(f"Selected {len(selected_classes)} classes for analysis")
    
    # Initialize grammar builder
    grammar_builder = ASTGrammarBuilder()
    
    # Output file in temp directory (only hard coded path allowed per requirements)
    with tempfile.NamedTemporaryFile(mode='w', suffix='_ast_analysis.txt', prefix=f'{count}_classes_', delete=False) as f:
        output_file = Path(f.name)
        
        f.write(f"# AST Analysis of {count} Unique Random Classes/Structs\n")
        f.write("# Generated by test_ast_grammar_analysis.py\n")
        f.write(f"# Total classes in database: {len(all_classes)}\n")
        f.write(f"# Selected for analysis: {len(selected_classes)}\n")
        f.write("\n" + "="*100 + "\n\n")
        
        for i, (class_name, entity_type) in enumerate(selected_classes, 1):
            print(f"Analyzing {i}/{len(selected_classes)}: {entity_type} {class_name}")
            
            f.write(f"## CLASS {i}/{count}: {entity_type} {class_name}\n")
            f.write("="*80 + "\n\n")
            
            # Get AST dump
            ast_output = run_ast_dump(class_name)
            f.write(ast_output)
            f.write("\n\n" + "="*100 + "\n\n")
            
            # BUILD GRAMMAR INCREMENTALLY HERE!
            grammar_builder.analyze_ast_output(class_name, ast_output)
            
            # Flush to disk periodically
            if i % 10 == 0:
                f.flush()
                print(f"Completed {i}/{len(selected_classes)} classes")
    
    print(f"\nRaw analysis written to: {output_file}")
    
    # PRINT COMPREHENSIVE GRAMMAR ANALYSIS
    grammar_builder.print_summary()

if __name__ == '__main__':
    # Set random seed for reproducibility
    random.seed(42)
    main()