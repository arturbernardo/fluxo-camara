import json, collections

raw = json.load(open("deputados_raw.json"))
hist = json.load(open("historico.json"))
LEGS = list(range(39, 58))  # 1951–2027 (a legislatura de 1946 está incompleta na base)


def canon(s, L):
    """Sigla da API -> chave canônica, considerando a época (siglas se repetem)."""
    if s is None:
        return "NI"
    s = s.replace("*", "").strip()
    if s == "PNI":
        return "NI"
    if s == "S.PART.":
        return "SP"
    if L <= 42:
        if s in ("ARENA", "MDB"):
            return s if L == 42 else "NI"
        if s == "PDS":
            return "NI"
        m = {"PSD": "PSD45", "PTB": "PTB45", "PR": "PR45", "PST": "PST45", "PTN": "PTN45", "PDC": "PDC45",
             "PL": "PL45", "PRP": "PRP45", "PSC": "PSC45", "PSB": "PSB47", "PTR": "PTR45", "PRT": "PRT45"}
        return m.get(s, s)
    if L <= 45:
        return s if s in ("ARENA", "MDB") else "NI"
    if s == "PTB":
        return "PTB81"
    if s == "PP":
        return "PP80" if L <= 47 else ("PP93" if L <= 50 else "PP")
    if s == "PDC":
        return "PDC85"
    if s == "PSD":
        return "PSD87" if L <= 51 else "PSD"
    if s == "PST":
        return "PST90"
    if s == "PRP":
        return "PRP89"
    if s in ("SD", "SDD"):
        return "SOLIDARIEDADE"
    if s == "PATRI":
        return "PATRIOTA"
    return s


