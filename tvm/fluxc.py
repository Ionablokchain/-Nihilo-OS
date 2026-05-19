#!/usr/bin/env python3
"""
fluxc.py - Flux language compiler

Usage:
    fluxc.py <source.flux> [--output OUTPUT] [--run] [--seed SEED] [--dump]

Options:
    --output OUTPUT   Write bytecode to OUTPUT (default: a.out.fluxb)
    --run             Execute the bytecode immediately using the TVM
    --seed SEED       RNG seed for VM (integer)
    --dump            Dump disassembled bytecode
"""

import argparse
import sys
import os
import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum, auto
import random
import time

# ----------------------------------------------------------------------
# Lexer
# ----------------------------------------------------------------------

class TokenType(Enum):
    # Keywords
    INTENTION = auto()
    FLOW = auto()
    FUNCTION = auto()
    STRUCT = auto()
    CAUSAL_MOSAIC = auto()
    LET = auto()
    IF = auto()
    ELSE = auto()
    FOR = auto()
    WHILE = auto()
    IN = auto()
    RETURN = auto()
    LAUNCH = auto()
    SEND = auto()
    LISTEN = auto()
    COLLAPSE = auto()
    DIST = auto()
    TRIGGER = auto()
    PRIORITY = auto()
    CONDITION = auto()
    EXECUTE = auto()
    TRUE = auto()
    FALSE = auto()
    # Operators and punctuation
    ASSIGN = auto()
    EQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LE = auto()
    GE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    CONCAT = auto()
    DOT = auto()
    COMMA = auto()
    COLON = auto()
    SEMICOLON = auto()
    ARROW = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    # Literals
    IDENT = auto()
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    DURATION = auto()
    EOF = auto()

KEYWORDS = {
    "intention": TokenType.INTENTION,
    "flow": TokenType.FLOW,
    "function": TokenType.FUNCTION,
    "struct": TokenType.STRUCT,
    "causal_mosaic": TokenType.CAUSAL_MOSAIC,
    "let": TokenType.LET,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "for": TokenType.FOR,
    "while": TokenType.WHILE,
    "in": TokenType.IN,
    "return": TokenType.RETURN,
    "launch": TokenType.LAUNCH,
    "send": TokenType.SEND,
    "listen": TokenType.LISTEN,
    "collapse": TokenType.COLLAPSE,
    "dist": TokenType.DIST,
    "trigger": TokenType.TRIGGER,
    "priority": TokenType.PRIORITY,
    "condition": TokenType.CONDITION,
    "execute": TokenType.EXECUTE,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
}

_DURATION_UNITS = {"ns": 1, "us": 1000, "ms": 1000000, "s": 1000000000, "cycles": 1}

@dataclass
class Token:
    type: TokenType
    value: Any
    line: int
    column: int

