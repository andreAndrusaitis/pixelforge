# Estúdio de agentes do PixelForge

Como as skills, os agentes e os comandos do Claude Code se encaixam. A sessão
principal (você conversando com o Claude) é a **produtora**: entrevista o autor,
decide e chama os agentes; os agentes executam uma parte e devolvem um relatório
no formato comum abaixo. Agentes **não** falam com o autor (não usam
`AskUserQuestion`): dúvida que só o autor responde volta em `PROBLEMAS` como
`[pergunta]`, e a produtora pergunta.

## Mapa

| Camada | Onde | O quê |
|---|---|---|
| Skills | `.claude/skills/<nome>/SKILL.md` | o *como*: entrevista, comandos reais, ciclo desenhar → pré-visualizar → ajustar, critérios de pronto |
| Agentes | `.claude/agents/<nome>.md` | o *quem*: um papel com ferramentas mínimas e contrato de retorno |
| Comandos | `.claude/commands/<nome>.md` | o *atalho*: `/cena <momento>` dispara a skill e orquestra os agentes |
| MCP | `python -m pixelforge mcp` | o motor para **outros** projetos (coletânea), sem shell |

| Skill | Agente que a executa | Comando |
|---|---|---|
| `pixel-art` (uma arte avulsa, foto → pixel) | `desenhista` | — |
| `pixel-personagem` | `desenhista` (+ `animador`) | `/personagem` |
| `pixel-cenario` | `cenografo` | `/cenario` |
| `pixel-cena` | `diretor-de-cena` (+ todos) | `/cena` |
| `pixel-som` | `sonoplasta` | `/som` |
| `pixel-revisao` | `revisor-visual` | `/revisar` |
| (acervo) | — | `/acervo` |

## Fluxo de uma cena

```
autor ─► produtora (entrevista: skill pixel-cena, seção 1)
            │
            ▼
      diretor-de-cena ── planos, ritmo, câmera, lista do que falta → roteiro
            │
            ├──► desenhista   (personagens/retratos que faltam)   ┐
            ├──► cenografo    (camadas do cenário, tiles)         ├ em paralelo
            └──► sonoplasta   (efeitos, trilha, voz — opcional)   ┘
            │
            ▼
         animador ── animações dos sprites + ações/tempos no roteiro
            │
            ▼
      revisor-visual ── storyboard, quadros, lint → problemas com coordenadas
            │        (volta ao responsável; máx. 3 voltas)
            ▼
         render ── python -m pixelforge cena … (+ som mix) → entrega
```

Regras: cada agente só mexe nos arquivos do seu briefing; dois agentes nunca editam
o mesmo arquivo (o roteiro é do diretor; o animador só mexe em `acoes` e nas specs dos
sprites); a produtora mostra ao autor **uma** versão por vez.

## Briefing (produtora → agente)

Um parágrafo com: o que fazer, arquivos de entrada (fichas, modelo, roteiro),
arquivos que pode criar/editar, decisões já tomadas na entrevista (tamanho, paleta,
resolução, clima, duração) e o critério de pronto.

## Retorno (agente → produtora)

Todo agente termina com exatamente este bloco (em português):

```
STATUS: pronto | parcial | bloqueado
ARQUIVOS:
- art/cenas/chegada/chegada.json — roteiro (criado)
- out/chegada/chegada_storyboard.png — storyboard (gerado)
RESUMO:
2–5 linhas: o que foi feito e as decisões tomadas.
PROBLEMAS:
- [grave] plano 3, t=7.2s, (212, 140): ator flutua 3 px acima do chão → cenografo/animador
- [aviso] lint: art/x.json (14, 9) pixel órfão
- [pergunta] a cicatriz fica na bochecha esquerda ou direita?
(ou "nenhum")
```

- `STATUS`: `pronto` = critério de pronto atingido e preview revisado; `parcial` = fez
  parte (diga o que falta); `bloqueado` = não dá para seguir sem resposta/arquivo.
- `ARQUIVOS`: caminhos relativos à raiz, um por linha, com papel e (criado/editado/gerado).
- `PROBLEMAS`: severidade (`grave`, `aviso`, `pergunta`), onde (arquivo, quadro/plano,
  instante, coordenada `(x, y)` em pixels da arte ou pixel lógico da cena) e, quando
  couber, `→ agente` responsável pela correção.

## Ciclo do crítico (melhoria contínua)

Toda arte de entrega passa pelo `critico-de-arte`: quem cria (desenhista, cenógrafo,
animador ou a via de IA) entrega a versão N → crítico dá NOTA (0,4 × técnica de
`estilo comparar` + 0,6 × rubrica visual) e melhorias com coordenadas → quem cria aplica →
volta N+1. Aprova só com **NOTA ≥ 95 e nenhum critério < 8**. Máximo de 6 voltas; sem
aprovação, o autor recebe a melhor versão + a última crítica + o que falta. Críticas em
`out/criticas/<arte>-v<N>.md`; evolução das notas em `out/criticas/<arte>-evolucao.md`.
O `revisor-visual` é o checklist rápido entre voltas; o `critico-de-arte`, a nota final.
Antes de criar, leia a análise das referências do mesmo tipo (`docs/estilo/analises/<n>.md`)
e siga as receitas de `docs/estilo/estilo-pixelforge.md`: elas são exemplos de criação.
