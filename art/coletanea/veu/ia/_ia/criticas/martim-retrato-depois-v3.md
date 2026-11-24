# Crítica — martim-retrato (r3-1) — volta 3

Arte: `out/ia/r3/martim-retrato-r3-1/martim-retrato-r3-1.json` (96x128, tipo retrato). Geração nova.
Folha: `out/estilo/comparar/martim-retrato-r3-1_comparar.png`
Refs mais próximas (técnica): 18, 20, 15. Refs guia: 21, 11, 10.

## Nota técnica: 97,1 (v2: 94,7)
Fora da faixa:
- proporção: 2,27 cabeças (nota 0,67)
- cores efetivas: 15 (mínimo 17,6; nota 0,81)
- dithering: 0,0003 (nota 0,94)
- rim light: 0,001 (nota 0,99)

## O que melhorou desde a v2
O rosto está limpo e lê como menino. Boca fechada, cabelo curto e escuro, linha do cabelo nítida, sobrancelhas mais marcadas, forro laranja como destaque único e sem ar de doente.

## Problema principal (novo)
**O corpo do moletom é exatamente a cor do fundo (#716f75)**: 8579 px, a cor nº 1 da imagem. Da gola para baixo (y 76–127) a figura só existe pelo contorno quebrado e por manchas marrons (#4c3f42/#433133/#605457). Isso derruba a silhueta, os materiais e o "não parece amador".

## Rubrica visual
| critério | peso | nota | observação |
|---|---|---|---|
| silhueta e leitura | 10 | 5 | cabeça lê bem; moletom some no fundo (mesmo #716f75) |
| proporção e pose | 10 | 6 | frontal e centrada de novo; pescoço em V longo (y 59–76); lê 13–15 anos, um pouco velho para 12 |
| rosto (discreto, sem olho de anime) | 10 | 6 | olhos com 9 px de largura e esclera branca #e1d5d4 (x 36–38 e 51–52/56–57, y 40–41), não traço; boca em laranja-batom #a94129 (x 43–50, y 55–58); nariz cinza #605457 (x 43–48, y 50–51) |
| sombreamento em blocos | 15 | 6 | rosto em blocos razoáveis, mas com brilho especular "oleoso" na testa (x 51–57, y 21–26) e na bochecha (x 57–61, y 44–48); moletom em manchas aleatórias |
| paleta contida + 1 destaque, sombra fria/luz quente | 10 | 6 | laranja como destaque ✓, mas o batom gasta o destaque; o moletom não tem rampa própria; 15 cores |
| contorno seletivo | 5 | 6 | queixo e cabelo bem contornados; contorno do moletom quebrado e com falhas (x 13–16, y 88–127) |
| luz e rim light | 10 | 5 | sem direção clara (brilho na testa à direita, sombra no forro à esquerda); sem rim |
| materiais e dobras | 10 | 5 | **cordões sumiram**; corpo sem dobras, só borrões; forro laranja bom à direita (x 64–77, y 59–75), marrom e sujo à esquerda (x 30–38, y 62–73) |
| composição e enquadramento | 10 | 6 | busto centralizado, simétrico, foto 3x4 |
| "não parece amador" | 10 | 6 | o rosto convence; o corpo parece inacabado |

**Rubrica: 57,0**

## NOTA FINAL: 0,4 × 97,1 + 0,6 × 57,0 = **73,0**

## Veredito: REFAZER

Estagnou em relação à v2 (73,6): o rosto ganhou e o corpo perdeu.

Contradições com o briefing:
- Cabelo curto, mas liso e penteado; não é crespo na máquina.
- Olho com esclera branca, contra o traço de 2–3×1 px da receita 5.1 §5.
- Cordões de 1 px ausentes (receita 5.1 §6).

## Melhorias (da que mais sobe a nota para a que menos)
1. **Separar moletom e fundo (retoque de paleta).** Duas frentes:
   - Fundo: troque #716f75 por um liso claro e quente, por ex. #b8aa98 (receita 5.1 item 3: "fundo liso claro e quente"). Isso exige recolorir só os pixels #716f75 conectados à borda (flood fill a partir de (0,0) e (95,0)).
   - Moletom: os #716f75 de dentro da figura viram uma rampa de 3 tons, #6a6873 (meio), #4d4b58 (sombra fria), #8d8a92 (luz).
   - Ref 21: figura com contraste de valor claro contra o fundo.
2. **Olhos em traço.** (35–41,40–41) e (50–59,40–41) viram traço de 3×1 px #190e0f em (37–39,40) e (54–56,40), com a pálpebra #82565e em y 39. Apague o branco #e1d5d4 para a pele #bc8e85. Ref 21 e receita 5.1 §5.
3. **Cordões e dobras.** Dois cordões de 1 px, #d3bcb5 com ponta #c85014, de (44,77) a (44,90) e de (52,77) a (52,90). Troque os borrões marrons de y 80–127 por 2 dobras diagonais em #4d4b58, de (26,82) a (36,120) e de (70,82) a (60,120). Ribana de 1 px no colar. Receita 5.1 §6.
4. **Tirar o brilho oleoso.** Testa #e1d5d4/#d3bcb5 em (51–57,21–26) e bochecha (57–61,44–48) passam para #c8a498. Se quiser luz, faça 1 bloco largo de 1 tom, não um ponto especular. Ref 11.
5. **Boca e nariz.** Boca #a94129/#79322e em (43–50,55–58) vira 2 px #a16e6e em (46–47,57) mais uma linha de 3 px #82565e em (45–48,58); o laranja fica só no forro. Nariz cinza #605457 em (43–48,50–51) vira 1–2 px #a16e6e em (46–47,51).
6. **Forro coerente.** Do lado esquerdo (x 30–38, y 62–73), troque #79322e por #a94129, mais 1 px #c85014 na borda superior, para ler como o mesmo forro laranja na sombra. Escolha a luz pela direita e mantenha o lado direito mais claro.
7. **Pose 3/4 e cabelo crespo (img2img, força 0,4–0,5 sobre esta imagem, com o fundo já corrigido).**
   - Prompt: "three-quarter view, head slightly turned, very short kinky coily hair, buzz cut, hoodie drawstrings".
   - Negativo: "front view, symmetrical, slicked hair, eye whites, lipstick, shiny skin, background-colored clothes".
   - Leve o centro do rosto de x 48 para x≈40 ou x≈56.
   - Refs 21 e 10.
8. **Rim e contorno.** Rim de 1 px quente (#d3bcb5 ou #c85014 clareado) em 3–4 pontos do ombro direito (x 86–90, y 88–100) e da borda do colar. Feche o contorno #190e0f do moletom onde ele encosta no fundo (x 13–16 e 88–93, y 88–127).
