"""Cassações de mandato de deputados federais durante a ditadura (legislaturas 1963–1987).

Lê a seção "Perdas de Mandato" das biografias oficiais em camara.leg.br e gera ../cassacoes.json:
{id: [[legislatura, ano, base], ...]}, em que base é o ato usado (AI-1, AI-2, AI-5, outro).
As biografias baixadas ficam em biografias.json (não versionado) para não baixar de novo.
"""
import html, json, os, re, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

LEGS = range(42, 48)  # 1963–1987
dados = json.load(open("../dados.json", encoding="utf-8"))
ids = sorted({i for i, _, _, seq in dados["deps"] if any(s[0] in LEGS for s in seq)})

cache = json.load(open("biografias.json", encoding="utf-8")) if os.path.exists("biografias.json") else {}


def baixa(i):
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


falta = [i for i in ids if str(i) not in cache]
with ThreadPoolExecutor(4) as ex:
    for k, v in ex.map(baixa, falta):
        if v:
            cache[k] = v
json.dump(cache, open("biografias.json", "w", encoding="utf-8"), ensure_ascii=False)

FIM = ("Registros Complementares", "Atividades", "Estudos e Cursos", "Obras Publicadas", "Mandatos Externos",
       "Condecorações", "Fontes", "Suplências e Efetivações", "Licenças")


def perdas(t):
    i = t.find("Perdas de Mandato:")
    if i < 0:
        return ""
    j = min([k for k in (t.find(s, i + 18) for s in FIM) if k > 0] or [len(t)])
    return t[i + 18:j]


out, sem_leg = {}, 0
for i in ids:
    t = cache.get(str(i)) or ""
    for trecho in re.split(r"(?:^|\s)-\s+(?=Mandato)|;\s*(?=Mandato)", perdas(t)):
        if not re.search(r"cassad", trecho, re.I):
            continue
        m = re.search(r"(4[2-7])ª Legislatura", trecho, re.I)
        r = re.search(r"Legislatura \(?(19[6-8]\d)\s*-\s*19[6-8]\d", trecho, re.I)
        # ano do ato: tira intervalos de legislatura e as datas dos próprios Atos Institucionais
        limpo = re.sub(r"19\d\d\s*-\s*19\d\d", " ", trecho)
        limpo = re.sub(r"Ato Institucional\s*(?:n[ºo°.]*\s*)?\d+\s*,?\s*de \d{1,2}(?:/\d{1,2}/| de \w+ de )19\d\d", " ", limpo)
        anos = [int(a) for a in re.findall(r"\b(19[6-8]\d)\b", limpo)]
        if m:
            L = int(m.group(1))
        elif r:
            L = 42 + (int(r.group(1)) - 1963) // 4
        elif anos:
            L = 42 + (anos[0] - 1963) // 4
        else:
            sem_leg += 1
            continue
        ini = 1963 + 4 * (L - 42)
        ano = next((a for a in anos if ini <= a <= ini + 4), None)
        if re.search(r"Ato Institucional\s*(?:n[ºo°.]*\s*)?5\b|AI-5", trecho):
            base = "AI-5"
        elif re.search(r"Ato Institucional\s*(?:n[ºo°.]*\s*)?2\b|AI-2", trecho):
            base = "AI-2"
        elif re.search(r"Ato Institucional\s*(?:n[ºo°.]*\s*)?1\b|AI-1|Comando Supremo da Revolução", trecho):
            base = "AI-1"
        else:
            base = "outro"
        ev = [L, ano, base]
        if ev not in out.setdefault(i, []):
            out[i].append(ev)

json.dump(out, open("../cassacoes.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
from collections import Counter
print(len(ids), "biografias;", len(out), "deputados cassados;", sem_leg, "trechos sem legislatura/ano")
print(sorted(Counter((e[0], e[2]) for v in out.values() for e in v).items()))