class LexerError(Exception):
    pass

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> List[Token]:
        tokens = []
        while self.pos < len(self.source):
            ch = self.source[self.pos]
            if ch.isspace():
                self._advance()
                continue
            if ch == '#':
                self._skip_comment()
                continue
            if ch == '/' and self._peek() == '/':
                self._skip_comment()
                continue
            if ch.isalpha() or ch == '_':
                tokens.append(self._read_identifier_or_keyword())
                continue
            if ch.isdigit():
                tokens.append(self._read_number_or_duration())
                continue
            if ch == '"':
                tokens.append(self._read_string())
                continue
            # Two‑character operators
            if self._match2("=="): tokens.append(self._make_token(TokenType.EQ, "==")); continue
            if self._match2("!="): tokens.append(self._make_token(TokenType.NEQ, "!=")); continue
            if self._match2("<="): tokens.append(self._make_token(TokenType.LE, "<=")); continue
            if self._match2(">="): tokens.append(self._make_token(TokenType.GE, ">=")); continue
            if self._match2("&&"): tokens.append(self._make_token(TokenType.AND, "&&")); continue
            if self._match2("||"): tokens.append(self._make_token(TokenType.OR, "||")); continue
            if self._match2("++"): tokens.append(self._make_token(TokenType.CONCAT, "++")); continue
            if self._match2("->"): tokens.append(self._make_token(TokenType.ARROW, "->")); continue
            # Single‑character operators
            single = {
                "=": TokenType.ASSIGN, "<": TokenType.LT, ">": TokenType.GT,
                "!": TokenType.NOT, "+": TokenType.PLUS, "-": TokenType.MINUS,
                "*": TokenType.STAR, "/": TokenType.SLASH, "%": TokenType.PERCENT,
                ".": TokenType.DOT, ",": TokenType.COMMA, ":": TokenType.COLON,
                ";": TokenType.SEMICOLON,
                "(": TokenType.LPAREN, ")": TokenType.RPAREN,
                "{": TokenType.LBRACE, "}": TokenType.RBRACE,
                "[": TokenType.LBRACKET, "]": TokenType.RBRACKET,
            }
            if ch in single:
                self._advance()
                tokens.append(self._make_token(single[ch], ch))
                continue
            raise LexerError(f"Unknown character '{ch}' at {self.line}:{self.column}")
        tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return tokens

    def _advance(self):
        if self.source[self.pos] == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        self.pos += 1

    def _peek(self, offset=1):
        p = self.pos + offset
        return self.source[p] if p < len(self.source) else '\0'

    def _match2(self, s):
        if self.pos + 1 < len(self.source) and self.source[self.pos:self.pos+2] == s:
            self._advance()
            self._advance()
            return True
        return False

    def _make_token(self, typ, val):
        return Token(typ, val, self.line, self.column - (len(str(val)) if isinstance(val, str) else 1))

    def _skip_comment(self):
        while self.pos < len(self.source) and self.source[self.pos] != '\n':
            self._advance()

    def _read_identifier_or_keyword(self):
        start_col = self.column
        start = self.pos
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            self._advance()
        text = self.source[start:self.pos]
        typ = KEYWORDS.get(text, TokenType.IDENT)
        return Token(typ, text, self.line, start_col)

    def _read_number_or_duration(self):
        start_col = self.column
        start = self.pos
        is_float = False
        while self.pos < len(self.source) and self.source[self.pos].isdigit():
            self._advance()
        if self.pos < len(self.source) and self.source[self.pos] == '.' and self._peek().isdigit():
            is_float = True
            self._advance()
            while self.pos < len(self.source) and self.source[self.pos].isdigit():
                self._advance()
        num_text = self.source[start:self.pos]
        # Check for duration suffix
        for unit in ("cycles", "ms", "us", "ns", "s"):
            if self.pos + len(unit) <= len(self.source) and self.source[self.pos:self.pos+len(unit)] == unit:
                next_char = self.source[self.pos+len(unit)] if self.pos+len(unit) < len(self.source) else ''
                if not (next_char.isalnum() or next_char == '_'):
                    mult = _DURATION_UNITS[unit]
                    if is_float:
                        nanos = int(float(num_text) * mult)
                    else:
                        nanos = int(num_text) * mult
                    for _ in range(len(unit)):
                        self._advance()
                    return Token(TokenType.DURATION, (nanos, num_text+unit), self.line, start_col)
        # Regular number
        if is_float:
            return Token(TokenType.FLOAT, float(num_text), self.line, start_col)
        else:
            return Token(TokenType.INTEGER, int(num_text), self.line, start_col)

    def _read_string(self):
        start_col = self.column
        self._advance()  # opening quote
        buf = []
        while self.pos < len(self.source) and self.source[self.pos] != '"':
            ch = self.source[self.pos]
            if ch == '\\':
                self._advance()
                esc = self.source[self.pos]
                buf.append({'n': '\n', 't': '\t', 'r': '\r', '"': '"', '\\': '\\'}.get(esc, esc))
                self._advance()
            else:
                buf.append(ch)
                self._advance()
        if self.pos >= len(self.source):
            raise LexerError("Unterminated string")
        self._advance()  # closing quote
        return Token(TokenType.STRING, ''.join(buf), self.line, start_col)


# ----------------------------------------------------------------------
# AST nodes (simplified for brevity – full definitions exist)
# ----------------------------------------------------------------------

class Node: pass

@dataclass
class Program(Node):
    declarations: List[Node]

@dataclass
class IntentionDecl(Node):
    name: str
    trigger: Optional[Node]
    priority: Optional[float]
    condition: Optional[Node]
    body: List[Node]
    line: int = 0

@dataclass
class FlowDecl(Node):
    name: str
    params: List[str]
    body: List[Node]

@dataclass
class FunctionDecl(Node):
    name: str
    params: List[Tuple[str, str]]
    return_type: Optional[str]
    body: List[Node]

@dataclass
class StructDecl(Node):
    name: str
    fields: Dict[str, Node]

@dataclass
class CausalMosaicDecl(Node):
    name: str
    components: Node

