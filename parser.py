import ply.yacc as yacc
from lexer import tokens, lexer   # tokens list required by PLY in this module
from ast_nodes import (
    Program, VarDecl, ArrayDecl, Assign, BinOp, UnaryMinus,
    IntLit, FloatLit, Identifier, ArrayAccess,
    If, While, For, Print, Block
)

# ---------------------------------------------------------------------------
# Operator precedence  (lowest → highest)
# IFX is a dummy token used to resolve the dangling-else shift/reduce conflict:
# giving ELSE higher precedence than IFX makes the parser shift on ELSE,
# attaching it to the nearest if.
# ---------------------------------------------------------------------------
precedence = (
    ('nonassoc', 'IFX'),
    ('nonassoc', 'ELSE'),
    ('left',     'EQ', 'NE'),
    ('left',     'LT', 'GT', 'LE', 'GE'),
    ('left',     'PLUS', 'MINUS'),
    ('left',     'TIMES', 'DIVIDE'),
    ('right',    'UMINUS'),
)

# ---------------------------------------------------------------------------
# Top-level
# ---------------------------------------------------------------------------
def p_program(p):
    'program : stmt_list'
    p[0] = Program(p[1])

def p_stmt_list_multi(p):
    'stmt_list : stmt_list stmt'
    p[0] = p[1] + [p[2]]

def p_stmt_list_empty(p):
    'stmt_list : empty'
    p[0] = []

# ---------------------------------------------------------------------------
# Statements
# ---------------------------------------------------------------------------
def p_stmt_var_decl(p):
    'stmt : var_decl'
    p[0] = p[1]

def p_stmt_array_decl(p):
    'stmt : array_decl'
    p[0] = p[1]

def p_stmt_assign(p):
    'stmt : assign_stmt'
    p[0] = p[1]

def p_stmt_if(p):
    'stmt : if_stmt'
    p[0] = p[1]

def p_stmt_while(p):
    'stmt : while_stmt'
    p[0] = p[1]

def p_stmt_for(p):
    'stmt : for_stmt'
    p[0] = p[1]

def p_stmt_print(p):
    'stmt : print_stmt'
    p[0] = p[1]

def p_stmt_block(p):
    'stmt : block'
    p[0] = p[1]

# ---------------------------------------------------------------------------
# Variable / array declarations
# ---------------------------------------------------------------------------
def p_var_decl_init(p):
    'var_decl : type ID ASSIGN expr SEMICOLON'
    p[0] = VarDecl(p[1], p[2], p[4], p.lineno(2))

def p_var_decl_no_init(p):
    'var_decl : type ID SEMICOLON'
    p[0] = VarDecl(p[1], p[2], None, p.lineno(2))

def p_array_decl(p):
    'array_decl : type ID LBRACKET INT_LIT RBRACKET SEMICOLON'
    p[0] = ArrayDecl(p[1], p[2], p[4], p.lineno(2))

# ---------------------------------------------------------------------------
# Assignment
# ---------------------------------------------------------------------------
def p_assign_var(p):
    'assign_stmt : ID ASSIGN expr SEMICOLON'
    p[0] = Assign(Identifier(p[1], p.lineno(1)), p[3], p.lineno(1))

def p_assign_array(p):
    'assign_stmt : ID LBRACKET expr RBRACKET ASSIGN expr SEMICOLON'
    p[0] = Assign(ArrayAccess(p[1], p[3], p.lineno(1)), p[6], p.lineno(1))

# ---------------------------------------------------------------------------
# If / if-else
# ---------------------------------------------------------------------------
def p_if_else(p):
    'if_stmt : IF LPAREN expr RPAREN stmt ELSE stmt'
    p[0] = If(p[3], p[5], p[7], p.lineno(1))

def p_if_only(p):
    'if_stmt : IF LPAREN expr RPAREN stmt %prec IFX'
    p[0] = If(p[3], p[5], None, p.lineno(1))

