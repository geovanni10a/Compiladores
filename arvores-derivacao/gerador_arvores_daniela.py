#!/usr/bin/env python3
"""Atividade de Compiladores - Daniela: arvores de derivacao MicroJava,
mesmo conteudo, estrutura de apresentacao diferente (arvores monocromaticas
com nao-terminais em caixas + derivacao mais a esquerda passo a passo)."""
import html as H

class Node:
    def __init__(self, label, kind, children=None, lexeme=None):
        self.label = label
        self.kind = kind  # 'nt', 't' (terminal literal), 'tc' (classe terminal)
        self.children = children or []
        self.lexeme = lexeme

def N(label, *children): return Node(label, 'nt', list(children))
def T(label):            return Node(label, 't')
def TC(cls, lexeme):     return Node(cls, 'tc', lexeme=lexeme)

def ident(name): return TC('ident', name)
def number(v):   return TC('number', v)
def charconst(v):return TC('charConst', v)

def desig(name): return N('Designator', ident(name))
def expr_simple(leaf): return N('Expr', N('Term', N('Factor', leaf)))
def expr_var(name):    return N('Expr', N('Term', N('Factor', desig(name))))
def desig_index(name, e): return N('Designator', ident(name), T('['), e, T(']'))
def assign_stmt(lhs, e):  return N('Statement', desig(lhs), T('='), e, T(';'))
def expr_binop(t1, op, t2): return N('Expr', t1, N('Addop', T(op)), t2)
def term_of(leaf): return N('Term', N('Factor', leaf))

trees = [
    ("sum = a + max;",
     assign_stmt('sum', expr_binop(term_of(desig('a')), '+', term_of(desig('max'))))),
    ("total = arr[0] + arr[1];",
     assign_stmt('total', expr_binop(
         term_of(desig_index('arr', expr_simple(number('0')))), '+',
         term_of(desig_index('arr', expr_simple(number('1'))))))),
    ("values = new int[size];",
     assign_stmt('values', N('Expr', N('Term', N('Factor',
         T('new'), ident('int'), T('['), expr_var('size'), T(']')))))),
    ("arr = new int[10];",
     assign_stmt('arr', N('Expr', N('Term', N('Factor',
         T('new'), ident('int'), T('['), expr_simple(number('10')), T(']')))))),
    ("letter = 'A';",
     assign_stmt('letter', expr_simple(charconst("'A'")))),
    ("class Node { int data; int[] next; }",
     N('ClassDecl',
        T('class'), ident('Node'), T('{'),
        N('VarDecl', N('Type', ident('int')), ident('data'), T(';')),
        N('VarDecl', N('Type', ident('int'), T('['), T(']')), ident('next'), T(';')),
        T('}'))),
    ("if (x > 0) x = x - 1; else x = x + 1;",
     N('Statement',
        T('if'), T('('),
        N('Condition', expr_var('x'), N('Relop', T('>')), expr_simple(number('0'))),
        T(')'),
        assign_stmt('x', expr_binop(term_of(desig('x')), '-', term_of(number('1')))),
        T('else'),
        assign_stmt('x', expr_binop(term_of(desig('x')), '+', term_of(number('1')))))),
    ("while (i < size) i = i + 1;",
     N('Statement',
        T('while'), T('('),
        N('Condition', expr_var('i'), N('Relop', T('<')), expr_var('size')),
        T(')'),
        assign_stmt('i', expr_binop(term_of(desig('i')), '+', term_of(number('1')))))),
]

# ---------- layout da arvore ----------
FONT = 15
CHAR_W = 0.62 * FONT
PAD_X = 10
NODE_H = 24
LEVEL_H = 58
BOX_PAD = 7

def node_w(node):
    w = len(node.label) * CHAR_W
    if node.kind == 'nt':
        w += 2 * BOX_PAD
    if node.kind == 'tc' and node.lexeme:
        w = max(w, (len(node.lexeme) + 2) * CHAR_W * 0.87)
    return max(w + 6, 26)

def measure(node):
    w_self = node_w(node)
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

MONO = 'Consolas, Menlo, monospace'
SANS = 'Arial, Helvetica, sans-serif'

