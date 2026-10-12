import json, urllib.request, time
out = {}
for L in range(38, 58):
    rows, page = [], 1
    while True:
        url = f"https://dadosabertos.camara.leg.br/api/v2/deputados?idLegislatura={L}&itens=100&pagina={page}&ordem=ASC&ordenarPor=nome"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        for t in range(4):
            try:
                d = json.load(urllib.request.urlopen(req, timeout=60)); break
            except Exception as e:
                time.sleep(2)
        rows += d["dados"]
        if not any(l["rel"] == "next" for l in d["links"]): break
        page += 1
    out[L] = rows
    print(L, len(rows), sum(r["idLegislatura"] == L for r in rows), sum(r["siglaPartido"] is None for r in rows), flush=True)
json.dump(out, open("deputados_raw.json", "w"), ensure_ascii=False)
