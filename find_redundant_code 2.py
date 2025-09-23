#!/usr/bin/env python3
"""
Comprehensive Redundant Code Detection Tool
Finds duplicate functions, methods, and similar code patterns that cause bugs.
"""

import os
import re
import ast
import difflib
from collections import defaultdict
from typing import Dict, List, Set, Tuple
import argparse

class RedundantCodeDetector:
    def __init__(self, root_dir: str = "."):
        self.root_dir = root_dir
        self.python_files = []
        self.functions = defaultdict(list)  # function_name -> [(file, line, signature)]
        self.classes = defaultdict(list)    # class_name -> [(file, line)]
        self.methods = defaultdict(list)    # method_name -> [(file, class, line, signature)]
        
    def scan_directory(self):
        """Find all Python files in directory"""
        print(f"🔍 Scanning directory: {self.root_dir}")
        for root, dirs, files in os.walk(self.root_dir):
            # Skip common cache and build directories
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', 'build', 'dist']]
            
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    self.python_files.append(filepath)
        
        print(f"📁 Found {len(self.python_files)} Python files")
        return self.python_files
    
    def extract_functions_and_methods(self, filepath: str):
        """Extract function and method signatures from a Python file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            relative_path = os.path.relpath(filepath, self.root_dir)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Get function signature
                    args = [arg.arg for arg in node.args.args]
                    defaults = len(node.args.defaults)
                    signature = f"def {node.name}({', '.join(args)})"
                    
                    self.functions[node.name].append({
                        'file': relative_path,
                        'line': node.lineno,
                        'signature': signature,
                        'args': args,
                        'defaults': defaults,
                        'full_signature': ast.unparse(node) if hasattr(ast, 'unparse') else signature
                    })
                
                elif isinstance(node, ast.ClassDef):
                    class_name = node.name
                    self.classes[class_name].append({
                        'file': relative_path,
                        'line': node.lineno
                    })
                    
                    # Extract methods from this class
                    for child in node.body:
                        if isinstance(child, ast.FunctionDef):
                            method_args = [arg.arg for arg in child.args.args]
                            method_signature = f"def {child.name}({', '.join(method_args)})"
                            
                            self.methods[child.name].append({
                                'file': relative_path,
                                'class': class_name,
                                'line': child.lineno,
                                'signature': method_signature,
                                'args': method_args,
                                'full_signature': ast.unparse(child) if hasattr(ast, 'unparse') else method_signature
                            })
        
        except Exception as e:
            print(f"⚠️  Error parsing {filepath}: {e}")
    
    def find_duplicate_functions(self) -> Dict[str, List]:
        """Find functions with same name in multiple files"""
        duplicates = {}
        
        for func_name, occurrences in self.functions.items():
            if len(occurrences) > 1:
                duplicates[func_name] = occurrences
        
        return duplicates
    
    def find_duplicate_methods(self) -> Dict[str, List]:
        """Find methods with same name in multiple classes/files"""
        duplicates = {}
        
        for method_name, occurrences in self.methods.items():
            if len(occurrences) > 1:
                # Group by signature to find true duplicates
                signature_groups = defaultdict(list)
                for occ in occurrences:
                    key = f"{method_name}({len(occ['args'])} args)"
                    signature_groups[key].append(occ)
                
                # Only report if multiple files have same method signature
                for sig_key, group in signature_groups.items():
                    if len(group) > 1:
                        duplicates[f"{method_name} ({sig_key})"] = group
        
        return duplicates
    
    def find_similar_signatures(self, threshold: float = 0.8) -> List[Tuple]:
        """Find functions/methods with very similar signatures"""
        similar = []
        
        all_items = []
        
        # Collect all functions
        for func_name, occurrences in self.functions.items():
            for occ in occurrences:
                all_items.append(('function', func_name, occ))
        
        # Collect all methods  
        for method_name, occurrences in self.methods.items():
            for occ in occurrences:
                all_items.append(('method', method_name, occ))
        
        # Compare all pairs
        for i, (type1, name1, occ1) in enumerate(all_items):
            for type2, name2, occ2 in all_items[i+1:]:
                # Skip exact duplicates (handled elsewhere)
                if name1 == name2:
                    continue
                
                # Compare signatures
                sig1 = occ1['signature']
                sig2 = occ2['signature']
                
                similarity = difflib.SequenceMatcher(None, sig1, sig2).ratio()
                
                if similarity >= threshold:
                    similar.append((
                        f"{type1}: {name1} in {occ1['file']}:{occ1['line']}",
                        f"{type2}: {name2} in {occ2['file']}:{occ2['line']}",
                        similarity,
                        sig1,
                        sig2
                    ))
        
        return sorted(similar, key=lambda x: x[2], reverse=True)
    
    def find_commented_duplicates(self) -> List[Tuple]:
        """Find commented-out functions that might be duplicates"""
        commented_functions = []
        
        for filepath in self.python_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                relative_path = os.path.relpath(filepath, self.root_dir)
                in_comment_block = False
                
                for i, line in enumerate(lines):
                    # Check for commented function definitions
                    if re.search(r'^\s*#\s*def\s+(\w+)', line):
                        func_match = re.search(r'^\s*#\s*def\s+(\w+)\s*\(', line)
                        if func_match:
                            func_name = func_match.group(1)
                            
                            # Check if this function exists elsewhere
                            if func_name in self.functions:
                                commented_functions.append((
                                    relative_path,
                                    i + 1,
                                    func_name,
                                    line.strip(),
                                    len(self.functions[func_name])
                                ))
            
            except Exception as e:
                print(f"⚠️  Error reading {filepath}: {e}")
        
        return commented_functions
    
    def generate_report(self):
        """Generate comprehensive redundant code report"""
        print("\n" + "="*80)
        print("🔍 REDUNDANT CODE DETECTION REPORT")
        print("="*80)
        
        # 1. Duplicate Functions
        duplicate_funcs = self.find_duplicate_functions()
        if duplicate_funcs:
            print(f"\n📋 DUPLICATE FUNCTIONS ({len(duplicate_funcs)} found)")
            print("-" * 50)
            for func_name, occurrences in duplicate_funcs.items():
                print(f"\n🔴 Function '{func_name}' appears in {len(occurrences)} files:")
                for occ in occurrences:
                    print(f"   📁 {occ['file']}:{occ['line']} - {occ['signature']}")
                    if occ.get('full_signature'):
                        print(f"      Full: {occ['full_signature'][:100]}...")
        else:
            print("\n✅ No duplicate functions found")
        
        # 2. Duplicate Methods
        duplicate_methods = self.find_duplicate_methods()
        if duplicate_methods:
            print(f"\n📋 DUPLICATE METHODS ({len(duplicate_methods)} found)")
            print("-" * 50)
            for method_key, occurrences in duplicate_methods.items():
                print(f"\n🟡 Method '{method_key}' appears in {len(occurrences)} classes:")
                for occ in occurrences:
                    print(f"   📁 {occ['file']}:{occ['line']} in class {occ['class']} - {occ['signature']}")
        else:
            print("\n✅ No duplicate methods found")
        
        # 3. Similar Signatures  
        similar_sigs = self.find_similar_signatures()
        if similar_sigs:
            print(f"\n📋 SIMILAR SIGNATURES ({len(similar_sigs)} found)")
            print("-" * 50)
            for item1, item2, similarity, sig1, sig2 in similar_sigs[:10]:  # Top 10
                print(f"\n🟠 {similarity:.2%} similarity:")
                print(f"   {item1}")
                print(f"   {item2}")
                print(f"   Sig1: {sig1}")
                print(f"   Sig2: {sig2}")
        else:
            print("\n✅ No similar signatures found")
        
        # 4. Commented Duplicates
        commented_dupes = self.find_commented_duplicates()
        if commented_dupes:
            print(f"\n📋 COMMENTED-OUT DUPLICATES ({len(commented_dupes)} found)")
            print("-" * 50)
            for filepath, line_num, func_name, line_content, active_count in commented_dupes:
                print(f"\n🔵 {filepath}:{line_num}")
                print(f"   Commented: {line_content}")
                print(f"   Active versions: {active_count} (in {', '.join([occ['file'] for occ in self.functions[func_name]])})")
        else:
            print("\n✅ No commented-out duplicates found")
        
        # 5. Summary Statistics
        print(f"\n📊 SUMMARY STATISTICS")
        print("-" * 30)
        print(f"📁 Files scanned: {len(self.python_files)}")
        print(f"🔧 Total functions: {sum(len(occs) for occs in self.functions.values())}")
        print(f"🔧 Unique function names: {len(self.functions)}")
        print(f"🏗️  Total methods: {sum(len(occs) for occs in self.methods.values())}")
        print(f"🏗️  Unique method names: {len(self.methods)}")
        print(f"🔴 Functions with duplicates: {len(duplicate_funcs)}")
        print(f"🟡 Methods with duplicates: {len(duplicate_methods)}")
        print(f"🟠 Similar signature pairs: {len(similar_sigs)}")
        print(f"🔵 Commented duplicates: {len(commented_dupes)}")
    
    def run_analysis(self):
        """Run complete redundant code analysis"""
        self.scan_directory()
        
        print("🔍 Analyzing Python files...")
        for filepath in self.python_files:
            self.extract_functions_and_methods(filepath)
        
        self.generate_report()

def main():
    parser = argparse.ArgumentParser(description="Find redundant code in Python codebase")
    parser.add_argument("--dir", default=".", help="Directory to scan (default: current)")
    parser.add_argument("--similarity", type=float, default=0.8, help="Similarity threshold for signatures (default: 0.8)")
    
    args = parser.parse_args()
    
    detector = RedundantCodeDetector(args.dir)
    detector.run_analysis()

if __name__ == "__main__":
    main()