# chave: (sigla exibida, nome, ideologia simplificada, sucessores institucionais: renomeação/fusão/extinção)
P = {
    "PSD45": ("PSD", "Partido Social Democrático (1945–65)", "C", ["ARENA", "MDB"]),
    "UDN": ("UDN", "União Democrática Nacional", "D", ["ARENA", "MDB"]),
    "PTB45": ("PTB", "Partido Trabalhista Brasileiro (1945–65)", "CE", ["ARENA", "MDB"]),
    "PSP": ("PSP", "Partido Social Progressista", "C", ["ARENA", "MDB"]),
    "PR45": ("PR", "Partido Republicano (1945–65)", "CD", ["ARENA", "MDB"]),
    "PST45": ("PST", "Partido Social Trabalhista (1946–65)", "CE", ["ARENA", "MDB"]),
    "PTN45": ("PTN", "Partido Trabalhista Nacional (1945–65)", "C", ["ARENA", "MDB"]),
    "PDC45": ("PDC", "Partido Democrata Cristão (1945–65)", "C", ["ARENA", "MDB"]),
    "PL45": ("PL", "Partido Libertador", "CD", ["ARENA", "MDB"]),
    "PRP45": ("PRP", "Partido de Representação Popular (integralista)", "D", ["ARENA", "MDB"]),
    "PSC45": ("PSC", "Partido Social Cristão (1945–65)", "C", ["ARENA", "MDB"]),
    "PSB47": ("PSB", "Partido Socialista Brasileiro (1947–65)", "E", ["ARENA", "MDB"]),
    "PTR45": ("PTR", "Partido Trabalhista Renovador", "CE", ["ARENA", "MDB"]),
    "PRT45": ("PRT", "Partido Rural Trabalhista", "CE", ["ARENA", "MDB"]),
    "MTR": ("MTR", "Movimento Trabalhista Renovador", "CE", ["ARENA", "MDB"]),
    "PCB": ("PCB", "Partido Comunista Brasileiro", "E", ["PPS"]),
    "ARENA": ("ARENA", "Aliança Renovadora Nacional (1966–79)", "D", ["PDS", "PP80", "PTB81", "PDT", "PMDB"]),
    "MDB": ("MDB", "Movimento Democrático Brasileiro (1966–79 e 2017–)", "C", ["PMDB", "PP80", "PDT", "PTB81", "PT", "PDS"]),
    "PDS": ("PDS", "Partido Democrático Social", "D", ["PPR"]),
    "PMDB": ("PMDB", "Partido do Movimento Democrático Brasileiro", "C", ["MDB"]),
    "PP80": ("PP", "Partido Popular (1980–82)", "C", ["PMDB"]),
    "PDT": ("PDT", "Partido Democrático Trabalhista", "CE", []),
    "PTB81": ("PTB", "Partido Trabalhista Brasileiro (1981–2023)", "CD", ["PRD"]),
    "PT": ("PT", "Partido dos Trabalhadores", "E", []),
    "PFL": ("PFL", "Partido da Frente Liberal", "D", ["DEM"]),
    "DEM": ("DEM", "Democratas", "D", ["UNIÃO"]),
    "UNIÃO": ("UNIÃO", "União Brasil", "D", []),
    "PSD": ("PSD", "Partido Social Democrático (2011–)", "CD", []),
    "PSDB": ("PSDB", "Partido da Social Democracia Brasileira", "C", []),
    "PCdoB": ("PCdoB", "Partido Comunista do Brasil", "E", []),
    "PDC85": ("PDC", "Partido Democrata Cristão (1985–93)", "D", ["PPR"]),
    "PL": ("PL", "Partido Liberal (1985–2006 e 2019–)", "D", ["PR"]),
    "PR": ("PR", "Partido da República (2006–19)", "D", ["PL"]),
    "PRONA": ("PRONA", "Partido de Reedificação da Ordem Nacional", "D", ["PR"]),
    "PJ": ("PJ", "Partido da Juventude", "CD", ["PRN"]),
    "PRN": ("PRN", "Partido da Reconstrução Nacional", "CD", ["PTC"]),
    "PTC": ("PTC", "Partido Trabalhista Cristão", "D", []),
    "PTdoB": ("PTdoB", "Partido Trabalhista do Brasil", "CD", ["AVANTE"]),
    "AVANTE": ("AVANTE", "Avante", "CD", []),
    "PSTU": ("PSTU", "Partido Socialista dos Trabalhadores Unificado", "E", []),
    "PMN": ("PMN", "Partido da Mobilização Nacional", "CD", []),
    "PRS": ("PRS", "Partido das Reformas Sociais", "CD", []),
    "PSD87": ("PSD", "Partido Social Democrático (1987–2003)", "CD", ["PTB81"]),
    "PST90": ("PST", "Partido Social Trabalhista (1988–2003)", "CD", ["PP93", "PL"]),
    "PTR": ("PTR", "Partido Trabalhista Reformador", "CD", ["PP93"]),
    "PP93": ("PP", "Partido Progressista (1993–95)", "CD", ["PPB"]),
    "PPR": ("PPR", "Partido Progressista Reformador", "D", ["PPB"]),
    "PPB": ("PPB", "Partido Progressista Brasileiro", "D", ["PP"]),
    "PP": ("PP", "Progressistas", "D", []),
    "PPS": ("PPS", "Partido Popular Socialista", "CE", ["CIDADANIA"]),
    "CIDADANIA": ("CIDADANIA", "Cidadania", "C", []),
    "PV": ("PV", "Partido Verde", "CE", []),
    "PSB": ("PSB", "Partido Socialista Brasileiro", "CE", []),
    "PSC": ("PSC", "Partido Social Cristão", "D", ["PODE"]),
    "PSL": ("PSL", "Partido Social Liberal", "D", ["UNIÃO"]),
    "PSOL": ("PSOL", "Partido Socialismo e Liberdade", "E", []),
    "PMR": ("PMR", "Partido Municipalista Renovador", "D", ["PRB"]),
    "PRB": ("PRB", "Partido Republicano Brasileiro", "D", ["REPUBLICANOS"]),
    "REPUBLICANOS": ("REPUBLICANOS", "Republicanos", "D", []),
    "PSDC": ("PSDC", "Partido Social Democrata Cristão", "D", ["DC"]),
    "DC": ("DC", "Democracia Cristã", "D", []),
    "PAN": ("PAN", "Partido dos Aposentados da Nação", "CD", ["PTB81"]),
    "PHS": ("PHS", "Partido Humanista da Solidariedade", "CD", ["PODE"]),
    "PRTB": ("PRTB", "Partido Renovador Trabalhista Brasileiro", "D", []),
    "PROS": ("PROS", "Partido Republicano da Ordem Social", "CD", ["SOLIDARIEDADE"]),
    "SOLIDARIEDADE": ("SD", "Solidariedade", "CD", []),
    "PEN": ("PEN", "Partido Ecológico Nacional", "D", ["PATRIOTA"]),
    "PATRIOTA": ("PATRIOTA", "Patriota", "D", ["PRD"]),
    "PRD": ("PRD", "Partido Renovação Democrática", "D", []),
    "PRP89": ("PRP", "Partido Republicano Progressista", "D", ["PATRIOTA"]),
    "PTN": ("PTN", "Partido Trabalhista Nacional", "CD", ["PODE"]),
    "PODE": ("PODE", "Podemos", "CD", []),
    "PMB": ("PMB", "Partido da Mulher Brasileira", "CD", []),
    "REDE": ("REDE", "Rede Sustentabilidade", "CE", []),
    "PPL": ("PPL", "Partido Pátria Livre", "CE", ["PCdoB"]),
    "NOVO": ("NOVO", "Partido Novo", "D", []),
    "MISSÃO": ("MISSÃO", "Missão", "D", []),
    "SP": ("s/ partido", "Sem partido", "NA", []),
    "NI": ("n/i", "Partido não informado na base", "NA", []),
}

