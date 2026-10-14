"""Gera 1933/index.html: a mesma página de template.html, estendida a 1933–1951 com dados1933.json.

A página principal (index.html) não muda. Aqui só se aplicam as diferenças sobre o mesmo código.
"""
import os

t = open("template.html", encoding="utf-8").read()


def troca(antes, depois):
    global t
    assert t.count(antes) == 1, antes[:70]
    t = t.replace(antes, depois)


troca("<title>Fluxo da Câmara</title>", "<title>Fluxo da Câmara desde 1933</title>")
troca("Câmara dos Deputados · 1951 – 2027", "Câmara dos Deputados · 1933 – 2027")
troca("<h1>O fluxo dos deputados entre partidos</h1>", "<h1>O fluxo dos deputados entre partidos, desde 1933</h1>")
troca("Clique num bloco para seguir os membros daquela bancada por todas as colunas.</p>",
      "Clique num bloco para seguir os membros daquela bancada por todas as colunas. Esta versão começa na Constituinte de "
      "1933–34; entre 1937 e 1946 o Congresso esteve fechado pelo Estado Novo. "
      '<a href="../">Ver a versão a partir de 1951</a>.</p>')
troca('<button type="button" data-r="39,57">Tudo</button>',
      '<button type="button" data-r="36,57">Tudo</button>\n      <button type="button" data-r="36,42">1933 → 1964</button>')
troca("const yrRange = L => `${YEAR[L]}–${L === 57 ? '2027' : YEAR[L + 1]}`;",
      "const ENDS = D.ends || {};\nconst yrRange = L => `${YEAR[L]}–${ENDS[L] || (L === 57 ? '2027' : YEAR[L + 1])}`;")
troca("fFrom.value = 39; fTo.value = 57;", "fFrom.value = 36; fTo.value = 57;")
troca("const ERAS = [", "const ERAS = [{L:38, t:'Estado Novo: Congresso fechado 1937–45'}, ")
troca("const ord = n => n.score == null ? 99 : n.score;",
      "const ord = n => n.score != null ? n.score : n.k === 'NI' || n.k === 'SP' ? 101 : n.k === 'CLASSISTA' ? 100 : 99;")
troca('hist = `<table class="ser">', "hist = !series.length ? '' : `<table class=\"ser\">")
troca("function colSource(L){", "function colSource(L){\n  if (L <= 37) return 'posições: sem classificação';")
troca('<div class="note sources">', '''<div class="note sources">
<p><b>1933–1951.</b> A Constituinte de 1933–34, a legislatura de 1935–37 e a de 1946–51 vêm das biografias oficiais da Câmara, que listam estado e partido de cada mandato (a API traz poucos deputados de 1946 e quase nenhum partido antes de 1945). Nos anos 1930 os partidos eram estaduais, por isso aparecem com sigla e estado (ex.: PP-MG). “Classistas” são os deputados eleitos por sindicatos e associações profissionais, previstos na Constituição de 1934. Cerca de um terço dos deputados de 1933–37 aparece sem partido (n/i) porque a biografia não o registra. Esses partidos não têm posição ideológica atribuída e aparecem em cinza. A faixa entre 1935–37 e 1946 atravessa os oito anos de Congresso fechado.</p>''')

d = open("dados1933.json", encoding="utf-8").read().replace("</", "<\\/")
p = open("posicoes.json", encoding="utf-8").read().replace("</", "<\\/")
c = open("cassacoes.json", encoding="utf-8").read().replace("</", "<\\/")
w = open("wikipedia.json", encoding="utf-8").read().replace("</", "<\\/")
pe = open("perseguicoes.json", encoding="utf-8").read().replace("</", "<\\/")
HEAD = ('<!doctype html>\n<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        '<meta name="description" content="Fluxo de deputados federais entre partidos de 1933 a 2027, '
        'da Constituinte de 1933–34 aos dias de hoje.">\n</head>\n<body>\n')
os.makedirs("1933", exist_ok=True)
open("1933/index.html", "w", encoding="utf-8").write(
    HEAD + t.replace("/*DATA*/", d).replace("/*POS*/", p).replace("/*CASS*/", c).replace("/*WIKI*/", w)
    .replace("/*PERS*/", pe) + "\n</body>\n</html>\n")
print("1933/index.html gerado")
