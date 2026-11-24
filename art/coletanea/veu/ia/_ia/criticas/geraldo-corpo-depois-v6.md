# Crítica — geraldo-corpo (v6) — volta 6 (final)

Arte: `out/ia/refino/geraldo-corpo-v6/geraldo-corpo-v6.json` (104x152, tipo personagem; v5 sem a escala 1,2× da cabeça, +4 px em y, dobra triangular, botões, botinas em 3 tons, sombra aparada, rim na copa)
Folha de comparação: `out/estilo/comparar/geraldo-corpo-v6_comparar.png`
Referências mais próximas (métrica): 1, 3, 11 · guias da receita 5.2: 14, 1, 22
Críticas anteriores: v1 69,5 · v2 73,5 · v3 75,2 · v4 80,9 · v5 81,2

## Nota técnica: 94.9

- **proporção 8,56 cabeças** de novo: desfazer a escala trouxe de volta a cabeça pequena (rosto ≈ 15×14 px, x 44–59, y 16–30). A receita 5.2 pede ~7, então aqui a métrica e a receita concordam que está errado.
- espaço negativo 0,689 e dithering 0,0005, os dois de peso baixo.

## O que melhorou desde a v5
- Cabeça de volta à escala de pixel do corpo, sem linhas nem colunas duplicadas.
- Margens boas: 9 px em cima, 6 px embaixo.
- Copa em formato de fedora, com rim #f0d2b0 no topo (47–51, 9).
- Linha de botões #5a4549 em x 52 (y 36–60), com botões em y 41, 46, 51 e 56.
- Botinas sem o xadrez rosa.

## Rubrica visual

| Critério | Peso | Nota | Observação |
|---|---|---|---|
| Silhueta e leitura | 10 | 8 | Lê "Seu Geraldo" de longe. |
| Proporção e pose | 10 | 7 | Cabeça pequena (8,6 cabeças) e pernas da calça longas e balofas (y 67–122). |
| Rosto | 10 | 7 | Olhos pequenos (47–49, 19) e (52–53, 19), aba fazendo sombra. Ainda há cinza solto em (55–57, 17–18) e (55–56, 21–22) e pontos de 1 px que sujam a pele. |
| Sombreamento em blocos | 15 | 7 | O jeans está bom. A dobra (55–62, 42–55) ainda é uma mancha marrom com pixels soltos, não um triângulo limpo. As botinas viraram 3 blocos chapados, sem volume no pé. |
| Paleta contida + destaque | 10 | 8 | Ok, com destaque único na fita. |
| Contorno seletivo | 5 | 7 | Ok. |
| Luz e rim light | 10 | 7 | O rim está coerente na copa, na aba e no lado esquerdo. Falta a luz na biqueira. |
| Materiais e dobras | 10 | 7 | **As botinas se fundem num único bloco na base**: em y 139–144, o vão x 44–52 foi pintado com #a14a4c/#70383c (provavelmente a sombra de chão aparada virou bota no filtro de moda), e os dois pés viram uma "panqueca" vermelha. Ainda há uma tira cinza #67656c em (58–60, 138–145). Os botões quase não aparecem em 1×: a linha escura contínua engole o pixel escuro de baixo. |
| Composição e pose no quadro | 10 | 8 | Centrado, margens ok. |
| Não parece amador | 10 | 7 | De longe já se sustenta ao lado da ref 1. De perto, os pés fundidos e a pele suja denunciam. |

**Rubrica** = 730 / 10 = **73,0**

## NOTA FINAL = 0,4 × 94,9 + 0,6 × 73,0 = **81,8**

## Veredito: **REFAZER** (volta 6 sem aprovação: encerra o ciclo)

## O que falta (resumo para o autor)

O personagem já está certo no conceito: chapéu de feltro com fita vermelha como destaque único, camisa bege de botão com manga dobrada, cinto, jeans com volume, botinas, barbeado, massa larga e paleta com rampas separadas. Para chegar a 95, faltam três coisas de construção e uma de acabamento:

1. **Cabeça maior sem escala mista.** É a causa da proporção (8,6 → ~7 cabeças). O caminho é gerar a cabeça já grande, via img2img da região ou nova seed com "large head", e re-pixelizar na escala do corpo. Escalar o pixel art pronto não serve: com 1,2× NEAREST duplica linhas e colunas, e com 2× fica com pixel de outra escala. Alvo: rosto ≈ 17×16 px, aba ≈ 27 px. Receita 5.2 §1, ref 14.
2. **Pés separados e com volume.** Devolva o vão entre as botinas a transparente (x 44–52, y 139–144) e apague a tira cinza (58–60, 138–145). Cada pé precisa de sola #361526 de 1 px, um pouco mais larga que o cano, e brilho #a14a4c de 1–2 px na biqueira, em (27,141) e (53,143). Aplique o filtro de moda só depois de recortar a sombra de chão. Receita 5.2 §6.
3. **Dobras da camisa em formas limpas.** A dobra triangular (55–62, 42–55) deve ser **uma** forma chapada #8a7262 com borda #5a4549, sem pixels soltos. As linhas vinho finas do peito viram 2 diagonais de 2–3 px. Ref 1.
4. **Acabamento da pele e dos botões.** Troque o cinza solto no rosto, em (55–57, 17–18) e (55–56, 21–22), por #8a4d48/#b97561, e limpe os órfãos de 1 px da pele. Nos botões, a linha deve ser #8a7262 (mais clara que o pixel escuro de baixo), com botões #f0d2b0 e #5a4549 só embaixo de cada um.

Com 1 e 2 feitos, proporção, materiais e "não parece amador" sobem a 8–9, e a nota fica na faixa de 86–88. Para chegar a 95, todos os critérios precisam ficar em ≥ 8,5, sobretudo o sombreamento (peso 15).
