# Crítica — geraldo-retrato-depois — volta 3

Arte: `out/ia/r3/geraldo-retrato-r3-3/geraldo-retrato-r3-3.json` (96x128, retrato; geração nova, 3/4, sem moda 3x3, paleta da própria pixelização)
Folha: `out/estilo/comparar/geraldo-retrato-r3-3_comparar.png`

## Nota técnica: 95,9 (v2: 84,8; v1: 99,8)
Fora da faixa:

| Métrica | Valor | Faixa | Nota | Peso |
|---|---|---|---|---|
| Pixels órfãos | 0,0505 | 0,070–0,248 | 0,85 | 10 |
| Cores efetivas | 16 | 17,6–55,6 | 0,89 | 10 |
| Tamanho médio dos blocos | 10,15 px | 2,6–9,6 | 0,93 | 15 |
| Foco × terços | 0,194 | 0,12–0,19 | 0,86 | 4 |
| Desvio de valor | 0,147 | 0,151–0,266 | 0,95 | 4 |

Paleta curta (16 cores) e blocos um pouco grandes. Faltam 2–3 tons intermediários e alguns pixels de detalhe. Refs mais próximas: 19, 20, 13.

## Rubrica visual
| Critério | Peso | Nota | Observação |
|---|---|---|---|
| Silhueta e leitura | 10 | 8 | Cabeça em 3/4 e ombro lêem bem contra o cinza #6a696e |
| Proporção e pose | 10 | 7 | 3/4 com a cabeça virada: bom. Pescoço longo e fino (x 40–60, y 55–70) e rosto magro: ainda não é o Geraldo pesado |
| Rosto (discreto, sem anime) | 10 | 7 | Olhos discretos e sérios (bom, ref 22). Mas há **barba por fazer cinza no queixo** (#a9a1a4/#8c838c em x 36–53, y 48–62), que contradiz o "barbeado". A testa tem manchas #e0d6ce da cor do cabelo (x 31–50, y 20–35), que confundem a linha do cabelo |
| Sombreamento em blocos | 15 | 7 | Rosto em blocos bons; camisa com pinceladas verticais ruidosas e uma mancha escura (x 60–75, y 95–125) que parece sujeira |
| Paleta contida + destaque | 10 | 7 | Contida (16 cores), mas a camisa e a pele estão no mesmo matiz bege-rosado e se fundem. Sombras marrom-avermelhadas, não frias. Sem destaque |
| Contorno seletivo | 5 | 7 | Gola e carcela em #11111c preto puro (x 34–69, y 60–98): pesado demais, vira uma faixa/tira preta |
| Luz e rim light | 10 | 7 | Luz **coerente, mas vem da direita**: rosto direito 151 contra esquerdo 128 de luminância média, camisa 135 contra 113. Não é a "luz quente da esquerda" do briefing. Sem rim light, e a sombra não é fria |
| Materiais e dobras | 10 | 6 | Gola de camisa lê; a carcela é uma linha preta sem botões; as dobras são ruído vertical, não 2–3 dobras grandes |
| Composição e enquadramento | 10 | 7 | Cabeça no terço de cima à esquerda, boa. Mas ele olha para a borda mais próxima (esquerda), sem espaço de respiro |
| "Não parece amador" | 10 | 7 | A melhor das três; o ruído da camisa e o preto chapado da gola ainda denunciam |

Rubrica = 700 / 10 = **70,0**

## NOTA FINAL = 0,4 × 95,9 + 0,6 × 70,0 = **80,4**: **REFAZER**
Todos os critérios estão em 7 ou 8; para aprovar, nenhum pode ficar abaixo de 8. É a melhor volta até aqui.

## Melhorias (da que mais sobe a nota para a que menos)
1. **Tirar a barba cinza do queixo (x 36–53, y 48–62).** Troque #a9a1a4/#8c838c pela rampa da pele: #c09882 na luz, #a98170 na meia-sombra e #916a60 na sombra sob o queixo. No img2img, reforce no negativo: `stubble, five o'clock shadow, grey beard, goatee`.
2. **Camisa: de ruído para 2–3 dobras grandes (y 70–128).**
   - Funda as pinceladas verticais em blocos com moda 2x2 só na camisa, ou reduzindo para 4 tons: #d8c3a8 (novo, luz), #c8ad91, #a98170 e #77564f.
   - Desenhe uma dobra diagonal grande do ombro direito à cintura, de (80,75) a (62,120), e uma do braço esquerdo, de (20,85) a (30,120), cada uma com 1 px claro sobre 1–2 px de sombra (ref 22).
   - Apague a mancha escura em x 60–75, y 95–125.
3. **Gola e carcela fora do preto puro.**
   - Troque #11111c (x 34–69, y 60–98) por #3f2b31 na gola e #5e3f41 na carcela. Deixe 1 px de luz #d8c3a8 na borda de cima da gola.
   - Ponha 3 botões de 1 px #e0d6ce ao longo da carcela, em (37,84), (36,92) e (35,100) (receita 5.2.4: gola de 1–2 px).
4. **Separar a camisa da pele e esfriar a sombra.**
   - Puxe a sombra da camisa e do lado da cabeça (orelha e pescoço x 58–68, y 30–62) para violeta-frio, de #5e3f41 para ~#4e4258 e de #77564f para ~#6a5866.
   - Mantenha a pele rosada-quente.
   - Isso dá a "sombra fria / luz quente" e adiciona 2 cores à paleta, que hoje tem 16 (faixa ≥ 17,6).
5. **Rim light no lado da sombra.**
   - A luz vem da direita; se quiser a da esquerda como no briefing, inverta o prompt ou espelhe a imagem.
   - Ponha 1 px frio #a9a1a4 no contorno de trás da nuca e da orelha (x 66–69, y 30–60) e no topo das costas (x 15–35, y 72–80), onde hoje há contorno escuro (refs 22 e 14).
6. **Testa: tire as manchas cor de cabelo (#e0d6ce em x 31–50, y 20–35).** Use #d1b8aa como a luz mais alta da pele, para separar a linha do cabelo; o branco #e0d6ce fica só no cabelo.
7. **Massa do corpo.** No prompt, use `thick neck, heavyset, broad chest`. Em código, encurte e alargue o pescoço: o colarinho sobe para y ≈ 58 e o pescoço fica em x 38–64. Assim a cabeça assenta nos ombros.
8. **Composição e detalhe.**
   - Desloque a figura ~6 px para a direita (cabeça em x 33–74), para dar respiro na direção do olhar; isso também ajusta o foco × terços.
   - Os 2 tons novos e as dobras devem levar os órfãos para ≥ 0,07 e os blocos para ≤ 9,5 px.
