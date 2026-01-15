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

## CLI Options

Both scripts support common arguments:
*   `--source` / `-s`: Root directory to scan (default: current directory).
*   `--exclude` / `-e`: Comma-separated list of folders to ignore (default: `vendor,build,third_party`).
*   `--output` / `-o`: Output file path.
*   `--verbose` / `-v`: Show detailed logs.