def render_node(node, parts):
    for c in node.children:
        parts.append(
            f'<line x1="{node.x:.1f}" y1="{node.y + 8:.1f}" '
            f'x2="{c.x:.1f}" y2="{c.y - FONT - 3:.1f}" stroke="#444" stroke-width="1"/>')
        render_node(c, parts)
    label = H.escape(node.label)
    if node.kind == 'nt':
        bw = len(node.label) * CHAR_W + 2 * BOX_PAD
        parts.append(
            f'<rect x="{node.x - bw/2:.1f}" y="{node.y - FONT - 3:.1f}" width="{bw:.1f}" '
            f'height="{FONT + 10}" rx="7" fill="#fff" stroke="#000" stroke-width="1.1"/>')
        parts.append(
            f'<text x="{node.x:.1f}" y="{node.y:.1f}" text-anchor="middle" '
            f'font-family="{SANS}" font-size="{FONT - 1}" fill="#000">{label}</text>')
    elif node.kind == 't':
        parts.append(
            f'<text x="{node.x:.1f}" y="{node.y:.1f}" text-anchor="middle" '
            f'font-family="{MONO}" font-size="{FONT}" font-weight="bold" fill="#000">{label}</text>')
    else:  # tc
        parts.append(
            f'<text x="{node.x:.1f}" y="{node.y:.1f}" text-anchor="middle" '
            f'font-family="{MONO}" font-size="{FONT - 1}" fill="#000" '
            f'text-decoration="underline">{label}</text>')
        parts.append(
            f'<text x="{node.x:.1f}" y="{node.y + 19:.1f}" text-anchor="middle" '
            f'font-family="{MONO}" font-size="{FONT - 2}" font-style="italic" '
            f'fill="#555">({H.escape(node.lexeme)})</text>')

def tree_svg(root, max_h_mm):
    measure(root)
    place(root, 10, 0)
    d = depth_of(root)
    w = root.subw + 20
    h = d * LEVEL_H + 34
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" '
             f'style="max-width:100%;max-height:{max_h_mm}mm;display:block;margin:0 auto;">']
    render_node(root, parts)
    parts.append('</svg>')
    return ''.join(parts)

# ---------- derivacao mais a esquerda ----------
def sentential(seq):
    out = []
    for n in seq:
        if n.kind == 't':
            out.append('"' + n.label + '"')
        else:
            out.append(n.label)
    return ' '.join(out)

def derivation(root):
    seq = [root]
    forms = [sentential(seq)]
    while True:
        idx = next((i for i, n in enumerate(seq) if n.kind == 'nt'), None)
        if idx is None:
            break
        seq = seq[:idx] + seq[idx].children + seq[idx + 1:]
        forms.append(sentential(seq))
    return forms

# ---------- documento ----------
with open('/tmp/claude-0/-home-user-Compiladores/aacc7efb-1e14-5b4f-9a39-f086a7696ac9/scratchpad/logo_b64.txt') as f:
    LOGO = f.read().strip()

decl_lines = '<br>'.join(H.escape(code) for code, _ in trees)

header = f'''
<div class="head">
  <img class="logo" src="data:image/png;base64,{LOGO}" alt="UNIFAP">
  <p class="inst">UNIVERSIDADE FEDERAL DO AMAP&Aacute;<br>CURSO DE CI&Ecirc;NCIA DA COMPUTA&Ccedil;&Atilde;O</p>
  <p class="autor">DANIELA MARQUES HABER SEPEDA</p>
  <p class="titulo">Atividade de Compiladores<br>Docente: Anderson dos Santos Guerra</p>
</div>
<p class="tarefa"><i>Tarefa: Construa a &aacute;rvore de deriva&ccedil;&atilde;o completa para cada uma das
declara&ccedil;&otilde;es MicroJava abaixo, de acordo com a gram&aacute;tica formal da linguagem
(MicroJava Quick Reference).</i></p>
<p class="codigo">{decl_lines}</p>
<p class="resposta">Resposta:</p>
<p class="texto">As &aacute;rvores de deriva&ccedil;&atilde;o a seguir foram constru&iacute;das a partir da gram&aacute;tica EBNF
do <i>MicroJava Quick Reference</i>. Em cada &aacute;rvore, os s&iacute;mbolos <b>n&atilde;o-terminais</b> aparecem dentro de
caixas arredondadas; os <b>terminais literais</b> (palavras reservadas, operadores e pontua&ccedil;&atilde;o) aparecem em
negrito; e as <b>classes terminais l&eacute;xicas</b> (<span class="mono">ident</span>, <span class="mono">number</span>,
<span class="mono">charConst</span>) aparecem sublinhadas, com o lexema correspondente indicado logo abaixo, entre
par&ecirc;nteses. Antes de cada &aacute;rvore &eacute; apresentada tamb&eacute;m a <b>deriva&ccedil;&atilde;o mais &agrave;
esquerda</b> completa, passo a passo, at&eacute; a forma sentencial composta apenas por s&iacute;mbolos terminais.
Vale notar que, em MicroJava, <span class="mono">int</span> &eacute; um nome de tipo pr&eacute;-declarado, reconhecido
pelo analisador l&eacute;xico como <span class="mono">ident</span>.</p>
<p class="texto"><b>Gram&aacute;tica de refer&ecirc;ncia (produ&ccedil;&otilde;es utilizadas):</b></p>
<pre class="gram">Statement  = Designator ("=" Expr | ActPars) ";"
           | "if" "(" Condition ")" Statement ["else" Statement]
           | "while" "(" Condition ")" Statement | ... .
ClassDecl  = "class" ident "{{" {{VarDecl}} "}}".
VarDecl    = Type ident {{"," ident}} ";".        Type = ident ["[" "]"].
Condition  = Expr Relop Expr.                   Relop = "==" | "!=" | ">" | ">=" | "<" | "<=".
Expr       = ["-"] Term {{Addop Term}}.           Term = Factor {{Mulop Factor}}.
Factor     = Designator [ActPars] | number | charConst | "new" ident ["[" Expr "]"] | "(" Expr ")".
Designator = ident {{"." ident | "[" Expr "]"}}.  Addop = "+" | "-".   Mulop = "*" | "/" | "%".</pre>
'''

