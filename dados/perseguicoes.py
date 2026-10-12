"""Deputados exilados e mortos pela ditadura (1964–1985). Lista revisada à mão.

Como foi montada:
- Mortos: deputados da base que estão na lista de mortos e desaparecidos políticos reconhecidos pela Comissão
  Nacional da Verdade (relatório final, vol. 3, 2014), cruzada pelo Wikidata (P7480 = código de deputado).
  Grabois, Marighella e Pomar também estão na lista, mas foram deputados só em 1946, legislatura fora da base.
- Exilados: menções a exílio, asilo ou banimento nos artigos da Wikipédia e nas biografias da Câmara dos
  deputados de 1951–1991, mais a categoria "Exilados na ditadura militar no Brasil (1964–1985)". Cada caso foi
  lido e só entrou exílio do próprio deputado durante a ditadura (ficaram de fora, por exemplo, exílios de
  1932 ou do Estado Novo e menções à anistia de outras pessoas).

Gera ../perseguicoes.json: {id: {"exilio": nota, "morte": nota}}.
"""
import json

EXILIO = {
    3120: "Exilado no Uruguai e na Argentina de 1964 até morrer, em 1976",               # João Goulart
    131041: "Exilado de 1964 a 1979 (Uruguai, Estados Unidos, Portugal)",                # Leonel Brizola
    65511: "Preso em 1964; exilado na Argélia de 1965 a 1979",                            # Miguel Arraes
    73429: "Cassado pelo AI-1; doze anos de exílio, até 1976",                            # Almino Affonso
    131308: "Cassado pelo AI-5; exilado no Chile a partir de dezembro de 1968",          # Márcio Moreira Alves
    131119: "Cassado pelo AI-1; nove meses de exílio na Iugoslávia e na França",          # Rubens Paiva
    130747: "Asilou-se na embaixada do Uruguai no fim de 1964; morreu no exílio em 1971", # Djalma Maranhão
    130967: "Exilado no México a partir de 1965",                                         # Francisco Julião
    74576: "Exilado no Uruguai a partir de abril de 1964",                                # Waldir Pires
    74225: "Exilado na Bolívia, no Uruguai, na Argentina e no Peru",                      # Neiva Moreira
    130925: "Quinze anos de exílio, até 1979",                                            # Benedito Cerqueira
    131058: "Exilado na Itália até 1979",                                                 # Paiva Muniz
    131100: "Exilado no Chile de 1964 a 1971",                                            # Paulo de Tarso
    130972: "Exilado no Chile; voltou em 1966",                                           # Mello Mourão
    65904: "Exilado no Uruguai, no Chile e na Argélia",                                   # Maurílio Ferreira Lima
    73662: "Exilado em Montevidéu de 1964 a 1965",                                        # Aldo Arantes
    131826: "Treze anos de exílio, a maior parte nos Estados Unidos",                     # Abdias Nascimento
    130825: "Cassado em 1964; exilado em Paris, onde morreu em 1973",                     # Josué de Castro
    3085: "Morreu exilado em Praga, em 1978",                                             # Roberto Morena
    65495: "Catorze anos de exílio (Bolívia, França, Chile, Estados Unidos)",             # José Serra
    74782: "Banido em 1969; exilado em Cuba",                                             # José Dirceu
    133985: "Saiu da prisão para o exílio em 1969",                                       # Vladimir Palmeira
    74496: "Banido em 1969 (classificado como exilado na Wikipédia)",                     # Ricardo Zarattini
    116663: "Oito anos e meio de exílio nos anos 1970",                                   # Alfredo Sirkis
    133987: "Exilado no Chile a partir de 1968",                                          # Cesar Maia
    139310: "Exilada no Chile, em Cuba e em Portugal",                                    # Moema São Thiago
    1526: "Exilado no Uruguai em 1971",                                                   # Tarso Genro
    133873: "Afastado da USP pelo AI-5; foi lecionar no Canadá (classificado como exilado na Wikipédia)",  # Florestan
}
MORTE = {
    131119: "Preso, torturado e morto por agentes do Estado em 1971; corpo nunca encontrado (CNV)",
    130747: "Morreu no exílio, em Montevidéu, em 1971; reconhecido como vítima da ditadura pela CNV",
}

dados = json.load(open("../dados.json", encoding="utf-8"))
ids = {d[0] for d in dados["deps"]}
out = {}
for i, nota in EXILIO.items():
    assert i in ids, i
    out.setdefault(str(i), {})["exilio"] = nota
for i, nota in MORTE.items():
    assert i in ids, i
    out.setdefault(str(i), {})["morte"] = nota
json.dump(out, open("../perseguicoes.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(len(EXILIO), "exilados;", len(MORTE), "mortos")
