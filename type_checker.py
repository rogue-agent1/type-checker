#!/usr/bin/env python3
"""Simple type checker for a mini typed language."""
import sys

class Type:
    def __init__(self, name, params=None): self.name = name; self.params = params or []
    def __eq__(self, o): return isinstance(o, Type) and self.name == o.name and self.params == o.params
    def __repr__(self):
        if self.name == "->": return f"({self.params[0]} -> {self.params[1]})"
        if self.params: return f"{self.name}<{', '.join(map(str, self.params))}>"
        return self.name

INT = Type("Int"); FLOAT = Type("Float"); BOOL = Type("Bool"); STRING = Type("String"); VOID = Type("Void")

def fn_type(a, b): return Type("->", [a, b])

class TypeEnv:
    def __init__(self, parent=None): self.bindings = {}; self.parent = parent
    def bind(self, name, t): self.bindings[name] = t
    def lookup(self, name):
        if name in self.bindings: return self.bindings[name]
        if self.parent: return self.parent.lookup(name)
        raise TypeError(f"Unbound: {name}")
    def child(self): return TypeEnv(self)

def check(expr, env):
    if isinstance(expr, int): return INT
    if isinstance(expr, float): return FLOAT
    if isinstance(expr, bool): return BOOL
    if isinstance(expr, str) and expr.startswith('"'): return STRING
    if isinstance(expr, str): return env.lookup(expr)
    if not isinstance(expr, list) or not expr: raise TypeError(f"Bad expr: {expr}")
    head = expr[0]
    if head == "let":
        name, val_expr, body = expr[1], expr[2], expr[3]
        val_type = check(val_expr, env)
        new_env = env.child(); new_env.bind(name, val_type)
        return check(body, new_env)
    if head == "lambda":
        param, param_type_str, body = expr[1], expr[2], expr[3]
        param_type = parse_type(param_type_str)
        new_env = env.child(); new_env.bind(param, param_type)
        ret_type = check(body, new_env)
        return fn_type(param_type, ret_type)
    if head == "if":
        cond_t = check(expr[1], env)
        if cond_t != BOOL: raise TypeError(f"If condition must be Bool, got {cond_t}")
        then_t = check(expr[2], env)
        else_t = check(expr[3], env)
        if then_t != else_t: raise TypeError(f"Branch mismatch: {then_t} vs {else_t}")
        return then_t
    if head in ("+", "-", "*", "/"):
        lt, rt = check(expr[1], env), check(expr[2], env)
        if lt == INT and rt == INT: return INT
        if lt in (INT, FLOAT) and rt in (INT, FLOAT): return FLOAT
        raise TypeError(f"Arithmetic on {lt}, {rt}")
    if head in ("==", "!=", "<", ">", "<=", ">="):
        check(expr[1], env); check(expr[2], env); return BOOL
    if head in ("and", "or"):
        lt, rt = check(expr[1], env), check(expr[2], env)
        if lt != BOOL or rt != BOOL: raise TypeError(f"Logic on {lt}, {rt}")
        return BOOL
    if head == "not":
        t = check(expr[1], env)
        if t != BOOL: raise TypeError(f"Not on {t}")
        return BOOL
    # Function application
    fn_t = check(expr[0], env)
    if fn_t.name != "->": raise TypeError(f"Not a function: {fn_t}")
    arg_t = check(expr[1], env)
    if arg_t != fn_t.params[0]: raise TypeError(f"Expected {fn_t.params[0]}, got {arg_t}")
    return fn_t.params[1]

def parse_type(s):
    s = s.strip()
    if s == "Int": return INT
    if s == "Float": return FLOAT
    if s == "Bool": return BOOL
    if s == "String": return STRING
    if "->" in s:
        parts = s.split("->", 1)
        return fn_type(parse_type(parts[0]), parse_type(parts[1]))
    return Type(s)

def parse_expr(s):
    import json
    return json.loads(s)

def main():
    env = TypeEnv()
    env.bind("print", fn_type(STRING, VOID))
    env.bind("toString", fn_type(INT, STRING))
    if len(sys.argv) > 1:
        expr = parse_expr(" ".join(sys.argv[1:]))
        try:
            t = check(expr, env)
            print(f"Type: {t}")
        except TypeError as e: print(f"Type error: {e}", file=sys.stderr); sys.exit(1)
    else:
        print("Type checker REPL (JSON s-expressions)")
        print('Example: ["+", 1, 2]')
        for line in sys.stdin:
            line = line.strip()
            if not line: continue
            try:
                expr = parse_expr(line)
                t = check(expr, env)
                print(f"  : {t}")
            except Exception as e: print(f"  Error: {e}")

if __name__ == "__main__": main()
