class Node:
    pass

class Program(Node):
    def __init__(self, stmts):
        self.stmts = stmts

class VarDecl(Node):
    def __init__(self, var_type, name, init=None, lineno=0):
        self.var_type = var_type   # 'int' or 'float'
        self.name = name
        self.init = init           # expression Node or None
        self.lineno = lineno

class ArrayDecl(Node):
    def __init__(self, var_type, name, size, lineno=0):
        self.var_type = var_type   # 'int'
        self.name = name
        self.size = size           # integer literal
        self.lineno = lineno

class Assign(Node):
    def __init__(self, target, value, lineno=0):
        self.target = target       # Identifier or ArrayAccess
        self.value = value
        self.lineno = lineno

class BinOp(Node):
    def __init__(self, op, left, right, lineno=0):
        self.op = op
        self.left = left
        self.right = right
        self.lineno = lineno

class UnaryMinus(Node):
    def __init__(self, operand, lineno=0):
        self.operand = operand
        self.lineno = lineno

class IntLit(Node):
    def __init__(self, value, lineno=0):
        self.value = value
        self.lineno = lineno

class FloatLit(Node):
    def __init__(self, value, lineno=0):
        self.value = value
        self.lineno = lineno

class Identifier(Node):
    def __init__(self, name, lineno=0):
        self.name = name
        self.lineno = lineno

class ArrayAccess(Node):
    def __init__(self, name, index, lineno=0):
        self.name = name
        self.index = index
        self.lineno = lineno

class If(Node):
    def __init__(self, condition, then_body, else_body=None, lineno=0):
        self.condition = condition
        self.then_body = then_body
        self.else_body = else_body
        self.lineno = lineno

class While(Node):
    def __init__(self, condition, body, lineno=0):
        self.condition = condition
        self.body = body
        self.lineno = lineno

class For(Node):
    def __init__(self, init, condition, update, body, lineno=0):
        self.init = init           # VarDecl, Assign, or None
        self.condition = condition # expression or None
        self.update = update       # Assign or None
        self.body = body
        self.lineno = lineno

class Print(Node):
    def __init__(self, expr, lineno=0):
        self.expr = expr
        self.lineno = lineno

class Block(Node):
    def __init__(self, stmts):
        self.stmts = stmts