names = collections.defaultdict(collections.Counter)
ufs = {}
per = collections.defaultdict(lambda: collections.defaultdict(list))
for Ls, rows in raw.items():
    L = int(Ls)
    if L not in LEGS:
        continue
    for r in rows:
        if r["idLegislatura"] != L:
            continue
        if r["nome"]:
            names[r["id"]][r["nome"]] += 1
        ufs[r["id"]] = r["siglaUf"]
        per[r["id"]][L].append(r["siglaPartido"])

deps, unknown = [], collections.Counter()
for i, byL in per.items():
    seq = []
    h = hist.get(str(i))
    for L in sorted(byL):
        start = end = None
        if h:
            ev = sorted([e for e in h if e["idLegislatura"] == L and e["siglaPartido"]
                         and not (e["descricaoStatus"] or "").startswith("Nome no início")],
                        key=lambda e: e["dataHora"])
            if ev:
                start, end = ev[0]["siglaPartido"], ev[-1]["siglaPartido"]
        if start is None:
            vals = [v for v in byL[L] if v] or [None]
            start = end = vals[0]
        a, b = canon(start, L), canon(end, L)
        for k in (a, b):
            if k not in P:
                unknown[k] += 1
        seq.append([L, a] if a == b else [L, a, b])
    nome = names[i].most_common(1)[0][0] if names[i] else f"Deputado #{i}"
    deps.append([i, nome, ufs.get(i), seq])

LD = {39: "1951", 40: "1955", 41: "1959", 42: "1963", 43: "1967", 44: "1971", 45: "1975", 46: "1979", 47: "1983",
      48: "1987", 49: "1991", 50: "1995", 51: "1999", 52: "2003", 53: "2007", 54: "2011", 55: "2015", 56: "2019", 57: "2023"}
out = {"legs": [[L, LD[L]] for L in LEGS], "parties": {k: list(v) for k, v in P.items()}, "deps": deps}
json.dump(out, open("../dados.json", "w"), ensure_ascii=False, separators=(",", ":"))

print("siglas sem mapeamento:", dict(unknown))
print(len(deps), "deputados")
print("por legislatura:", sorted(collections.Counter(s[0] for d in deps for s in d[3]).items()))
print("trocas dentro do mandato:", sum(len(s) == 3 for d in deps for s in d[3]))
