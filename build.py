"""Gera index.html a partir de template.html e dados.json."""
HEAD = ('<!doctype html>\n<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        '<meta name="description" content="Fluxo de deputados federais entre partidos de 1951 a 2027, '
        'com partidos ordenados por posição ideológica de cada época.">\n</head>\n<body>\n')
t = open("template.html", encoding="utf-8").read()
d = open("dados.json", encoding="utf-8").read().replace("</", "<\\/")
p = open("posicoes.json", encoding="utf-8").read().replace("</", "<\\/")
open("index.html", "w", encoding="utf-8").write(HEAD + t.replace("/*DATA*/", d).replace("/*POS*/", p) + "\n</body>\n</html>\n")
