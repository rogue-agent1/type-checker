#!/usr/bin/env python3
"""type_checker - Bidirectional type checker with generics and union types."""
import sys, json
from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass
class TType:
    pass

@dataclass
class TInt(TType):
    def __repr__(self): return "Int"

@dataclass
class TStr(TType):
    def __repr__(self): return "Str"

@dataclass
class TBool(TType):
    def __repr__(self): return "Bool"

@dataclass
class TFunc(TType):
    params: list
    ret: 'TType'
    def __repr__(self): return f"({', '.join(map(str,self.params))}) -> {self.ret}"

@dataclass
class TGeneric(TType):
    name: str
    bound: Optional['TType'] = None
    def __repr__(self): return f"<{self.name}>"

@dataclass
class TUnion(TType):
    types: list
    def __repr__(self): return " | ".join(map(str, self.types))

@dataclass
class TList(TType):
    elem: 'TType'
    def __repr__(self): return f"List[{self.elem}]"

class TypeChecker:
    def __init__(self):
        self.env = {}
        self.errors = []
        self.substitutions = {}
    
    def unify(self, a, b):
        a, b = self.resolve(a), self.resolve(b)
        if isinstance(a, TGeneric):
            self.substitutions[a.name] = b; return b
        if isinstance(b, TGeneric):
            self.substitutions[b.name] = a; return a
        if type(a) == type(b):
            if isinstance(a, (TInt, TStr, TBool)): return a
            if isinstance(a, TFunc):
                if len(a.params) != len(b.params):
                    self.errors.append(f"Arity mismatch: {a} vs {b}"); return a
                params = [self.unify(p1, p2) for p1, p2 in zip(a.params, b.params)]
                ret = self.unify(a.ret, b.ret)
                return TFunc(params, ret)
            if isinstance(a, TList):
                return TList(self.unify(a.elem, b.elem))
        if isinstance(a, TUnion):
            if self.is_subtype(b, a): return a
        if isinstance(b, TUnion):
            if self.is_subtype(a, b): return b
        self.errors.append(f"Cannot unify {a} with {b}")
        return a
    
    def resolve(self, t):
        if isinstance(t, TGeneric) and t.name in self.substitutions:
            return self.resolve(self.substitutions[t.name])
        return t
    
    def is_subtype(self, a, b):
        a, b = self.resolve(a), self.resolve(b)
        if type(a) == type(b) and isinstance(a, (TInt, TStr, TBool)): return True
        if isinstance(b, TUnion): return any(self.is_subtype(a, t) for t in b.types)
        if isinstance(a, TGeneric) or isinstance(b, TGeneric): return True
        return False
    
    def check_expr(self, expr):
        if isinstance(expr, int): return TInt()
        if isinstance(expr, str) and expr.startswith('"'): return TStr()
        if isinstance(expr, bool): return TBool()
        if isinstance(expr, str):
            if expr in self.env: return self.env[expr]
            self.errors.append(f"Undefined: {expr}"); return TInt()
        if isinstance(expr, dict):
            if "call" in expr:
                ft = self.check_expr(expr["call"])
                ft = self.resolve(ft)
                if isinstance(ft, TFunc):
                    args = [self.check_expr(a) for a in expr.get("args", [])]
                    for p, a in zip(ft.params, args): self.unify(p, a)
                    return self.resolve(ft.ret)
                self.errors.append(f"Not callable: {ft}"); return TInt()
            if "let" in expr:
                val_t = self.check_expr(expr["val"])
                self.env[expr["let"]] = val_t
                return self.check_expr(expr["body"])
            if "list" in expr:
                elems = [self.check_expr(e) for e in expr["list"]]
                if elems: return TList(elems[0])
                return TList(TGeneric("?"))
        return TInt()

def main():
    tc = TypeChecker()
    tc.env["add"] = TFunc([TInt(), TInt()], TInt())
    tc.env["concat"] = TFunc([TStr(), TStr()], TStr())
    tc.env["id"] = TFunc([TGeneric("T")], TGeneric("T"))
    
    tests = [
        ({"call": "add", "args": [1, 2]}, "add(1, 2)"),
        ({"call": "concat", "args": ['"a"', '"b"']}, 'concat("a", "b")'),
        ({"call": "id", "args": [42]}, "id(42)"),
        ({"let": "x", "val": 10, "body": {"call": "add", "args": ["x", 5]}}, "let x=10 in add(x,5)"),
        ({"list": [1, 2, 3]}, "[1, 2, 3]"),
    ]
    
    for expr, desc in tests:
        tc.substitutions.clear()
        t = tc.check_expr(expr)
        print(f"  {desc} : {t}")
    
    if tc.errors:
        print(f"\nErrors: {tc.errors}")
    else:
        print("\nAll checks passed!")

if __name__ == "__main__":
    main()
