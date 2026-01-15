#!/usr/bin/env python3
"""
Knowledge Tracker.

This script processes the `AGENT_TRACE.jsonl` log and synthesizes a
"Current Understanding" document. It aggregates hypotheses to track
the agent's evolving mental model.
"""

import os
import json
import argparse
from typing import List, Dict

class KnowledgeTracker:
    def __init__(self, log_dir: str = "logs"):
        self.log_file = os.path.join(log_dir, "AGENT_TRACE.jsonl")
        self.output_file = "CURRENT_UNDERSTANDING.md"

    def read_logs(self) -> List[Dict]:
        if not os.path.exists(self.log_file):
            return []
        
        entries = []
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        entries.append(json.loads(line))
                    except: 
                        pass
        return entries

    def generate_report(self):
        entries = self.read_logs()
        if not entries:
            print("No logs found.")
            return

        hypotheses = [e for e in entries if e['type'] == 'hypothesis']
        recent_thoughts = [e for e in entries if e['type'] == 'thought'][-10:] # Last 10
        edits = [e for e in entries if e['type'] == 'edit']
        
        lines = ["# Current Agent Understanding\n"]
        
        # 1. Active Hypotheses
        lines.append("## Active Hypotheses")
        if hypotheses:
            for i, h in enumerate(reversed(hypotheses)): # Newest first
                ts = h.get('timestamp', '').split('T')[1].split('.')[0]
                lines.append(f"- [{ts}] **{h['content']}**")
        else:
            lines.append("_No active hypotheses recorded._")
        lines.append("")

        # 2. Recent Thoughts
        lines.append("## Recent Chain-of-Thought")
        for t in recent_thoughts:
            ts = t.get('timestamp', '').split('T')[1].split('.')[0]
            lines.append(f"> [{ts}] {t['content']}")
        lines.append("")
        
        # 3. Work Log (Edits)
        lines.append("## Code Changes")
        if edits:
            for e in edits:
                f_name = e.get('meta', {}).get('file', 'unknown')
                lines.append(f"- Modified `{f_name}`: {e['content']}")
        else:
             lines.append("_No code changes recorded yet._")

        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
            
        print(f"Updated {self.output_file} based on {len(entries)} events.")

def main():
    tracker = KnowledgeTracker()
    tracker.generate_report()

if __name__ == "__main__":
    main()
