---
description: Cria ou ajusta um personagem recorrente (folha: retrato + sprite + animações + paleta)
argument-hint: <descrição, ficha ou modelo .personagem.json>
---

Pedido do autor: $ARGUMENTS

Siga a skill `pixel-personagem` (`.claude/skills/pixel-personagem/SKILL.md`):

1. Se o pedido citar ficha, foto ou modelo existente, leia-o primeiro e procure no
   acervo (`python -m pixelforge acervo buscar "<nome>"`) se o personagem já existe.
2. **Entrevista** (seção 1) com `AskUserQuestion`, só o que faltar.
3. Delegue ao agente `desenhista` com um briefing completo (decisões da entrevista,
   arquivos de entrada e saída, critério de pronto). Se o pedido incluir animar um
   sprite desenhado à mão, depois chame o `animador`.
4. Leia o retorno (STATUS / ARQUIVOS / RESUMO / PROBLEMAS); `[pergunta]` → pergunte ao
   autor e devolva ao agente.
5. Revisão: agente `revisor-visual` sobre o modelo (rigor "entrega"); graves voltam ao
   desenhista (máx. 3 voltas).
6. Abra você mesmo `out/<nome>/<nome>_preview.png` com Read, mostre **uma** versão ao
   autor com os caminhos gerados e pergunte o que ajustar.
