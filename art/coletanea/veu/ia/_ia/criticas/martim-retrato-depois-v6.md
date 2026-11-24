# Crítica — martim-retrato (v6) — volta 6 (final)

Arte: `out/ia/refino/martim-retrato-v6/martim-retrato-v6.json` (96x128, tipo retrato). É a v5 com os retoques 1–5 e 8.
Folha: `out/estilo/comparar/martim-retrato-v6_comparar.png`
Refs mais próximas (técnica): 9, 19, 14. Refs guia: 21, 11, 10.

## Nota técnica: 84,9 (v5: 88,0)
Fora da faixa:
- tamanho médio dos blocos: 21,9 px (máximo 9,6; nota 0,38)
- pixels órfãos: 0,024 (nota 0,68)
- densidade de detalhe: 0,32 (mínimo 0,42; nota 0,72)
- contraste de valor: 0,456 (nota 0,95)
- cores efetivas: 17 (nota 0,96)
- dithering: 0,0007 (nota 0,97)

Limpar os borrões aumentou o chapado: o moletom tem 3716 px de #6a6873. A metade direita do tronco (x 66–92, y 84–127) está em 1 tom só, e por isso blocos e densidade pioraram.

## O que melhorou desde a v5
- As faixas retas sumiram.
- As dobras do ombro afinam (3 → 1 px), com luz em cima.
- O ombro esquerdo ganhou contorno #190e0f.
- O rim da orelha agora é curto.
- Os pontos claros do rosto foram quase todos limpos.

## Rubrica visual
| critério | peso | nota | observação |
|---|---|---|---|
| silhueta e leitura | 10 | 7 | figura destacada; contorno do ombro esquerdo serrilhado (x 8–13, y 84–127, degraus irregulares) |
| proporção e pose | 10 | 6 | frontal, simétrica, de foto 3x4; pescoço em V longo |
| rosto (discreto, sem olho de anime) | 10 | 7 | olhos e boca discretos ✓; 1 px claro #e1d5d4 no nariz (49,47–48); o lado de sombra virou o rosto inteiro em #bc8e85, sem plano de luz |
| sombreamento em blocos | 15 | 6 | rosto ok; corpo em 1 tom; a dobra direita continua como coluna de 1–2 px #605457 em x 63–64, y 104–126 |
| paleta contida + 1 destaque, sombra fria/luz quente | 10 | 7 | coerente e contida |
| contorno seletivo | 5 | 7 | contorno escuro no lado da sombra e rim no lado da luz ✓ |
| luz e rim light | 10 | 6 | rim no ombro direito e na orelha ✓; volume do tronco sem lado de sombra |
| materiais e dobras | 10 | 6 | as dobras afinam ✓, mas ainda são traços sobre o chapado; sombra do colar ainda reta em y 78 (x 25–71, 47 px) |
| composição e enquadramento | 10 | 6 | busto centralizado e frontal |
| "não parece amador" | 10 | 6 | rosto aceitável; o corpo parece não terminado ao lado da ref 21 |

**Rubrica: 63,5**

## NOTA FINAL: 0,4 × 84,9 + 0,6 × 63,5 = **72,1**

## Veredito: REFAZER (volta 6, fim do ciclo, sem aprovação)

Evolução: 68,8 → 73,6 → 73,0 → 70,6 → 73,0 → 72,1. Desde a volta 2 a nota oscila em ~72–73. O retoque pontual sobre esta base não chega a 95. A base (r3-1) tem pose frontal de documento, cabelo liso penteado e um moletom sem volume, e nada disso se conserta pixel a pixel.

### O que falta (resumo para o autor)
1. **Base nova em 3/4.** Gere de novo, não refine a r3-1.
   - Prompt: "three-quarter view, head slightly turned, 12-year-old thin boy, very short kinky coily buzz cut, thick eyebrows, closed mouth, gray hoodie with hood down, orange hood lining, two drawstrings, flat cel shading, light from the right".
   - Negativo: "front view, symmetrical, passport photo, slicked hair, eye whites, shiny skin, stripes".
   - Escolha a seed pela pose e pela silhueta, não pelo rosto.
   - Refs 21 e 10.
2. **Volume do moletom em blocos.** Lado da sombra do tronco (esquerda, x 12–30) e axila direita em blocos #4d4b58 de 4+ px; dobras como formas de 3–4 px que afinam, não traços; sombra do colar curva, 2–3 px no centro (40–56,78–80), afinando até as pontas, e não a linha reta de y 78. É o que corrige a nota técnica (blocos 21,9 → <10, densidade e órfãos).
3. **Planos do rosto.** Luz pela direita: plano iluminado #c8a498 na metade direita da testa, da maçã e do queixo (x 48–62); sombra #bc8e85 só na metade esquerda (x 30–44), com borda limpa. Apague o px #e1d5d4 do nariz (49,47).
4. **Cabelo crespo na máquina.** Borda em grão de 1–2 px #392626/#4c3f42, 4–6 pontos fora do contorno, têmporas rentes (receita 5.1 §4 adaptada).
5. **Manter o que funcionou.** Olho em traço de 3×1 px com pupila abaixo, boca de 3 px, fundo liso e quente #b8aa98, moletom cinza com forro laranja como destaque único, cordões de 1 px com ponta laranja, rim #d3bcb5 do lado da luz e contorno #190e0f do lado da sombra.

## Melhorias pontuais nesta v6 (se ainda quiser retocar)
1. Sombra do lado esquerdo do tronco: bloco #4d4b58 em x 12–26, y 92–127, com borda interna em degraus.
2. Axila e lateral direita: bloco #4d4b58 em x 78–86, y 96–112.
3. Troque a linha reta de y 78 (x 25–71) por uma curva: 1 px nas pontas e 3 px no centro (x 40–56).
4. A coluna #605457 em x 63–64, y 104–126 vira uma dobra em forma: 2–3 px até y 112 e 1 px até y 120; apague o resto.
5. Corrija o serrilhado do contorno esquerdo (x 8–13, y 84–127) em degraus regulares.
6. Apague o px #e1d5d4 em (49,47) e devolva #c8a498 à metade direita do rosto.
