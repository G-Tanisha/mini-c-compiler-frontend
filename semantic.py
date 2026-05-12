from ast_nodes import (
    Program, VarDecl, ArrayDecl, Assign, BinOp, UnaryMinus,
    IntLit, FloatLit, Identifier, ArrayAccess,
    If, While, For, Print, Block
)


# ---------------------------------------------------------------------------
# Symbol table
# ---------------------------------------------------------------------------
class SymbolTable:
    def __init__(self):
        self.scopes = [{}]     # stack; index 0 = global scope
        self.all_decls = []    # ordered list of every declaration (for printing)

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    def declare(self, name, sym_type, lineno):
        """Add name to the current (innermost) scope.
        Returns False if the name is already declared in this exact scope."""
        level = len(self.scopes) - 1
        if name in self.scopes[-1]:
            return False
        entry = {'type': sym_type, 'scope': level, 'line': lineno}
        self.scopes[-1][name] = entry
        self.all_decls.append({'name': name, **entry})
        return True

    def lookup(self, name):
        """Search from innermost to outermost scope."""
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def print_table(self):
        header = f"{'Name':<15} {'Type':<10} {'Scope':<8} {'Line'}"
        print(header)
        print('-' * len(header))
        for e in self.all_decls:
            print(f"  {e['name']:<13} {e['type']:<10} {e['scope']:<8} {e['line']}")


# ---------------------------------------------------------------------------
# Semantic analyser — visitor pattern
# ---------------------------------------------------------------------------
class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors = []

    def error(self, msg, lineno):
        self.errors.append(f"Line {lineno}: {msg}")

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def analyze(self, node):
        self.visit(node)
        return self.errors

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
    # Visitors — each expression visitor returns its type string
    # ------------------------------------------------------------------
    def visit_Program(self, node):
        for stmt in node.stmts:
            self.visit(stmt)

    def visit_VarDecl(self, node):
        init_type = None
        if node.init is not None:
            init_type = self.visit(node.init)

        if init_type is not None and node.var_type == 'int' and init_type == 'float':
            self.error(
                f"Cannot assign float expression to int variable '{node.name}'",
                node.lineno
            )

        if not self.symbol_table.declare(node.name, node.var_type, node.lineno):
            self.error(
                f"Variable '{node.name}' already declared in this scope",
                node.lineno
            )

    def visit_ArrayDecl(self, node):
        array_type = f'{node.var_type}[]'
        if not self.symbol_table.declare(node.name, array_type, node.lineno):
            self.error(
                f"Variable '{node.name}' already declared in this scope",
                node.lineno
            )

    def visit_Assign(self, node):
        val_type = self.visit(node.value)

        if isinstance(node.target, Identifier):
            sym = self.symbol_table.lookup(node.target.name)
            if sym is None:
                self.error(f"Undeclared variable '{node.target.name}'", node.lineno)
            else:
                if sym['type'].endswith('[]'):
                    self.error(
                        f"Array '{node.target.name}' used without index in assignment",
                        node.lineno
                    )
                elif sym['type'] == 'int' and val_type == 'float':
                    self.error(
                        f"Cannot assign float to int variable '{node.target.name}'",
                        node.lineno
                    )

        elif isinstance(node.target, ArrayAccess):
            sym = self.symbol_table.lookup(node.target.name)
            if sym is None:
                self.error(f"Undeclared array '{node.target.name}'", node.lineno)
            elif not sym['type'].endswith('[]'):
                self.error(f"'{node.target.name}' is not an array", node.lineno)
            else:
                elem_type = sym['type'].replace('[]', '')
                if elem_type == 'int' and val_type == 'float':
                    self.error(
                        f"Cannot assign float to int array '{node.target.name}'",
                        node.lineno
                    )

            idx_type = self.visit(node.target.index)
            if idx_type is not None and idx_type != 'int':
                self.error(
                    f"Array index must be int, got '{idx_type}'",
                    node.lineno
                )

    def visit_BinOp(self, node):
        left_type  = self.visit(node.left)
        right_type = self.visit(node.right)

        # Relational operators produce an int (boolean) result
        if node.op in ('<', '>', '<=', '>=', '==', '!='):
            return 'int'

        # Arithmetic: float wins over int
        if 'float' in (left_type, right_type):
            return 'float'
        return 'int'

    def visit_UnaryMinus(self, node):
        return self.visit(node.operand)

    def visit_IntLit(self, node):
        return 'int'

    def visit_FloatLit(self, node):
        return 'float'

    def visit_Identifier(self, node):
        sym = self.symbol_table.lookup(node.name)
        if sym is None:
            self.error(f"Undeclared variable '{node.name}'", node.lineno)
            return 'int'   # default prevents cascading errors
        if sym['type'].endswith('[]'):
            self.error(f"Array '{node.name}' used without index", node.lineno)
            return sym['type'].replace('[]', '')
        return sym['type']

    def visit_ArrayAccess(self, node):
        sym = self.symbol_table.lookup(node.name)
        if sym is None:
            self.error(f"Undeclared variable '{node.name}'", node.lineno)
            return 'int'
        if not sym['type'].endswith('[]'):
            self.error(f"'{node.name}' is not an array", node.lineno)
            return 'int'

        idx_type = self.visit(node.index)
        if idx_type is not None and idx_type != 'int':
            self.error(
                f"Array index must be int, got '{idx_type}'",
                node.lineno
            )
        return sym['type'].replace('[]', '')

    def visit_If(self, node):
        self.visit(node.condition)
        self.visit(node.then_body)
        if node.else_body is not None:
            self.visit(node.else_body)

    def visit_While(self, node):
        self.visit(node.condition)
        self.visit(node.body)

    def visit_For(self, node):
        # The for header gets its own scope so the init variable (e.g. int j)
        # is scoped to the loop and not visible after it.
        self.symbol_table.enter_scope()
        if node.init is not None:
            self.visit(node.init)
        if node.condition is not None:
            self.visit(node.condition)
        if node.update is not None:
            self.visit(node.update)
        self.visit(node.body)
        self.symbol_table.exit_scope()

    def visit_Print(self, node):
        self.visit(node.expr)

    def visit_Block(self, node):
        self.symbol_table.enter_scope()
        for stmt in node.stmts:
            self.visit(stmt)
        self.symbol_table.exit_scope()
