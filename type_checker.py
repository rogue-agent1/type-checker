#!/usr/bin/env python3
"""Hindley-Milner type inference for a simple lambda calculus."""
import sys

class TVar:
    _id = 0
    def __init__(self, name=None):
        if name is None: TVar._id += 1; name = f"t{TVar._id}"
        self.name = name; self.instance = None
    def __repr__(self): return self.name if not self.instance else repr(self.instance)

class TCon:
    def __init__(self, name, args=None): self.name = name; self.args = args or []
    def __repr__(self):
        if not self.args: return self.name
        if self.name == "->": return f"({self.args[0]} -> {self.args[1]})"
        return f"{self.name}[{', '.join(map(str, self.args))}]"

Int = TCon("Int"); Bool = TCon("Bool"); String = TCon("String")
def Arrow(a, b): return TCon("->", [a, b])

def prune(t):
    if isinstance(t, TVar) and t.instance: t.instance = prune(t.instance); return t.instance
    return t

def unify(t1, t2):
    t1, t2 = prune(t1), prune(t2)
    if isinstance(t1, TVar): t1.instance = t2; return
    if isinstance(t2, TVar): t2.instance = t1; return
    if isinstance(t1, TCon) and isinstance(t2, TCon):
        if t1.name != t2.name or len(t1.args) != len(t2.args):
            raise TypeError(f"Cannot unify {t1} with {t2}")
        for a, b in zip(t1.args, t2.args): unify(a, b)

def infer(expr, env):
    if isinstance(expr, int): return Int
    if isinstance(expr, bool): return Bool
    if isinstance(expr, str):
        if expr in env: return env[expr]
        raise NameError(f"Undefined: {expr}")
    if isinstance(expr, tuple):
        if expr[0] == "lambda":
            _, param, body = expr
            param_type = TVar(); new_env = {**env, param: param_type}
            body_type = infer(body, new_env)
            return Arrow(param_type, body_type)
        if expr[0] == "let":
            _, name, value, body = expr
            val_type = infer(value, env)
            return infer(body, {**env, name: val_type})
        if expr[0] == "if":
            _, cond, then, else_ = expr
            unify(infer(cond, env), Bool)
            then_t = infer(then, env); else_t = infer(else_, env)
            unify(then_t, else_t); return then_t
        # Application
        fn, arg = expr
        fn_type = infer(fn, env); arg_type = infer(arg, env)
        result_type = TVar()
        unify(fn_type, Arrow(arg_type, result_type))
        return prune(result_type)

def main():
    env = {"+": Arrow(Int, Arrow(Int, Int)), "==": Arrow(Int, Arrow(Int, Bool)),
           "not": Arrow(Bool, Bool)}
    tests = [
        42, True,
        ("lambda", "x", ("+", "x")),
        ("let", "id", ("lambda", "x", "x"), ("id", 42)),
        ("if", True, 1, 2),
    ]
    for expr in tests:
        TVar._id = 0
        try:
            t = infer(expr, env)
            print(f"  {expr!r:40s} : {prune(t)}")
        except Exception as e: print(f"  {expr!r:40s} : ERROR {e}")

if __name__ == "__main__": main()