# Statements
@dataclass
class Let(Node): name: str; value: Node
@dataclass
class Assign(Node): name: str; value: Node
@dataclass
class SendSensation(Node): kind: Node; content: Node; duration: Optional[Node]
@dataclass
class Collapse(Node): expression: Node; method: str
@dataclass
class IfNode(Node): condition: Node; then_branch: List[Node]; else_branch: List[Node] = field(default_factory=list)
@dataclass
class ForNode(Node): variable: str; source: Node; body: List[Node]
@dataclass
class WhileNode(Node): condition: Node; body: List[Node]
@dataclass
class ReturnNode(Node): value: Optional[Node]
@dataclass
class Launch(Node): name: str; args: List[Node]
@dataclass
class ExpressionStmt(Node): expression: Node

# Expressions
@dataclass
class Identifier(Node): name: str
@dataclass
class StringLiteral(Node): value: str
@dataclass
class NumberLiteral(Node): value: float
@dataclass
class BoolLiteral(Node): value: bool
@dataclass
class DurationLiteral(Node): nanoseconds: int; original: str
@dataclass
class Probability(Node): value: float
@dataclass
class ListenIntention(Node): source: str; timeout: Optional[Node]; fallback: Optional[Node]
@dataclass
class BinOp(Node): left: Node; op: str; right: Node
@dataclass
class UnaryOp(Node): op: str; operand: Node
@dataclass
class Call(Node): name: str; args: List[Node]
@dataclass
class MethodCall(Node): obj: Node; method: str; args: List[Node]
@dataclass
class FieldAccess(Node): obj: Node; field: str
@dataclass
class ListLiteral(Node): items: List[Node]
@dataclass
class DistLiteral(Node): entries: List[Tuple[Node, Node]]


# ----------------------------------------------------------------------
# Parser (recursive descent)
# ----------------------------------------------------------------------

