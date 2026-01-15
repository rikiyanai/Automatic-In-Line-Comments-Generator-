#!/usr/bin/env python3
"""
Semantic C++ Analyzer.

This module provides a fuzzy parser for C++ to extract semantic information
needed for context-aware comment generation.
It does NOT perform full compilation but understands enough structure (scopes, types)
to provide meaningful context.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

# --- Tokenization ---

@dataclass
class Token:
    type: str  # 'IDENTIFIER', 'KEYWORD', 'OPERATOR', 'LITERAL', 'COMMENT', 'WHITESPACE'
    value: str
    line: int
    col: int

KEYWORDS = {
    'int', 'float', 'double', 'char', 'void', 'bool', 'auto', 
    'const', 'static', 'unsigned', 'signed', 'uint8_t', 'uint16_t', 'uint32_t', 'uint64_t',
    'class', 'struct', 'enum', 'namespace', 'template',
    'if', 'else', 'for', 'while', 'switch', 'case', 'return', 'break',
    'public', 'private', 'protected', 'virtual', 'override'
}

OPERATORS = set('{}[]()=<>!+-*/%&|^~?:.,;')

class CppTokenizer:
    def __init__(self, code: str):
        self.code = code
        self.pos = 0
        self.line = 1
        self.col = 1
        self.len = len(code)

    def tokenize(self) -> List[Token]:
        tokens = []
        while self.pos < self.len:
            char = self.code[self.pos]
            
            if char.isspace():
                if char == '\n':
                    self.line += 1
                    self.col = 1
                else:
                    self.col += 1
                self.pos += 1
                continue

            # Identifiers & Keywords
            if char.isalpha() or char == '_':
                start = self.pos
                self.pos += 1
                self.col += 1
                while self.pos < self.len and (self.code[self.pos].isalnum() or self.code[self.pos] == '_'):
                    self.pos += 1
                    self.col += 1
                text = self.code[start:self.pos]
                t_type = 'KEYWORD' if text in KEYWORDS else 'IDENTIFIER'
                tokens.append(Token(t_type, text, self.line, self.col - len(text)))
                continue

            # Numbers (Hex, Dec, Float - rudimentary)
            if char.isdigit():
                start = self.pos
                while self.pos < self.len and (self.code[self.pos].isalnum() or self.code[self.pos] == '.'):
                    self.pos += 1
                    self.col += 1
                text = self.code[start:self.pos]
                tokens.append(Token('LITERAL', text, self.line, self.col - len(text)))
                continue

            # Strings
            if char == '"' or char == "'":
                quote = char
                start = self.pos
                self.pos += 1
                self.col += 1
                while self.pos < self.len:
                    curr = self.code[self.pos]
                    if curr == '\\': # Skip escape
                        self.pos += 2
                        self.col += 2
                        continue
                    if curr == quote:
                        self.pos += 1
                        self.col += 1
                        break
                    if curr == '\n':
                        self.line += 1
                        self.col = 1
                    else:
                        self.col += 1
                    self.pos += 1
                text = self.code[start:self.pos]
                tokens.append(Token('LITERAL', text, self.line, self.col - len(text)))
                continue

            # Comments (Skip or Tokenize? Let's skip tokenizing inline for now, assumes comments stripped or handled separately)
            # For simplicity, we assume Basic Text or Pre-stripped, but let's handle // and /*
            if char == '/' and self.pos + 1 < self.len:
                next_char = self.code[self.pos+1]
                if next_char == '/': # Line comment
                    start = self.pos
                    while self.pos < self.len and self.code[self.pos] != '\n':
                        self.pos += 1
                    text = self.code[start:self.pos] # Exclude newline
                    # We skip comments in parser flow usually
                    continue 
                elif next_char == '*': # Block comment
                    start = self.pos
                    self.pos += 2
                    while self.pos + 1 < self.len and not (self.code[self.pos] == '*' and self.code[self.pos+1] == '/'):
                        if self.code[self.pos] == '\n':
                            self.line += 1
                            self.col = 1
                        self.pos += 1
                    self.pos += 2 # Eat */
                    continue

            # Operators
            if char in OPERATORS:
                 tokens.append(Token('OPERATOR', char, self.line, self.col))
                 self.pos += 1
                 self.col += 1
                 continue

            self.pos += 1
            self.col += 1
            
        return tokens

# --- Parsing & Context ---

@dataclass
class VariableInfo:
    name: str
    type: str
    value: Optional[str] = None
    line: int = 0
    is_static: bool = False
    is_const: bool = False

@dataclass
class Scope:
    type: str # 'global', 'function', 'class', 'block'
    name: str = ""
    start_line: int = 0
    variables: List[VariableInfo] = field(default_factory=list)

class CppParser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.scopes = [Scope('global')]
        self.extracted_vars = []

    def current_token(self) -> Optional[Token]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def peek(self, offset=1) -> Optional[Token]:
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else None
        
    def advance(self):
        self.pos += 1

    def parse(self):
        while self.pos < len(self.tokens):
            token = self.current_token()
            
            # Scope Enter
            if token.value == '{':
                self.scopes.append(Scope('block', start_line=token.line))
                self.advance()
                continue
            
            # Scope Exit
            if token.value == '}':
                if len(self.scopes) > 1:
                    popped = self.scopes.pop()
                    # Could capture scope end line here
                self.advance()
                continue

            # Detect Variable Declaration (Heuristic)
            # Pattern: [static/const] Type Name [= Value] [;]
            # Must start with Type (Identifier or Keyword like int)
            if token.type in ('IDENTIFIER', 'KEYWORD'):
                self._try_parse_decl()
            
            self.advance()

    def _try_parse_decl(self):
        # Very simplified fuzzy matcher for declarations
        start_pos = self.pos
        
        is_static = False
        is_const = False
        
        # Eat modifiers
        while self.current_token().value in ('static', 'const', 'unsigned', 'signed'):
            val = self.current_token().value
            if val == 'static': is_static = True
            if val == 'const': is_const = True
            self.advance()
            if not self.current_token(): return

        # Type (Identifier or Basic Type)
        type_token = self.current_token()
        if type_token.type not in ('IDENTIFIER', 'KEYWORD') and type_token.value not in KEYWORDS:
             self.pos = start_pos # Backtrack
             return
        
        type_str = type_token.value
        self.advance()
        
        # Pointers/Refs
        while self.current_token() and self.current_token().value in ('*', '&'):
            type_str += self.current_token().value
            self.advance()

        # Name
        name_token = self.current_token()
        if not name_token or name_token.type != 'IDENTIFIER':
             self.pos = start_pos # Backtrack
             return
        
        name_str = name_token.value
        self.advance()

        # Array?
        if self.current_token() and self.current_token().value == '[':
             # Skip to ]
             while self.current_token() and self.current_token().value != ']':
                 self.advance()
             if self.current_token() and self.current_token().value == ']':
                 self.advance()
                 type_str += "[]"
        
        # Assignment?
        val_str = None
        if self.current_token() and self.current_token().value == '=':
            self.advance()
            # Capture value until ; or ,
            val_tokens = []
            while self.current_token() and self.current_token().value not in (';', ','):
                val_tokens.append(self.current_token().value)
                self.advance()
            val_str = " ".join(val_tokens)

        # Expect terminator or comma
        if self.current_token() and self.current_token().value in (';', ','):
             # Found a variable!
             var_info = VariableInfo(name_str, type_str, val_str, name_token.line, is_static, is_const)
             self.scopes[-1].variables.append(var_info)
             self.extracted_vars.append(var_info)
             # Don't advance past ; let parse loop handle it
             self.pos -= 1 
        else:
             # Failed match
             self.pos = start_pos

def analyze_code(code: str):
    tokenizer = CppTokenizer(code)
    tokens = tokenizer.tokenize()
    parser = CppParser(tokens)
    parser.parse()
    return parser.extracted_vars

if __name__ == '__main__':
    # Test
    test_code = """
    int global_var = 10;
    void main() {
        static float kEpsilon = 0.001;
        if (true) {
             unsigned int count = 0;
        }
    }
    """
    vars = analyze_code(test_code)
    for v in vars:
        print(f"Found var: {v}")
