import ply.lex as lex

# ---------------------------------------------------------------------------
# Reserved keywords — the lexer maps matching identifiers to their token type
# ---------------------------------------------------------------------------
reserved = {
    'int':   'INT',
    'float': 'FLOAT',
    'if':    'IF',
    'else':  'ELSE',
    'while': 'WHILE',
    'for':   'FOR',
    'print': 'PRINT',
}

tokens = [
    'ID', 'INT_LIT', 'FLOAT_LIT',
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE',
    'LE', 'GE', 'EQ', 'NE', 'LT', 'GT',
    'ASSIGN',
    'LPAREN', 'RPAREN',
    'LBRACE', 'RBRACE',
    'LBRACKET', 'RBRACKET',
    'SEMICOLON', 'COMMA',
] + list(reserved.values())

# ---------------------------------------------------------------------------
# Operators — function rules so multi-char operators are matched before
# their single-char prefixes (PLY adds function rules in source order)
# ---------------------------------------------------------------------------
def t_LE(t):
    r'<='
    return t

def t_GE(t):
    r'>='
    return t

def t_EQ(t):
    r'=='
    return t

def t_NE(t):
    r'!='
    return t

def t_LT(t):
    r'<'
    return t

def t_GT(t):
    r'>'
    return t

def t_ASSIGN(t):
    r'='
    return t

# Simple single-character operators as string rules
t_PLUS      = r'\+'
t_MINUS     = r'-'
t_TIMES     = r'\*'
t_DIVIDE    = r'/'
t_LPAREN    = r'\('
t_RPAREN    = r'\)'
t_LBRACE    = r'\{'
t_RBRACE    = r'\}'
t_LBRACKET  = r'\['
t_RBRACKET  = r'\]'
t_SEMICOLON = r';'
t_COMMA     = r','

# ---------------------------------------------------------------------------
# Literals — float must be checked before int so "3.14" isn't split
# ---------------------------------------------------------------------------
def t_FLOAT_LIT(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t

def t_INT_LIT(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'ID')
    return t

# ---------------------------------------------------------------------------
# Whitespace, newlines, comments
# ---------------------------------------------------------------------------
def t_COMMENT(t):
    r'//[^\n]*'
    pass  # discard line comments

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

t_ignore = ' \t\r'

def t_error(t):
    print(f"  [Lexer] Illegal character '{t.value[0]}' at line {t.lexer.lineno}")
    t.lexer.skip(1)

# ---------------------------------------------------------------------------
# Build the lexer
# ---------------------------------------------------------------------------
lexer = lex.lex()
