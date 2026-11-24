# Crítica — martim-retrato (v4) — volta 4

Arte: `out/ia/refino/martim-retrato-v4/martim-retrato-v4.json` (96x128, tipo retrato). É a r3-1 com retoque em código.
Folha: `out/estilo/comparar/martim-retrato-v4_comparar.png`
Refs mais próximas (técnica): 19, 14, 9. Refs guia: 21, 11, 10.

## Nota técnica: 85,1 (v3: 97,1)
Fora da faixa:
- tamanho médio dos blocos: 19,8 px (máximo 9,6; nota 0,43)
- pixels órfãos: 0,024 (mínimo 0,070; nota 0,68)
- densidade de detalhe: 0,36 (mínimo 0,42; nota 0,83)
- cores efetivas: 15 (nota 0,81)
- contraste de valor: 0,456 (mínimo 0,47)
- dithering: 0,0005

A queda é o efeito esperado de duas grandes áreas chapadas, o fundo liso (5039 px) e o corpo do moletom em 1 tom (#6a6873, 3441 px), sem dobras nem textura. As dobras (melhoria 2) devolvem densidade, órfãos e blocos menores.

## O que melhorou desde a v3
A silhueta agora lê contra o fundo quente. Os cordões estão presentes, o forro laranja dos dois lados está coerente, a esclera branca saiu e o laranja ficou como destaque único.

## Rubrica visual
| critério | peso | nota | observação |
|---|---|---|---|
| silhueta e leitura | 10 | 7 | figura destacada; ombro esquerdo em escada irregular (x 11–22, y 85–127) |
| proporção e pose | 10 | 6 | frontal, centrada, cabeça levemente baixa; pescoço em V longo |
| rosto (discreto, sem olho de anime) | 10 | 6 | **olhos leem FECHADOS**: pálpebra #82565e de 6–7 px (x 34–40 e 52–57, y 39) sobre um traço de 3 px; moldura clara #d3bcb5 em volta; boca em "bico" 5×5 (x 44–48, y 55–59) |
| sombreamento em blocos | 15 | 6 | brilho oleoso da testa (x 51–57, y 21–26) e da bochecha (x 57–61, y 44–48) ainda lá; moletom = 1 tom chapado + borrões marrons |
| paleta contida + 1 destaque, sombra fria/luz quente | 10 | 7 | fundo quente, moletom cinza, laranja único ✓; sobra #716f75 no topo do capuz (x 22–35 e 58–78, y 56–59), tom diferente do corpo |
| contorno seletivo | 5 | 6 | queixo e cabelo bem; ombros sem contorno contínuo |
| luz e rim light | 10 | 5 | sem direção definida, sem rim |
| materiais e dobras | 10 | 6 | cordões e forro ✓; corpo sem dobras, borrões #4c3f42/#433133 aleatórios |
| composição e enquadramento | 10 | 6 | busto frontal centralizado |
| "não parece amador" | 10 | 6 | o rosto de olho fechado e o moletom chapado ainda denunciam |

**Rubrica: 61,0**

## NOTA FINAL: 0,4 × 85,1 + 0,6 × 61,0 = **70,6**

## Veredito: REFAZER

A rubrica subiu (57,0 → 61,0), mas a nota técnica caiu (97,1 → 85,1).

Contradições com o briefing que ainda restam: cabelo liso e penteado (não crespo na máquina), pose frontal e expressão de olho fechado.

## Melhorias (da que mais sobe a nota para a que menos)
1. **Abrir os olhos.** A pálpebra comprida em cima de um traço curto lê como olho fechado (sonolento). Com o traço em (37–39,40) e (53–55,40):
   - (a) Encurte a pálpebra #82565e de y 39 para os mesmos 3 px do traço, (37–39,39) e (53–55,39), e devolva o resto a #c8a498.
   - (b) Faça o olho com 2 px de altura no centro: (38,41) e (54,41) em #190e0f.
   - (c) Apague a moldura clara #d3bcb5 em (35,40), (40,40–42), (41,41), (50–55,42), (58,40) e (59,36–37) para #c8a498.
   - Ref 21: o olho lê aberto porque é um bloco escuro sob a sombra da sobrancelha, sem pálpebra visível.
2. **Dobras no moletom (sobe nota técnica e materiais).** No corpo #6a6873, desenhe:
   - 2 dobras diagonais de 2 tons (#4d4b58 sombra, #8d8a92 luz do lado de cima), uma de (26,82) a (38,122) e outra de (70,82) a (58,122);
   - 1 dobra por manga, em (16–20,95–120) e (80–86,95–120);
   - sombra projetada do colar sob a gola, faixa de 2 px #4d4b58 em y 78–79, x 24–72.
   - Remova os borrões #4c3f42/#433133/#605457 soltos em y 80–127 que não fizerem parte das dobras. Receita 5.1 §6.
3. **Tirar o brilho oleoso** (pedido na v3, não feito). Testa #e1d5d4/#d3bcb5 em (51–57,21–26) e bochecha em (57–61,44–48) passam para #c8a498. Se quiser luz, use 1 bloco largo #c8a498 → #d3bcb5 de 4×3 px sem núcleo branco. Ref 11.
4. **Boca menor.** A boca em bico (44–48,55–59) vira uma linha de 3 px #82565e em (45–47,57) mais 2 px #a16e6e em (45–46,58); o resto volta a #c8a498/#bc8e85. Receita 5.1 §5: boca 2 px.
5. **Unificar o capuz.** Os 83 px restantes de #716f75 (topo do capuz, x 22–35 e 58–78, y 56–59) viram a luz do capuz #8d8a92: é a borda externa clara pedida na receita 5.1 §6.
6. **Rim e contorno.** Escolha a luz pela direita. Rim de 1 px #d3bcb5 em 3–4 pontos: ombro direito (x 86–90, y 88–100), borda do capuz (x 70–76, y 57) e orelha direita (x 70, y 38–44). Contorno #190e0f de 1 px nos ombros onde o cinza toca o fundo; alise a escada do ombro esquerdo (x 11–22, y 85–127) em degraus regulares de 1:2.
7. **Cabelo crespo na máquina.** Na massa #392626/#28191a (y 4–35), troque a borda lisa por grão de 1–2 px alternando #392626 e #4c3f42, com 4–6 pontos de 1 px fora do contorno no topo (y 3–6). Linha do cabelo reta e rente nas têmporas (x 30–33 e 63–66). Ref 21 (tufos) adaptada para cabelo rente.
8. **Pose 3/4 (img2img, força 0,35–0,45 sobre a v4 retocada).** Prompt "three-quarter view, head slightly turned, eyes open looking at viewer"; negativo "closed eyes, sleepy, pouting lips, shiny skin, front view". Depois reaplique os retoques 1–6. Refs 21 e 10.
