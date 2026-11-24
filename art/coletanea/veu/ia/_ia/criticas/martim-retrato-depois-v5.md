# Crítica — martim-retrato (v5) — volta 5

Arte: `out/ia/refino/martim-retrato-v5/martim-retrato-v5.json` (96x128, tipo retrato). É a v4 com os retoques 1–6.
Folha: `out/estilo/comparar/martim-retrato-v5_comparar.png`
Refs mais próximas (técnica): 19, 14, 9. Refs guia: 21, 11, 10.

## Nota técnica: 88,0 (v4: 85,1)
Fora da faixa:
- tamanho médio dos blocos: 18,3 px (máximo 9,6; nota 0,47)
- pixels órfãos: 0,025 (mínimo 0,070; nota 0,68)
- densidade de detalhe: 0,40 (nota 0,92)
- contraste de valor: 0,456 (nota 0,95)
- cores efetivas: 17 (nota 0,96)
- dithering: 0,0006 (nota 0,96)

O corpo do moletom continua quase todo em 1 tom (#6a6873, 3145 px), e o fundo é liso. As duas dobras novas são linhas finas e não quebram essa área em blocos.

## O que melhorou desde a v4
- Os olhos agora leem abertos: traço em (37–39,40) e (53–55,40), com pupila em (38,41) e (54,41).
- A boca está pequena e o brilho oleoso saiu.
- O topo do capuz tem borda clara #8d8a92.
- Há rim #d3bcb5 no ombro direito (x 88–95, y 85–100) e na orelha (x 71, y 36–45).

## Rubrica visual
| critério | peso | nota | observação |
|---|---|---|---|
| silhueta e leitura | 10 | 7 | figura lê bem; ombro esquerdo em escada, sem contorno (x 10–20, y 88–127) |
| proporção e pose | 10 | 6 | frontal, simétrica, de foto 3x4; pescoço em V longo |
| rosto (discreto, sem olho de anime) | 10 | 7 | olhos discretos e abertos ✓, boca ✓; ainda restam pontos claros soltos em (56,27), (53–54,30–31), (44–45,48) e (56–57,42) |
| sombreamento em blocos | 15 | 6 | rosto ok; moletom = chapado + borrões marrons antigos ainda lá (#605457/#4c3f42/#433133 em x 10–25 e x 70–92, y 82–127) |
| paleta contida + 1 destaque, sombra fria/luz quente | 10 | 7 | coerente: fundo quente, cinza frio, laranja único |
| contorno seletivo | 5 | 6 | contorno no queixo e no cabelo; ombro esquerdo aberto e serrilhado |
| luz e rim light | 10 | 6 | rim à direita ✓, mas o rosto ainda tem luz frontal, sem lado de sombra |
| materiais e dobras | 10 | 6 | **as "dobras" são 2 faixas retas de 3 px** (#8d8a92 + 2×#4d4b58) de (26,82) a (39,121) e de (72,82) a (57,121): largura constante, paralelas, em V, leem como **friso de agasalho / alça**, não tecido; a sombra do colar em y 79 é **uma régua de 1 px** de x 23 a 75 |
| composição e enquadramento | 10 | 6 | busto frontal centralizado |
| "não parece amador" | 10 | 6 | as linhas mecânicas no moletom e a pose de documento ainda denunciam |

**Rubrica: 63,0**

## NOTA FINAL: 0,4 × 88,0 + 0,6 × 63,0 = **73,0**

## Veredito: REFAZER

Evolução: 68,8 → 73,6 → 73,0 → 70,6 → 73,0. O retoque pontual estabilizou em ~73. Para passar de 80 falta o que não dá para remendar: pose 3/4, cabelo crespo e um moletom com volume, não linhas sobre um chapado. Na volta 6, pela regra, sai REFAZER se não aprovar.

## Melhorias (da que mais sobe a nota para a que menos)
1. **Trocar as faixas por dobras de verdade.** Apague as duas faixas retas e redesenhe cada dobra como forma, não como linha:
   - Sombra #4d4b58: largura de 3–4 px perto do ombro, afinando para 1 px na ponta, com 1–2 quebras (degraus) no caminho. Esquerda: de (22–25,84) a (34,112). Direita: de (74–77,84) a (64,112).
   - Luz #8d8a92: 1–2 px **só do lado de cima/da luz** de cada dobra, e só no terço superior.
   - Duas áreas de sombra em bloco (não linha): lateral esquerda do tronco (x 12–22, y 90–127) e axila direita (x 76–84, y 96–110), em #4d4b58.
   - Isso quebra o chapado e devolve blocos, órfãos e densidade.
   - Receita 5.1 §6; ref 21 (dobras em bloco ombro → cintura).
2. **Sombra do colar em forma, não em régua.** Troque a linha de y 79 (x 23–75) por uma sombra projetada que segue a curva do capuz: 2–3 px de altura no centro, em (40–56,78–80), afinando para 1 px nas pontas (x 26 e x 70), em #4d4b58.
3. **Limpar os borrões antigos.** Os #605457/#4c3f42/#433133 soltos em x 10–25 e x 70–92, y 82–127 viram #6a6873, ou são absorvidos pelas áreas de sombra da melhoria 1. Mantenha só o que formar bloco de 4+ px.
4. **Contorno e ombro esquerdo.** Contorno de 1 px #190e0f no ombro e no braço esquerdos (x 10–20, y 86–127), em degraus regulares 1:2. Esse é o lado da sombra, sem rim.
5. **Lado de sombra no rosto.** Com a luz pela direita, o lado esquerdo do rosto (x 30–40, y 36–58) desce um tom: #c8a498 → #bc8e85, em bloco com borda limpa, seguindo a maçã e o queixo. Apague os pontos claros soltos em (56,27), (53–54,30–31), (44–45,48) e (56–57,42). Ref 21.
6. **Cabelo crespo na máquina.** Ainda não foi feito; receita da v4, item 7: borda em grão de 1–2 px #392626/#4c3f42, 4–6 pontos fora do contorno no topo, têmporas rentes (x 30–33 e 63–66).
7. **Pose 3/4 (o que mais falta para "não parecer foto de documento").** Img2img com força 0,35–0,45 sobre a v5.
   - Prompt: "three-quarter view, head slightly turned to the right, eyes open, short kinky buzz cut, gray hoodie with orange hood lining, drawstrings".
   - Negativo: "front view, symmetrical, straight lines, stripes, piping, closed eyes".
   - Depois reaplique os retoques de olho, boca e capuz.
   - Refs 21 e 10.
8. **Rim só na borda.** Hoje o rim da orelha (x 71, y 36–45) é uma coluna contínua de 10 px. Deixe 3–4 px na parte de cima da orelha, (71,37–40), para não parecer contorno claro.
