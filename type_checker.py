#!/usr/bin/env python3
"""type_checker - Simple typed lambda calculus type checker."""
import argparse, sys

class Type:
    pass

class TInt(Type):
    def __repr__(self): return "Int"
    def __eq__(self, other): return isinstance(other, TInt)
    def __hash__(self): return hash("Int")

class TBool(Type):
    def __repr__(self): return "Bool"
    def __eq__(self, other): return isinstance(other, TBool)
    def __hash__(self): return hash("Bool")

class TFun(Type):
    def __init__(self, arg, ret): self.arg = arg; self.ret = ret
    def __repr__(self): return f"({self.arg} -> {self.ret})"
    def __eq__(self, other): return isinstance(other, TFun) and self.arg == other.arg and self.ret == other.ret
    def __hash__(self): return hash(("Fun", self.arg, self.ret))

# AST
class Lit:
    def __init__(self, val, ty): self.val = val; self.ty = ty
class Var:
    def __init__(self, name): self.name = name
class Lam:
    def __init__(self, param, param_ty, body): self.param = param; self.param_ty = param_ty; self.body = body
class App:
    def __init__(self, fn, arg): self.fn = fn; self.arg = arg
class If:
    def __init__(self, cond, then, else_): self.cond = cond; self.then = then; self.else_ = else_
class Let:
    def __init__(self, name, val, body): self.name = name; self.val = val; self.body = body
class BinOp:
    def __init__(self, op, left, right): self.op = op; self.left = left; self.right = right

def typecheck(expr, env=None):
    if env is None: env = {}
    if isinstance(expr, Lit): return expr.ty
    if isinstance(expr, Var):
        if expr.name in env: return env[expr.name]
        raise TypeError(f"Unbound variable: {expr.name}")
    if isinstance(expr, Lam):
        new_env = dict(env); new_env[expr.param] = expr.param_ty
        ret_ty = typecheck(expr.body, new_env)
        return TFun(expr.param_ty, ret_ty)
    if isinstance(expr, App):
        fn_ty = typecheck(expr.fn, env)
        arg_ty = typecheck(expr.arg, env)
        if not isinstance(fn_ty, TFun): raise TypeError(f"Not a function: {fn_ty}")
        if fn_ty.arg != arg_ty: raise TypeError(f"Type mismatch: expected {fn_ty.arg}, got {arg_ty}")
        return fn_ty.ret
    if isinstance(expr, If):
        cond_ty = typecheck(expr.cond, env)
        if cond_ty != TBool(): raise TypeError(f"Condition must be Bool, got {cond_ty}")
        then_ty = typecheck(expr.then, env)
        else_ty = typecheck(expr.else_, env)
        if then_ty != else_ty: raise TypeError(f"Branch mismatch: {then_ty} vs {else_ty}")
        return then_ty
    if isinstance(expr, Let):
        val_ty = typecheck(expr.val, env)
        new_env = dict(env); new_env[expr.name] = val_ty
        return typecheck(expr.body, new_env)
    if isinstance(expr, BinOp):
        lt = typecheck(expr.left, env); rt = typecheck(expr.right, env)
        if expr.op in ("+","-","*","/"):
            if lt != TInt() or rt != TInt(): raise TypeError(f"{expr.op}: expected Int, got {lt}, {rt}")
            return TInt()
        if expr.op in ("==","<",">"):
            if lt != rt: raise TypeError(f"{expr.op}: type mismatch {lt} vs {rt}")
            return TBool()
    raise TypeError(f"Unknown expression: {type(expr)}")

def main():
    p = argparse.ArgumentParser(description="Type checker")
    p.add_argument("--demo", action="store_true", default=True)
    a = p.parse_args()
    examples = [
        ("42", Lit(42, TInt())),
        ("true", Lit(True, TBool())),
        ("λx:Int. x+1", Lam("x", TInt(), BinOp("+", Var("x"), Lit(1, TInt())))),
        ("(λx:Int. x+1) 5", App(Lam("x", TInt(), BinOp("+", Var("x"), Lit(1, TInt()))), Lit(5, TInt()))),
        ("if true then 1 else 2", If(Lit(True, TBool()), Lit(1, TInt()), Lit(2, TInt()))),
        ("let x = 5 in x + 3", Let("x", Lit(5, TInt()), BinOp("+", Var("x"), Lit(3, TInt())))),
    ]
    for desc, expr in examples:
        try:
            ty = typecheck(expr)
            print(f"  {desc} : {ty}")
        except TypeError as e:
            print(f"  {desc} : ERROR - {e}")
    # Type error example
    print("\nType errors:")
    errors = [
        ("1 + true", BinOp("+", Lit(1, TInt()), Lit(True, TBool()))),
        ("if 1 then 2 else 3", If(Lit(1, TInt()), Lit(2, TInt()), Lit(3, TInt()))),
    ]
    for desc, expr in errors:
        try:
            ty = typecheck(expr)
            print(f"  {desc} : {ty}")
        except TypeError as e:
            print(f"  {desc} : ERROR - {e}")

if __name__ == "__main__": main()
