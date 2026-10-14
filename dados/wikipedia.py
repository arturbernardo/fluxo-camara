"""Artigos da Wikipédia em português para cada deputado.

1. Wikidata: itens com a propriedade P7480 (código de deputado federal na Câmara) que têm artigo na pt.wikipedia.
2. Para os cassados sem artigo ligado no Wikidata, busca na própria Wikipédia e só aceita o resultado se o título
   contém todas as palavras do nome parlamentar e o texto menciona "deputado federal", a cassação e o estado.

Gera ../wikipedia.json: {id: título do artigo}.
"""
import json, os, re, time, unicodedata, urllib.parse, urllib.request

UA = {"User-Agent": "fluxo-camara/1.0 (https://github.com/arturbernardo/fluxo-camara)"}
UF = {"AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá", "BA": "Bahia", "CE": "Ceará",
      "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão", "MG": "Minas Gerais",
      "MS": "Mato Grosso do Sul", "MT": "Mato Grosso", "PA": "Pará", "PB": "Paraíba", "PE": "Pernambuco",
      "PI": "Piauí", "PR": "Paraná", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RO": "Rondônia",
      "RR": "Roraima", "RS": "Rio Grande do Sul", "SC": "Santa Catarina", "SE": "Sergipe", "SP": "São Paulo",
      "TO": "Tocantins", "GB": "Guanabara"}
STOP = {"de", "da", "do", "dos", "das", "e"}


def get(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))


def fold(s):
    return re.sub(r"[^a-z ]", " ", unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()).split()


def wiki(params):
    return get("https://pt.wikipedia.org/w/api.php?" + urllib.parse.urlencode({**params, "format": "json"}))


# dados1933.json (versão desde 1933) contém todos os deputados de dados.json e mais os de 1933–51
base = "../dados1933.json" if os.path.exists("../dados1933.json") else "../dados.json"
dados = json.load(open(base, encoding="utf-8"))
dep = {str(d[0]): d for d in dados["deps"]}
cass = json.load(open("../cassacoes.json", encoding="utf-8"))
if os.path.exists("../cassacoes1933.json"):
    cass.update(json.load(open("../cassacoes1933.json", encoding="utf-8")))

q = ("SELECT ?item ?id ?pt WHERE { ?item wdt:P7480 ?id . ?pt schema:about ?item ; "
     "schema:isPartOf <https://pt.wikipedia.org/> . }")
res = get("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"}))
por_item = {}
for b in res["results"]["bindings"]:
    por_item.setdefault(b["item"]["value"], []).append(b)


def confere(nome, titulo):
    """Para itens do Wikidata com mais de um código: o último sobrenome tem de estar no título, e o título
    não pode indicar outra pessoa da família (Filho, Júnior, Neto) se o nome parlamentar não indica."""
    n, tt = fold(nome), fold(titulo)
    if not n or n[-1] not in tt:
        return False
    return not any(s in tt and s not in n for s in ("filho", "junior", "neto", "sobrinho"))


out, descartados = {}, []
for item, bs in por_item.items():
    for b in bs:
        i = b["id"]["value"]
        if i not in dep:
            continue
        titulo = urllib.parse.unquote(b["pt"]["value"].split("/wiki/", 1)[1])
        if len(bs) > 1 and not confere(dep[i][1], titulo.replace("_", " ")):
            descartados.append((dep[i][1], titulo))
            continue
        out[i] = titulo
print("Wikidata:", len(out), "| vínculos descartados (código errado no Wikidata):", descartados)

achados = 0
for i in cass:
    if i in out:
        continue
    nome, uf = dep[i][1], dep[i][2]
    toks = [t for t in fold(nome) if t not in STOP]
    for s in wiki({"action": "query", "list": "search", "srsearch": f"{nome} deputado", "srlimit": 6})["query"]["search"]:
        title = s["title"]
        if not all(t in set(fold(re.sub(r"\s*\(.*\)$", "", title))) for t in toks):
            continue
        pages = wiki({"action": "query", "prop": "extracts", "explaintext": 1, "titles": title})["query"]["pages"]
        txt = next(iter(pages.values())).get("extract", "")[:20000]
        estado = UF.get(uf, "")
        if (re.search(r"deputad[oa] federal", txt, re.I) and re.search(r"cassad|AI-5|AI-1|Ato Institucional|1948", txt, re.I)
                and (not estado or estado in txt)):
            out[i] = title.replace(" ", "_")
            achados += 1
            break
    time.sleep(0.2)
print("busca na Wikipédia (cassados):", achados)

json.dump(out, open("../wikipedia.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("total com artigo:", len(out), "de", len(dep), "| cassados:", sum(i in out for i in cass), "de", len(cass))
