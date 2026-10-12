"""Posição ideológica medida (0 = esquerda, 10 = direita) por partido e legislatura.

Fontes, em ordem de prioridade:
  1. BLS — Brazilian Legislative Surveys (Zucco & Power 2024, doi:10.7910/DVN/6KVTUV): deputados
     situam os partidos; 9 ondas, 1990–2021. Escala original de -1 a +1, convertida para 0–10.
  2. V-Party (V-Dem, variável v2pariglef): especialistas situam os partidos na dimensão econômica,
     eleições de 1970 a 2018. Convertido para a escala BLS por regressão linear nas observações
     em que as duas fontes coincidem.
  3. A mesma fonte numa legislatura vizinha (±1), quando o partido não foi avaliado naquela.
Partidos e períodos sem nenhuma dessas medidas ficam com a classificação provisória da página.

Gera ../posicoes.json: {chave: {legislatura: [posição, fonte]}} e um resumo da calibração.
"""
import csv, json

# legislatura em que cada onda do BLS foi a campo
BLS_LEG = {1990: 48, 1993: 49, 1997: 50, 2001: 51, 2005: 52, 2009: 53, 2013: 54, 2017: 55, 2021: 56}
# código do BLS -> chaves da nossa base (linhagem: renomeações e fusões descritas no apêndice do BLS)
BLS_KEYS = {
    "CID": ["PCB", "PPS", "CIDADANIA"], "DEM": ["PFL", "DEM"], "MDB": ["PMDB", "MDB"], "PCDOB": ["PCdoB"],
    "PDC": ["PDC85"], "PDT": ["PDT"], "PL": ["PL", "PR"], "PODE": ["PTN", "PODE"],
    "PP": ["PDS", "PPR", "PPB", "PP"], "PPold": ["PP93"], "PRN": ["PJ", "PRN"], "PROS": ["PROS"],
    "PSB": ["PSB"], "PSC": ["PSC"], "PSD": ["PSD"], "PSDB": ["PSDB"], "PSL": ["PSL"], "PSOL": ["PSOL"],
    "PSTU": ["PSTU"], "PT": ["PT"], "PTB": ["PTB81"], "PV": ["PV"], "REDE": ["REDE"],
    "REP": ["PRB", "REPUBLICANOS"], "SD": ["SOLIDARIEDADE"], "NOVO": ["NOVO"],
}
# eleição -> legislatura que ela elegeu
VP_LEG = {1970: 44, 1974: 45, 1978: 46, 1982: 47, 1986: 48, 1990: 49, 1994: 50, 1998: 51,
          2002: 52, 2006: 53, 2010: 54, 2014: 55, 2018: 56}
VP_KEYS = {
    "ARENA": ["ARENA"], "MDB": ["MDB"], "PMDB": ["PMDB", "MDB"], "PDT": ["PDT"], "PTB": ["PTB81"],
    "PDS": ["PDS"], "PFL": ["PFL", "DEM"], "PT": ["PT"], "PSDB": ["PSDB"], "PDC": ["PDC85"],
    "PL": ["PL"], "PR / PL": ["PR", "PL"], "PPR": ["PPR"], "PPB": ["PPB", "PP"], "PSB": ["PSB"],
    "PPS": ["PPS"], "PSD": ["PSD"], "PRB": ["PRB", "REPUBLICANOS"], "PSL": ["PSL"],
}

dados = json.load(open("../dados.json", encoding="utf-8"))
present = {}  # (chave, legislatura) existentes na base
for _, _, _, seq in dados["deps"]:
    for s in seq:
        for k in s[1:]:
            present[(k, s[0])] = True
LEGS = [l[0] for l in dados["legs"]]

bls = {}
for r in csv.DictReader(open("fontes/bls9_estimates_partiespresidents_long.tab", encoding="utf-8")):
    code, year = r["party.or.pres"], int(r["year"])
    if code not in BLS_KEYS:
        continue  # presidentes
    for k in BLS_KEYS[code]:
        bls[(k, BLS_LEG[year])] = (float(r["ideo"]) + 1) * 5
# União Brasil (fusão DEM + PSL em 2022): estimativa dos próprios autores (apêndice A), 0,66
for L in (56, 57):
    bls[("UNIÃO", L)] = (0.66 + 1) * 5

vp = {}
for r in csv.DictReader(open("fontes/vparty_brasil.csv", encoding="utf-8")):
    year = int(float(r["year"]))
    if year not in VP_LEG or r["v2pashname"] not in VP_KEYS:
        continue
    L = VP_LEG[year]
    for k in VP_KEYS[r["v2pashname"]]:
        if k == "MDB" and L >= 47:
            continue  # o MDB pós-2017 vem do PMDB; o MDB de 1966–79 só até 1979
        vp[(k, L)] = float(r["v2pariglef"])

# calibração V-Party -> escala BLS (0–10)
# uma observação por partido e legislatura (siglas da mesma linhagem repetem o mesmo valor)
pairs = sorted({(x[1], vp[x], bls[x]) for x in vp if x in bls})
pairs = [(v, s) for _, v, s in pairs]
n = len(pairs)
mx = sum(p[0] for p in pairs) / n
my = sum(p[1] for p in pairs) / n
b = sum((p[0] - mx) * (p[1] - my) for p in pairs) / sum((p[0] - mx) ** 2 for p in pairs)
a = my - b * mx
r = sum((p[0] - mx) * (p[1] - my) for p in pairs) / (
    sum((p[0] - mx) ** 2 for p in pairs) * sum((p[1] - my) ** 2 for p in pairs)) ** 0.5
vp10 = {x: min(10, max(0, a + b * v)) for x, v in vp.items()}

out, counts = {}, {}
for (k, L) in sorted(present):
    if k in ("NI", "SP"):
        continue
    val = None
    if (k, L) in bls:
        val = (bls[(k, L)], "BLS")
    elif (k, L) in vp10:
        val = (vp10[(k, L)], "V-Party")
    else:
        for src, tab in (("BLS", bls), ("V-Party", vp10)):
            near = [tab[(k, M)] for M in (L - 1, L + 1) if (k, M) in tab]
            if near:
                val = (sum(near) / len(near), src + "~")
                break
    if val:
        out.setdefault(k, {})[L] = [round(val[0], 2), val[1]]
        counts[val[1]] = counts.get(val[1], 0) + 1

json.dump({"pos": out, "calib": {"a": round(a, 3), "b": round(b, 3), "r": round(r, 3), "n": n}},
          open("../posicoes.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"calibração V-Party -> BLS: 0–10 = {a:.2f} + {b:.2f}·v2pariglef  (r = {r:.2f}, n = {n})")
print("partido-legislaturas por fonte:", counts)