class ParseError(Exception):
    pass

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        t = self.tokens[self.pos]
        if t.type != TokenType.EOF:
            self.pos += 1
        return t

    def match(self, *types) -> bool:
        if self.pos < len(self.tokens) and self.peek().type in types:
            self.advance()
            return True
        return False

    def expect(self, typ: TokenType, msg: str = None):
        if self.peek().type == typ:
            return self.advance()
        raise ParseError(msg or f"Expected {typ}")

    def parse(self) -> Program:
        decls = []
        while self.peek().type != TokenType.EOF:
            decls.append(self.declaration())
        return Program(decls)

    def declaration(self):
        tok = self.peek()
        if tok.type == TokenType.INTENTION:
            return self.parse_intention()
        elif tok.type == TokenType.FLOW:
            return self.parse_flow()
        elif tok.type == TokenType.FUNCTION:
            return self.parse_function()
        elif tok.type == TokenType.STRUCT:
            return self.parse_struct()
        elif tok.type == TokenType.CAUSAL_MOSAIC:
            return self.parse_causal_mosaic()
        else:
            raise ParseError(f"Unexpected token {tok.value}")

    def parse_intention(self) -> IntentionDecl:
        start = self.expect(TokenType.INTENTION)
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.LBRACE)
        trigger = None
        priority = None
        condition = None
        body = []
        while self.peek().type != TokenType.RBRACE:
            if self.match(TokenType.TRIGGER):
                self.expect(TokenType.COLON)
                trigger = self.expression()
            elif self.match(TokenType.PRIORITY):
                self.expect(TokenType.COLON)
                expr = self.expression()
                if isinstance(expr, NumberLiteral):
                    priority = expr.value
                else:
                    raise ParseError("Priority must be a number")
            elif self.match(TokenType.CONDITION):
                self.expect(TokenType.COLON)
                condition = self.expression()
            elif self.match(TokenType.EXECUTE):
                self.expect(TokenType.COLON)
                body = self.block()
            else:
                raise ParseError("Invalid intention field")
        self.expect(TokenType.RBRACE)
        return IntentionDecl(name, trigger, priority, condition, body, start.line)

    def parse_flow(self) -> FlowDecl:
        self.expect(TokenType.FLOW)
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.LPAREN)
        params = []
        if not self.match(TokenType.RPAREN):
            params.append(self.expect(TokenType.IDENT).value)
            while self.match(TokenType.COMMA):
                params.append(self.expect(TokenType.IDENT).value)
            self.expect(TokenType.RPAREN)
        else:
            self.expect(TokenType.RPAREN)
        body = self.block()
        return FlowDecl(name, params, body)

    def parse_function(self) -> FunctionDecl:
        self.expect(TokenType.FUNCTION)
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.LPAREN)
        params = []
        if not self.match(TokenType.RPAREN):
            pname = self.expect(TokenType.IDENT).value
            self.expect(TokenType.COLON)
            ptype = self.expect(TokenType.IDENT).value
            params.append((pname, ptype))
            while self.match(TokenType.COMMA):
                pname = self.expect(TokenType.IDENT).value
                self.expect(TokenType.COLON)
                ptype = self.expect(TokenType.IDENT).value
                params.append((pname, ptype))
            self.expect(TokenType.RPAREN)
        else:
            self.expect(TokenType.RPAREN)
        ret_type = None
        if self.match(TokenType.ARROW):
            ret_type = self.expect(TokenType.IDENT).value
        body = self.block()
        return FunctionDecl(name, params, ret_type, body)

    def parse_struct(self) -> StructDecl:
        self.expect(TokenType.STRUCT)
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.LBRACE)
        fields = {}
        while self.peek().type != TokenType.RBRACE:
            fname = self.expect(TokenType.IDENT).value
            self.expect(TokenType.COLON)
            ftype = self.expect(TokenType.IDENT).value
            fields[fname] = Identifier(ftype)
            if self.match(TokenType.SEMICOLON) or self.match(TokenType.COMMA):
                pass
        self.expect(TokenType.RBRACE)
        return StructDecl(name, fields)

    def parse_causal_mosaic(self) -> CausalMosaicDecl:
        self.expect(TokenType.CAUSAL_MOSAIC)
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.ASSIGN)
        comp = self.expression()
        self.match(TokenType.SEMICOLON)
        return CausalMosaicDecl(name, comp)

    def block(self) -> List[Node]:
        self.expect(TokenType.LBRACE)
        stmts = []
        while self.peek().type != TokenType.RBRACE and self.peek().type != TokenType.EOF:
            stmts.append(self.statement())
        self.expect(TokenType.RBRACE)
        return stmts

    def statement(self) -> Node:
        tok = self.peek()
        if tok.type == TokenType.LET:
            return self.parse_let()
        elif tok.type == TokenType.IF:
            return self.parse_if()
        elif tok.type == TokenType.FOR:
            return self.parse_for()
        elif tok.type == TokenType.WHILE:
            return self.parse_while()
        elif tok.type == TokenType.RETURN:
            return self.parse_return()
        elif tok.type == TokenType.LAUNCH:
            return self.parse_launch()
        elif tok.type == TokenType.SEND:
            return self.parse_send()
        elif tok.type == TokenType.COLLAPSE:
            return self.parse_collapse_stmt()
        else:
            # Assignment or expression statement
            return self.parse_assign_or_expr()

    def parse_let(self) -> Let:
        self.expect(TokenType.LET)
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.ASSIGN)
        value = self.expression()
        self.expect(TokenType.SEMICOLON)
        return Let(name, value)

    def parse_if(self) -> IfNode:
        self.expect(TokenType.IF)
        cond = self.expression()
        then_block = self.block()
        else_block = []
        if self.match(TokenType.ELSE):
            if self.peek().type == TokenType.IF:
                else_block = [self.parse_if()]
            else:
                else_block = self.block()
        return IfNode(cond, then_block, else_block)

    def parse_for(self) -> ForNode:
        self.expect(TokenType.FOR)
        var = self.expect(TokenType.IDENT).value
        self.expect(TokenType.IN)
        source = self.expression()
        body = self.block()
        return ForNode(var, source, body)

    def parse_while(self) -> WhileNode:
        self.expect(TokenType.WHILE)
        cond = self.expression()
        body = self.block()
        return WhileNode(cond, body)

    def parse_return(self) -> ReturnNode:
        self.expect(TokenType.RETURN)
        val = None
        if self.peek().type != TokenType.SEMICOLON:
            val = self.expression()
        self.expect(TokenType.SEMICOLON)
        return ReturnNode(val)

    def parse_launch(self) -> Launch:
        self.expect(TokenType.LAUNCH)
        self.expect(TokenType.LPAREN)
        name = self.expect(TokenType.IDENT).value
        args = []
        while self.match(TokenType.COMMA):
            args.append(self.expression())
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.SEMICOLON)
        return Launch(name, args)

    def parse_send(self) -> SendSensation:
        self.expect(TokenType.SEND)
        self.expect(TokenType.LPAREN)
        kind = self.expression()
        self.expect(TokenType.COMMA)
        content = self.expression()
        duration = None
        if self.match(TokenType.COMMA):
            duration = self.expression()
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.SEMICOLON)
        return SendSensation(kind, content, duration)

    def parse_collapse_stmt(self) -> Node:
        # statement form: collapse(expr, method);
        c = self.parse_collapse_expr()
        self.expect(TokenType.SEMICOLON)
        return c

    def parse_collapse_expr(self) -> Collapse:
        self.expect(TokenType.COLLAPSE)
        self.expect(TokenType.LPAREN)
        expr = self.expression()
        self.expect(TokenType.COMMA)
        method = self.expect(TokenType.IDENT).value
        self.expect(TokenType.RPAREN)
        return Collapse(expr, method)

    def parse_assign_or_expr(self) -> Node:
        # lookahead for IDENT = ...
        if self.peek().type == TokenType.IDENT and self.tokens[self.pos+1].type == TokenType.ASSIGN:
            name = self.expect(TokenType.IDENT).value
            self.expect(TokenType.ASSIGN)
            value = self.expression()
            self.expect(TokenType.SEMICOLON)
            return Assign(name, value)
        expr = self.expression()
        self.expect(TokenType.SEMICOLON)
        return ExpressionStmt(expr)

    # Expression parsing (Pratt)
    def expression(self, min_prec=0):
        left = self.unary()
        while True:
            tok = self.peek()
            prec = self.binop_precedence(tok.type)
            if prec < min_prec:
                break
            self.advance()
            right = self.expression(prec+1)
            left = BinOp(left, tok.value, right)
        return left

    def binop_precedence(self, typ: TokenType) -> int:
        return {
            TokenType.OR: 1,
            TokenType.AND: 2,
            TokenType.EQ: 3, TokenType.NEQ: 3,
            TokenType.LT: 4, TokenType.GT: 4, TokenType.LE: 4, TokenType.GE: 4,
            TokenType.CONCAT: 5,
            TokenType.PLUS: 6, TokenType.MINUS: 6,
            TokenType.STAR: 7, TokenType.SLASH: 7, TokenType.PERCENT: 7,
        }.get(typ, 0)

    def unary(self) -> Node:
        if self.match(TokenType.MINUS, TokenType.NOT):
            op = self.tokens[self.pos-1].value
            operand = self.unary()
            return UnaryOp(op, operand)
        return self.postfix()

    def postfix(self) -> Node:
        expr = self.primary()
        while True:
            if self.match(TokenType.DOT):
                member = self.expect(TokenType.IDENT).value
                if self.peek().type == TokenType.LPAREN:
                    args = self.parse_args()
                    expr = MethodCall(expr, member, args)
                else:
                    expr = FieldAccess(expr, member)
            elif self.peek().type == TokenType.LPAREN and isinstance(expr, Identifier):
                args = self.parse_args()
                expr = Call(expr.name, args)
            else:
                break
        return expr

    def parse_args(self) -> List[Node]:
        self.expect(TokenType.LPAREN)
        args = []
        if not self.match(TokenType.RPAREN):
            args.append(self.expression())
            while self.match(TokenType.COMMA):
                args.append(self.expression())
            self.expect(TokenType.RPAREN)
        else:
            self.expect(TokenType.RPAREN)
        return args

    def primary(self) -> Node:
        tok = self.peek()
        if tok.type == TokenType.INTEGER:
            self.advance()
            return NumberLiteral(float(tok.value))
        elif tok.type == TokenType.FLOAT:
            self.advance()
            return NumberLiteral(tok.value)
        elif tok.type == TokenType.DURATION:
            self.advance()
            nanos, orig = tok.value
            return DurationLiteral(nanos, orig)
        elif tok.type == TokenType.STRING:
            self.advance()
            return StringLiteral(tok.value)
        elif tok.type == TokenType.TRUE:
            self.advance()
            return BoolLiteral(True)
        elif tok.type == TokenType.FALSE:
            self.advance()
            return BoolLiteral(False)
        elif tok.type == TokenType.LISTEN:
            return self.parse_listen()
        elif tok.type == TokenType.COLLAPSE:
            return self.parse_collapse_expr()
        elif tok.type == TokenType.DIST:
            return self.parse_dist()
        elif tok.type == TokenType.IDENT:
            self.advance()
            return Identifier(tok.value)
        elif tok.type == TokenType.LPAREN:
            self.advance()
            expr = self.expression()
            self.expect(TokenType.RPAREN)
            return expr
        elif tok.type == TokenType.LBRACKET:
            return self.parse_list()
        else:
            raise ParseError(f"Unexpected token {tok.value}")

    def parse_listen(self) -> ListenIntention:
        self.expect(TokenType.LISTEN)
        self.expect(TokenType.LPAREN)
        source = self.expect(TokenType.IDENT).value
        timeout = None
        fallback = None
        if self.match(TokenType.COMMA):
            timeout = self.expression()
            if self.match(TokenType.COMMA):
                fallback = self.expression()
        self.expect(TokenType.RPAREN)
        return ListenIntention(source, timeout, fallback)

    def parse_dist(self) -> DistLiteral:
        self.expect(TokenType.DIST)
        self.expect(TokenType.LBRACE)
        entries = []
        while self.peek().type != TokenType.RBRACE:
            val = self.expression()
            self.expect(TokenType.COLON)
            weight = self.expression()
            entries.append((val, weight))
            if not self.match(TokenType.COMMA):
                break
        self.expect(TokenType.RBRACE)
        return DistLiteral(entries)

    def parse_list(self) -> ListLiteral:
        self.expect(TokenType.LBRACKET)
        items = []
        while self.peek().type != TokenType.RBRACKET:
            items.append(self.expression())
            if not self.match(TokenType.COMMA):
                break
        self.expect(TokenType.RBRACKET)
        return ListLiteral(items)


