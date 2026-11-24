# Crítica — geraldo-corpo (v4) — volta 4

Arte: `out/ia/refino/geraldo-corpo-v4/geraldo-corpo-v4.json` (104x152, tipo personagem; r3-2 + retoque em código dos itens 1–3 e 5–8 da v3; figura deslocada −8 px)
Folha de comparação: `out/estilo/comparar/geraldo-corpo-v4_comparar.png`
Referências mais próximas (métrica): 1, 3, 11 · guias da receita 5.2: 14, 1, 22
Críticas anteriores: v1 69,5 · v2 73,5 · v3 75,2

## Nota técnica: 95.1 (v3: 90.6)

Paleta recuperada: 27 cores no total, com cores efetivas, tons por rampa e níveis de valor de volta à faixa. Ainda fora:
- **proporção 8,56 cabeças** (receita ~7). A cabeça não foi aumentada: rosto ≈ 15×13 px (x 43–58, y 13–26).
- espaço negativo 0,677, por causa da sombra de chão comprida (x 25–84) e da figura estreita.
- dithering 0,0007, irrelevante.

## O que melhorou desde a v3
- Pele (#d9a184…#8a4d48) e camisa (#d8c3a5…#5a4549) agora são rampas distintas.
- Fita vermelha #a8403a (x 46–59, y 10–11, 28 px ≈ 0,7%) é o destaque certo, lido de longe.
- Barba removida.
- O vão entre as botinas ficou transparente (x 45–52, y 118–134).
- Rim quente #f0d2b0 no lado esquerdo da camisa (x 33–36, y 32–58).
- Figura centrada (corpo em x 31–77).

## Rubrica visual

| Critério | Peso | Nota | Observação |
|---|---|---|---|
| Silhueta e leitura | 10 | 8 | Lê "Seu Geraldo" de longe: chapéu com fita, tronco largo, braços soltos e pernas separadas. |
| Proporção e pose | 10 | 7 | Cabeça pequena para o corpo (8,6 cabeças). Pernas da calça longas e balofas (y 63–118). |
| Rosto | 10 | 7 | Barbeado. Ainda todo claro, sem sombra de aba no terço de cima, e salpicado de pontos rosa #cb7071 de 1 px (x 44–56, y 15–24). Sobra cinza #878690 sob a aba em (53–56, 14). |
| Sombreamento em blocos | 15 | 6 | Na camisa, uma cunha escura de pixels soltos em x 54–62, y 44–56 e dobras ainda em linhas finas. Jeans manchado do joelho ao tornozelo (x 32–63, y 85–118), sem coluna de luz (item não feito). |
| Paleta contida + destaque | 10 | 8 | Rampas separadas, um destaque, sombra fria no jeans e luz quente no rim. Copa do chapéu ainda clara e manchada (#e5c2a4/#835f5a em x 46–58, y 5–9), pouco "feltro marrom". |
| Contorno seletivo | 5 | 7 | Rim quente na esquerda e escuro na direita. Ainda há linha vinho na aba esquerda (x 40–45, y 12–13). |
| Luz e rim light | 10 | 7 | Direção coerente e rim do lado certo. O rim para no ombro: falta no braço (x 31, y 58–74) e na aba (y 11). |
| Materiais e dobras | 10 | 7 | Feltro, camisa, cinto e botina leem. A linha de botões (x 52–53, y 34–55) quase não aparece. Mancha ferrugem no jeans em (51–52, 94–98) e cinza no antebraço direito em (63–65, 59–62) continuam. Salpico rosa nas botinas reduziu, mas sobra em (37–43, 125–133) e (53–56, 120–126). |
| Composição e pose no quadro | 10 | 8 | Centrado e com boa altura. A sombra de chão está bem à direita (até x 84). |
| Não parece amador | 10 | 7 | Ao lado da ref 1 já se sustenta de longe; de perto, a camisa e o jeans manchados ainda denunciam a origem. |

**Rubrica** = 715 / 10 = **71,5**

## NOTA FINAL = 0,4 × 95,1 + 0,6 × 71,5 = **80,9** (v1 69,5 · v2 73,5 · v3 75,2)

## Veredito: **REFAZER**

## Melhorias (da que mais sobe a nota para a que menos)

1. **Jeans em 3 blocos por perna (sombreamento 6→8)**: aplicar moda 3x3 **só na máscara do jeans** (x 32–63, y 64–118) e reclassificar por valor em 3 tons.
   - Luz #878690: coluna de 3 px no lado esquerdo de cada perna (x 34–36 e x 49–51).
   - Meio: #67656c.
   - Sombra: #272938, em 3 px do lado direito de cada perna (x 43–45 e x 60–62).
   - Avesso/entreperna: #201927.
   - Joelho com 1 px de luz em (36,98) e (51,98); 2 dobras horizontais de 4 px em y 110 e 114.
   - Apagar a mancha ferrugem (51–52, 94–98).
   Refs 1 e 22.
2. **Camisa: limpar a cunha e marcar os botões (sombreamento, materiais)**: a cunha de x 54–62, y 44–56 vira um bloco sólido #8a7262, com borda de 1 px #5a4549 do lado de fora. As linhas finas vinho viram 2 dobras diagonais de 2–3 px (ombro direito → cintura). Linha de botões: 1 px #8a7262 contínuo em x 52, y 33–56, com 4 botões #e6d6bc em y 37, 42, 47 e 52, mais 1 px #5a4549 embaixo de cada um. Ref 1 e receita 5.2 §4.
3. **Cabeça maior (proporção 7→8)**: este é o item que falta para tirar a métrica de proporção do vermelho.
   - Recortar cabeça + chapéu (x 39–64, y 4–27) e escalar 1,2× com NEAREST, ancorando no pescoço (y 27).
   - Reaplicar a rampa de pele e limpar os pixels duplicados.
   - Alvo: rosto ≈ 17×16 px, aba ≈ 27 px, 7–7,5 cabeças.
   - Alternativa: img2img na região da cabeça com força 0,3.
   Receita 5.2 §1.
4. **Rosto sob a aba (rosto 7→8,5)**:
   - Escurecer y 13–15 (x 44–57) para #b97561/#8a4d48 como sombra da aba, deixando claro só nariz e maçã (47–49, 18–19), com #d9a184.
   - Remover os pontos rosa #cb7071 isolados (x 44–56, y 15–24) para o tom vizinho.
   - Cinza em (53–56, 14) → #8a4d48.
   Ref 14.
5. **Copa de feltro marrom (paleta 8→9)**: remapear a copa (x 46–58, y 5–9) de #e5c2a4/#835f5a para 3 tons de feltro (#a07367 luz, #835f5a meio, #51242e vinco central de 1 px em x 52), mantendo a aba clara de 1 px em y 11–12 e a faixa escura embaixo. Ref 14 e receita 5.2 §2.
6. **Completar o rim e trocar o vinho da aba (luz, contorno)**: 1 px #f0d2b0 na borda superior da aba (x 40–47, y 11), na borda externa do antebraço esquerdo (x 31, y 58–74) e nos nós da mão esquerda (x 31–32, y 76–78). Trocar o vinho em (40–45, 12–13) pelo rim. Ref 22 e receita 5.2 §7.
7. **Restos de artefato (materiais, não amador)**:
   - cinza no antebraço direito (63–65, 59–62) → #c88a6e;
   - salpico rosa nas botinas, em (37–43, 125–133) e (53–56, 120–126) → #70383c/#51242e, deixando só o brilho da biqueira.
8. **Sombra de chão mais curta (composição)**: limitar a sombra a x 25–72, com 2 px de altura (y 138–140), sob os pés. Isso também melhora o espaço negativo.
