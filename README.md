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
- A posição ideológica (0 = esquerda, 10 = direita) é uma classificação simplificada, atribuída à mão por partido
  e por período, com base na literatura (para a fase recente, aproximada de Bolognesi, Ribeiro & Codato, 2023).
  Ainda está em revisão; a tabela completa está no fim da página e no objeto `POS` em `template.html`.

## Como atualizar

```bash
cd dados
python3 fetch.py        # baixa deputados por legislatura
python3 fetch_hist.py   # baixa o histórico de quem trocou de partido
python3 process.py      # padroniza siglas por época e gera ../dados.json
cd ..
python3 build.py        # gera index.html
```