# ----------------------------------------------------------------------
# Semantic analyzer (simplified)
# ----------------------------------------------------------------------

class SemanticError:
    def __init__(self, kind, msg, line=0):
        self.kind = kind
        self.message = msg
        self.line = line

class SemanticAnalyzer:
    def __init__(self):
        self.diagnostics = []

    def analyze(self, program: Program) -> List[SemanticError]:
        # Very simple: just check priority range
        for decl in program.declarations:
            if isinstance(decl, IntentionDecl):
                if decl.priority is not None and (decl.priority < 0 or decl.priority > 1):
                    self.diagnostics.append(SemanticError("error", f"Priority {decl.priority} out of range [0,1]", decl.line))
        return self.diagnostics


# ----------------------------------------------------------------------
# Bytecode generation
# ----------------------------------------------------------------------

from enum import Enum as OpEnum

class Op(OpEnum):
    PUSH_NUM = auto()
    PUSH_STR = auto()
    PUSH_BOOL = auto()
    PUSH_DURATION = auto()
    PUSH_NIL = auto()
    POP = auto()
    DUP = auto()
    MAKE_LIST = auto()
    MAKE_DIST = auto()
    LOAD_VAR = auto()
    STORE_VAR = auto()
    DECLARE_VAR = auto()
    BIN_OP = auto()
    UNARY_OP = auto()
    JUMP = auto()
    JUMP_IF_FALSE = auto()
    CALL = auto()
    METHOD_CALL = auto()
    FIELD_ACCESS = auto()
    RETURN = auto()
    SEND_SENSATION = auto()
    LISTEN = auto()
    COLLAPSE = auto()
    LAUNCH = auto()
    BEGIN_INTENTION = auto()
    END_INTENTION = auto()
    HALT = auto()

