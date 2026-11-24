---
description: Revisão visual com coordenadas de uma arte, personagem, cenário ou cena (não corrige)
argument-hint: <arquivo — arte .json/.py, modelo .personagem.json ou roteiro de cena>
---

Alvo: $ARGUMENTS

Siga a skill `pixel-revisao` (`.claude/skills/pixel-revisao/SKILL.md`):

1. Sem alvo: procure `pedidos/*.md` com `estado: aberto` e revise o mais antigo; sem
   pedidos, pergunte ao autor o que revisar.
2. Se faltar a referência (folha do personagem, foto, ficha) ou o rigor, pergunte com
   `AskUserQuestion` (só o que faltar).
3. Delegue ao agente `revisor-visual` (ele só lê e gera material em `out/`).
4. Abra você mesmo as imagens citadas (preview/storyboard) com Read para conferir, e
   entregue ao autor o veredito e a lista de problemas com coordenadas e o responsável.
5. Pergunte se deve aplicar as correções (pelas skills `pixel-art`, `pixel-personagem`,
   `pixel-cenario` ou `pixel-cena`).
