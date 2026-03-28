#!/usr/bin/env python3
"""type_checker - Hindley-Milner type inference."""
import argparse

class Type:
    pass

class TVar(Type):
    _counter = 0
    def __init__(self, name=None):
        if name is None: TVar._counter += 1; name = f"t{TVar._counter}"
        self.name = name
    def __repr__(self): return self.name

class TCon(Type):
    def __init__(self, name, args=None):
        self.name = name; self.args = args or []
    def __repr__(self):
        if not self.args: return self.name
        if self.name == "->": return f"({self.args[0]} -> {self.args[1]})"
        return f"{self.name}[{', '.join(map(str, self.args))}]"

INT = TCon("Int"); BOOL = TCon("Bool"); STR = TCon("String")
def FUN(a, b): return TCon("->", [a, b])

def occurs_in(tvar, typ):
    if isinstance(typ, TVar): return tvar.name == typ.name
    if isinstance(typ, TCon): return any(occurs_in(tvar, a) for a in typ.args)
    return False

def unify(t1, t2, subst):
    t1, t2 = apply_subst(subst, t1), apply_subst(subst, t2)
    if isinstance(t1, TVar):
        if isinstance(t2, TVar) and t1.name == t2.name: return subst
        if occurs_in(t1, t2): raise TypeError(f"Infinite type: {t1} in {t2}")
        return {**subst, t1.name: t2}
    if isinstance(t2, TVar): return unify(t2, t1, subst)
    if isinstance(t1, TCon) and isinstance(t2, TCon):
        if t1.name != t2.name or len(t1.args) != len(t2.args):
            raise TypeError(f"Cannot unify {t1} with {t2}")
        for a1, a2 in zip(t1.args, t2.args): subst = unify(a1, a2, subst)
        return subst
    raise TypeError(f"Cannot unify {t1} with {t2}")

def apply_subst(subst, typ):
    if isinstance(typ, TVar): return apply_subst(subst, subst[typ.name]) if typ.name in subst else typ
    if isinstance(typ, TCon): return TCon(typ.name, [apply_subst(subst, a) for a in typ.args])
    return typ

def infer(expr, env, subst):
    if isinstance(expr, int): return INT, subst
    if isinstance(expr, bool): return BOOL, subst
    if isinstance(expr, str):
        if expr in env: return env[expr], subst
        raise TypeError(f"Unbound: {expr}")
    if isinstance(expr, tuple):
        if expr[0] == "let":
            _, name, val, body = expr
            val_t, subst = infer(val, env, subst)
            return infer(body, {**env, name: val_t}, subst)
        if expr[0] == "lambda":
            _, param, body = expr
            param_t = TVar()
            body_t, subst = infer(body, {**env, param: param_t}, subst)
            return FUN(apply_subst(subst, param_t), body_t), subst
        if expr[0] == "if":
            _, cond, then, els = expr
            cond_t, subst = infer(cond, env, subst)
            subst = unify(cond_t, BOOL, subst)
            then_t, subst = infer(then, env, subst)
            else_t, subst = infer(els, env, subst)
            subst = unify(then_t, else_t, subst)
            return apply_subst(subst, then_t), subst
        func, arg = expr
        func_t, subst = infer(func, env, subst)
        arg_t, subst = infer(arg, env, subst)
        ret_t = TVar()
        subst = unify(func_t, FUN(arg_t, ret_t), subst)
        return apply_subst(subst, ret_t), subst

def main():
    p = argparse.ArgumentParser(description="Type inference demo")
    p.add_argument("--demo", action="store_true")
    args = p.parse_args()
    env = {"+": FUN(INT, FUN(INT, INT)), "not": FUN(BOOL, BOOL), "==": FUN(INT, FUN(INT, BOOL))}
    examples = [
        ("42", 42),
        ("true", True),
        ("identity", ("lambda", "x", "x")),
        ("let", ("let", "f", ("lambda", "x", ("+", "x")), ("f", 5))),
        ("if", ("if", True, 1, 2)),
    ]
    for name, expr in examples:
        try:
            t, _ = infer(expr, env, {})
            print(f"  {name}: {t}")
        except TypeError as e:
            print(f"  {name}: Error: {e}")

if __name__ == "__main__":
    main()
