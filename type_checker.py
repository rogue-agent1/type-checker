#!/usr/bin/env python3
"""Simple type checker for a mini language."""
class Type:
    def __init__(self,name,params=None): self.name=name;self.params=params or []
    def __eq__(self,o): return self.name==o.name and self.params==o.params
    def __repr__(self): 
        if self.params: return f"{self.name}<{','.join(str(p) for p in self.params)}>"
        return self.name
INT=Type("int");FLOAT=Type("float");BOOL=Type("bool");STRING=Type("str");VOID=Type("void")
def list_of(t): return Type("list",[t])
def func_type(params,ret): return Type("fn",params+[ret])
class TypeEnv:
    def __init__(self,parent=None): self.bindings={};self.parent=parent
    def define(self,name,typ): self.bindings[name]=typ
    def lookup(self,name):
        if name in self.bindings: return self.bindings[name]
        if self.parent: return self.parent.lookup(name)
        raise TypeError(f"Undefined: {name}")
def check(expr,env):
    if isinstance(expr,int): return INT
    if isinstance(expr,float): return FLOAT
    if isinstance(expr,bool): return BOOL
    if isinstance(expr,str): return STRING
    if isinstance(expr,tuple):
        op=expr[0]
        if op in ("+","-","*","/"):
            lt=check(expr[1],env);rt=check(expr[2],env)
            if lt==INT and rt==INT: return INT
            if lt in (INT,FLOAT) and rt in (INT,FLOAT): return FLOAT
            if op=="+" and lt==STRING and rt==STRING: return STRING
            raise TypeError(f"Cannot {op} {lt} and {rt}")
        if op in ("==","!=","<",">","<=",">="):
            check(expr[1],env);check(expr[2],env);return BOOL
        if op=="if":
            ct=check(expr[1],env)
            if ct!=BOOL: raise TypeError(f"Condition must be bool, got {ct}")
            tt=check(expr[2],env);ft=check(expr[3],env)
            if tt!=ft: raise TypeError(f"Branch types differ: {tt} vs {ft}")
            return tt
        if op=="let": env.define(expr[1],check(expr[2],env));return check(expr[3],env)
        if op=="var": return env.lookup(expr[1])
    raise TypeError(f"Cannot type: {expr}")
if __name__=="__main__":
    env=TypeEnv()
    assert check(42,env)==INT
    assert check(("+",1,2),env)==INT
    assert check(("+",1,2.0),env)==FLOAT
    assert check(("==",1,2),env)==BOOL
    assert check(("if",True,1,2),env)==INT
    assert check(("let","x",42,("var","x")),env)==INT
    try: check(("+",1,"hi"),env);assert False
    except TypeError: pass
    print("Type checker OK")
