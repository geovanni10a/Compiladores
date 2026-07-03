#!/usr/bin/env python3
"""Gera arvores de derivacao MicroJava como SVG embutido em HTML (para PDF)."""
import html as H

# ---------- modelo de no ----------
class Node:
    def __init__(self, label, kind, children=None):
        self.label = label
        self.kind = kind  # 'nt' = nao-terminal, 't' = terminal literal, 'tc' = classe terminal, 'lex' = lexema
        self.children = children or []

def N(label, *children):  # nao-terminal
    return Node(label, 'nt', list(children))

def T(label):             # terminal literal (palavra reservada / operador / pontuacao)
    return Node(label, 't')

def TC(cls, lexeme):      # classe terminal (ident, number, charConst) com lexema abaixo
    return Node(cls, 'tc', [Node(lexeme, 'lex')])

# atalhos frequentes
def ident(name): return TC('ident', name)
def number(v):   return TC('number', v)
def charconst(v):return TC('charConst', v)

def desig(name): return N('Designator', ident(name))

def expr_simple(leaf):
    """Expr -> Term -> Factor -> (leaf)"""
    return N('Expr', N('Term', N('Factor', leaf)))

def expr_var(name):
    return N('Expr', N('Term', N('Factor', desig(name))))

def desig_index(name, index_expr):
    """Designator -> ident [ Expr ]"""
    return N('Designator', ident(name), T('['), index_expr, T(']'))

def assign_stmt(lhs, expr):
    return N('Statement', desig(lhs), T('='), expr, T(';'))

def expr_binop(t1, op, t2):
    """Expr -> Term Addop Term"""
    return N('Expr', t1, N('Addop', T(op)), t2)

def term_of(leaf):
    return N('Term', N('Factor', leaf))

# ---------- as 8 arvores ----------
trees = []

# 1) sum = a + max;
trees.append((
    "sum = a + max;",
    "Statement = Designator “=” Expr “;”",
    ["Statement = Designator (\"=\" Expr | ActPars) \";\"",
     "Designator = ident {\".\" ident | \"[\" Expr \"]\"}",
     "Expr = [\"-\"] Term {Addop Term}",
     "Term = Factor {Mulop Factor}",
     "Factor = Designator [ActPars]",
     "Addop = \"+\" | \"-\""],
    assign_stmt('sum',
        expr_binop(term_of(desig('a')), '+', term_of(desig('max'))))
))

# 2) total = arr[0] + arr[1];
trees.append((
    "total = arr[0] + arr[1];",
    "Statement = Designator “=” Expr “;”",
    ["Statement = Designator (\"=\" Expr | ActPars) \";\"",
     "Designator = ident {\".\" ident | \"[\" Expr \"]\"}",
     "Expr = [\"-\"] Term {Addop Term}",
     "Term = Factor {Mulop Factor}",
     "Factor = Designator [ActPars] | number",
     "Addop = \"+\" | \"-\""],
    assign_stmt('total',
        expr_binop(
            term_of(desig_index('arr', expr_simple(number('0')))),
            '+',
            term_of(desig_index('arr', expr_simple(number('1'))))))
))

# 3) values = new int[size];
trees.append((
    "values = new int[size];",
    "Statement = Designator “=” Expr “;”",
    ["Statement = Designator (\"=\" Expr | ActPars) \";\"",
     "Designator = ident {\".\" ident | \"[\" Expr \"]\"}",
     "Expr = [\"-\"] Term {Addop Term}",
     "Term = Factor {Mulop Factor}",
     "Factor = \"new\" ident [\"[\" Expr \"]\"]"],
    assign_stmt('values',
        N('Expr', N('Term', N('Factor',
            T('new'), ident('int'), T('['), expr_var('size'), T(']')))))
))

# 4) arr = new int[10];
trees.append((
    "arr = new int[10];",
    "Statement = Designator “=” Expr “;”",
    ["Statement = Designator (\"=\" Expr | ActPars) \";\"",
     "Designator = ident {\".\" ident | \"[\" Expr \"]\"}",
     "Expr = [\"-\"] Term {Addop Term}",
     "Term = Factor {Mulop Factor}",
     "Factor = \"new\" ident [\"[\" Expr \"]\"] | number"],
    assign_stmt('arr',
        N('Expr', N('Term', N('Factor',
            T('new'), ident('int'), T('['), expr_simple(number('10')), T(']')))))
))