# ---------------------------------------------------------------------------
# While
# ---------------------------------------------------------------------------
def p_while(p):
    'while_stmt : WHILE LPAREN expr RPAREN stmt'
    p[0] = While(p[3], p[5], p.lineno(1))

# ---------------------------------------------------------------------------
# For loop
# for ( for_init ; for_cond ; for_update ) stmt
# ---------------------------------------------------------------------------
def p_for(p):
    'for_stmt : FOR LPAREN for_init SEMICOLON for_cond SEMICOLON for_update RPAREN stmt'
    p[0] = For(p[3], p[5], p[7], p[9], p.lineno(1))

def p_for_init_decl(p):
    'for_init : type ID ASSIGN expr'
    p[0] = VarDecl(p[1], p[2], p[4], p.lineno(2))

def p_for_init_assign(p):
    'for_init : ID ASSIGN expr'
    p[0] = Assign(Identifier(p[1], p.lineno(1)), p[3], p.lineno(1))

def p_for_init_empty(p):
    'for_init : empty'
    p[0] = None

def p_for_cond_expr(p):
    'for_cond : expr'
    p[0] = p[1]

def p_for_cond_empty(p):
    'for_cond : empty'
    p[0] = None

def p_for_update_assign(p):
    'for_update : ID ASSIGN expr'
    p[0] = Assign(Identifier(p[1], p.lineno(1)), p[3], p.lineno(1))

def p_for_update_empty(p):
    'for_update : empty'
    p[0] = None

# ---------------------------------------------------------------------------
# Print
# ---------------------------------------------------------------------------
def p_print(p):
    'print_stmt : PRINT LPAREN expr RPAREN SEMICOLON'
    p[0] = Print(p[3], p.lineno(1))

# ---------------------------------------------------------------------------
# Block
# ---------------------------------------------------------------------------
def p_block(p):
    'block : LBRACE stmt_list RBRACE'
    p[0] = Block(p[2])

# ---------------------------------------------------------------------------
# Type keyword
# ---------------------------------------------------------------------------
def p_type_int(p):
    'type : INT'
    p[0] = 'int'

def p_type_float(p):
    'type : FLOAT'
    p[0] = 'float'

# ---------------------------------------------------------------------------
# Expressions (with precedence climbing via PLY's %prec)
# ---------------------------------------------------------------------------
def p_expr_binop(p):
    '''expr : expr PLUS   expr
            | expr MINUS  expr
            | expr TIMES  expr
            | expr DIVIDE expr
            | expr LT     expr
            | expr GT     expr
            | expr LE     expr
            | expr GE     expr
            | expr EQ     expr
            | expr NE     expr'''
    p[0] = BinOp(p[2], p[1], p[3], p.lineno(2))

def p_expr_uminus(p):
    'expr : MINUS expr %prec UMINUS'
    p[0] = UnaryMinus(p[2], p.lineno(1))

def p_expr_group(p):
    'expr : LPAREN expr RPAREN'
    p[0] = p[2]

def p_expr_array_access(p):
    'expr : ID LBRACKET expr RBRACKET'
    p[0] = ArrayAccess(p[1], p[3], p.lineno(1))

def p_expr_id(p):
    'expr : ID'
    p[0] = Identifier(p[1], p.lineno(1))

def p_expr_int_lit(p):
    'expr : INT_LIT'
    p[0] = IntLit(p[1], p.lineno(1))

def p_expr_float_lit(p):
    'expr : FLOAT_LIT'
    p[0] = FloatLit(p[1], p.lineno(1))

# ---------------------------------------------------------------------------
# Empty production
# ---------------------------------------------------------------------------
def p_empty(p):
    'empty :'
    p[0] = None

# ---------------------------------------------------------------------------
# Error
# ---------------------------------------------------------------------------
def p_error(p):
    if p:
        print(f"  [Parser] Syntax error at '{p.value}' (line {p.lineno})")
    else:
        print("  [Parser] Syntax error at EOF")

# ---------------------------------------------------------------------------
# Build the parser (suppress table dump to keep output clean)
# ---------------------------------------------------------------------------
parser = yacc.yacc(debug=False, write_tables=False)
