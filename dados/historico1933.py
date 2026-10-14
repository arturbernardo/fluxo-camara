"""Estende a base para 1933–1951: Constituinte de 1933–34, legislatura de 1935–37 e legislatura de 1946–51.

A API da Câmara lista poucos deputados de 1946 e quase nenhum partido antes de 1945. As biografias oficiais
listam cada mandato com estado, partido e data de posse; daqui saem os partidos. Nos anos 1930 os partidos eram
estaduais e a mesma sigla mudava de sentido conforme o estado, então a chave é sigla + estado (ex.: PP-MG).

Lê ../dados.json, deputados_1930_1946.json e biografias.json (gerados por historico1933 na primeira execução)
e gera ../dados1933.json no mesmo formato de dados.json.
"""
import html, json, os, re, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
# siglas de 1946–51: mesma padronização de process.py para o período 1945–65
CANON_45 = {"PSD": "PSD45", "PTB": "PTB45", "PR": "PR45", "PST": "PST45", "PTN": "PTN45", "PDC": "PDC45",
            "PL": "PL45", "PRP": "PRP45", "PSC": "PSC45", "PSB": "PSB47", "PTR": "PTR45", "PRT": "PRT45"}

UFS = {"AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR",
       "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO", "GB"}
NOMES_30 = {  # nomes dos partidos estaduais mais conhecidos (os demais aparecem só pela sigla)
    "PP-MG": "Partido Progressista (MG)", "PRM-MG": "Partido Republicano Mineiro", "PRP-SP": "Partido Republicano Paulista",
    "PC-SP": "Partido Constitucionalista (SP)", "PRL-RS": "Partido Republicano Liberal (RS)", "FUG-RS": "Frente Única Gaúcha",
    "PL-RS": "Partido Libertador (RS)", "LEC": "Liga Eleitoral Católica", "UPF-RJ": "União Progressista Fluminense",
    "PNS-PI": "Partido Nacional Socialista (PI)", "PLC-SC": "Partido Liberal Catarinense", "PL-PA": "Partido Liberal do Pará",
    "PSD-PE": "Partido Social Democrático (PE, anos 1930)", "PSD-BA": "Partido Social Democrático (BA, anos 1930)",
    "PP-PB": "Partido Progressista da Paraíba",
}
SUCESSORES_45 = ["PSD45", "UDN", "PTB45", "PSP", "PR45", "PST45", "PTN45", "PDC45", "PL45", "PRP45", "PSC45", "PSB47", "PCB", "PPS46"]


def lista(L):
    rows, page = [], 1
    while True:
        u = f"https://dadosabertos.camara.leg.br/api/v2/deputados?idLegislatura={L}&itens=100&pagina={page}"
        d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"Accept": "application/json"}), timeout=60))
        rows += d["dados"]
        if not any(l["rel"] == "next" for l in d["links"]):
            return rows
        page += 1


def baixa_bio(i):
    url = f"https://www.camara.leg.br/deputados/{i}/biografia"
    for t in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (pesquisa academica)"})
            raw = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "ignore")
            raw = re.sub(r"<script.*?</script>|<style.*?</style>", "", raw, flags=re.S)
            txt = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw)))
            return str(i), txt[txt.find("Biografia"):][:15000]
        except Exception:
            time.sleep(3 + 3 * t)
    return str(i), None


dados = json.load(open("../dados.json", encoding="utf-8"))
if os.path.exists("deputados_1930_1946.json"):
    api = {int(k): v for k, v in json.load(open("deputados_1930_1946.json", encoding="utf-8")).items()}
else:
    api = {L: [r for r in lista(L) if r["idLegislatura"] == L] for L in (36, 37, 38)}
    json.dump(api, open("deputados_1930_1946.json", "w", encoding="utf-8"), ensure_ascii=False)
cache = json.load(open("biografias.json", encoding="utf-8")) if os.path.exists("biografias.json") else {}
ids = {r["id"] for L in (36, 37, 38) for r in api.get(L, [])} | \
      {i for i, _, _, seq in dados["deps"] if any(s[0] in (39, 40, 41) for s in seq)}
