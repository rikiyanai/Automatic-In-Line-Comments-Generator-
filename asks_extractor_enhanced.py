#!/usr/bin/env python3
"""
Advanced Comment Generator for Asciicker.

This script combines:
1. Semantic Analysis (parse code structure)
2. Pattern Matching (learn from existing comments)
3. Domain Knowledge (dictionary of Asciicker terms)

To generate context-aware comments for undocumented code.
"""

import os
import json
import glob
import argparse
import sys
from typing import List, Dict, Optional

# --- Import Custom Modules ---
# Ensure we can find sibling modules even if running from elsewhere
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

try:
    import semantic_analyzer
    from semantic_analyzer import VariableInfo
except ImportError as e:
    print(f"Error: Could not import semantic_analyzer. Make sure it is in {script_dir}")
    sys.exit(1)

# --- Domain Knowledge ---

DOMAIN_DICTIONARY = {}

# Load domain dictionary from JSON if available
domain_file = os.path.join(script_dir, "domain.json")
if os.path.exists(domain_file):
    try:
        with open(domain_file, 'r', encoding='utf-8') as f:
            DOMAIN_DICTIONARY = json.load(f)
    except Exception as e:
        print(f"Warning: Error loading domain.json: {e}. Proceeding with empty domain knowledge.")

OPERATOR_DESCRIPTIONS = {
    "&": "Bitwise MASK",
    "|": "Bitwise MERGE",
    "<<": "Bitwise SHIFT LEFT",
    ">>": "Bitwise SHIFT RIGHT",
    "%": "Modulo / Wrap Around"
}

# --- Generation Logic ---

class CommentGenerator:
    def __init__(self, pattern_filename: str = "comment_patterns.json"):
        self.patterns = {}
        # Look for pattern file in script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        pattern_path = os.path.join(script_dir, pattern_filename)
        
        if os.path.exists(pattern_path):
            try:
                with open(pattern_path, 'r', encoding='utf-8') as f:
                    self.patterns = json.load(f)
            except Exception as e:
                 print(f"Warning: Failed to load patterns from {pattern_path}: {e}")
        else:
            # Silent warning if using defaults, usually fine
            pass

    def generate_for_var(self, var: VariableInfo) -> Optional[str]:
        """Generate a comment for a variable declaration."""
        
        # 1. Dictionary Lookup (Highest Priority)
        # Check specific values
        if var.value and var.value.strip() in DOMAIN_DICTIONARY:
            desc = DOMAIN_DICTIONARY[var.value.strip()]
            return f"// {desc}"
            
        # Check variable name parts
        name_lower = var.name.lower()
        # Sort keys by length desc to match longest terms first
        sorted_keys = sorted(DOMAIN_DICTIONARY.keys(), key=len, reverse=True)
        
        for key in sorted_keys:
            desc = DOMAIN_DICTIONARY[key]
            if key.isdigit(): continue
            
            # For short keys (<3 chars), require exact match or word boundary (simplified)
            if len(key) < 3:
                if key == name_lower or f"_{key}" in name_lower or f"{key}_" in name_lower:
                     return f"// {desc} ({var.name})"
            # For longer keys, allow containment
            elif key in name_lower:
                 return f"// {desc} ({var.name})"

        # 2. Pattern Matching (Learned from codebase)
        # Check if we have learned patterns for this type
        if "variable" in self.patterns:
            type_patterns = self.patterns["variable"].get(var.type, [])
            if type_patterns:
                # Naive: return the most common comment for this type
                from collections import Counter
                most_common = Counter(type_patterns).most_common(1)
                if most_common:
                    return f"// {most_common[0][0]} (Suggested)"

        # 3. Heuristic / Type Analysis
        if "flags" in name_lower or "mask" in name_lower:
            return "// Bitmask configuration"
        
        if var.type.startswith("uint") and "[" in var.type: # Array
             return f"// Buffer for {var.name}"
             
        if var.value and any(op in var.value for op in OPERATOR_DESCRIPTIONS):
            for op, desc in OPERATOR_DESCRIPTIONS.items():
                if op in var.value:
                    return f"// {desc} operation"

        return None

    def analyze_file(self, file_path: str) -> List[str]:
        suggestions = []
        try:
            # Robust file reading with encoding fallback
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='latin-1') as f:
                    code = f.read()
            
            # Use Phase 2 Semantic Analyzer
            extracted_vars = semantic_analyzer.analyze_code(code)
            
            for var in extracted_vars:
                # Only suggest if no comment exists? 
                # Our parser doesn't return line comments yet, but we can check the line in raw code
                # For now, let's just generate all suggestions for review
                comment = self.generate_for_var(var)
                if comment:
                    suggestions.append(f"Line {var.line}: {var.type} {var.name} {f'= {var.value}' if var.value else ''};  {comment}")
                    
        except Exception as e:
            suggestions.append(f"Error analyzing {file_path}: {e}")
            
        return suggestions

def get_cpp_files(source_dir: str, excludes: List[str]) -> List[str]:
    cpp_files = []
    for root, dirs, files in os.walk(source_dir):
        # Filter directories in place
        dirs[:] = [d for d in dirs if d not in excludes and not d.startswith('.')]
        
        for file in files:
            if file.endswith('.cpp') or file.endswith('.h') or file.endswith('.hpp'):
                cpp_files.append(os.path.join(root, file))
    return cpp_files

def main():
    parser = argparse.ArgumentParser(description="Generate comment suggestions for C++ code.")
    parser.add_argument("--source", "-s", default=".", help="Root directory to scan (default: current dir)")
    parser.add_argument("--output", "-o", help="Output report file path (default: scripts/comment_suggestions_report.md)")
    parser.add_argument("--exclude", "-e", default="third-party,vendor,build,scripts", help="Comma-separated folders to exclude")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print detailed logs")
    
    args = parser.parse_args()
    
    # Path handling
    source_dir = os.path.abspath(args.source)
    if not os.path.isdir(source_dir):
        print(f"Error: Source directory '{source_dir}' does not exist.")
        sys.exit(1)
        
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = args.output if args.output else os.path.join(script_dir, "comment_suggestions_report.md")
    excludes = [e.strip() for e in args.exclude.split(',')]
    
    if args.verbose:
        print(f"Scanning {source_dir}")
        print(f"Excluding: {excludes}")
        print(f"Domain Dictionary loaded: {len(DOMAIN_DICTIONARY)} items")

    generator = CommentGenerator()
    
    files = get_cpp_files(source_dir, excludes)
    
    if not files:
        print("No C++ files found to analyze.")
        sys.exit(0)
    
    report_lines = ["# Comment Suggestions Report\n"]
    
    count = 0
    errors = 0
    for f in files:
        if args.verbose:
            print(f"Analyzing {f}...")
            
        suggs = generator.analyze_file(f)
        if suggs:
            # Check for error messages in suggestions
            has_error = any(s.startswith("Error analyzing") for s in suggs)
            if has_error:
                errors += 1
                if args.verbose: print(f"  -> Error in {f}")
            else:
                report_lines.append(f"\n## File: `{f}`")
                report_lines.extend(suggs)
                count += len(suggs)
            
    with open(output_path, "w", encoding='utf-8') as f:
        f.write("\n".join(report_lines))
        
    print(f"Generated {count} suggestions in {output_path}")
    if errors > 0:
        print(f"Encountered errors in {errors} files (use --verbose to see details).")

if __name__ == "__main__":
    main()
