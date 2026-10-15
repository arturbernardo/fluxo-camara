"""Gera index.html a partir de template.html e perfil.json."""
HEAD = ('<!doctype html>\n<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        '<meta name="description" content="Perfil dos deputados federais por legislatura, de 1933 a 2027: gênero, idade, '
        'escolaridade, profissões, renovação e cor ou raça.">\n</head>\n<body>\n')
t = open("template.html", encoding="utf-8").read()
d = open("perfil.json", encoding="utf-8").read().replace("</", "<\\/")
open("index.html", "w", encoding="utf-8").write(HEAD + t.replace("/*DATA*/", d) + "\n</body>\n</html>\n")