# deputados que não estão em nenhuma lista da API (ex.: comunistas de 1946, cassados em 1948): todos os códigos
# de deputado federal registrados no Wikidata (P7480) que ainda não estão na base; só ficam os que tiveram
# mandato entre 1933 e 1951 segundo a biografia
q = "SELECT ?id WHERE { ?item wdt:P7480 ?id . }"
req = urllib.request.Request("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"}),
                             headers={"User-Agent": "fluxo-camara/1.0 (https://github.com/arturbernardo/fluxo-camara)"})
na_base = {d[0] for d in dados["deps"]}
wd = {int(b["id"]["value"]) for b in json.load(urllib.request.urlopen(req, timeout=120))["results"]["bindings"]
      if b["id"]["value"].isdigit()}
ids |= wd - na_base
falta = [i for i in ids if str(i) not in cache]
with ThreadPoolExecutor(4) as ex:
    for k, v in ex.map(baixa_bio, falta):
        if v:
            cache[k] = v
json.dump(cache, open("biografias.json", "w", encoding="utf-8"), ensure_ascii=False)


def mandatos(t):
    i = t.find("Mandatos (na Câmara dos Deputados):")
    if i < 0:
        return []
    seg = t[i + 35:]
    fim = [k for k in (seg.find(s) for s in ("Mandatos Externos", "Proposições", "Atividades", "Filiações", "Estudos",
                                              "Profissões", "Registros", "Suplências")) if k > 0]
    seg = seg[:min(fim)] if fim else seg
    out = []
    for e in seg.split(";"):
        if "Deputado" not in e:
            continue
        posse = re.search(r"Dt\. Posse:\s*(\d{1,2})/(\d{1,2})/(\d{4})", e)
        data = f"{posse.group(3)}-{int(posse.group(2)):02d}-{int(posse.group(1)):02d}" if posse else None
        if not data:
            y = re.search(r"\b(19[34]\d)\b", e)
            data = f"{y.group(1)}-06-01" if y else None
        corpo = re.sub(r",?\s*Dt\. Posse:.*", "", re.sub(r"Deputado\(a\) Federal\s*-\s*", "", e))
        partes = [p.strip() for p in corpo.split(",") if p.strip()]
        uf = partido = None
        for k, p in enumerate(partes):
            if p in UFS:
                uf = p
                nxt = partes[k + 1] if k + 1 < len(partes) else None
                if nxt and nxt not in UFS and re.fullmatch(r"[A-ZÀ-Ú.\-]{2,12}", nxt):
                    partido = nxt
                break
        out.append((data, uf, partido))
    return out


def leg(data):
    if not data:
        return None
    if "1933-11-01" <= data <= "1935-04-27":
        return 36
    if "1935-04-28" <= data <= "1937-11-10":
        return 37
    if "1945-12-01" <= data <= "1951-03-09":
        return 38
    return None


def chave(sigla, uf, L):
    if not sigla or sigla in ("NÃOINFORMA", "NAOINFORMA"):
        return "NI"
    if sigla in ("S.PARTIDO", "S.PART."):
        return "SP"
    sigla = sigla.replace("*", "")
    if L == 38:
        return "PPS46" if sigla == "PPS" else CANON_45.get(sigla, sigla)
    if sigla == "LEC":
        return "LEC"
    return f"{sigla}-{uf}" if uf else sigla


novos = {}   # id -> {L: chave}
nomes, ufs = {}, {}
for L in (36, 37, 38):
    for r in api.get(L, []):
        ufs[r["id"]] = r["siglaUf"]
        if r["nome"]:
            nomes[r["id"]] = r["nome"]
        novos.setdefault(r["id"], {})[L] = chave(r["siglaPartido"], r["siglaUf"], L) if L == 38 else None
for i in ids:
    for data, uf, partido in mandatos(cache.get(str(i)) or ""):
        L = leg(data)
        if not L:
            continue
        # sem estado nos anos 1930: deputado classista (representação profissional, eleito por sindicatos)
        k = "CLASSISTA" if (L in (36, 37) and not uf) else chave(partido, uf, L)
        atual = novos.setdefault(i, {}).get(L)
        if atual in (None, "NI"):
            novos[i][L] = k
        if uf:
            ufs.setdefault(i, uf)
# partido da lista da API quando a biografia não traz
api_sigla = {(r["id"], L): (r["siglaPartido"], r["siglaUf"]) for L in (36, 37) for r in api.get(L, [])}
for i in novos:
    for L in novos[i]:
        if novos[i][L] in (None, "NI") and (i, L) in api_sigla and api_sigla[(i, L)][0]:
            s, uf = api_sigla[(i, L)]
            novos[i][L] = chave(s.replace("*", ""), uf, L)
        if novos[i][L] is None:
            novos[i][L] = "NI"

