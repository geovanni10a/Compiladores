#!/usr/bin/env python3
"""Gera as arvores de derivacao MicroJava em HTML no modelo academico UNIFAP (para PDF A4 retrato)."""
import html as H

# ---------- modelo de no ----------
class Node:
    def __init__(self, label, kind, children=None):
        self.label = label
        self.kind = kind  # 'nt' = nao-terminal, 't' = terminal literal, 'tc' = classe terminal, 'lex' = lexema
        self.children = children or []

def N(label, *children):
    return Node(label, 'nt', list(children))

def T(label):
    return Node(label, 't')

def TC(cls, lexeme):
    return Node(cls, 'tc', [Node(lexeme, 'lex')])

def ident(name): return TC('ident', name)
def number(v):   return TC('number', v)
def charconst(v):return TC('charConst', v)

def desig(name): return N('Designator', ident(name))

def expr_simple(leaf):
    return N('Expr', N('Term', N('Factor', leaf)))

def expr_var(name):
    return N('Expr', N('Term', N('Factor', desig(name))))

def desig_index(name, index_expr):
    return N('Designator', ident(name), T('['), index_expr, T(']'))

def assign_stmt(lhs, expr):
    return N('Statement', desig(lhs), T('='), expr, T(';'))

def expr_binop(t1, op, t2):
    return N('Expr', t1, N('Addop', T(op)), t2)

def term_of(leaf):
    return N('Term', N('Factor', leaf))

# ---------- as 8 arvores ----------
trees = []

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
FONT = 15
CHAR_W = 0.62 * FONT
PAD_X = 9          # mais compacto para pagina retrato
NODE_H = 22
LEVEL_H = 56

def text_w(label):
    return max(len(label) * CHAR_W + 8, 24)

def measure(node):
    w_self = text_w(node.label)
    if not node.children:
        node.subw = w_self
        return node.subw
    total = sum(measure(c) for c in node.children) + PAD_X * (len(node.children) - 1)
    node.subw = max(w_self, total)
    return node.subw

def place(node, x0, depth):
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
        label = '&#8220;' + label + '&#8221;'
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

def tree_svg(root, max_h_mm=170):
    measure(root)
    place(root, 10, 0)
    d = depth_of(root)
    w = root.subw + 20
    h = d * LEVEL_H + 20
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" '
             f'style="max-width:100%;max-height:{max_h_mm}mm;display:block;margin:0 auto;">']
    render_node(root, parts)
    parts.append('</svg>')
    return ''.join(parts)

# ---------- documento HTML ----------
with open('/tmp/claude-0/-home-user-Compiladores/aacc7efb-1e14-5b4f-9a39-f086a7696ac9/scratchpad/logo_b64.txt') as f:
    LOGO = f.read().strip()

decl_lines = '<br>'.join(H.escape(code) for code, _, _, _ in trees)

# --- pagina 1: capa no modelo UNIFAP ---
page1 = f'''
<section class="page cover">
  <div class="covertop">
    <img class="logo" src="data:image/png;base64,{LOGO}" alt="UNIFAP">
    <p class="inst">UNIVERSIDADE FEDERAL DO AMAP&Aacute;<br>
    DEPARTAMENTO DE CI&Ecirc;NCIAS EXATAS E TECNOL&Oacute;GICAS<br>
    CURSO DE CI&Ecirc;NCIA DA COMPUTA&Ccedil;&Atilde;O</p>
    <p class="autor">GEOVANNI RODRIGUES DA SILVA</p>
    <p class="titulo">Atividade de Compiladores</p>
  </div>
  <div class="tarefa">
    <p class="enun"><b>Tarefa: Construa a &aacute;rvore de deriva&ccedil;&atilde;o completa para cada uma das
    declara&ccedil;&otilde;es MicroJava abaixo, de acordo com a gram&aacute;tica formal da linguagem
    (<i>MicroJava Quick Reference</i>).</b></p>
    <p class="codigo">{decl_lines}</p>
  </div>
  <p class="cidade">Macap&aacute;, 2026</p>
</section>'''

# --- pagina 2: convencoes e gramatica ---
page2 = '''
<section class="page">
  <h2>Conven&ccedil;&otilde;es utilizadas nas &aacute;rvores de deriva&ccedil;&atilde;o</h2>
  <table class="leg">
    <tr><th>Nota&ccedil;&atilde;o</th><th>Significado</th></tr>
    <tr><td class="nt">S&iacute;mbolo em azul (it&aacute;lico)</td><td>N&atilde;o-terminal da gram&aacute;tica (ex.: <span class="nt">Statement</span>, <span class="nt">Expr</span>, <span class="nt">Term</span>)</td></tr>
    <tr><td class="t">&#8220;s&iacute;mbolo&#8221; em preto (negrito)</td><td>Terminal literal: palavra reservada, operador ou pontua&ccedil;&atilde;o (ex.: <span class="t">&#8220;=&#8221;</span>, <span class="t">&#8220;while&#8221;</span>, <span class="t">&#8220;;&#8221;</span>)</td></tr>
    <tr><td class="tc">s&iacute;mbolo em verde</td><td>Classe terminal l&eacute;xica: <span class="tc">ident</span>, <span class="tc">number</span>, <span class="tc">charConst</span></td></tr>
    <tr><td class="lex">texto em laranja (liga&ccedil;&atilde;o tracejada)</td><td>Lexema concreto reconhecido pelo analisador l&eacute;xico (ex.: <span class="lex">sum</span>, <span class="lex">10</span>, <span class="lex">'A'</span>)</td></tr>
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
</section>'''

