"""
compiler.py — CLI entry point for the Mini-C compiler.

Usage:
    python compiler.py [source_file]   (defaults to test_program.mc)

Stages executed:
    1. Lexer        — tokenise the source
    2. Parser       — build the AST
    3. Semantic     — symbol table + type checking
    4. TAC gen      — emit three-address code

Output:
    - Token stream  (stage 1)
    - Symbol table  (after stage 3)
    - Numbered TAC  (stage 4, also written to tac_output.txt)
"""

import sys
from lexer import lexer
from parser import parser
from semantic import SemanticAnalyzer
from tac_gen import TACGenerator


def divider(title):
    width = 62
    print()
    print('=' * width)
    print(f'  {title}')
    print('=' * width)


def run(source_file):
    try:
        with open(source_file, 'r') as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Error: cannot open '{source_file}'")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Stage 1 — Lexer
    # ------------------------------------------------------------------
    divider('STAGE 1: LEXER')
    lexer.lineno = 1
    lexer.input(source)
    tokens_found = list(lexer)           # consume full token stream
    for tok in tokens_found:
        print(f'  {tok.type:<12} {repr(tok.value):<18} line {tok.lineno}')
    print(f'\n  {len(tokens_found)} tokens produced.')

    # ------------------------------------------------------------------
    # Stage 2 — Parser
    # ------------------------------------------------------------------
    divider('STAGE 2: PARSER  (building AST)')
    lexer.lineno = 1                     # reset line counter for parse pass
    ast = parser.parse(source, lexer=lexer)
    if ast is None:
        print('  Parse failed — aborting.')
        sys.exit(1)
    print('  AST built successfully.')

    # ------------------------------------------------------------------
    # Stage 3 — Semantic analysis
    # ------------------------------------------------------------------
    divider('STAGE 3: SEMANTIC ANALYSIS')
    analyzer = SemanticAnalyzer()
    errors = analyzer.analyze(ast)

    if errors:
        print(f'  {len(errors)} semantic error(s) found:\n')
        for err in errors:
            print(f'    {err}')
        print()
        print('  Halting — fix errors before TAC generation.')
        sys.exit(1)

    print('  No semantic errors.\n')
    divider('SYMBOL TABLE')
    analyzer.symbol_table.print_table()

    # ------------------------------------------------------------------
    # Stage 4 — TAC generation
    # ------------------------------------------------------------------
    divider('STAGE 4: THREE-ADDRESS CODE')
    gen = TACGenerator()
    gen.generate(ast)
    gen.print_instructions()
    gen.write_to_file('tac_output.txt')
    print(f'\n  {len(gen.instructions)} instructions written to tac_output.txt')


if __name__ == '__main__':
    source_file = sys.argv[1] if len(sys.argv) > 1 else 'test_program.mc'
    run(source_file)
