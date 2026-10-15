"""Cor/raça autodeclarada dos deputados, a partir das candidaturas no TSE (eleições de 2014, 2018 e 2022).

A Câmara não registra cor/raça; o TSE pergunta desde 2014. Cada deputado da legislatura seguinte à eleição é
ligado à sua candidatura pela data de nascimento e pelo estado (com o nome como desempate). Gera cor_raca.json:
{id: {legislatura: cor}} e a composição da população nos censos de 2010 e 2022 (IBGE, SIDRA tabela 9605).
"""
import csv, io, json, os, unicodedata, urllib.request, zipfile

ELEICAO_LEG = {2014: 55, 2018: 56, 2022: 57}
dados = json.load(open("../dados1933.json", encoding="utf-8"))
cad = json.load(open("cadastro.json", encoding="utf-8"))


def fold(s):
    return unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode().upper().split()


def candidatos(ano):
    arq = f"consulta_cand_{ano}.zip"
    if not os.path.exists(arq):
        urllib.request.urlretrieve(f"https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_{ano}.zip", arq)
    z = zipfile.ZipFile(arq)
    nome = next(n for n in z.namelist() if n.endswith("_BRASIL.csv"))
    linhas = csv.DictReader(io.TextIOWrapper(z.open(nome), encoding="latin-1"), delimiter=";")
    return [r for r in linhas if r["DS_CARGO"] == "DEPUTADO FEDERAL"]


out, sem = {}, {}
for ano, L in ELEICAO_LEG.items():
    por_chave = {}
    for r in candidatos(ano):
        partes = r["DT_NASCIMENTO"].split("/")
        if len(partes) != 3:  # data ausente ou mascarada no arquivo do TSE
            continue
        d, m, a = partes
        por_chave.setdefault((f"{a}-{m}-{d}", r["SG_UF"]), []).append(r)
    ids = [d[0] for d in dados["deps"] if any(s[0] == L for s in d[3])]
    achados = 0
    for i in ids:
        c = cad.get(str(i)) or {}
        uf = next((d[2] for d in dados["deps"] if d[0] == i), None)
        cands = por_chave.get((c.get("nascimento"), uf), [])
        if len(cands) > 1:  # desempate pelo nome civil
            n = set(fold(c.get("nome_civil")))
            cands = sorted(cands, key=lambda r: -len(n & set(fold(r["NM_CANDIDATO"]))))[:1]
        if cands:
            out.setdefault(str(i), {})[L] = cands[0]["DS_COR_RACA"].capitalize()
            achados += 1
    sem[L] = len(ids) - achados
    print(ano, "-> legislatura", L, ":", achados, "de", len(ids), "deputados ligados ao TSE")

u = "https://apisidra.ibge.gov.br/values/t/9605/n1/all/v/93/p/all/c86/all"
pop = {}
for r in json.load(urllib.request.urlopen(u, timeout=120))[1:]:
    ano = next(v for k, v in r.items() if k.endswith("N") and v in ("2010", "2022"))
    cor = next(v for k, v in r.items() if k.endswith("N") and v in ("Total", "Branca", "Preta", "Amarela", "Parda", "Indígena"))
    pop.setdefault(ano, {})[cor] = int(r["V"])
json.dump({"deputados": out, "sem_ligacao": sem, "populacao": pop}, open("cor_raca.json", "w", encoding="utf-8"),
          ensure_ascii=False, separators=(",", ":"))
print("população (censos):", pop)
