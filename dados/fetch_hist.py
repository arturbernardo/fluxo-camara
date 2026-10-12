import json, urllib.request, time, collections
from concurrent.futures import ThreadPoolExecutor
d = json.load(open("deputados_raw.json"))
ids = set()
for L, rows in d.items():
    if int(L) < 48: continue
    c = collections.defaultdict(set)
    for r in rows: c[r["id"]].add(r["siglaPartido"])
    ids |= {i for i, s in c.items() if len(s) > 1}
def get(i):
    url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{i}/historico"
    for t in range(5):
        try:
            return i, json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"Accept": "application/json"}), timeout=60))["dados"]
        except Exception:
            time.sleep(2 + t * 2)
    return i, None
with ThreadPoolExecutor(8) as ex:
    res = dict(ex.map(get, sorted(ids)))
print(len(ids), sum(v is None for v in res.values()))
json.dump(res, open("historico.json", "w"), ensure_ascii=False)
