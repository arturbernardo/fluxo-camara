"""Perfil dos deputados por legislatura, 1933–2027: gênero, idade, escolaridade, profissões, renovação e cor/raça.

Entradas: ../dados1933.json (quem tomou posse em cada legislatura, inclusive suplentes), cadastro.json
(cadastro.py) e cor_raca.json (cor_raca.py). Para a renovação, as listas de deputados das legislaturas
anteriores a 1933 vêm da API da Câmara. Gera perfil.json.
"""
import json, statistics, urllib.request
from datetime import date

dados = json.load(open("../dados1933.json", encoding="utf-8"))
cad = json.load(open("cadastro.json", encoding="utf-8"))
cor = json.load(open("cor_raca.json", encoding="utf-8"))
ANOS = dict(dados["legs"])
LEGS = [l[0] for l in dados["legs"]]
INICIO = {36: date(1933, 11, 15), 37: date(1935, 5, 3), 38: date(1946, 2, 2)}  # posse; demais: 1º de fevereiro

GRUPOS = {
    "Direito": ["Advogad", "Promotor", "Procurador", "Juiz", "Tabeli", "Serventuári", "Escriv", "Jurista", "Magistrad", "Defensor"],
    "Empresários e comércio": ["Empresári", "Banqueir", "Corretor", "Representante comercial", "Vendedor", "Armador",
                               "Construtor", "Comerciante", "Industrial"],
    "Agropecuária": ["Agricultor", "Pecuarista", "Agropecuarist", "Fazendeir", "Proprietári", "Criador", "Agrônom", "Produtor rural", "Pescador", "Avicultor", "Piscicultor"],
    "Saúde": ["Médic", "Dentista", "Farmacêutic", "Enfermeir", "Veterinári", "Psicólog", "Fisioterapeut", "Nutricionist", "Psicanalist", "Auxiliar de enfermagem"],
    "Educação": ["Professor", "Pedagog"],
    "Comunicação e cultura": ["Jornalist", "Comunicador", "Radialist", "Publicitári", "Escritor", "Poet", "Músic", "Ator", "Atriz",
                              "Artista", "Relações públicas", "Comunicólog", "Cantor", "Apresentador", "Dramaturg"],
    "Engenharia, economia e gestão": ["Engenheir", "Arquitet", "Economist", "Administrador", "Contador", "Consultor", "Químic",
                                      "Geólog", "Analista", "Agrimensor", "Estatístic"],
    "Serviço público": ["Servidor", "Gestor", "Gestora", "Diplomat", "Agente fiscal", "Auditor", "Empregado públic", "Funcionári"],
    "Segurança e militares": ["Militar", "Policial", "Delegad", "Bombeiro"],
    "Religiosos": ["Pastor", "Padre", "Teólog", "Sacerdot", "Missionári", "Bispo"],
    "Trabalhadores e sindicalistas": ["Bancári", "Comerciári", "Metalúrgic", "Operári", "Industriári", "Eletricist", "Motorista",
                                      "Ferroviári", "Sindicalist", "Profissional técnic", "Profissional gráfic", "Torneiro",
                                      "Telegrafist", "Escriturári", "Trabalhador", "Mecânic", "Gráfic", "Portuári", "Garimpeir", "Ferramenteir",
                                      "Balconist", "Jornaleir", "Carpinteir", "Marceneir", "Impressor", "Siderúrgic",
                                      "Aeroviári", "Radiotelegrafist", "Auxiliar administrativ"],
}


def grupo(titulo):
    for g, chaves in GRUPOS.items():
        if any(titulo.startswith(c) for c in chaves):
            return g
    return "Outros"


ESC = [("Superior completo ou mais", ["Superior", "Pós-Graduação", "Mestrado", "Doutorado", "Mestrado Incompleto",
                                      "Doutorado Incompleto", "Pós-Graduação Incompleta"]),
       ("Superior incompleto", ["Superior Incompleto"]),
       ("Ensino médio ou técnico", ["Secundário", "Ensino Médio", "Ensino Técnico", "Secundário Incompleto",
                                    "Ensino Médio Incompleto", "Ensino Técnico Incompleto"]),
       ("Ensino fundamental ou menos", ["Primário", "Ensino Fundamental", "Ginasial", "Primário Incompleto",
                                        "Ensino Fundamental Incompleto", "Ginasial Incompleto", "Lê e escreve"])]
ESC_DE = {v: g for g, vs in ESC for v in vs}

