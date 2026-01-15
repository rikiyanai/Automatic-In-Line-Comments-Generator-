#!/usr/bin/env python3
"""
Agent Logger.

This script logs agent actions (thoughts, code edits, reads) to a chronological JSONL file.
It serves as the "black box" recorder for the agent's session.
"""

import os
import json
import argparse
import time
from datetime import datetime

class AgentLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        self.log_file = os.path.join(self.log_dir, "AGENT_TRACE.jsonl")

    def log(self, event_type: str, content: str, meta: dict = None):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "timestamp_unix": time.time(),
            "type": event_type,
            "content": content,
            "meta": meta or {}
        }
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + "\n")
            
        print(f"Logged [{event_type}]: {content[:50]}...")

def main():
    parser = argparse.ArgumentParser(description="Log agent events.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # General Log (Thought)
    parser_log = subparsers.add_parser("log", help="Log a general event or thought")
    parser_log.add_argument("--type", "-t", default="thought", choices=["thought", "edit", "read", "hypothesis"], help="Event type")
    parser_log.add_argument("--content", "-c", required=True, help="Main content string")
    parser_log.add_argument("--meta", "-m", help="JSON string for metadata")

    # Convenience: Hypothesis
    parser_hyp = subparsers.add_parser("hypothesis", help="Log a hypothesis")
    parser_hyp.add_argument("--content", "-c", required=True, help="Hypothesis statement")
    
    # Convenience: Edit
    parser_edit = subparsers.add_parser("edit", help="Log a code edit")
    parser_edit.add_argument("--file", "-f", required=True, help="File edited")
    parser_edit.add_argument("--desc", "-d", required=True, help="Description of edit")
    
    args = parser.parse_args()
    logger = AgentLogger()

    if args.command == "log":
        meta = json.loads(args.meta) if args.meta else {}
        logger.log(args.type, args.content, meta)
        
    elif args.command == "hypothesis":
        logger.log("hypothesis", args.content)
        
    elif args.command == "edit":
        logger.log("edit", args.desc, {"file": args.file})

if __name__ == "__main__":
    main()
