"""Artigos da Wikipédia em português para cada deputado.

1. Wikidata: itens com a propriedade P7480 (código de deputado federal na Câmara) que têm artigo na pt.wikipedia.
2. Para os cassados sem artigo ligado no Wikidata, busca na própria Wikipédia e só aceita o resultado se o título
   contém todas as palavras do nome parlamentar e o texto menciona "deputado federal", a cassação e o estado.

Gera ../wikipedia.json: {id: título do artigo}.
"""
import json, re, time, unicodedata, urllib.parse, urllib.request

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


dados = json.load(open("../dados.json", encoding="utf-8"))
dep = {str(d[0]): d for d in dados["deps"]}
cass = json.load(open("../cassacoes.json", encoding="utf-8"))

q = ("SELECT ?id ?pt WHERE { ?item wdt:P7480 ?id . ?pt schema:about ?item ; "
     "schema:isPartOf <https://pt.wikipedia.org/> . }")
res = get("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"}))
out = {}
for b in res["results"]["bindings"]:
    i = b["id"]["value"]
    if i in dep:
        out[i] = urllib.parse.unquote(b["pt"]["value"].split("/wiki/", 1)[1])
print("Wikidata:", len(out))

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
        if (re.search(r"deputad[oa] federal", txt, re.I) and re.search(r"cassad|AI-5|AI-1|Ato Institucional", txt, re.I)
                and (not estado or estado in txt)):
            out[i] = title.replace(" ", "_")
            achados += 1
            break
    time.sleep(0.2)
print("busca na Wikipédia (cassados):", achados)

json.dump(out, open("../wikipedia.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("total com artigo:", len(out), "de", len(dep), "| cassados:", sum(i in out for i in cass), "de", len(cass))