@dataclass
class Instr:
    op: Op
    arg: Any = None

@dataclass
class CodeObject:
    name: str
    kind: str
    instructions: List[Instr]
    params: List[str]
    priority: float = 1.0
    trigger: Optional[Node] = None
    condition: Optional[Node] = None

@dataclass
class Module:
    intentions: List[CodeObject]
    functions: List[CodeObject]
    flows: List[CodeObject]
    mosaics: List[Tuple[str, Node]]

class Codegen:
    def __init__(self):
        self.inst = []
        self.const_pool = []

    def emit(self, op: Op, arg=None):
        self.inst.append(Instr(op, arg))

    def generate(self, program: Program) -> Module:
        intentions = []
        functions = []
        flows = []
        mosaics = []
        for decl in program.declarations:
            if isinstance(decl, IntentionDecl):
                intentions.append(self.gen_intention(decl))
            elif isinstance(decl, FunctionDecl):
                functions.append(self.gen_function(decl))
            elif isinstance(decl, FlowDecl):
                flows.append(self.gen_flow(decl))
            elif isinstance(decl, CausalMosaicDecl):
                mosaics.append((decl.name, decl.components))
        return Module(intentions, functions, flows, mosaics)

    def gen_intention(self, decl: IntentionDecl) -> CodeObject:
        self.inst = []
        self.emit(Op.BEGIN_INTENTION, decl.name)
        self.gen_block(decl.body)
        self.emit(Op.PUSH_NIL)
        self.emit(Op.RETURN)
        return CodeObject(decl.name, "intention", self.inst.copy(), [],
                          priority=decl.priority or 1.0,
                          trigger=decl.trigger, condition=decl.condition)

    def gen_function(self, decl: FunctionDecl) -> CodeObject:
        self.inst = []
        self.gen_block(decl.body)
        if not self.inst or self.inst[-1].op != Op.RETURN:
            self.emit(Op.PUSH_NIL)
            self.emit(Op.RETURN)
        return CodeObject(decl.name, "function", self.inst.copy(), [p[0] for p in decl.params])

    def gen_flow(self, decl: FlowDecl) -> CodeObject:
        self.inst = []
        self.gen_block(decl.body)
        if not self.inst or self.inst[-1].op != Op.RETURN:
            self.emit(Op.PUSH_NIL)
            self.emit(Op.RETURN)
        return CodeObject(decl.name, "flow", self.inst.copy(), decl.params)

    def gen_block(self, stmts):
        for s in stmts:
            self.gen_stmt(s)

    def gen_stmt(self, stmt):
        if isinstance(stmt, Let):
            self.gen_expr(stmt.value)
            self.emit(Op.DECLARE_VAR, stmt.name)
        elif isinstance(stmt, Assign):
            self.gen_expr(stmt.value)
            self.emit(Op.STORE_VAR, stmt.name)
        elif isinstance(stmt, SendSensation):
            self.gen_expr(stmt.kind)
            self.gen_expr(stmt.content)
            if stmt.duration:
                self.gen_expr(stmt.duration)
            else:
                self.emit(Op.PUSH_NIL)
            self.emit(Op.SEND_SENSATION)
        elif isinstance(stmt, Collapse):
            self.gen_expr(stmt.expression)
            self.emit(Op.COLLAPSE, stmt.method)
            self.emit(Op.POP)  # discard result for statement form
        elif isinstance(stmt, IfNode):
            self.gen_if(stmt)
        elif isinstance(stmt, ForNode):
            self.gen_for(stmt)
        elif isinstance(stmt, WhileNode):
            self.gen_while(stmt)
        elif isinstance(stmt, ReturnNode):
            if stmt.value:
                self.gen_expr(stmt.value)
            else:
                self.emit(Op.PUSH_NIL)
            self.emit(Op.RETURN)
        elif isinstance(stmt, Launch):
            for a in stmt.args:
                self.gen_expr(a)
            self.emit(Op.LAUNCH, (stmt.name, len(stmt.args)))
        elif isinstance(stmt, ExpressionStmt):
            self.gen_expr(stmt.expression)
            self.emit(Op.POP)
        else:
            raise Exception(f"Unhandled statement {type(stmt)}")

    def gen_if(self, node: IfNode):
        self.gen_expr(node.condition)
        jfalse = self.emit(Op.JUMP_IF_FALSE, 0)
        self.gen_block(node.then_branch)
        jend = self.emit(Op.JUMP, 0)
        # patch jfalse
        self.inst[jfalse].arg = len(self.inst)
        if node.else_branch:
            self.gen_block(node.else_branch)
        self.inst[jend].arg = len(self.inst)

    def gen_while(self, node: WhileNode):
        start = len(self.inst)
        self.gen_expr(node.condition)
        jexit = self.emit(Op.JUMP_IF_FALSE, 0)
        self.gen_block(node.body)
        self.emit(Op.JUMP, start)
        self.inst[jexit].arg = len(self.inst)

    def gen_for(self, node: ForNode):
        # desugar: iter = __iter(source); while __has_next(iter): i = __next(iter); body
        iter_var = f"__iter_{id(node)}"
        self.gen_expr(node.source)
        self.emit(Op.CALL, ("__iter", 1))
        self.emit(Op.DECLARE_VAR, iter_var)
        start = len(self.inst)
        self.emit(Op.LOAD_VAR, iter_var)
        self.emit(Op.CALL, ("__has_next", 1))
        jexit = self.emit(Op.JUMP_IF_FALSE, 0)
        self.emit(Op.LOAD_VAR, iter_var)
        self.emit(Op.CALL, ("__next", 1))
        self.emit(Op.DECLARE_VAR, node.variable)
        self.gen_block(node.body)
        self.emit(Op.JUMP, start)
        self.inst[jexit].arg = len(self.inst)

    def gen_expr(self, expr):
        if isinstance(expr, NumberLiteral):
            self.emit(Op.PUSH_NUM, expr.value)
        elif isinstance(expr, StringLiteral):
            self.emit(Op.PUSH_STR, expr.value)
        elif isinstance(expr, BoolLiteral):
            self.emit(Op.PUSH_BOOL, expr.value)
        elif isinstance(expr, DurationLiteral):
            self.emit(Op.PUSH_DURATION, (expr.nanoseconds, expr.original))
        elif isinstance(expr, Identifier):
            self.emit(Op.LOAD_VAR, expr.name)
        elif isinstance(expr, BinOp):
            self.gen_expr(expr.left)
            self.gen_expr(expr.right)
            self.emit(Op.BIN_OP, expr.op)
        elif isinstance(expr, UnaryOp):
            self.gen_expr(expr.operand)
            self.emit(Op.UNARY_OP, expr.op)
        elif isinstance(expr, Call):
            for a in expr.args:
                self.gen_expr(a)
            self.emit(Op.CALL, (expr.name, len(expr.args)))
        elif isinstance(expr, MethodCall):
            self.gen_expr(expr.obj)
            for a in expr.args:
                self.gen_expr(a)
            self.emit(Op.METHOD_CALL, (expr.method, len(expr.args)))
        elif isinstance(expr, FieldAccess):
            self.gen_expr(expr.obj)
            self.emit(Op.FIELD_ACCESS, expr.field)
        elif isinstance(expr, ListenIntention):
            has_timeout = expr.timeout is not None
            has_fallback = expr.fallback is not None
            if has_timeout:
                self.gen_expr(expr.timeout)
            if has_fallback:
                self.gen_expr(expr.fallback)
            self.emit(Op.LISTEN, (expr.source, has_timeout, has_fallback))
        elif isinstance(expr, Collapse):
            self.gen_expr(expr.expression)
            self.emit(Op.COLLAPSE, expr.method)
        elif isinstance(expr, ListLiteral):
            for item in expr.items:
                self.gen_expr(item)
            self.emit(Op.MAKE_LIST, len(expr.items))
        elif isinstance(expr, DistLiteral):
            for val, w in expr.entries:
                self.gen_expr(val)
                self.gen_expr(w)
            self.emit(Op.MAKE_DIST, len(expr.entries))
        else:
            raise Exception(f"Unhandled expression {type(expr)}")


