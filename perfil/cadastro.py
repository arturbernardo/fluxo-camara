"""Baixa o cadastro (sexo, nascimento, escolaridade, naturalidade) e as profissões de cada deputado da base
desde 1933 (../dados1933.json), pela API de Dados Abertos da Câmara. Gera cadastro.json (não versionado)."""
import json, os, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

dados = json.load(open("../dados1933.json", encoding="utf-8"))
cache = json.load(open("cadastro.json", encoding="utf-8")) if os.path.exists("cadastro.json") else {}


def get(url):
    for t in range(5):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"Accept": "application/json"}), timeout=60))["dados"]
        except Exception:
            time.sleep(2 + 2 * t)
    return None


def baixa(i):
    base = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{i}"
    d, p = get(base), get(base + "/profissoes")
    if d is None:
        return str(i), None
    return str(i), {"sexo": d.get("sexo"), "nascimento": d.get("dataNascimento"), "escolaridade": d.get("escolaridade"),
                    "uf_nasc": d.get("ufNascimento"), "mun_nasc": d.get("municipioNascimento"), "nome_civil": d.get("nomeCivil"),
                    "profissoes": [x.get("titulo") for x in (p or []) if x.get("titulo")]}


falta = [d[0] for d in dados["deps"] if str(d[0]) not in cache]
# grava a cada 200 deputados: se o processo for interrompido, a próxima execução continua de onde parou
with ThreadPoolExecutor(8) as ex:
    for n, (k, v) in enumerate(ex.map(baixa, falta), 1):
        if v:
            cache[k] = v
        if n % 200 == 0:
            json.dump(cache, open("cadastro.json", "w", encoding="utf-8"), ensure_ascii=False)
            print(n, "de", len(falta), flush=True)
json.dump(cache, open("cadastro.json", "w", encoding="utf-8"), ensure_ascii=False)
print(len(cache), "de", len(dados["deps"]))
