# Fluxo da Câmara

Visualização do fluxo de deputados federais entre partidos, de 1951 a 2027.

**Site:** https://arturbernardo.github.io/fluxo-camara/

Cada coluna é uma legislatura e cada bloco, uma bancada na posse. Dentro da coluna, os partidos
estão ordenados da esquerda para a direita conforme a posição que tinham naquela época. As faixas
ligam os deputados que voltaram na legislatura seguinte. A página também lista a trajetória de
cada deputado, com filtros por migração (ex.: passou pelo PMDB e depois pelo PCdoB).

## Fonte

[API de Dados Abertos da Câmara dos Deputados](https://dadosabertos.camara.leg.br): deputados por
legislatura e, para quem aparece com mais de um partido, o histórico de eventos com data.

## Limitações

- Até 1987 a base registra um partido por deputado e legislatura; trocas no meio do mandato só aparecem de 1987 em diante.
- A legislatura de 1946 está incompleta na base e ficou de fora.
- A legislatura 2023–27 ainda não tem onda própria do BLS e repete a de 2021.

## Cassações

Deputados cassados pelo regime militar (AI-1, AI-2 e AI-5), extraídos da seção “Perdas de Mandato” das
biografias oficiais em camara.leg.br por `dados/cassacoes.py`. Na página, aparecem como uma faixa escura na base de
cada bloco de partido e marcados na lista de deputados.

## Exilados e mortos pela ditadura

Mortos: deputados da base na lista de mortos e desaparecidos políticos da Comissão Nacional da Verdade (2014),
cruzada pelo Wikidata. Exilados: lista revisada à mão a partir de menções a exílio nos artigos da Wikipédia e nas
biografias da Câmara, mais a categoria de exilados da Wikipédia; só conta exílio durante a ditadura. A lista de
exilados é incompleta. Detalhes e critérios em `dados/perseguicoes.py`.

## Biografias

Cada deputado tem link para a biografia oficial na Câmara. O link para a Wikipédia vem do Wikidata (propriedade
P7480, código de deputado federal) e, para cassados sem esse vínculo, de uma busca na Wikipédia aceita só quando
título, estado e menção à cassação conferem (`dados/wikipedia.py`).

## Posição ideológica (0 = esquerda, 10 = direita)

| Período | Fonte | O que mede |
|---|---|---|
| 1987–2027 | [Brazilian Legislative Surveys](https://doi.org/10.7910/DVN/6KVTUV) (Zucco & Power, 2024), 9 ondas de 1990 a 2021 | Deputados situam os partidos na escala esquerda–direita. Escala original de −1 a +1, convertida para 0–10. |
| 1967–1987 | [V-Party](https://www.v-dem.net/data/v-party-dataset/) (V-Dem), variável `v2pariglef`, eleições de 1970 a 1986 | Especialistas situam os partidos na dimensão econômica. Convertido para a escala BLS por regressão linear nas observações em que as duas fontes coincidem (r = 0,97, n = 78). |
| 1951–1967 e partidos não avaliados | Classificação provisória, atribuída à mão | Sem medida publicada; aparece hachurada na página. |

Quando um partido não foi avaliado numa legislatura, mas foi na vizinha, usa-se o valor da vizinha. As siglas
seguem a genealogia do apêndice do BLS (ex.: PDS → PPR → PPB → PP; PFL → DEM; PL → PR → PL). Os arquivos de origem
estão em `dados/fontes/`, e a junção é feita por `dados/posicoes.py`. A classificação provisória e as notas de
contexto ficam no objeto `POS` em `template.html`.

Licenças das fontes: BLS em CC0; o extrato do V-Party (só partidos brasileiros, vindo do pacote
[vdemdata](https://github.com/vdeminstitute/vdemdata)) segue a licença CC BY-SA 4.0 do V-Dem.

## Como atualizar

```bash
cd dados
python3 fetch.py        # baixa deputados por legislatura
python3 fetch_hist.py   # baixa o histórico de quem trocou de partido
python3 process.py      # padroniza siglas por época e gera ../dados.json
python3 posicoes.py     # junta BLS e V-Party e gera ../posicoes.json
python3 cassacoes.py    # lê as cassações nas biografias da Câmara e gera ../cassacoes.json
python3 wikipedia.py    # liga deputados a artigos da Wikipédia (Wikidata + busca) e gera ../wikipedia.json
python3 perseguicoes.py # lista revisada de exilados e mortos pela ditadura -> ../perseguicoes.json
cd ..
python3 build.py        # gera index.html
```