# 5) letter = 'A';
trees.append((
    "letter = 'A';",
    "Statement = Designator “=” Expr “;”",
    ["Statement = Designator (\"=\" Expr | ActPars) \";\"",
     "Designator = ident {\".\" ident | \"[\" Expr \"]\"}",
     "Expr = [\"-\"] Term {Addop Term}",
     "Term = Factor {Mulop Factor}",
     "Factor = charConst"],
    assign_stmt('letter', expr_simple(charconst("'A'")))
))

# 6) class Node { int data; int[] next; }
trees.append((
    "class Node { int data; int[] next; }",
    "ClassDecl = “class” ident “{” {VarDecl} “}”",
    ["ClassDecl = \"class\" ident \"{\" {VarDecl} \"}\"",
     "VarDecl = Type ident {\",\" ident} \";\"",
     "Type = ident [\"[\" \"]\"]"],
    N('ClassDecl',
        T('class'), ident('Node'), T('{'),
        N('VarDecl', N('Type', ident('int')), ident('data'), T(';')),
        N('VarDecl', N('Type', ident('int'), T('['), T(']')), ident('next'), T(';')),
        T('}'))
))

# 7) if (x > 0) x = x - 1; else x = x + 1;
trees.append((
    "if (x > 0) x = x - 1; else x = x + 1;",
    "Statement = “if” “(” Condition “)” Statement [“else” Statement]",
    ["Statement = \"if\" \"(\" Condition \")\" Statement [\"else\" Statement]",
     "Statement = Designator (\"=\" Expr | ActPars) \";\"",
     "Condition = Expr Relop Expr",
     "Relop = \"==\" | \"!=\" | \">\" | \">=\" | \"<\" | \"<=\"",
     "Expr = [\"-\"] Term {Addop Term}",
     "Term = Factor {Mulop Factor}",
     "Factor = Designator [ActPars] | number",
     "Addop = \"+\" | \"-\""],
    N('Statement',
        T('if'), T('('),
        N('Condition', expr_var('x'), N('Relop', T('>')), expr_simple(number('0'))),
        T(')'),
        assign_stmt('x', expr_binop(term_of(desig('x')), '-', term_of(number('1')))),
        T('else'),
        assign_stmt('x', expr_binop(term_of(desig('x')), '+', term_of(number('1')))))
))

# 8) while (i < size) i = i + 1;
trees.append((
    "while (i < size) i = i + 1;",
    "Statement = “while” “(” Condition “)” Statement",
    ["Statement = \"while\" \"(\" Condition \")\" Statement",
     "Statement = Designator (\"=\" Expr | ActPars) \";\"",
     "Condition = Expr Relop Expr",
     "Relop = \"==\" | \"!=\" | \">\" | \">=\" | \"<\" | \"<=\"",
     "Expr = [\"-\"] Term {Addop Term}",
     "Term = Factor {Mulop Factor}",
     "Factor = Designator [ActPars] | number",
     "Addop = \"+\" | \"-\""],
    N('Statement',
        T('while'), T('('),
        N('Condition', expr_var('i'), N('Relop', T('<')), expr_var('size')),
        T(')'),
        assign_stmt('i', expr_binop(term_of(desig('i')), '+', term_of(number('1')))))
))

# ---------- layout ----------
FONT = 15          # px
CHAR_W = 0.62 * FONT
PAD_X = 14         # espaco horizontal entre subarvores irmas
NODE_H = 22
LEVEL_H = 58       # distancia vertical entre niveis

def text_w(label):
    return max(len(label) * CHAR_W + 10, 26)

def measure(node):
    """largura da subarvore"""
    w_self = text_w(node.label)
    if not node.children:
        node.subw = w_self
        return node.subw
    total = sum(measure(c) for c in node.children) + PAD_X * (len(node.children) - 1)
    node.subw = max(w_self, total)
    return node.subw

def place(node, x0, depth):
    """define node.x (centro) e node.y"""
    node.y = depth * LEVEL_H + NODE_H
    if not node.children:
        node.x = x0 + node.subw / 2
        return
    total = sum(c.subw for c in node.children) + PAD_X * (len(node.children) - 1)
    cx = x0 + (node.subw - total) / 2
    for c in node.children:
        place(c, cx, depth + 1)
        cx += c.subw + PAD_X
    node.x = (node.children[0].x + node.children[-1].x) / 2

