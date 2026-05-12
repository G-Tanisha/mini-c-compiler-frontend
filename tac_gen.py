from ast_nodes import (
    Program, VarDecl, ArrayDecl, Assign, BinOp, UnaryMinus,
    IntLit, FloatLit, Identifier, ArrayAccess,
    If, While, For, Print, Block
)


class TACGenerator:
    def __init__(self):
        self.instructions = []
        self._temp_n  = 0
        self._label_n = 0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _new_temp(self):
        self._temp_n += 1
        return f't{self._temp_n}'

    def _new_label(self):
        self._label_n += 1
        return f'L{self._label_n}'

    def _emit(self, instr):
        self.instructions.append(instr)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def generate(self, ast):
        self.visit(ast)

    # ------------------------------------------------------------------
    # Dispatcher
    # ------------------------------------------------------------------
    def visit(self, node):
        if node is None:
            return None
        method = 'visit_' + type(node).__name__
        return getattr(self, method, self._noop)(node)

    def _noop(self, node):
        return None

    # ------------------------------------------------------------------
    # Statement visitors (return nothing; side-effect: emit instructions)
    # ------------------------------------------------------------------
    def visit_Program(self, node):
        for stmt in node.stmts:
            self.visit(stmt)

    def visit_VarDecl(self, node):
        if node.init is not None:
            src = self.visit(node.init)
            self._emit(f'{node.name} = {src}')

    def visit_ArrayDecl(self, node):
        # Reserve space annotation; no runtime allocation needed for TAC
        self._emit(f'alloc {node.name}[{node.size}]')

    def visit_Assign(self, node):
        val = self.visit(node.value)
        if isinstance(node.target, Identifier):
            self._emit(f'{node.target.name} = {val}')
        elif isinstance(node.target, ArrayAccess):
            idx = self.visit(node.target.index)
            self._emit(f'{node.target.name}[{idx}] = {val}')

    def visit_If(self, node):
        if node.else_body is not None:
            l_else = self._new_label()
            l_end  = self._new_label()
            cond = self.visit(node.condition)
            self._emit(f'ifFalse {cond} goto {l_else}')
            self.visit(node.then_body)
            self._emit(f'goto {l_end}')
            self._emit(f'{l_else}:')
            self.visit(node.else_body)
            self._emit(f'{l_end}:')
        else:
            l_end = self._new_label()
            cond = self.visit(node.condition)
            self._emit(f'ifFalse {cond} goto {l_end}')
            self.visit(node.then_body)
            self._emit(f'{l_end}:')

    def visit_While(self, node):
        l_start = self._new_label()
        l_end   = self._new_label()
        self._emit(f'{l_start}:')
        cond = self.visit(node.condition)
        self._emit(f'ifFalse {cond} goto {l_end}')
        self.visit(node.body)
        self._emit(f'goto {l_start}')
        self._emit(f'{l_end}:')

    def visit_For(self, node):
        # init code runs once before the loop
        if node.init is not None:
            self.visit(node.init)

        l_start = self._new_label()
        l_end   = self._new_label()
        self._emit(f'{l_start}:')

        if node.condition is not None:
            cond = self.visit(node.condition)
            self._emit(f'ifFalse {cond} goto {l_end}')

        self.visit(node.body)

        # update runs at the bottom of every iteration
        if node.update is not None:
            self.visit(node.update)

        self._emit(f'goto {l_start}')
        self._emit(f'{l_end}:')

    def visit_Print(self, node):
        val = self.visit(node.expr)
        self._emit(f'print {val}')

    def visit_Block(self, node):
        for stmt in node.stmts:
            self.visit(stmt)

    # ------------------------------------------------------------------
    # Expression visitors — return the operand name / temp holding result
    # ------------------------------------------------------------------
    def visit_BinOp(self, node):
        left  = self.visit(node.left)
        right = self.visit(node.right)
        t = self._new_temp()
        self._emit(f'{t} = {left} {node.op} {right}')
        return t

    def visit_UnaryMinus(self, node):
        operand = self.visit(node.operand)
        t = self._new_temp()
        self._emit(f'{t} = -{operand}')
        return t

    def visit_IntLit(self, node):
        return str(node.value)

    def visit_FloatLit(self, node):
        return str(node.value)

    def visit_Identifier(self, node):
        return node.name

    def visit_ArrayAccess(self, node):
        idx = self.visit(node.index)
        t = self._new_temp()
        self._emit(f'{t} = {node.name}[{idx}]')
        return t

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------
    def print_instructions(self):
        for i, instr in enumerate(self.instructions, 1):
            print(f'  {i:3}: {instr}')

    def write_to_file(self, filename):
        with open(filename, 'w') as f:
            for i, instr in enumerate(self.instructions, 1):
                f.write(f'{i:3}: {instr}\n')