# --- deputados sem partido em 1933–37: procura a legenda no texto das biografias e da Wikipédia ---
# 1) frases do tipo "elegeu-se ... na legenda do Partido X" (com o ano, quando houver: 1933 -> Constituinte,
#    1934 -> legislatura de 1935–37); 2) nomes de partidos que só existiram nos anos 1930, em qualquer parte do texto.
LEGENDAS = [  # (padrão, chave; {uf} = estado do mandato)
    (r"Chapa Única|São Paulo Unido", "CHAPA-SP"), (r"Partido Autonomista", "PA-DF"),
    (r"Partido Constitucionalista", "PC-SP"), (r"Partido Republicano Paulista", "PRP-SP"),
    (r"Partido Democrático de São Paulo|Partido Democrático \(SP\)", "PD-SP"), (r"Partido Economista", "PE-DF"),
    (r"Partido Republicano Liberal", "PRL-RS"), (r"Frente Única", "FUG-RS"), (r"Partido Republicano Mineiro", "PRM-MG"),
    (r"Liga Eleitoral Católica", "LEC"), (r"Ação Integralista", "AIB"), (r"Partido Nacional de Alagoas", "PN-AL"),
    (r"Partido Socialista Flumin", "PSF-RJ"), (r"União Progressista Fluminense", "UPF-RJ"),
    (r"Partido Popular Radical", "PPR-RJ"),
]
AMBIGUOS = [(r"Partido Social Democrático", "PSD-{uf}"), (r"Partido Progressista", "PP-{uf}"),
            (r"Partido Libertador", "PL-{uf}"), (r"Partido Republicano", "PR-{uf}")]
NOMES_30.update({"CHAPA-SP": "Chapa Única por São Paulo Unido (PRP + Partido Democrático, 1933)",
                 "PA-DF": "Partido Autonomista do Distrito Federal", "PD-SP": "Partido Democrático de São Paulo",
                 "PE-DF": "Partido Economista do Distrito Federal", "AIB": "Ação Integralista Brasileira",
                 "PN-AL": "Partido Nacional de Alagoas", "PSF-RJ": "Partido Socialista Fluminense",
                 "PPR-RJ": "Partido Popular Radical (RJ)"})

wiki_titulos = json.load(open("../wikipedia.json", encoding="utf-8")) if os.path.exists("../wikipedia.json") else {}


def texto_wiki(i):
    tit = wiki_titulos.get(str(i))
    if not tit:
        return ""
    p = {"action": "query", "prop": "extracts", "explaintext": 1, "titles": tit.replace("_", " "), "format": "json", "redirects": 1}
    try:
        r = json.load(urllib.request.urlopen(urllib.request.Request("https://pt.wikipedia.org/w/api.php?" + urllib.parse.urlencode(p),
                                             headers={"User-Agent": "fluxo-camara/1.0 (https://github.com/arturbernardo/fluxo-camara)"}), timeout=60))
        return next(iter(r["query"]["pages"].values())).get("extract", "")[:30000]
    except Exception:
        return ""


def uf_do_mandato(i, L):
    for data, uf, _ in mandatos(cache.get(str(i)) or ""):
        if leg(data) == L and uf:
            return uf
    return ufs.get(i)


def acha_legenda(texto, L, uf):
    ano = "1933" if L == 36 else "1934|1935"
    # frases com "legenda"/"pelo partido" perto do ano da eleição
    for m in re.finditer(r"[^.]*(?:%s)[^.]*\." % ano, texto):
        frase = m.group(0)
        if not re.search(r"legenda|elegeu|eleit|candidat|pel[oa] (?:Partido|Chapa|Liga|Frente|União)", frase):
            continue
        for pad, k in LEGENDAS + AMBIGUOS:
            if re.search(pad, frase):
                if k == "CHAPA-SP" and L != 36:
                    continue
                return k.format(uf=uf)
    # nomes exclusivos dos anos 1930 em qualquer parte do texto
    for pad, k in LEGENDAS:
        if re.search(pad, texto) and not (k == "CHAPA-SP" and L != 36):
            if k in ("PA-DF", "PE-DF") and uf != "DF":
                continue
            return k
    return None


