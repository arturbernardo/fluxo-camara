"""Quem podia votar no Brasil, 1872–2026: eleitorado e comparecimento como % da população, e analfabetismo.

Fontes:
- Eleitorado (1910–2026) e comparecimento (1945–2024): TSE, via Ipeadata (séries ELEMUN e COMP, nível Brasil).
- População: censos do IBGE via Ipeadata (POPTOT), com interpolação geométrica entre censos e, depois de 2022,
  a taxa de crescimento 2010–2022.
- 1872 e 1881: artigo "Lei Saraiva" da Wikipédia em português (eleitores de paróquia em 1872; eleitorado e
  comparecimento na primeira eleição sob a lei, em 1881).
- 1894–1930: soma dos votos dos dois principais candidatos nas eleições presidenciais, segundo os artigos da
  Wikipédia em português de cada eleição (que citam Walter Costa Porto, "O voto no Brasil"). É uma aproximação
  do comparecimento: não inclui votos em outros candidatos, brancos e nulos.
- Analfabetismo de pessoas com 15 anos ou mais: 1900–1991, IBGE (censos), apud Anuário Estatístico 1995, em
  Souza, M. M. C., "O analfabetismo no Brasil sob o enfoque demográfico", IPEA, TD 639, 1999, tabela 1;
  2000–2022, Atlas do Desenvolvimento Humano / IBGE via Ipeadata (ADH_T_ANALF15M).

Gera eleitorado.json.
"""
import json, re, urllib.parse, urllib.request

UA = {"User-Agent": "fluxo-camara/1.0 (https://github.com/arturbernardo/fluxo-camara)"}


def ipea(cod):
    url = f"http://www.ipeadata.gov.br/api/odata4/ValoresSerie(SERCODIGO='{cod}')"
    v = json.load(urllib.request.urlopen(url, timeout=180))["value"]
    return {int(x["VALDATA"][:4]): x["VALVALOR"] for x in v if x.get("NIVNOME") == "Brasil" and x["VALVALOR"] is not None}


def wikitext(titulo):
    p = {"action": "parse", "page": titulo, "prop": "wikitext", "format": "json", "redirects": 1}
    u = "https://pt.wikipedia.org/w/api.php?" + urllib.parse.urlencode(p)
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60))["parse"]["wikitext"]["*"]


eleitorado = ipea("ELEMUN")
comparecimento = ipea("COMP")
pop_censo = {a: v for a, v in ipea("POPTOT").items() if a not in (1910,)}  # 1910 não teve censo (é estimativa)
analf_atlas = ipea("ADH_T_ANALF15M")


def populacao(ano):
    anos = sorted(pop_censo)
    if ano in pop_censo:
        return pop_censo[ano]
    if ano > anos[-1]:
        a0, a1 = 2010, 2022
        r = (pop_censo[a1] / pop_censo[a0]) ** (1 / (a1 - a0))
        return pop_censo[a1] * r ** (ano - a1)
    a0 = max(a for a in anos if a < ano)
    a1 = min(a for a in anos if a > ano)
    r = (pop_censo[a1] / pop_censo[a0]) ** (1 / (a1 - a0))
    return pop_censo[a0] * r ** (ano - a0)


# Império (Wikipédia, "Lei Saraiva")
pontos = [
    {"ano": 1872, "eleitorado": 1089659, "fonte_e": "Wikipédia, “Lei Saraiva” (eleitores de paróquia, 1872)"},
    {"ano": 1881, "eleitorado": 145296, "comparecimento": 96411, "fonte_e": "Wikipédia, “Lei Saraiva” (eleição de 31/10/1881)",
     "fonte_c": "Wikipédia, “Lei Saraiva”"},
]
# Primeira República: votos nos dois principais candidatos a presidente
for ano in (1894, 1898, 1902, 1906, 1910, 1914, 1918, 1919, 1922, 1926, 1930):
    t = wikitext(f"Eleição presidencial no Brasil em {ano}")
    votos = re.findall(r"\|\s*votos([12])\s*=\s*'*\{\{fmtn\|([\d.\s]+)", t)[:2]   # o 1º par (1930 tem dois quadros)
    soma = sum(int(re.sub(r"\D", "", v)) for _, v in votos)
    p = next((x for x in pontos if x["ano"] == ano), None)
    if not p:
        p = {"ano": ano}
        pontos.append(p)
    p["comparecimento"] = soma
    p["aprox_c"] = True
    p["fonte_c"] = f"Wikipédia, “Eleição presidencial no Brasil em {ano}” (dois principais candidatos)"
# TSE via Ipeadata
for ano, v in eleitorado.items():
    p = next((x for x in pontos if x["ano"] == ano), None)
    if not p:
        p = {"ano": ano}
        pontos.append(p)
    p["eleitorado"] = v
    p["fonte_e"] = "TSE, via Ipeadata (ELEMUN)"
for ano, v in comparecimento.items():
    p = next((x for x in pontos if x["ano"] == ano), None)
    if not p:
        p = {"ano": ano}
        pontos.append(p)
    p["comparecimento"] = v
    p.pop("aprox_c", None)
    p["fonte_c"] = "TSE, via Ipeadata (COMP)"

for p in pontos:
    pop = populacao(p["ano"])
    p["populacao"] = round(pop)
    p["pop_censo"] = p["ano"] in pop_censo
    if "eleitorado" in p:
        p["pct_e"] = round(100 * p["eleitorado"] / pop, 2)
    if "comparecimento" in p:
        p["pct_c"] = round(100 * p["comparecimento"] / pop, 2)
pontos.sort(key=lambda x: x["ano"])

# Analfabetismo (15 anos ou mais). 1900–1991: IPEA TD 639, tabela 1 (alfabetizados, analfabetos, sem declaração)
td639 = {1900: (3380451, 6348869, 22791), 1920: (6155567, 11401715, 0), 1940: (10379990, 13269381, 60398),
         1950: (14916779, 15272632, 60012), 1960: (24259284, 15964852, 54466), 1970: (35586771, 18146977, 274856),
         1980: (54793268, 18716847, 31828), 1991: (76603804, 19233239, 0)}
analf = [{"ano": a, "pct": round(100 * an / (al + an + sd), 1), "fonte": "IBGE (censos), em IPEA TD 639, tabela 1"}
         for a, (al, an, sd) in td639.items()]
for a in (2000, 2010, 2022):
    analf.append({"ano": a, "pct": round(analf_atlas[a], 1), "fonte": "Atlas do Desenvolvimento Humano / IBGE, via Ipeadata"})

json.dump({"pontos": pontos, "analfabetismo": analf, "populacao_censos": pop_censo},
          open("eleitorado.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for p in pontos:
    print(p["ano"], p.get("pct_e"), p.get("pct_c"), "aprox" if p.get("aprox_c") else "")
print([(a["ano"], a["pct"]) for a in analf])
