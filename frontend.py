"""
frontend.py - browser UI for the Mini-C compiler.

Run:
    python frontend.py

Then open:
    http://localhost:8000
"""

from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import StringIO
import json
import os
import webbrowser

from ast_nodes import (
    Program, VarDecl, ArrayDecl, Assign, BinOp, UnaryMinus,
    IntLit, FloatLit, Identifier, ArrayAccess,
    If, While, For, Print, Block
)
from lexer import lexer
from parser import parser
from semantic import SemanticAnalyzer
from tac_gen import TACGenerator


HOST = "localhost"
PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SOURCE = os.path.join(BASE_DIR, "test_program.mc")


HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mini-C Compiler Frontend</title>
  <style>
    :root {
      --ink: #1d2433;
      --muted: #667085;
      --line: #d7dce5;
      --paper: #f7f8fb;
      --panel: #ffffff;
      --accent: #176b87;
      --accent-2: #b54708;
      --ok: #067647;
      --bad: #b42318;
      --code: #111827;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      color: var(--ink);
      background: var(--paper);
      font-family: Inter, Segoe UI, Arial, sans-serif;
    }

    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 16px 22px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
    }

    h1 {
      margin: 0;
      font-size: 20px;
      line-height: 1.2;
      letter-spacing: 0;
    }

    .status {
      min-width: 160px;
      text-align: right;
      color: var(--muted);
      font-size: 14px;
    }

    main {
      display: grid;
      grid-template-columns: minmax(340px, 0.95fr) minmax(420px, 1.25fr);
      gap: 16px;
      padding: 16px;
      min-height: calc(100vh - 65px);
    }

    .editor,
    .results {
      min-width: 0;
    }

    .toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 10px;
    }

    .toolbar h2,
    .panel-title {
      margin: 0;
      font-size: 15px;
      line-height: 1.2;
      letter-spacing: 0;
    }

    button {
      border: 1px solid #125a70;
      background: var(--accent);
      color: white;
      min-height: 36px;
      padding: 0 14px;
      border-radius: 6px;
      font: inherit;
      font-weight: 600;
      cursor: pointer;
    }

    button.secondary {
      color: var(--accent);
      background: white;
      border-color: #8bb7c5;
    }

    textarea {
      width: 100%;
      min-height: calc(100vh - 145px);
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      color: var(--code);
      background: var(--panel);
      font: 14px/1.5 Consolas, "Courier New", monospace;
      tab-size: 4;
    }

    .tabs {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
      margin-bottom: 10px;
    }

    .tab {
      border-color: var(--line);
      background: white;
      color: var(--ink);
      min-height: 34px;
      padding: 0 12px;
      font-weight: 600;
    }

    .tab.active {
      border-color: #ad6a18;
      background: #fff4e5;
      color: #7a3d00;
    }

    .panel {
      display: none;
      min-height: calc(100vh - 145px);
      max-height: calc(100vh - 145px);
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      padding: 14px;
    }

    .panel.active { display: block; }

    .summary {
      display: grid;
      grid-template-columns: repeat(3, minmax(110px, 1fr));
      gap: 10px;
      margin-bottom: 14px;
    }

    .metric {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      background: #fbfcff;
    }

    .metric strong {
      display: block;
      font-size: 22px;
      line-height: 1.1;
    }

    .metric span {
      color: var(--muted);
      font-size: 12px;
    }

    pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      font: 13px/1.5 Consolas, "Courier New", monospace;
      color: var(--code);
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }

    th,
    td {
      padding: 8px 9px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }

    th {
      position: sticky;
      top: 0;
      background: #f2f5f9;
      z-index: 1;
    }

    .empty {
      color: var(--muted);
      padding: 12px 0;
    }

    .error {
      color: var(--bad);
      font-weight: 600;
    }

    .ok {
      color: var(--ok);
      font-weight: 600;
    }

    .ast-canvas {
      display: inline-block;
      padding: 10px;
    }

    .ast-svg {
      display: block;
      background:
        linear-gradient(#eef2f7 1px, transparent 1px),
        linear-gradient(90deg, #eef2f7 1px, transparent 1px);
      background-size: 24px 24px;
      border-radius: 8px;
    }

    .ast-link {
      stroke: #8ea0b8;
      stroke-width: 2;
      fill: none;
    }

    .ast-node rect {
      fill: #ffffff;
      stroke: #176b87;
      stroke-width: 1.5;
      rx: 8;
    }

    .ast-node.depth-0 rect {
      fill: #e8f5f8;
      stroke-width: 2;
    }

    .ast-node text {
      text-anchor: middle;
      font-family: Consolas, "Courier New", monospace;
      letter-spacing: 0;
      pointer-events: none;
    }

    .ast-label {
      fill: #164e63;
      font-size: 13px;
      font-weight: 700;
    }

    .ast-meta {
      fill: #92400e;
      font-size: 11px;
    }

    .ast-note {
      margin-bottom: 10px;
      color: var(--muted);
      font-size: 13px;
    }

    .ast-meta-text {
      color: #92400e;
      font-family: Consolas, "Courier New", monospace;
      font-size: 12px;
    }

    @media (max-width: 900px) {
      header {
        align-items: flex-start;
        flex-direction: column;
      }

      .status { text-align: left; }

      main {
        grid-template-columns: 1fr;
      }

      textarea,
      .panel {
        min-height: 420px;
        max-height: none;
      }
    }
  </style>
</head>
<body>
  <header>
    <h1>Mini-C Compiler Frontend</h1>
    <div class="status" id="status">Ready</div>
  </header>

  <main>
    <section class="editor">
      <div class="toolbar">
        <h2>Source Code</h2>
        <div>
          <button class="secondary" id="sampleBtn" type="button">Sample</button>
          <button id="compileBtn" type="button">Compile</button>
        </div>
      </div>
      <textarea id="source" spellcheck="false"></textarea>
    </section>

    <section class="results">
      <div class="tabs" role="tablist" aria-label="Compiler output">
        <button class="tab active" data-tab="overview" type="button">Overview</button>
        <button class="tab" data-tab="ast" type="button">AST Diagram</button>
        <button class="tab" data-tab="tokens" type="button">Tokens</button>
        <button class="tab" data-tab="symbols" type="button">Symbols</button>
        <button class="tab" data-tab="tac" type="button">TAC</button>
        <button class="tab" data-tab="raw" type="button">Raw</button>
      </div>

      <div class="panel active" id="overview"></div>
      <div class="panel" id="ast"></div>
      <div class="panel" id="tokens"></div>
      <div class="panel" id="symbols"></div>
      <div class="panel" id="tac"></div>
      <div class="panel" id="raw"></div>
    </section>
  </main>

  <script>
    const sampleSource = __SAMPLE_SOURCE__;
    const source = document.querySelector("#source");
    const statusEl = document.querySelector("#status");
    const compileBtn = document.querySelector("#compileBtn");
    const sampleBtn = document.querySelector("#sampleBtn");
    const panels = [...document.querySelectorAll(".panel")];
    const tabs = [...document.querySelectorAll(".tab")];

    source.value = sampleSource;

    tabs.forEach(tab => {
      tab.addEventListener("click", () => {
        tabs.forEach(t => t.classList.toggle("active", t === tab));
        panels.forEach(panel => panel.classList.toggle("active", panel.id === tab.dataset.tab));
      });
    });

    sampleBtn.addEventListener("click", () => {
      source.value = sampleSource;
      compile();
    });

    compileBtn.addEventListener("click", compile);

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    function shorten(value, maxLength) {
      const text = String(value || "");
      return text.length > maxLength ? `${text.slice(0, maxLength - 3)}...` : text;
    }

    function renderCompactTree(node) {
      if (!node) return "";
      const meta = node.meta ? ` <span class="ast-meta-text">${escapeHtml(node.meta)}</span>` : "";
      const children = node.children && node.children.length
        ? `<ul>${node.children.map(child => `<li>${renderCompactTree(child)}</li>`).join("")}</ul>`
        : "";
      return `<strong>${escapeHtml(node.label)}</strong>${meta}${children}`;
    }

    function layoutAst(root) {
      const nodeWidth = 190;
      const nodeHeight = 58;
      const leafGap = 230;
      const levelGap = 118;
      const margin = 42;
      const positioned = [];
      const links = [];
      let leafIndex = 0;
      let maxDepth = 0;

      function place(node, depth, parent) {
        const children = node.children || [];
        maxDepth = Math.max(maxDepth, depth);

        let x;
        if (!children.length) {
          x = margin + leafIndex * leafGap;
          leafIndex += 1;
        } else {
          const childNodes = children.map(child => place(child, depth + 1, node));
          x = (childNodes[0].x + childNodes[childNodes.length - 1].x) / 2;
        }

        const item = {
          node,
          x,
          y: margin + depth * levelGap,
          depth,
          width: nodeWidth,
          height: nodeHeight,
        };
        positioned.push(item);
        if (parent) {
          links.push({ parent, child: item });
        }
        return item;
      }

      const rootItem = place(root, 0, null);
      links.forEach(link => {
        link.parent = positioned.find(item => item.node === link.parent);
      });

      return {
        nodes: positioned,
        links,
        width: Math.max(rootItem.x + margin + nodeWidth, leafIndex * leafGap + margin),
        height: margin * 2 + (maxDepth + 1) * levelGap,
      };
    }

    function renderAstDiagram(node) {
      if (!node) return '<div class="empty">No AST was built.</div>';

      let layout;
      try {
        layout = layoutAst(node);
      } catch (error) {
        return `
          <p class="error">Could not draw the AST diagram: ${escapeHtml(error.message)}</p>
          <div>${renderCompactTree(node)}</div>
        `;
      }

      const links = layout.links.map(link => {
        const x1 = link.parent.x;
        const y1 = link.parent.y + link.parent.height / 2;
        const x2 = link.child.x;
        const y2 = link.child.y - link.child.height / 2;
        const midY = (y1 + y2) / 2;
        return `<path class="ast-link" d="M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}" />`;
      }).join("");

      const nodes = layout.nodes.map(item => {
        const fullText = item.node.label + (item.node.meta ? " | " + item.node.meta : "");
        const label = shorten(item.node.label, 24);
        const meta = shorten(item.node.meta, 28);
        return `
          <g class="ast-node depth-${item.depth}" transform="translate(${item.x - item.width / 2}, ${item.y - item.height / 2})">
            <title>${escapeHtml(fullText)}</title>
            <rect width="${item.width}" height="${item.height}"></rect>
            <text x="${item.width / 2}" y="${meta ? 24 : 34}" class="ast-label">${escapeHtml(label)}</text>
            ${meta ? `<text x="${item.width / 2}" y="43" class="ast-meta">${escapeHtml(meta)}</text>` : ""}
          </g>
        `;
      }).join("");

      return `
        <div class="ast-note">${layout.nodes.length} AST node(s). Scroll sideways or down if the diagram is larger than the panel.</div>
        <div class="ast-canvas">
          <svg class="ast-svg" width="${layout.width}" height="${layout.height}" viewBox="0 0 ${layout.width} ${layout.height}" role="img" aria-label="AST parse tree diagram">
            ${links}
            ${nodes}
          </svg>
        </div>
      `;
    }

    function renderTokens(tokens) {
      if (!tokens.length) return '<div class="empty">No tokens.</div>';
      return `<table><thead><tr><th>Line</th><th>Type</th><th>Value</th></tr></thead><tbody>${
        tokens.map(tok => `<tr><td>${tok.line}</td><td>${escapeHtml(tok.type)}</td><td>${escapeHtml(tok.value)}</td></tr>`).join("")
      }</tbody></table>`;
    }

    function renderSymbols(symbols) {
      if (!symbols.length) return '<div class="empty">No symbols yet.</div>';
      return `<table><thead><tr><th>Name</th><th>Type</th><th>Scope</th><th>Line</th></tr></thead><tbody>${
        symbols.map(sym => `<tr><td>${escapeHtml(sym.name)}</td><td>${escapeHtml(sym.type)}</td><td>${sym.scope}</td><td>${sym.line}</td></tr>`).join("")
      }</tbody></table>`;
    }

    function renderOverview(data) {
      const state = data.ok ? '<span class="ok">Compilation successful</span>' : '<span class="error">Compilation stopped</span>';
      const messages = data.messages.length
        ? `<pre>${escapeHtml(data.messages.join("\n"))}</pre>`
        : '<div class="empty">No lexer, parser, or semantic errors.</div>';
      return `
        <div class="summary">
          <div class="metric"><strong>${data.tokens.length}</strong><span>tokens</span></div>
          <div class="metric"><strong>${data.symbols.length}</strong><span>symbols</span></div>
          <div class="metric"><strong>${data.tac.length}</strong><span>TAC lines</span></div>
        </div>
        <p>${state}</p>
        <h3 class="panel-title">Messages</h3>
        ${messages}
      `;
    }

    async function compile() {
      statusEl.textContent = "Compiling...";
      compileBtn.disabled = true;
      try {
        const response = await fetch("/api/compile", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ source: source.value })
        });
        const data = await response.json();
        document.querySelector("#overview").innerHTML = renderOverview(data);
        document.querySelector("#ast").innerHTML = renderAstDiagram(data.ast);
        document.querySelector("#tokens").innerHTML = renderTokens(data.tokens);
        document.querySelector("#symbols").innerHTML = renderSymbols(data.symbols);
        document.querySelector("#tac").innerHTML = data.tac.length
          ? `<pre>${escapeHtml(data.tac.map((line, i) => `${String(i + 1).padStart(3, " ")}: ${line}`).join("\n"))}</pre>`
          : '<div class="empty">No TAC generated.</div>';
        document.querySelector("#raw").innerHTML = `<pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
        statusEl.textContent = data.ok ? "Compiled" : "Needs fixes";
      } catch (error) {
        statusEl.textContent = "Request failed";
        document.querySelector("#overview").innerHTML = `<p class="error">${escapeHtml(error.message)}</p>`;
      } finally {
        compileBtn.disabled = false;
      }
    }

    compile();
  </script>
</body>
</html>
"""


def token_stream(source):
    lexer.lineno = 1
    lexer.input(source)
    return [
        {"type": tok.type, "value": repr(tok.value), "line": tok.lineno}
        for tok in lexer
    ]


def line(node):
    value = getattr(node, "lineno", 0)
    return f"line {value}" if value else ""


def tree(label, meta="", children=None):
    return {
        "label": label,
        "meta": meta,
        "children": [child for child in (children or []) if child is not None],
    }


def ast_to_tree(node, name=None):
    if node is None:
        return tree(name or "None")

    prefix = f"{name}: " if name else ""

    if isinstance(node, Program):
        return tree(prefix + "Program", f"{len(node.stmts)} statement(s)", [
            ast_to_tree(stmt, f"stmt {i + 1}") for i, stmt in enumerate(node.stmts)
        ])

    if isinstance(node, VarDecl):
        return tree(prefix + "VarDecl", f"{node.var_type} {node.name} {line(node)}", [
            ast_to_tree(node.init, "init") if node.init is not None else tree("init", "None")
        ])

    if isinstance(node, ArrayDecl):
        return tree(prefix + "ArrayDecl", f"{node.var_type} {node.name}[{node.size}] {line(node)}")

    if isinstance(node, Assign):
        return tree(prefix + "Assign", line(node), [
            ast_to_tree(node.target, "target"),
            ast_to_tree(node.value, "value"),
        ])

    if isinstance(node, BinOp):
        return tree(prefix + "BinOp", f"op {node.op} {line(node)}", [
            ast_to_tree(node.left, "left"),
            ast_to_tree(node.right, "right"),
        ])

    if isinstance(node, UnaryMinus):
        return tree(prefix + "UnaryMinus", line(node), [
            ast_to_tree(node.operand, "operand")
        ])

    if isinstance(node, IntLit):
        return tree(prefix + "IntLit", f"{node.value} {line(node)}")

    if isinstance(node, FloatLit):
        return tree(prefix + "FloatLit", f"{node.value} {line(node)}")

    if isinstance(node, Identifier):
        return tree(prefix + "Identifier", f"{node.name} {line(node)}")

    if isinstance(node, ArrayAccess):
        return tree(prefix + "ArrayAccess", f"{node.name} {line(node)}", [
            ast_to_tree(node.index, "index")
        ])

    if isinstance(node, If):
        return tree(prefix + "If", line(node), [
            ast_to_tree(node.condition, "condition"),
            ast_to_tree(node.then_body, "then"),
            ast_to_tree(node.else_body, "else") if node.else_body is not None else None,
        ])

    if isinstance(node, While):
        return tree(prefix + "While", line(node), [
            ast_to_tree(node.condition, "condition"),
            ast_to_tree(node.body, "body"),
        ])

    if isinstance(node, For):
        return tree(prefix + "For", line(node), [
            ast_to_tree(node.init, "init") if node.init is not None else tree("init", "None"),
            ast_to_tree(node.condition, "condition") if node.condition is not None else tree("condition", "None"),
            ast_to_tree(node.update, "update") if node.update is not None else tree("update", "None"),
            ast_to_tree(node.body, "body"),
        ])

    if isinstance(node, Print):
        return tree(prefix + "Print", line(node), [
            ast_to_tree(node.expr, "expr")
        ])

    if isinstance(node, Block):
        return tree(prefix + "Block", f"{len(node.stmts)} statement(s)", [
            ast_to_tree(stmt, f"stmt {i + 1}") for i, stmt in enumerate(node.stmts)
        ])

    return tree(prefix + type(node).__name__)


def compile_source(source):
    messages = []

    lexer_output = StringIO()
    with redirect_stdout(lexer_output):
        tokens = token_stream(source)
    if lexer_output.getvalue().strip():
        messages.extend(lexer_output.getvalue().strip().splitlines())

    parser_output = StringIO()
    lexer.lineno = 1
    with redirect_stdout(parser_output):
        ast = parser.parse(source, lexer=lexer)
    if parser_output.getvalue().strip():
        messages.extend(parser_output.getvalue().strip().splitlines())

    result = {
        "ok": False,
        "tokens": tokens,
        "ast": ast_to_tree(ast) if ast is not None else None,
        "symbols": [],
        "semantic_errors": [],
        "tac": [],
        "messages": messages,
    }

    if ast is None:
        result["messages"].append("Parse failed. Fix syntax errors before semantic analysis.")
        return result

    analyzer = SemanticAnalyzer()
    semantic_errors = analyzer.analyze(ast)
    result["symbols"] = analyzer.symbol_table.all_decls
    result["semantic_errors"] = semantic_errors

    if semantic_errors:
        result["messages"].extend(semantic_errors)
        result["messages"].append("Semantic analysis failed. TAC was not generated.")
        return result

    generator = TACGenerator()
    generator.generate(ast)
    result["tac"] = generator.instructions
    result["ok"] = True
    return result


class FrontendHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/", "/index.html"):
            self.send_error(404)
            return

        with open(DEFAULT_SOURCE, "r") as f:
            sample = f.read()

        page = HTML.replace("__SAMPLE_SOURCE__", json.dumps(sample))
        self.respond(200, page.encode("utf-8"), "text/html; charset=utf-8")

    def do_POST(self):
        if self.path != "/api/compile":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        try:
            payload = json.loads(body) if body else {}
            source = payload.get("source", "")
            data = compile_source(source)
            self.respond(200, json.dumps(data).encode("utf-8"), "application/json")
        except Exception as exc:
            data = {"ok": False, "messages": [str(exc)]}
            self.respond(500, json.dumps(data).encode("utf-8"), "application/json")

    def respond(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))


def main():
    server = ThreadingHTTPServer((HOST, PORT), FrontendHandler)
    url = f"http://{HOST}:{PORT}"
    print(f"Mini-C frontend running at {url}")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    server.serve_forever()


if __name__ == "__main__":
    main()