# ----------------------------------------------------------------------
# Main CLI
# ----------------------------------------------------------------------

def compile_file(source_path: str) -> Module:
    with open(source_path, 'r') as f:
        source = f.read()
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    sem = SemanticAnalyzer()
    diag = sem.analyze(ast)
    errors = [d for d in diag if d.kind == 'error']
    if errors:
        for e in errors:
            print(f"Semantic error: {e.message}", file=sys.stderr)
        sys.exit(1)
    codegen = Codegen()
    module = codegen.generate(ast)
    return module

def save_bytecode(module: Module, output_path: str):
    # For simplicity, we use JSON to store the module
    data = {
        "version": 1,
        "intentions": [],
        "functions": [],
        "flows": [],
        "mosaics": []
    }
    for i in module.intentions:
        data["intentions"].append({
            "name": i.name,
            "priority": i.priority,
            "instructions": [(ins.op.name, ins.arg) for ins in i.instructions],
            "params": i.params,
            "trigger": str(i.trigger) if i.trigger else None,
            "condition": str(i.condition) if i.condition else None,
        })
    for f in module.functions:
        data["functions"].append({
            "name": f.name,
            "instructions": [(ins.op.name, ins.arg) for ins in f.instructions],
            "params": f.params,
        })
    for f in module.flows:
        data["flows"].append({
            "name": f.name,
            "instructions": [(ins.op.name, ins.arg) for ins in f.instructions],
            "params": f.params,
        })
    for name, comp in module.mosaics:
        data["mosaics"].append({"name": name, "components": str(comp)})
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