pendentes = [(i, L) for i in novos for L in novos[i] if L in (36, 37) and novos[i][L] == "NI"]
textos = {}
with ThreadPoolExecutor(3) as ex:
    for i, w in zip({i for i, _ in pendentes}, ex.map(texto_wiki, {i for i, _ in pendentes})):
        textos[i] = w
achados = 0
for i, L in pendentes:
    uf = uf_do_mandato(i, L)
    k = acha_legenda((cache.get(str(i)) or "") + " " + textos.get(i, ""), L, uf)
    if k:
        novos[i][L] = k
        achados += 1
print("legendas encontradas no texto para deputados sem partido em 1933–37:", achados, "de", len(pendentes))
# Constituinte de 1933 em São Paulo: PRP e Partido Democrático concorreram juntos na Chapa Única por São Paulo Unido,
# e o Partido Constitucionalista (sucessor do PD) só foi fundado em 1934 -> todos contam como Chapa Única
for i in novos:
    if novos[i].get(36) in ("PRP-SP", "PD-SP", "PC-SP"):
        novos[i][36] = "CHAPA-SP"

partidos = dict(dados["parties"])
partidos["PPS46"] = ["PPS", "Partido Popular Sindicalista (1946)", "C", ["PSP"]]
partidos["CLASSISTA"] = ["classistas", "Deputados classistas (representação profissional, 1933–37)", "NA", SUCESSORES_45]
for i, por_leg in novos.items():
    for L, k in por_leg.items():
        if k not in partidos:
            sig = k.split("-")[0]
            partidos[k] = [k, NOMES_30.get(k, f"{sig} — partido estadual ({k.split('-')[1] if '-' in k else 'nacional'}, 1933–37)"),
                           "NA", SUCESSORES_45]
    # a classificação ideológica de 1933–37 fica em aberto (sem medida nem classificação provisória)

# nome dos deputados que não estão em nenhuma lista (vindos do Wikidata): dados cadastrais da API
def cadastro(i):
    u = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{i}"
    for t in range(4):
        try:
            s = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"Accept": "application/json"}), timeout=60))["dados"]
            return i, (s["ultimoStatus"].get("nomeEleitoral") or s["ultimoStatus"].get("nome") or s.get("nomeCivil"), s["ultimoStatus"].get("siglaUf"))
        except Exception:
            time.sleep(2 + 2 * t)
    return i, (None, None)


sem_nome = [i for i, por_leg in novos.items() if por_leg and i not in nomes and i not in {d[0] for d in dados["deps"]}]
with ThreadPoolExecutor(4) as ex:
    for i, (n, uf) in ex.map(cadastro, sem_nome):
        if n:
            nomes[i] = n.upper()
        if uf:
            ufs.setdefault(i, uf)
print("deputados acrescentados pelo Wikidata:", len(sem_nome))

deps = {d[0]: d for d in dados["deps"]}
for i, por_leg in novos.items():
    if not por_leg:
        continue
    pre = [[L, por_leg[L]] for L in sorted(por_leg)]
    if i in deps:
        deps[i][3] = pre + deps[i][3]
    else:
        deps[i] = [i, nomes.get(i, f"Deputado #{i}"), ufs.get(i), pre]

# cassação dos eleitos pelo PCB (Lei nº 211, de 7/1/1948, depois do cancelamento do registro do partido pelo TSE)
cass48 = {}
for i in novos:
    t = cache.get(str(i)) or ""
    j = t.find("Perdas de Mandato:")
    if j >= 0 and re.search(r"Lei n[ºo°]\s*211|registro do Partido Comunista", t[j:j + 600]):
        cass48[str(i)] = [[38, 1948, "Lei 211/1948"]]
json.dump(cass48, open("../cassacoes1933.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("cassados em 1948 (PCB):", len(cass48))

out = {"legs": [[36, "1933"], [37, "1935"], [38, "1946"]] + dados["legs"],
       "ends": {"36": "1935", "37": "1937", "38": "1951"},
       "parties": partidos, "deps": list(deps.values())}
json.dump(out, open("../dados1933.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
from collections import Counter
for L in (36, 37, 38):
    c = Counter(por_leg[L] for por_leg in novos.values() if L in por_leg)
    print(L, sum(c.values()), "deputados;", c.most_common(12))
