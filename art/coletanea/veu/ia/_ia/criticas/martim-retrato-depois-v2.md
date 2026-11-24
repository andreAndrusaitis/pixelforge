# Crítica — martim-retrato (v2) — volta 2

Arte: `out/ia/refino/martim-retrato-v2/martim-retrato-v2.json` (96x128, tipo retrato). Geração nova com o prompt corrigido.
Folha: `out/estilo/comparar/martim-retrato-v2_comparar.png`
Refs mais próximas (técnica): 20, 19, 13. Refs guia do personagem: 21, 11, 10.

## Nota técnica: 94,7 (v1: 98,5)
Fora da faixa:
- foco × terços: 0,228 (faixa 0,12–0,19; nota 0,39). O rosto está cravado no centro.
- cores efetivas: 15 (mínimo 17,6; nota 0,81).
- pixels órfãos: 0,057 (mínimo 0,070; nota 0,89).
- tamanho médio dos blocos: 9,74 px (máximo 9,56; nota 0,98).

## O que melhorou desde a v1
Lê como criança, o moletom é cinza, o capuz está abaixado como colar (y ~85–100), o cabelo é escuro, os cordões têm 1 px, e o verde, o roxo e o ruivo sumiram. Os blocos ficaram maiores e o ruído de foto diminuiu bastante.

## Rubrica visual
| critério | peso | nota | observação |
|---|---|---|---|
| silhueta e leitura | 10 | 7 | cabeça e colar do capuz bem lidos; halo de pixels soltos no cabelo (x 15–80, y 6–40) |
| proporção e pose | 10 | 6 | proporção de criança ok; pose de frente, rígida, de foto 3x4; orelhas grandes (x 19–28 e 68–77, y 57–73) |
| rosto (discreto, sem olho de anime) | 10 | 5 | olho lê FECHADO/sonolento: pupila abaixo do traço e escorrendo (x 60, y 64–66) como lágrima; olheiras #6a3739 (y 67); boca aberta com dentes brancos #d5c9c9 em (48–50,78); manchas nas bochechas |
| sombreamento em blocos | 15 | 6 | blocos maiores, mas as bochechas são manchadas (#a36562/#8b5453 salpicado em x 41–47 e 57–63, y 70–74); moletom com tracinhos verticais em vez de dobras |
| paleta contida + 1 destaque, sombra fria/luz quente | 10 | 6 | contida e cinza ✓, mas SEM destaque (15 cores, tudo cinza-quente barrento); sombras da pele marrom-avermelhadas, não frias |
| contorno seletivo | 5 | 7 | contorno escuro no cabelo, no queixo e nos ombros; razoável |
| luz e rim light | 10 | 5 | luz frontal chapada; sem direção clara e sem rim |
| materiais e dobras | 10 | 6 | colar do capuz e cordões ✓; corpo do moletom com textura de risquinhos, sem as 2 dobras grandes da receita 5.1 |
| composição e enquadramento | 10 | 6 | busto centralizado e simétrico; foco fora dos terços |
| "não parece amador" | 10 | 6 | bem mais perto, mas a expressão (olho fechado, lágrima, dente) lê como menino doente/chorando |

**Rubrica: 59,5**

## NOTA FINAL: 0,4 × 94,7 + 0,6 × 59,5 = **73,6**

## Veredito: REFAZER

Contradições com o briefing que ainda restam:
- O cabelo é ondulado/desgrenhado, com tufos de 4–6 px e franja até y ~48. Não é crespo na máquina (rente, curto).
- Não há sobrancelha grossa: a de y 55–56 é fina e clara (#695858/#535056).
- Rosto estreito: ok. Idade: ok.

## Melhorias (da que mais sobe a nota para a que menos)
1. **Corrigir os olhos (retoque em código).** A pupila de 1 px abaixo do traço faz o olho ler fechado, e a coluna em (60,64–66) parece lágrima. Olho esquerdo: traço de 3×1 px #120e0f em (34–36,62) com a pupila DENTRO do traço, e não abaixo. Olho direito: traço em (59–61,62). Apagar (36–37,64) e (60,64–66) para a pele #c3958d. A pálpebra sombreada vai ACIMA do traço (y 61), não abaixo. Ref 21 e receita 5.1 §5.
2. **Tirar o aspecto doente.** Olheiras #6a3739/#8b5453 em (33–38,67) e (56–62,67) → #c3958d. Dentes #d5c9c9 em (48–50,78) → #a36562 (boca fechada). Linha da boca (43–52,80) encurtada para 3–4 px em (47–50,80). Bochechas: trocar o salpicado de x 41–47 e 57–63, y 70–74 por 1 bloco de 2 px #b07d78 de cada lado (ref 11).
3. **Sobrancelha grossa.** Em (33–40,55–56) e (56–63,55–56), 2 px de altura em #322729 (cor do cabelo), com a ponta externa caída 1 px. É o traço que dá expressão ao Martim (receita 5.1).
4. **Um destaque de cor.** Hoje faltam cores e o resultado é barrento. Opções: estampa de ~8×10 px no peito em (44–52,108–118), numa cor quente saturada com 3–4 tons (ex.: laranja #d0703a/#a04a2a/#6e2e22), ou forro interno do capuz-colar (y 86–92) nessa mesma cor. Sombra da pele puxando para o frio: #8b5453 → #7a5260. Isso também resolve "cores efetivas". Ref 21 (1 destaque forte).
5. **Pose 3/4 e terços (img2img, força 0,45–0,55).** Acrescentar ao prompt "three-quarter view, head turned slightly, looking to the side" e ao negativo "front view, symmetrical, passport photo, closed eyes, crying, open mouth, teeth, eye bags". O centro do rosto deve cair perto de x≈38 ou x≈58 (terços), não em x 48. Ref 21 e ref 10 (contrapposto).
6. **Cabelo crespo na máquina.** Na geração: "very short kinky coily hair, buzz cut, tight curls" (negativo: "wavy hair, messy fringe, long bangs"). Em código: subir a massa do cabelo de y 6–48 para ~y 14–44, com a borda em grão miúdo de 1–2 px (não tufos de 4–6 px) e só 3–4 pontas de franja até y ~50. Limpar os pixels soltos do halo, fora da silhueta.
7. **Luz e rim.** Escolher a luz pela direita: o lado direito do rosto (x 50–64) em #cfafa5 em bloco, o esquerdo (x 30–42) em #c3958d/#b07d78. Rim de 1 px quente (#cfaaa0) em 3–4 pontos do ombro direito (~x 70–78, y 98–104) e da borda do capuz-colar.
8. **Dobras do moletom.** Trocar os tracinhos verticais #44393a (y 104–127) por 2 dobras diagonais de 2 tons, ombro → peito, por ex. de (24,104) a (36,124) e de (72,104) a (60,124). Ribana de 1 px no colar.
