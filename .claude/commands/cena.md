---
description: Dirige uma cena em pixel art — momento → planos → roteiro → storyboard → revisão → vídeo
argument-hint: <o momento — ex.: "a Ana chega atrasada e o mestre a repreende">
---

Momento pedido: $ARGUMENTS

Você é a produtora; siga a skill `pixel-cena` (`.claude/skills/pixel-cena/SKILL.md`) e a
equipe de `docs/agentes.md`.

1. **Entrevista** (seção 1) com `AskUserQuestion`: momento, duração, clima, resolução/
   saída, som, fonte — só o que faltar. Se houver fonte (capítulo, ficha), leia antes.
2. Agente `diretor-de-cena`: decupagem, inventário (o que existe/falta) e primeira versão
   do roteiro. Mostre a decupagem ao autor e confirme antes de produzir o que falta.
3. Em paralelo (uma chamada com vários agentes), só o que faltar, com briefings que não
   se cruzam: `desenhista` (personagens), `cenografo` (cenário), `sonoplasta` (som, se
   pedido; IA local só com autorização do autor).
4. `animador`: animações dos sprites e `acoes` no roteiro.
5. `revisor-visual` sobre o roteiro (storyboard + quadros); graves voltam ao responsável
   (máx. 3 voltas). Abra você mesmo o storyboard com Read e mostre ao autor.
6. Com o autor de acordo: `python -m pixelforge cena <roteiro>` (e `som mix` se houver
   som), `acervo indexar`, entregue os caminhos (roteiro, storyboard, GIF, MP4).

Cada agente devolve STATUS / ARQUIVOS / RESUMO / PROBLEMAS; `[pergunta]` → pergunte ao
autor. Uma versão por vez.