def depth_of(node):
    if not node.children:
        return 1
    return 1 + max(depth_of(c) for c in node.children)

STYLE = {
    'nt':  ('#1a3f7a', 'italic',  'normal', 'Georgia, serif'),
    't':   ('#111111', 'normal',  'bold',   'Consolas, Menlo, monospace'),
    'tc':  ('#0a6b3d', 'normal',  'normal', 'Consolas, Menlo, monospace'),
    'lex': ('#8a5a00', 'italic',  'normal', 'Consolas, Menlo, monospace'),
}

def render_node(node, parts):
    color, fstyle, fweight, ffam = STYLE[node.kind]
    label = H.escape(node.label)
    if node.kind == 't':
        label = '&#8220;' + label + '&#8221;'  # aspas tipograficas em terminais literais
    for c in node.children:
        dash = ' stroke-dasharray="4,3"' if c.kind == 'lex' else ''
        parts.append(
            f'<line x1="{node.x:.1f}" y1="{node.y + 6:.1f}" '
            f'x2="{c.x:.1f}" y2="{c.y - FONT:.1f}" stroke="#999" stroke-width="1.1"{dash}/>')
        render_node(c, parts)
    parts.append(
        f'<text x="{node.x:.1f}" y="{node.y:.1f}" text-anchor="middle" '
        f'font-family="{ffam}" font-size="{FONT}" fill="{color}" '
        f'font-style="{fstyle}" font-weight="{fweight}">{label}</text>')

def tree_svg(root):
    measure(root)
    place(root, 10, 0)
    d = depth_of(root)
    w = root.subw + 20
    h = d * LEVEL_H + 20
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" '
             f'style="max-width:100%;max-height:168mm;display:block;margin:0 auto;">']
    render_node(root, parts)
    parts.append('</svg>')
    return ''.join(parts)

# ---------- documento HTML ----------
pages = []
for i, (code, start_rule, rules, root) in enumerate(trees, 1):
    rules_html = ''.join(f'<li><code>{H.escape(r)}</code></li>' for r in rules)
    pages.append(f'''
<section class="page">
  <div class="head">
    <span class="num">Declara&ccedil;&atilde;o {i}</span>
    <code class="code">{H.escape(code)}</code>
  </div>
  <p class="start">Produ&ccedil;&atilde;o inicial: <code>{H.escape(start_rule)}</code></p>
  <div class="treebox">{tree_svg(root)}</div>
  <div class="rules"><b>Produ&ccedil;&otilde;es da gram&aacute;tica utilizadas:</b><ul>{rules_html}</ul></div>
</section>''')

