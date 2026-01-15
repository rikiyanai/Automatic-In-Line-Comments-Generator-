#!/usr/bin/env python3
"""
Reference Linker.

This script scans `CURRENT_UNDERSTANDING.md` (or any text file) and 
scans the codebase to find definitions of mentioned terms.
It then replaces plain text like `MyClass` with `[MyClass](../src/MyClass.cpp#L10)`.
"""

import os
import re
import glob
import sys
import argparse

# Ensure we can import sibling
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)
import semantic_analyzer

class ReferenceLinker:
    def __init__(self, root_dir: str = "."):
        self.root_dir = root_dir
        self.symbol_map = {} # Name -> (File, Line)

    def build_symbol_map(self):
        """Scans C++ files to build a map of class/struct/function names."""
        ignore = ["third-party", "vendor", "build"]
        cpp_files = []
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in ignore and not d.startswith('.')]
            for f in files:
                if f.endswith(('.cpp', '.h', '.hpp')):
                    cpp_files.append(os.path.join(root, f))
        
        print(f"Indexing symbols from {len(cpp_files)} files...")
        
        for f_path in cpp_files:
            try:
                # Use our semantic analyzer
                with open(f_path, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()
                
                # We can reuse the tokenizer/parser logic, but specifically we want definitions
                # The semantic_analyzer.analyze_code returns variables. 
                # We might need to extend it or just do a quick regex scan for this 'linker' prototype
                # For robustness, let's use a simplified regex approach here 
                # as the semantic analyzer is focused on variables inside scopes.
                
                # Simple regex for Class/Struct/Function
                idx_regex = re.compile(r'^\s*(class|struct|enum)\s+(\w+)')
                lines = code.splitlines()
                for i, line in enumerate(lines):
                    if m := idx_regex.match(line):
                        name = m.group(2)
                        # Store relative path for markdown
                        rel_path = os.path.relpath(f_path, start=".")
                        self.symbol_map[name] = (rel_path, i + 1)
                        
            except Exception:
                continue
        print(f"Indexed {len(self.symbol_map)} symbols.")

    def link_file(self, target_file: str):
        if not os.path.exists(target_file):
            print(f"Target {target_file} not found.")
            return

        with open(target_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Naive replacement: specific enough to avoid replacing common words
        # Only replace if word boundary
        
        new_content = content
        for symbol, (path, line) in self.symbol_map.items():
            if len(symbol) < 4: continue # Skip short ones to avoid noise
            
            # Regex to find unlinked mentions: \bSymbol\b not preceded by [
            # This is tricky in regex, simpler:
            # We construct the link
            link = f"[{symbol}]({path}#L{line})"
            
            # If symbol present and not already part of a markdown link
            if symbol in new_content and link not in new_content:
                 # Very basic safety: only replace if surrounded by spaces or punctuation
                 # This is a 'dumb' linker but fits the MVP request
                 pattern = r'(?<!\[)\b' + re.escape(symbol) + r'\b'
                 new_content = re.sub(pattern, link, new_content)
                 
        if new_content != content:
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Linked symbols in {target_file}")
        else:
            print("No new links added.")

def main():
    linker = ReferenceLinker()
    linker.build_symbol_map()
    linker.link_file("CURRENT_UNDERSTANDING.md")

if __name__ == "__main__":
    main()
