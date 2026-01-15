#!/usr/bin/env python3
"""
Enhanced Comment Pattern Analyzer for Asciicker.

This script scans the codebase to "learn" how comments are currently written.
It categorizes comments into:
- Header Comments (File descriptions)
- Function Comments (API documentation)
- Variable Comments (Data definitions)
- Logic Comments (Control flow explanations)

Output is saved to `comment_patterns.json` for use by the generator.
"""

import os
import re
import glob
import json
import argparse
import sys
from collections import defaultdict
from typing import Dict, List, Any

# Regex patterns for C++ constructs
RE_FUNC_START = re.compile(r'^([\w:]+)\s+([\w]+)\s*\([^)]*\)\s*{')
RE_VAR_DECL = re.compile(r'^\s*(static\s+|const\s+)?([\w:<>\*&]+)\s+(\w+)(\[[^\]]+\])?(?:\s*=\s*[^;]+)?;')
RE_CONTROL_FLOW = re.compile(r'^\s*(if|for|while|switch|else)\s*\(?')
RE_STRUCT_CLASS = re.compile(r'^\s*(struct|class|enum)\s+(\w+)')

class PatternLearner:
    def __init__(self):
        self.patterns = {
            "header": [],
            "function": [],
            "variable": defaultdict(list),  # Keyed by basic type (int, float, etc.)
            "control_flow": defaultdict(list), # Keyed by keyword (if, for)
            "data_structures": [],
            "general": []
        }
        self.stats = {
            "files_scanned": 0,
            "comments_found": 0
        }

    def analyze_file(self, file_path: str):
        self.stats["files_scanned"] += 1
        try:
            # Robust file reading
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='latin-1') as f:
                    lines = f.readlines()
        except Exception as e:
            # print(f"Error reading {file_path}: {e}")
            return

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 1. Block Comments (/** ... */)
            if line.startswith('/*'):
                comment_block = []
                while i < len(lines):
                    l_strip = lines[i].strip()
                    comment_block.append(l_strip)
                    if '*/' in l_strip:
                        break
                    i += 1
                self._classify_block_comment(comment_block, lines, i + 1)
            
            # 2. Inline Comments (// ...)
            elif '//' in line:
                self._classify_inline_comment(line, lines, i)
            
            i += 1

    def _classify_block_comment(self, comment_block: List[str], all_lines: List[str], next_line_idx: int):
        self.stats["comments_found"] += 1
        full_text = "\n".join(comment_block)
        
        # Check context immediately following the comment
        next_code_line = ""
        for j in range(next_line_idx, min(len(all_lines), next_line_idx + 5)):
            clean = all_lines[j].strip()
            if clean and not clean.startswith('//') and not clean.startswith('/*'):
                next_code_line = clean
                break

        if "@file" in full_text or next_line_idx < 10:
            self.patterns["header"].append(full_text)
        elif RE_FUNC_START.match(next_code_line):
            self.patterns["function"].append({
                "comment": full_text,
                "signature": next_code_line
            })
        elif RE_STRUCT_CLASS.match(next_code_line):
             self.patterns["data_structures"].append({
                "comment": full_text,
                "struct": next_code_line
            })
        else:
             self.patterns["general"].append(full_text)

    def _classify_inline_comment(self, line: str, all_lines: List[str], line_idx: int):
        self.stats["comments_found"] += 1
        parts = line.split('//', 1)
        code_part = parts[0].strip()
        comment_part = parts[1].strip()

        if not comment_part: return

        # Case A: Comment on its own line -> look at next line
        if not code_part:
            next_code_line = ""
            for j in range(line_idx + 1, min(len(all_lines), line_idx + 5)):
                clean = all_lines[j].strip()
                if clean and not clean.startswith('//'):
                    next_code_line = clean
                    break
            
            # Logic flow?
            if m := RE_CONTROL_FLOW.match(next_code_line):
                self.patterns["control_flow"][m.group(1)].append(comment_part)
            # Function?
            elif RE_FUNC_START.match(next_code_line):
                self.patterns["function"].append({"comment": comment_part, "signature": next_code_line})
            else:
                self.patterns["general"].append(comment_part)
            return

        # Case B: End-of-line comment
        # Variable declaration?
        if m := RE_VAR_DECL.match(code_part):
            var_type = m.group(2)
            self.patterns["variable"][var_type].append(comment_part)
        elif m := RE_CONTROL_FLOW.match(code_part):
            self.patterns["control_flow"][m.group(1)].append(comment_part)
        else:
             self.patterns["general"].append(comment_part)

    def save_report(self, output_path: str):
        # Convert defaultdicts to dicts for JSON serialization
        out_patterns = {
            "header": self.patterns["header"],
            "function": self.patterns["function"],
            "variable": dict(self.patterns["variable"]),
            "control_flow": dict(self.patterns["control_flow"]),
            "data_structures": self.patterns["data_structures"],
            "stats": self.stats
        }
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(out_patterns, f, indent=2)
            print(f"Learned patterns saved to {output_path}")
            print(f"Scanned {self.stats['files_scanned']} files, found {self.stats['comments_found']} comments.")
        except Exception as e:
            print(f"Error saving report to {output_path}: {e}")

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
    parser = argparse.ArgumentParser(description="Learn comment patterns from existing C++ code.")
    parser.add_argument("--source", "-s", default=".", help="Root directory to scan (default: current dir)")
    parser.add_argument("--output", "-o", help="Output JSON file path (default: scripts/comment_patterns.json)")
    parser.add_argument("--exclude", "-e", default="third-party,vendor,build,scripts", help="Comma-separated folders to exclude")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print detailed logs")
    
    args = parser.parse_args()
    
    source_dir = os.path.abspath(args.source)
    if not os.path.isdir(source_dir):
        print(f"Error: Source directory '{source_dir}' does not exist.")
        sys.exit(1)
        
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = args.output if args.output else os.path.join(script_dir, "comment_patterns.json")
    excludes = [e.strip() for e in args.exclude.split(',')]
    
    learner = PatternLearner()
    files = get_cpp_files(source_dir, excludes)
    
    if not files:
        print("No C++ files found to scan.")
        sys.exit(0)
        
    print(f"Scanning {len(files)} files...")
    for f in files:
        if args.verbose: print(f"Scanning {f}")
        learner.analyze_file(f)
    
    learner.save_report(output_path)

if __name__ == "__main__":
    main()