WIDE = {7}
sections = []
for i, (code, root) in enumerate(trees, 1):
    forms = derivation(root)
    lines = [f'<div class="dline first">{H.escape(forms[0])}</div>']
    for fm in forms[1:]:
        lines.append(f'<div class="dline">&rArr;&nbsp; {H.escape(fm)}</div>')
    lines.append(f'<div class="dline final">Senten&ccedil;a derivada:&nbsp; <i>{H.escape(code)}</i></div>')
    ncols = ' cols2' if len(forms) > 14 else ''
    cls = ' wide' if i in WIDE else ''
    max_h = 95 if i in WIDE else 130
    sections.append(f'''
<section class="decl{cls}">
  <p class="declhead">Declara&ccedil;&atilde;o {i}: <span class="codigo2">{H.escape(code)}</span></p>
  <p class="sub">a) Deriva&ccedil;&atilde;o mais &agrave; esquerda:</p>
  <div class="deriv{ncols}">{''.join(lines)}</div>
  <div class="treewrap"><p class="sub">b) &Aacute;rvore de deriva&ccedil;&atilde;o:</p>
  <div class="treebox">{tree_svg(root, max_h)}</div></div>
</section>''')

doc = f'''<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8">
<style>
  @page {{ size: A4 portrait; margin: 18mm 18mm 16mm; }}
  @page land {{ size: A4 landscape; margin: 14mm 16mm; }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: Arial, Helvetica, sans-serif; color:#000; font-size: 11.5pt; line-height: 1.45; }}
  .head {{ text-align: center; margin-bottom: 8mm; }}
  .logo {{ width: 20mm; height: auto; }}
  .inst {{ margin-top: 3mm; }}
  .autor {{ margin-top: 7mm; }}
  .titulo {{ margin-top: 7mm; }}
  .tarefa {{ margin-bottom: 5mm; text-align: justify; }}
  .codigo {{ font-family: Arial, Helvetica, sans-serif; font-style: italic; margin-left: 10mm;
             margin-bottom: 5mm; line-height: 1.55; }}
  .resposta {{ margin-bottom: 4mm; }}
  .texto {{ text-align: justify; margin-bottom: 4mm; }}
  .mono {{ font-family: Consolas, 'Courier New', monospace; font-size: 10pt; }}
  .gram {{ font-family: Consolas, 'Courier New', monospace; font-size: 8.5pt; line-height: 1.5;
           border: 1px solid #888; padding: 3mm; }}
  .decl {{ page-break-before: always; }}
  .decl.wide {{ page: land; }}
  .declhead {{ font-weight: bold; border-bottom: 1px solid #000; padding-bottom: 1.5mm; margin-bottom: 3mm; }}
  .codigo2 {{ font-family: Consolas, 'Courier New', monospace; }}
  .sub {{ font-weight: bold; margin: 2.5mm 0 2mm; }}
  .deriv {{ font-family: Consolas, 'Courier New', monospace; font-size: 8.8pt; line-height: 1.5;
            border: 1px solid #aaa; padding: 2.5mm 3mm; }}
  .deriv.cols2 {{ columns: 2; column-gap: 7mm; column-rule: 1px solid #ddd; }}
  .dline {{ padding-left: 5.5em; text-indent: -5.5em; }}
  .dline.first {{ font-weight: bold; }}
  .dline.final {{ margin-top: 1.5mm; font-family: Arial, sans-serif; font-size: 9.5pt; }}
  .treebox {{ text-align: center; margin-top: 2mm; }}
  .treewrap {{ page-break-inside: avoid; }}
</style></head><body>
{header}
{''.join(sections)}
</body></html>'''

out = '/tmp/claude-0/-home-user-Compiladores/aacc7efb-1e14-5b4f-9a39-f086a7696ac9/scratchpad/atividade_daniela.html'
with open(out, 'w', encoding='utf-8') as f:
    f.write(doc)
for i, (code, root) in enumerate(trees, 1):
    print(i, len(derivation(root)), 'passos')
print('ok', out)