def disassemble(module: Module):
    for i in module.intentions:
        print(f"Intention {i.name} [priority={i.priority}]")
        for idx, ins in enumerate(i.instructions):
            print(f"  {idx:3d}  {ins.op.name} {ins.arg if ins.arg is not None else ''}")
    for f in module.functions:
        print(f"Function {f.name}")
        for idx, ins in enumerate(f.instructions):
            print(f"  {idx:3d}  {ins.op.name} {ins.arg if ins.arg is not None else ''}")

def main():
    parser = argparse.ArgumentParser(description="Flux compiler")
    parser.add_argument("source", help="Input .flux file")
    parser.add_argument("--output", "-o", help="Output bytecode file", default="a.out.fluxb")
    parser.add_argument("--run", action="store_true", help="Run the program using TVM")
    parser.add_argument("--seed", type=int, help="RNG seed for TVM")
    parser.add_argument("--dump", action="store_true", help="Dump disassembled bytecode")
    args = parser.parse_args()

    module = compile_file(args.source)
    if args.dump:
        disassemble(module)
    save_bytecode(module, args.output)
    print(f"Compiled to {args.output}")
    if args.run:
        # Run with TVM (import tvm module)
        sys.path.insert(0, os.path.dirname(__file__))
        from tvm import TemporalVM, InputProvider, OutputSink
        vm = TemporalVM(input_provider=InputProvider(), sink=OutputSink(), rng_seed=args.seed)
        vm.load_module(args.output)
        vm.run_module()

if __name__ == "__main__":
    main()