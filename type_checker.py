#!/usr/bin/env python3
"""Simple type checker for a toy language."""

class Type:
    def __init__(self, name, params=None):
        self.name = name
        self.params = params or []
    def __eq__(self, other):
        return isinstance(other, Type) and self.name == other.name and self.params == other.params
    def __repr__(self):
        if self.params:
            return f"{self.name}<{', '.join(str(p) for p in self.params)}>"
        return self.name

INT = Type("Int")
FLOAT = Type("Float")
BOOL = Type("Bool")
STRING = Type("String")
VOID = Type("Void")

def func_type(params, ret):
    return Type("Func", params + [ret])

class TypeEnv:
    def __init__(self, parent=None):
        self.bindings = {}
        self.parent = parent
    def define(self, name, typ):
        self.bindings[name] = typ
    def lookup(self, name):
        if name in self.bindings:
            return self.bindings[name]
        if self.parent:
            return self.parent.lookup(name)
        raise TypeError(f"Undefined: {name}")

def check_expr(expr, env):
    if isinstance(expr, bool): return BOOL
    if isinstance(expr, int): return INT
    if isinstance(expr, float): return FLOAT
    if isinstance(expr, str) and expr.startswith('"'): return STRING
    if isinstance(expr, str): return env.lookup(expr)
    if isinstance(expr, tuple):
        op = expr[0]
        if op in ("+", "-", "*", "/"):
            lt = check_expr(expr[1], env)
            rt = check_expr(expr[2], env)
            if lt == INT and rt == INT: return INT
            if lt in (INT, FLOAT) and rt in (INT, FLOAT): return FLOAT
            raise TypeError(f"Cannot {op} {lt} and {rt}")
        if op in ("==", "!=", "<", ">", "<=", ">="):
            check_expr(expr[1], env)
            check_expr(expr[2], env)
            return BOOL
        if op == "and" or op == "or":
            lt = check_expr(expr[1], env)
            rt = check_expr(expr[2], env)
            if lt != BOOL or rt != BOOL:
                raise TypeError(f"Boolean op on non-bool")
            return BOOL
        if op == "not":
            t = check_expr(expr[1], env)
            if t != BOOL: raise TypeError("not on non-bool")
            return BOOL
        if op == "if":
            ct = check_expr(expr[1], env)
            if ct != BOOL: raise TypeError("if condition must be Bool")
            tt = check_expr(expr[2], env)
            ft = check_expr(expr[3], env)
            if tt != ft: raise TypeError(f"if branches differ: {tt} vs {ft}")
            return tt
        if op == "call":
            ft = check_expr(expr[1], env)
            if ft.name != "Func": raise TypeError(f"Not callable: {ft}")
            args = [check_expr(a, env) for a in expr[2:]]
            expected = ft.params[:-1]
            ret = ft.params[-1]
            if len(args) != len(expected):
                raise TypeError(f"Arity mismatch: expected {len(expected)}, got {len(args)}")
            for i, (a, e) in enumerate(zip(args, expected)):
                if a != e: raise TypeError(f"Arg {i}: expected {e}, got {a}")
            return ret
        if op == "let":
            val_t = check_expr(expr[2], env)
            new_env = TypeEnv(env)
            new_env.define(expr[1], val_t)
            return check_expr(expr[3], new_env)
    raise TypeError(f"Unknown expr: {expr}")

def test():
    env = TypeEnv()
    assert check_expr(42, env) == INT
    assert check_expr(3.14, env) == FLOAT
    assert check_expr(("+", 1, 2), env) == INT
    assert check_expr(("+", 1, 2.0), env) == FLOAT
    assert check_expr(("<", 1, 2), env) == BOOL
    assert check_expr(("and", True, False), env) == BOOL
    assert check_expr(("if", True, 1, 2), env) == INT
    # Let binding
    assert check_expr(("let", "x", 10, ("+", "x", 1)), env) == INT
    # Function call
    env.define("add", func_type([INT, INT], INT))
    assert check_expr(("call", "add", 1, 2), env) == INT
    # Errors
    try:
        check_expr(("+", 1, True), env)
        assert False
    except TypeError:
        pass
    try:
        check_expr(("if", 1, 2, 3), env)
        assert False
    except TypeError:
        pass
    print("  type_checker: ALL TESTS PASSED")

if __name__ == "__main__":
    test()
