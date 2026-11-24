# Crítica — geraldo-corpo (v5) — volta 5

Arte: `out/ia/refino/geraldo-corpo-v5/geraldo-corpo-v5.json` (104x152, tipo personagem; v4 + retoque em código; cabeça + chapéu escalados 1,2× NEAREST)
Folha de comparação: `out/estilo/comparar/geraldo-corpo-v5_comparar.png`
Referências mais próximas (métrica): 1, 11, 3 · guias da receita 5.2: 14, 1, 22
Críticas anteriores: v1 69,5 · v2 73,5 · v3 75,2 · v4 80,9

## Nota técnica: 95.0 (v4: 95.1)

Proporção 7,1 cabeças, como pede a receita 5.2 (a faixa genérica das refs não se aplica). Altura 142 px (ok pela receita). Espaço negativo 0,667. Dithering irrelevante.

## O que melhorou desde a v4
Proporção certa. O jeans agora tem coluna de luz e de sombra por perna (x 34–36 e 49–51) e lê como volume cilíndrico. Mancha ferrugem removida, cinza do antebraço removido, copa em 3 tons de feltro, rim na aba e no antebraço esquerdo, sombra da aba no rosto.

## Rubrica visual

| Critério | Peso | Nota | Observação |
|---|---|---|---|
| Silhueta e leitura | 10 | 8 | Leitura clara de longe. |
| Proporção e pose | 10 | 8 | 7,1 cabeças, ombros e base largos. A copa termina num "bico" estreito (x 46–51, y 0–3), que não é forma de fedora. |
| Rosto | 10 | 6 | O 1,2× NEAREST **duplicou linhas e colunas** (linhas 0/1, 6/7, 12/13, 17/18, 23/24; colunas 42/43, 48/49, 54/55, 60/61). A cabeça ficou com pixel de escala mista, diferente do corpo. Os olhos viraram blocos 2–3×2 (45–48, 12–14) e (52–54, 12–13), e o rosto lê como máscara. Cinza #67656c em (54–55, 22) volta a sugerir barba. |
| Sombreamento em blocos | 15 | 7 | Jeans bem melhor. O bloco #8a7262 na camisa (55–62, 44–56) é um retângulo chapado que lê como bolso ou mancha, não como dobra. Botinas ainda em xadrez #a14a4c/#70383c (x 36–44 e 52–57, y 118–135). |
| Paleta contida + destaque | 10 | 8 | Rampas separadas e um destaque só. Ok. |
| Contorno seletivo | 5 | 7 | Ok. Do lado escuro, a borda da aba tem o mesmo peso do contorno do corpo. |
| Luz e rim light | 10 | 7 | Rim coerente na esquerda; luz de cima sem rim no topo da copa. |
| Materiais e dobras | 10 | 7 | A linha de botões em x 52 ainda quase não aparece em 1×. O feltro lê. O bloco da camisa parece remendo. |
| Composição e pose no quadro | 10 | 7 | **O chapéu encosta na borda de cima (y 0)**, com 0 px de margem contra 10 px embaixo. Sobra uma tira fina na sombra de chão (x 73–83, y 134–135). |
| Não parece amador | 10 | 7 | A escala mista na cabeça é o tipo de erro que um pixel artist nota na hora. O resto já fica bem ao lado da ref 1. |

**Rubrica** = 720 / 10 = **72,0**

## NOTA FINAL = 0,4 × 95,0 + 0,6 × 72,0 = **81,2** (v4 80,9)

## Veredito: **REFAZER**

A próxima é a volta 6, a última: priorize os itens 1–4.

## Melhorias (da que mais sobe a nota para a que menos)

1. **Refazer a escala da cabeça sem pixel duplicado (rosto 6→8, não amador)**: não usar fator 1,2× NEAREST, porque gera linhas e colunas repetidas. Duas saídas:
   (a) Remover as linhas duplicadas 1, 7, 13, 18, 24 e as colunas 43, 49, 55, 61, voltando ao tamanho original, e ganhar altura de cabeça **redesenhando** 2 px de copa e 1 px de queixo.
   (b) Escalar a cabeça da imagem *bruta* 1,2× com LANCZOS e re-pixelizar só essa região com a paleta atual.
   Em seguida, olhos como traço 2×1 #51242e em (45–46, 13) e (52–53, 13), sombra da aba só em y 10–11, nariz e maçã claros em (48–49, 16–17), e o cinza em (54–55, 22) trocado por #b97561. Ref 14.
2. **Descer a figura e achatar a copa (composição 7→8, proporção)**: deslocar tudo **+4 px em y** (pés em y≈145; sobram 6 px embaixo) para a copa sair da borda. Apagar o bico (46–51, 0–3). Fazer a copa com topo reto de 12–13 px de largura em y 4 e um vinco de 1 px #51242e no centro (x 51, y 4–5), no formato fedora. Receita 5.2 §2, ref 14.
3. **Bloco da camisa vira dobra (sombreamento 7→8, materiais)**: transformar o retângulo (55–62, 44–56) num triângulo de sombra com a ponta no ombro direito, aproximadamente (58,40) → (62,56) → (55,56). Meio-tom #b8a084 de 1 px na borda superior esquerda, avesso #5a4549 em 1 px no limite inferior, curvado com a barriga em y 55–57. Ref 1 (dobras em 3 massas).
4. **Botinas limpas (sombreamento)**: moda 3x3 só na máscara das botinas (x 25–58, y 118–141) e reclassificar em 3 tons: luz #a14a4c em 2 px do lado esquerdo do cano, meio #70383c, sombra #361526 no lado direito. Cadarço como 3 traços de 1 px #a07367 em y 122, 126 e 130, no centro de cada cano. Biqueira com brilho de 1–2 px. Receita 5.2 §6.
5. **Botões legíveis (materiais)**: trocar a linha de x 52 (y 33–56) por #5a4549 e pôr botões #f0d2b0 de 1 px em y 37, 42, 47 e 52, cada um com 1 px #5a4549 embaixo. Hoje o contraste é baixo demais para ler em 1×.
6. **Sombra de chão (composição)**: apagar a tira (73–83, 134–135) e deixar a sombra como uma elipse achatada de x 26–68, y 137–140 (depois do deslocamento do item 2, y 141–144).
7. **Rim no topo da copa (luz)**: 1 px #f0d2b0 na borda superior esquerda da copa (x 45–50, y 4 após o item 2), coerente com a luz de cima e da esquerda. Ref 22.
