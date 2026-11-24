---
description: Efeitos, trilha, voz ou ambiente para uma cena (ou avulso) e mixagem no MP4
argument-hint: <o que soa — ex.: "passos e porta na cena chegada" ou "efeito de moeda">
---

Pedido do autor: $ARGUMENTS

Siga a skill `pixel-som` (`.claude/skills/pixel-som/SKILL.md`):

1. Pedido simples (um efeito chiptune por preset): rode direto
   `python -m pixelforge som efeito <preset>` e entregue o caminho + `som info`.
2. Senão, **entrevista** (seção 1) com `AskUserQuestion`: o que soa, trilha por código ou
   IA, voz, clima. IA local baixa modelos: confirme com o autor antes.
3. Delegue ao agente `sonoplasta` (briefing com o roteiro da cena, se houver, e se a IA
   está autorizada).
4. Leia o retorno; entregue os caminhos (WAVs, roteiro de áudio, MP4 com som) e peça
   que o autor ouça e diga o que ajustar.
