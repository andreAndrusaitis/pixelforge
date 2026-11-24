---
description: Cria ou ajusta um cenário (camadas com parallax para cena, tileset, mapa)
argument-hint: <lugar, clima e uso — ex.: "floresta à noite para panorâmica">
---

Pedido do autor: $ARGUMENTS

Siga a skill `pixel-cenario` (`.claude/skills/pixel-cenario/SKILL.md`):

1. Procure no acervo o que já existe (`python -m pixelforge acervo listar --tipo cenario`,
   `acervo buscar "<palavras>"`).
2. **Entrevista** (seção 1) com `AskUserQuestion`: uso, lugar/clima, resolução, movimento
   de câmera, paleta — só o que faltar.
3. Delegue ao agente `cenografo` com o briefing (tamanho do mundo, pasta, linha do chão
   desejada, critério de pronto).
4. Leia o retorno; `[pergunta]` → pergunte ao autor e devolva ao agente.
5. Revisão com o `revisor-visual` (storyboard de teste + previews das camadas).
6. Abra o storyboard de teste (`out/<teste>/<teste>_storyboard.png`) com Read, mostre ao
   autor **uma** versão com os caminhos e pergunte o que ajustar.