WIDE = {7}  # declaracoes cuja arvore e larga demais para retrato -> pagina paisagem

pages = []
for i, (code, start_rule, rules, root) in enumerate(trees, 1):
    rules_html = ''.join(f'<li><span class="mono">{H.escape(r)}</span></li>' for r in rules)
    cls = ' wide' if i in WIDE else ''
    pages.append(f'''
<section class="page{cls}">
  <p class="declhead"><b>Declara&ccedil;&atilde;o {i}:</b> <span class="codigo2">{H.escape(code)}</span></p>
  <p class="start">Produ&ccedil;&atilde;o inicial: <span class="mono">{H.escape(start_rule)}</span></p>
  <div class="treebox">{tree_svg(root)}</div>
  <div class="rules"><b>Produ&ccedil;&otilde;es da gram&aacute;tica utilizadas:</b><ul>{rules_html}</ul></div>
</section>''')

doc = f'''<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8">
<style>
  @page {{ size: A4 portrait; margin: 0; }}
  @page land {{ size: A4 landscape; margin: 0; }}
  .page.wide {{ page: land; width: 297mm; height: 209mm; }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: 'Times New Roman', Times, serif; color:#000; font-size: 12pt; }}
  .page {{ width: 210mm; height: 296mm; padding: 20mm 20mm 16mm; page-break-after: always;
           display: flex; flex-direction: column; overflow: hidden; }}
  .page:last-child {{ page-break-after: auto; }}
  .cover {{ text-align: left; }}
  .covertop {{ text-align: center; padding-top: 8mm; }}
  .logo {{ width: 24mm; height: auto; }}
  .inst {{ margin-top: 4mm; font-size: 12pt; line-height: 1.5; }}
  .autor {{ margin-top: 10mm; font-size: 12pt; }}
  .titulo {{ margin-top: 10mm; font-weight: bold; font-size: 12.5pt; }}
  .tarefa {{ margin-top: 12mm; }}
  .enun {{ text-align: justify; margin-bottom: 6mm; }}
  .codigo {{ font-family: Consolas, 'Courier New', monospace; font-style: italic;
             font-size: 11pt; line-height: 1.7; margin-left: 8mm; }}
  .codigo2 {{ font-family: Consolas, 'Courier New', monospace; font-weight: bold; font-size: 12.5pt; }}
  .cidade {{ margin-top: auto; text-align: center; font-size: 12pt; }}
  h2 {{ font-size: 12.5pt; margin: 0 0 4mm; }}
  h2 + .leg, .gram {{ margin-bottom: 8mm; }}
  .leg {{ border-collapse: collapse; font-size: 11pt; width: 100%; }}
  .leg th {{ background: #dce6f1; }}
  .leg th, .leg td {{ border: 1px solid #000; padding: 2mm 3mm; text-align: left; }}
  .nt {{ color:#1a3f7a; font-style: italic; }}
  .t  {{ color:#111; font-weight: bold; font-family: Consolas, monospace; }}
  .tc {{ color:#0a6b3d; font-family: Consolas, monospace; }}
  .lex {{ color:#8a5a00; font-style: italic; font-family: Consolas, monospace; }}
  .mono {{ font-family: Consolas, 'Courier New', monospace; font-size: 9.5pt; }}
  .gram {{ font-family: Consolas, 'Courier New', monospace; font-size: 9.5pt;
           border: 1px solid #000; padding: 3mm; line-height: 1.5; }}
  .note {{ font-size: 11pt; text-align: justify; }}
  .declhead {{ border-bottom: 1.5px solid #000; padding-bottom: 2mm; margin-bottom: 3mm; }}
  .start {{ font-size: 11pt; margin-bottom: 4mm; }}
  .treebox {{ text-align: center; flex: 1 1 auto; display: flex; align-items: center; justify-content: center; }}
  .treebox svg {{ flex: 0 1 auto; }}
  .page.wide .treebox svg {{ max-height: 105mm !important; }}
  .page.wide .rules {{ font-size: 9.5pt; }}
  .page.wide .rules ul {{ columns: 2; }}
  .rules {{ font-size: 10.5pt; margin-top: 3mm; }}
  .rules ul {{ margin: 1mm 0 0 7mm; }}
  .rules li {{ margin-bottom: 0.5mm; }}
</style></head><body>
{page1}
{page2}
{''.join(pages)}
</body></html>'''

out = '/tmp/claude-0/-home-user-Compiladores/aacc7efb-1e14-5b4f-9a39-f086a7696ac9/scratchpad/atividade.html'
with open(out, 'w', encoding='utf-8') as f:
    f.write(doc)
print('ok', out)