legend = '''
<section class="page cover">
  <h1>&Aacute;rvores de Deriva&ccedil;&atilde;o &mdash; Linguagem MicroJava</h1>
  <p class="sub">Constru&iacute;das de acordo com a gram&aacute;tica formal do <i>MicroJava Quick Reference</i> (H.&nbsp;M&ouml;ssenb&ouml;ck).</p>
  <h2>Conven&ccedil;&otilde;es utilizadas nas &aacute;rvores</h2>
  <table class="leg">
    <tr><td class="nt">S&iacute;mbolo em azul (it&aacute;lico)</td><td>N&atilde;o-terminal da gram&aacute;tica (ex.: <span class="nt">Statement</span>, <span class="nt">Expr</span>, <span class="nt">Term</span>)</td></tr>
    <tr><td class="t">&#8220;s&iacute;mbolo&#8221; em preto (negrito)</td><td>Terminal literal: palavra reservada, operador ou pontua&ccedil;&atilde;o (ex.: <span class="t">&#8220;=&#8221;</span>, <span class="t">&#8220;while&#8221;</span>, <span class="t">&#8220;;&#8221;</span>)</td></tr>
    <tr><td class="tc">s&iacute;mbolo em verde</td><td>Classe terminal l&eacute;xica: <span class="tc">ident</span>, <span class="tc">number</span>, <span class="tc">charConst</span></td></tr>
    <tr><td class="lex">texto em laranja (tracejado)</td><td>Lexema concreto reconhecido pelo analisador l&eacute;xico (ex.: <span class="lex">sum</span>, <span class="lex">10</span>, <span class="lex">'A'</span>)</td></tr>
  </table>
  <h2>Gram&aacute;tica de refer&ecirc;ncia (trecho relevante)</h2>
  <pre class="gram">Statement  = Designator ("=" Expr | ActPars) ";"
           | "if" "(" Condition ")" Statement ["else" Statement]
           | "while" "(" Condition ")" Statement
           | "return" [Expr] ";"  |  "read" "(" Designator ")" ";"
           | "print" "(" Expr ["," number] ")" ";"  |  Block  |  ";".
ClassDecl  = "class" ident "{" {VarDecl} "}".
VarDecl    = Type ident {"," ident} ";".
Type       = ident ["[" "]"].
Condition  = Expr Relop Expr.
Relop      = "==" | "!=" | ">" | ">=" | "<" | "<=".
Expr       = ["-"] Term {Addop Term}.
Term       = Factor {Mulop Factor}.
Factor     = Designator [ActPars] | number | charConst
           | "new" ident ["[" Expr "]"] | "(" Expr ")".
Designator = ident {"." ident | "[" Expr "]"}.
Addop      = "+" | "-".      Mulop = "*" | "/" | "%".</pre>
  <p class="note">Observa&ccedil;&otilde;es: (1) em MicroJava, <code>int</code> e <code>char</code> s&atilde;o nomes de tipos pr&eacute;-declarados e s&atilde;o reconhecidos pelo analisador l&eacute;xico como <i>ident</i> (n&atilde;o constam na lista de palavras reservadas do guia de refer&ecirc;ncia); (2) as partes opcionais <code>[&nbsp;]</code> e repetitivas <code>{&nbsp;}</code> da EBNF aparecem nas &aacute;rvores apenas quando efetivamente utilizadas na deriva&ccedil;&atilde;o.</p>
</section>'''

doc = f'''<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: Georgia, 'Times New Roman', serif; color:#222; }}
  .page {{ page-break-after: always; padding: 10mm 8mm; }}
  .page:last-child {{ page-break-after: auto; }}
  .cover h1 {{ font-size: 24pt; margin-bottom: 4mm; color:#1a3f7a; }}
  .cover .sub {{ font-size: 12pt; margin-bottom: 8mm; }}
  .cover h2 {{ font-size: 13pt; margin: 6mm 0 3mm; }}
  .leg {{ border-collapse: collapse; font-size: 10.5pt; }}
  .leg td {{ border: 1px solid #bbb; padding: 2mm 3mm; }}
  .nt {{ color:#1a3f7a; font-style: italic; }}
  .t  {{ color:#111; font-weight: bold; font-family: Consolas, monospace; }}
  .tc {{ color:#0a6b3d; font-family: Consolas, monospace; }}
  .lex {{ color:#8a5a00; font-style: italic; font-family: Consolas, monospace; }}
  .gram {{ font-family: Consolas, Menlo, monospace; font-size: 9.5pt; background:#f5f5f0;
          border:1px solid #ddd; padding: 3mm; line-height: 1.45; }}
  .note {{ font-size: 10pt; margin-top: 5mm; color:#444; }}
  .head {{ border-bottom: 2px solid #1a3f7a; padding-bottom: 2mm; margin-bottom: 3mm; }}
  .head .num {{ font-size: 11pt; color:#1a3f7a; font-weight: bold; margin-right: 6mm; }}
  .head .code {{ font-family: Consolas, Menlo, monospace; font-size: 14pt; font-weight: bold; }}
  .start {{ font-size: 10.5pt; margin-bottom: 4mm; }}
  .start code {{ font-family: Consolas, Menlo, monospace; }}
  .treebox {{ text-align:center; }}
  .rules {{ font-size: 9.5pt; margin-top: 4mm; color:#333; }}
  .rules ul {{ margin: 1mm 0 0 6mm; }}
  .rules code {{ font-family: Consolas, Menlo, monospace; }}
</style></head><body>
{legend}
{''.join(pages)}
</body></html>'''

out = '/tmp/claude-0/-home-user-Compiladores/aacc7efb-1e14-5b4f-9a39-f086a7696ac9/scratchpad/arvores.html'
with open(out, 'w', encoding='utf-8') as f:
    f.write(doc)
print('ok', out)
