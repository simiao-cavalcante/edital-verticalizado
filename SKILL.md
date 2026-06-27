---
name: verticalizar-edital-pro
description: "Verticaliza qualquer edital de concurso público e gera o plano de estudo em TRÊS formatos a partir de uma fonte única: PLANILHA viva (Excel .xlsx), PAINEL interativo (HTML) e documento imprimível (DOCX). Use sempre que o usuário quiser transformar um edital (PDF ou conteúdo programático) em um plano de estudo estruturado, priorizável e acompanhável. Gatilhos: 'verticalizar edital', 'planilha do edital', 'edital verticalizado', 'plano de estudo do edital', 'organizar o edital pra estudar', 'acompanhar o edital'. Detecta os cargos/especialidades do edital e deixa o usuário escolher um; extrai disciplinas, assuntos e subitens preservando a numeração e a ordem do edital."
metadata:
  version: "1.0.0"
---

# Verticalizar Edital PRO — plano de estudo em 3 formatos

Transforma o edital de um concurso em um plano de estudo acompanhável, em três formatos gerados de uma fonte única: **Excel** (planilha viva), **HTML** (painel interativo) e **DOCX** (imprimível).

<args>$ARGUMENTS</args>

## Início — pergunte primeiro (sempre)

Ao acionar esta skill, **não comece a processar sem antes alinhar o básico com o usuário**:

1. **Peça o edital.** Solicite que o usuário **anexe o PDF do edital** (ou informe o caminho do arquivo, ou cole o conteúdo programático). Sem o edital não há o que verticalizar. Se o usuário já tiver anexado/citado um arquivo, use-o.
2. **Cargo/especialidade.** Rode a extração em modo lista (`--listar`) e **mostre os cargos detectados numerados**; pergunte qual o usuário quer. Editais grandes têm vários cargos — verticalizar todos seria inútil.
3. **Formatos.** Pergunte quais formatos gerar: **Excel, HTML, DOCX ou todos** (padrão sugerido: todos).
4. **(Opcional) Cabeçalho.** Confirme nome do concurso / órgão / banca / data, se quiser que apareçam no topo dos arquivos.

Use `AskUserQuestion` para os itens 2 e 3 quando ajudar. Só siga para o pipeline depois que tiver o edital e o cargo.

## Arquitetura — "extrair uma vez → vários geradores"

O edital é extraído **uma única vez** para um **JSON canônico** (a fonte da verdade); cada formato é gerado a partir dele, garantindo conteúdo idêntico nas três versões.

```
edital (.pdf ou .md) ─▶ extrair_edital.py ─▶ edital.json ─┬─▶ gerar_excel.py ─▶ planilha viva (.xlsx)
                                                          ├─▶ gerar_html.py  ─▶ painel interativo (.html)
                                                          └─▶ gerar_docx.py  ─▶ imprimível (.docx)
```

## Extração fiel + seleção de cargo

Regras de extração: **preservar a numeração e a ordem exatas do edital**, respeitar disciplinas agrupadas (não separar blocos que a banca uniu), ignorar seções administrativas (inscrições, cronograma), contar todos os níveis (assunto + subitem + sub-subitem). Editais reais trazem **vários cargos/especialidades** — a extração separa **Conhecimentos Gerais (comuns)** dos **Específicos por cargo** e monta a saída como *Gerais + cargo escolhido*.

- `.md` (conteúdo já verticalizado): extração **exata**, cargo único.
- `.pdf`: extração **heurística** — itens inline são tokenizados distinguindo nº de item de nº de lei; sempre confira o resumo impresso.

## Pipeline

### 1. Listar cargos e extrair o JSON
```bash
python3 scripts/extrair_edital.py <edital.pdf|edital.md> --listar
python3 scripts/extrair_edital.py <edital.pdf> --cargo "<nº|nome>" --out edital.json \
  [--concurso "..."] [--orgao "..."] [--banca "..."]
```
Saída: `edital.json` = `{concurso, orgao, banca, cargo, data_edital, disciplinas[ {nome, itens[ {numero, nivel, texto} ]} ]}`.

### 2. Gerar os formatos pedidos (todos consomem o mesmo `edital.json`)
```bash
python3 scripts/gerar_excel.py edital.json --out plano.xlsx
python3 scripts/gerar_html.py  edital.json --out painel.html
python3 scripts/gerar_docx.py  edital.json --out plano.docx
```
- **Excel** — 1 linha por item; colunas Status / Incidência / Prioridade (dropdowns), cores por estado, abas **Resumo** (% de cobertura + gráfico) e **Como usar**.
- **HTML** — painel de estudo (arquivo único): disciplinas recolhíveis, status por item (clique cicla A estudar → Estudando → Estudado → Revisão), progresso por disciplina e global, busca e filtro — salvo automaticamente no navegador (localStorage) + botões **Salvar/Carregar progresso** que exportam/importam um `.json` (não perde ao trocar de navegador ou dispositivo).
- **DOCX** — verticalizado imprimível com caixas ☐, quadro-resumo, uma disciplina por página, nº de página no rodapé.

### 3. Conferir e entregar
Leia o resumo da extração, abra cada arquivo, confirme que disciplinas/itens batem com o edital, e entregue os arquivos ao usuário.

## Incidência: honestidade

A skill **nunca inventa a incidência** (o que "mais cai"). No Excel a coluna nasce com **"Sem dado"**; para preenchê-la de verdade, o usuário junta os assuntos das **últimas provas reais da banca** e classifica cada item em Alta/Média/Baixa. Princípio: **a IA organiza, você decide — ela não chuta no seu lugar.**

## Marca (opcional)

Os arquivos exibem a logo em `assets/logo.png`, se existir. Para usar outra marca, substitua esse arquivo ou defina a variável de ambiente `EDITAL_LOGO` com o caminho de um PNG. Sem logo, os títulos se sustentam sozinhos.

## Dependências
`pip install pymupdf openpyxl python-docx`

## Scripts
| Script | Função |
|--------|--------|
| `scripts/extrair_edital.py` | Edital (.md/.pdf/.txt) → JSON canônico, com `--listar`/`--cargo` |
| `scripts/gerar_excel.py` | JSON → planilha de estudo viva (.xlsx) |
| `scripts/gerar_html.py` | JSON → painel de estudo interativo (.html) |
| `scripts/gerar_docx.py` | JSON → verticalizado imprimível (.docx) |
