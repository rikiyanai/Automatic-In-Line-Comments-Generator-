#!/usr/bin/env python3
"""
Unified Agent Hook.

This script acts as the primary "nervous system" hook for agents working on this repo.
When an agent (or user) runs this, it:
1. Logs the thought/event.
2. Updates the global understanding.
3. specific links references back to code.

Usage:
  python scripts/agent_hook.py "I am refactoring the renderer."
  python scripts/agent_hook.py --hypothesis "The issue might be in the Z-buffer."
"""

import os
import sys
import argparse
import subprocess

def run_script(script_name, args):
    """Runs a sibling script via subprocess."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, script_name)
    
    cmd = [sys.executable, script_path] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error running {script_name}:")
        print(result.stderr)
        return False
    
    # Optional: Print stdout if verbose
    # print(result.stdout)
    return True

def main():
    parser = argparse.ArgumentParser(description="Unified Agent Ops Hook")
    parser.add_argument("content", nargs="?", help="The thought or content to log")
    parser.add_argument("--hypothesis", "-H", help="Log as a hypothesis instead of generic thought")
    parser.add_argument("--edit", "-e", help="Log as an edit (requires description)")
    parser.add_argument("--file", "-f", help="File associated with edit")
    
    args = parser.parse_args()
    
    # 1. Logging Phase
    log_args = []
    if args.hypothesis:
        log_args = ["hypothesis", "--content", args.hypothesis]
    elif args.edit and args.file:
        log_args = ["edit", "--file", args.file, "--desc", args.edit]
    elif args.content:
        log_args = ["log", "--content", args.content]
    else:
        # If no args, just run tracker/linker (maintenance mode)
        print("No content provided. Running maintenance (Tracker + Linker)...")
    
    if log_args:
        print(f"-> Logging event...")
        if not run_script("agent_logger.py", log_args):
            print("Failed to log event.")
            sys.exit(1)

    # 2. Key Knowledge Phase
    print(f"-> Updating Knowledge Tracker...")
    if not run_script("knowledge_tracker.py", []):
        print("Failed to update knowledge.")

    # 3. Context Linking Phase
    print(f"-> Linking References...")
    if not run_script("reference_linker.py", []):
        print("Failed to link references.")
        
    print("Done. Agent state synced.")

if __name__ == "__main__":
    main()
