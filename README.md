# Asciicker Comment Generator

A set of Python tools to automatically generate context-aware inline comments for C++ codebases. It learns from existing code patterns and uses a domain dictionary to provide meaningful explanations.

## Overview

The system operates in 3 phases:

1.  **Pattern Learning**: `comment_pattern_analyzer.py` scans your codebase to learn how you document different constructs (variables, functions, loops).
2.  **Semantic Analysis**: `semantic_analyzer.py` parses your C++ code to understand scope, types, and values.
3.  **Generation**: `asks_extractor_enhanced.py` combines learned patterns, parsed context, and the `domain.json` dictionary to suggest comments.

## Installation

Requires Python 3.7+. No external dependencies are needed (standard library only).

## Usage

### 1. (Optional) Learn Patterns
If you have an existing codebase with comments, learn usage patterns first:
```bash
python3 comment_pattern_analyzer.py --source /path/to/src
```
This will create `comment_patterns.json`.

### 2. Generate Suggestions
Run the extractor to generate a report of suggested comments:
```bash
python3 asks_extractor_enhanced.py --source /path/to/src --output report.md
```

### 3. Review
Open `report.md` (or your specified output file) to see the suggestions.

## Configuration

### `domain.json`
This file contains the "knowledge base" of your project. Add magic numbers, common variable names, and domain terms here to improve comment quality.

```json
{
    "0xA000": "Terrain Height Base",
    "player_id": "Unique Entity ID",
    "cw": "Cell Width"
}
```

## Agent Ops (Self-Documentation)

This repository includes tools to let AI Agents document their own work automatically.

### Integration
To enable an Agent to "think" into the system logs:
1.  Copy the contents of `AGENT_INSTRUCTIONS.md`.
2.  Paste it into the **System Prompt** of your Agent (e.g. ChatGPT, Claude, custom script).
3.  The Agent will now automatically run the `agent_hook.py` tool as it works.

### Manual Tool Usage
If you are manually operating only, you can still use the hook:

*   **Log a thought**: `python3 agent_hook.py "Analyzing the rendering pipeline"`
*   **Log a hypothesis**: `python3 agent_hook.py --hypothesis "Maybe the Z-index is flipped"`

### Underlying Tools
*   **`agent_hook.py`**: The primary entry point.
*   **`agent_logger.py`**: Records raw logs.
*   **`knowledge_tracker.py`**: Updates `CURRENT_UNDERSTANDING.md`.
*   **`reference_linker.py`**: Links symbols.

## CLI Options

Both extractor and analyzer scripts support common arguments:
*   `--source` / `-S`: Root directory to scan (default: current directory).
*   `--exclude` / `-e`: Comma-separated list of folders to ignore (default: `vendor,build,third_party`).
*   `--output` / `-o`: Output file path.
*   `--verbose` / `-v`: Show detailed logs.
