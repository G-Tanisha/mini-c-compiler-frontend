# Mini-C Compiler

A hand-written, four-stage compiler for a subset of C, built in Python using [PLY](https://github.com/dabeaz/ply) (Python Lex-Yacc). Every stage is implemented explicitly so the logic is readable and explainable.

---

## Language features

| Feature | Example |
|---|---|
| int / float declarations | `int x = 5;` `float y = 10.5;` |
| Uninitialized declaration | `int z;` |
| Int arrays | `int list[10];` |
| Arithmetic (`+ - * /`) | `z = x + 2;` |
| Relational (`< > <= >= == !=`) | `if (x < 10)` |
| If-else | `if (cond) { } else { }` |
| While loop | `while (i < 5) { }` |
| For loop | `for (int j = 0; j < 5; j = j + 1) { }` |
| Built-in print | `print(sum);` |
| Block scoping | Inner `{ }` creates a new scope |
| Type checking | `int bad = y;` → compile error |

---

## Project structure

```
compiler_assignment/
├── ast_nodes.py   — AST node classes (14 nodes)
├── lexer.py       — Stage 1: PLY tokenizer
├── parser.py      — Stage 2: LALR(1) grammar, builds AST
├── semantic.py    — Stage 3: symbol table + type checker
├── tac_gen.py     — Stage 4: three-address code generator
├── compiler.py    — CLI entry point
├── frontend.py    — Browser frontend with AST diagram view
└── test_program.mc — sample Mini-C source
```

---

## Quick start

```bash
pip install ply
python compiler.py              # uses test_program.mc by default
python compiler.py myfile.mc    # or pass any .mc file
```

TAC output is also written to **`tac_output.txt`**.

## Browser frontend

```bash
python frontend.py
```

Open **http://localhost:8000**. The page lets you edit Mini-C source and view:
- token stream
- AST parse tree diagram
- semantic messages
- symbol table
- generated three-address code

---

## Compiler stages

### Stage 1 — Lexer (`lexer.py`)

Tokenizes the source using PLY's `lex` module. Handles:
- Reserved keywords: `int float if else while for print`
- Identifiers, integer literals, float literals
- Operators (multi-char operators `<=` `>=` `==` `!=` are matched before their single-char prefixes via ordered function rules)
- Line comments (`//`)
- Line-number tracking

### Stage 2 — Parser (`parser.py`)

Builds the AST using an LALR(1) grammar. Key decisions:
- Operator precedence (low → high): relational → additive → multiplicative → unary minus
- Dangling-else resolved with a dummy `IFX` precedence token so `else` always binds to the nearest `if`
- For-loop header grammar: `FOR ( for_init ; for_cond ; for_update ) stmt`
- All productions return typed AST nodes from `ast_nodes.py`

### Stage 3 — Semantic analysis (`semantic.py`)

Walks the AST with a visitor and maintains a **scope stack** (list of dicts).

**Symbol table columns:** `Name | Type | Scope level | Line`

Checks performed:
| Check | Example error |
|---|---|
| Undeclared variable | `x = y + 1` when `y` not declared |
| Duplicate declaration | `int x; int x;` in same scope |
| int ← float assignment | `int bad = 10.5;` |
| Array used without index | `print(list);` |
| Non-array used as array | `x[0] = 1;` when `x` is `int` |
| Array index must be int | `list[1.5]` |

Scoping rules:
- `Block { }` always opens its own scope
- `for` header opens a scope so the init variable (e.g. `int j`) is invisible after the loop

Compilation **halts** with printed errors if any semantic errors are found.

### Stage 4 — TAC generation (`tac_gen.py`)

Emits three-address code using temporaries `t1, t2, …` and labels `L1, L2, …`.

| Construct | Emitted TAC |
|---|---|
| Binary op | `t1 = a + b` |
| Unary minus | `t1 = -a` |
| Assignment | `x = t1` |
| Array write | `list[i] = t1` |
| Array read | `t1 = list[i]` |
| If-else | `ifFalse cond goto Lelse` … `goto Lend` … `Lelse:` … `Lend:` |
| While | `Lstart:` … `ifFalse cond goto Lend` … `goto Lstart` … `Lend:` |
| For | init … `Lstart:` … condition check … body … update … `goto Lstart` … `Lend:` |
| Print | `print val` |
| Array alloc | `alloc list[10]` |

---

## Example output (truncated)

```
SYMBOL TABLE
Name            Type       Scope    Line
-----------------------------------------
  x             int        0        6
  y             float      0        7
  z             int        0        8
  list          int[]      0        11
  i             int        0        29
  sum           int        0        37
  j             int        1        38    ← for-loop scope
  result        float      0        44
  x             int        1        49    ← inner block shadows outer x

THREE-ADDRESS CODE
    1: x = 5
    2: y = 10.5
    3: alloc list[10]
    ...
   10: t3 = x < 10
   11: ifFalse t3 goto L1
   12: print x
   13: goto L2
   14: L1:
   15: print z
   16: L2:
   ...
   30: L5:
   31: t7 = j < 5
   32: ifFalse t7 goto L6
   33: t8 = sum + j
   34: sum = t8
   35: t9 = j + 1
   36: j = t9
   37: goto L5
   38: L6:
```

---

## Triggering a type error

Uncomment the last line in `test_program.mc`:

```c
int bad = y;   // y is float — cannot assign to int
```

The compiler will catch it at stage 3 and halt:

```
Line 55: Cannot assign float expression to int variable 'bad'
Halting — fix errors before TAC generation.
```

---

## Dependencies

- Python 3.7+
- [PLY 3.11](https://pypi.org/project/ply/) (`pip install ply`)