# renovação: presença em legislaturas anteriores a 1933 (listas da API) e na própria base
antes = set()
for L in range(1, 36):
    page = 1
    while True:
        u = f"https://dadosabertos.camara.leg.br/api/v2/deputados?idLegislatura={L}&itens=100&pagina={page}"
        d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"Accept": "application/json"}), timeout=60))
        antes |= {r["id"] for r in d["dados"] if r["idLegislatura"] == L}
        if not any(l["rel"] == "next" for l in d["links"]):
            break
        page += 1
leg_de = {d[0]: sorted({s[0] for s in d[3]}) for d in dados["deps"]}

out, sem_classe = [], {}
for L in LEGS:
    ids = [i for i, ls in leg_de.items() if L in ls]
    n = len(ids)
    c = [cad.get(str(i)) or {} for i in ids]
    mulheres = [i for i, x in zip(ids, c) if x.get("sexo") == "F"]
    ini = INICIO.get(L, date(int(ANOS[L]), 2, 1))
    idades = sorted((ini - date.fromisoformat(x["nascimento"])).days / 365.25 for x in c if x.get("nascimento"))
    q = statistics.quantiles(idades, n=4) if len(idades) > 4 else [None] * 3
    esc = {g: 0 for g, _ in ESC}
    esc_n = 0
    for x in c:
        g = ESC_DE.get(x.get("escolaridade"))
        if g:
            esc[g] += 1
            esc_n += 1
        elif x.get("escolaridade"):
            sem_classe[x["escolaridade"]] = sem_classe.get(x["escolaridade"], 0) + 1
    com_prof = [x for x in c if x.get("profissoes")]
    prof = {g: 0 for g in list(GRUPOS) + ["Outros"]}
    for x in com_prof:
        for g in {grupo(t) for t in x["profissoes"]}:
            prof[g] += 1
    novos = [i for i in ids if i not in antes and not any(M < L for M in leg_de[i])]
    raca = {}
    for i in ids:
        r = cor["deputados"].get(str(i), {}).get(str(L))
        if r:
            raca[r] = raca.get(r, 0) + 1
    out.append({
        "L": L, "ano": ANOS[L], "n": n,
        "mulheres": len(mulheres), "nomes_mulheres": [next(d[1] for d in dados["deps"] if d[0] == i) for i in mulheres] if len(mulheres) <= 12 else None,
        "idade": {"mediana": round(statistics.median(idades), 1) if idades else None,
                  "p25": round(q[0], 1) if q[0] else None, "p75": round(q[2], 1) if q[2] else None,
                  "n": len(idades), "menos40": sum(a < 40 for a in idades), "mais60": sum(a >= 60 for a in idades)},
        "escolaridade": esc, "esc_n": esc_n,
        "profissoes": prof, "prof_n": len(com_prof),
        "novos": len(novos), "renovacao_valida": True,
        "cor": raca or None,
    })

# eleição de 2026 (legislatura que toma posse em 2027): eleitos segundo o TSE, ainda sem dados da Câmara
import csv, io, os, zipfile
eleitos2026 = None
if os.path.exists("consulta_cand_2026.zip"):
    z = zipfile.ZipFile("consulta_cand_2026.zip")
    nome = next(n for n in z.namelist() if n.endswith("_BRASIL.csv"))
    linhas = [r for r in csv.DictReader(io.TextIOWrapper(z.open(nome), encoding="latin-1"), delimiter=";")
              if r["DS_CARGO"] == "DEPUTADO FEDERAL" and r["DS_SIT_TOT_TURNO"].startswith("ELEITO")]
    eleitos2026 = {"n": len(linhas), "mulheres": sum(r["DS_GENERO"] == "FEMININO" for r in linhas),
                   "gerado": linhas[0]["DT_GERACAO"] if linhas else None}

json.dump({"eleitos2026": eleitos2026, "legislaturas": out, "ends": dados.get("ends", {}), "grupos": GRUPOS, "esc": [g for g, _ in ESC],
           "populacao_cor": cor["populacao"]},
          open("perfil.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("escolaridades não classificadas:", sem_classe)
for o in out:
    print(o["ano"], o["n"], f"mulheres {o['mulheres']}", f"idade {o['idade']['mediana']}", f"sup {o['escolaridade']['Superior completo ou mais']}/{o['esc_n']}",
          f"novos {o['novos']}", o["cor"] or "")
