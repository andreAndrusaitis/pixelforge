# Crítica — geraldo-retrato-depois — volta 4

Arte: `out/ia/refino/geraldo-retrato-v4/geraldo-retrato-v4.json` (96x128, retrato; v3/r3-3 + retoques em código)
Folha: `out/estilo/comparar/geraldo-retrato-v4_comparar.png`

## Nota técnica: 95,7 (v3: 95,9)
Fora da faixa:

| Métrica | Valor | Faixa | Nota | Peso |
|---|---|---|---|---|
| Pixels órfãos | 0,050 | 0,070–0,248 | 0,85 | 10 |
| Foco × terços | 0,192 | 0,12–0,19 | 0,90 | 4 |
| Tamanho médio dos blocos | 10,29 px | 2,6–9,6 | 0,92 | 15 |
| Tons por rampa | 2,83 | 3,1–8,5 | 0,93 | 10 |
| Desvio de valor | 0,145 | 0,151–0,266 | 0,93 | 4 |
| Cores efetivas | 17 | 17,6–55,6 | 0,96 | 10 |

Os retoques trocaram cor por cor, sem acrescentar tons nem detalhe; por isso a técnica ficou parada. Refs mais próximas: 19, 20, 13.

## Conferência dos retoques
| Retoque pedido | Resultado |
|---|---|
| Barba cinza → pele | Quase todo feito. **Restam 7 px #8c838c no queixo em x 37–44, y 56–61**, que ainda lêem como sombra de barba na escala 1 |
| Gola #11111c → #3f2b31 | Feito; a gola lê como tecido escuro. Restam 19 px #11111c: em (64–65, 56–63), atrás da mandíbula, e (62,104) |
| 3 botões em (37,84), (36,92), (35,100) | Feito; mas 1 px isolado lê como cisco, não como botão |
| Testa #e0d6ce → #d1b8aa | Feito; a linha do cabelo ficou limpa. Boa |
| Sombra da camisa → #5d4a5e | Feito (548 px). A camisa se separou da pele e a sombra esfriou, mas as listras verticais ficaram **mais** visíveis: viraram um padrão listrado lilás. A mancha de x 60–75, y 95–125 continua |
| Sombra da cabeça → #4e4258 | **Quase não pegou**: só 30 px trocaram (x 58–66, y 30–59). Nuca, orelha e pescoço continuam em #5e3f41/#3f2b31 quentes |

## Rubrica visual
| Critério | Peso | Nota | Observação |
|---|---|---|---|
| Silhueta e leitura | 10 | 8 | Igual à v3 |
| Proporção e pose | 10 | 7 | 3/4 bom; pescoço longo e fino, sem massa |
| Rosto (discreto, sem anime) | 10 | 8 | Barbeado na leitura geral, testa limpa, olhos discretos. Falta limpar os 7 px no queixo |
| Sombreamento em blocos | 15 | 7 | Rosto em blocos; camisa ainda em pinceladas verticais, agora acentuadas pelo violeta |
| Paleta contida + destaque | 10 | 7 | A sombra fria na camisa ajudou; a cabeça continua toda quente e não há destaque |
| Contorno seletivo | 5 | 8 | Gola e carcela sem preto puro; contorno escuro só nas costas, ok |
| Luz e rim light | 10 | 7 | Luz coerente vinda da direita; sem rim light |
| Materiais e dobras | 10 | 6 | Gola ok; botões são ciscos de 1 px; dobras não feitas, listras e a mancha seguem |
| Composição e enquadramento | 10 | 7 | Ele olha para a borda mais próxima; figura não deslocada |
| "Não parece amador" | 10 | 7 | O rosto está quase lá; a camisa listrada ainda denuncia |

Rubrica = 715 / 10 = **71,5**

## NOTA FINAL = 0,4 × 95,7 + 0,6 × 71,5 = **81,2**: **REFAZER**
Melhor nota até aqui. Faltam 6 critérios para chegar a 8; o maior peso está na camisa (sombreamento e materiais).

## Melhorias (da que mais sobe a nota para a que menos)
1. **Camisa: dobras de verdade e menos listra (y 66–128).**
   - Nas áreas grandes, faça moda 2x2 só na máscara da camisa: funde as pinceladas de 1 px em blocos.
   - Pinte 2 dobras diagonais: uma de (80,75) a (62,120) e outra de (20,85) a (30,120). Cada uma tem 1 px #d8c3a8 (tom novo, luz) do lado da luz e 2 px #5d4a5e embaixo.
   - O lado esquerdo (x 16–35), longe da luz, vira um bloco contínuo de #5d4a5e/#3f2b31.
   - Apague a mancha de x 60–75, y 95–125 com #c8ad91/#a98170.
   - Isso sobe sombreamento, materiais e "amador", e o tom novo ajuda nas rampas (ref 22).
2. **Terminar a sombra fria da cabeça.** Troque #5e3f41 → #4e4258 e #3f2b31 → #3a3044 na orelha, nuca e pescoço (x 56–70, y 28–66) e sob o queixo (x 33–56, y 56–64). Mantenha o calor só na pele iluminada.
3. **Rim light frio no lado oculto.** Ponha 1 px #a9a1a4 no contorno da nuca e da orelha (x 67–70, y 30–60) e no topo das costas (x 15–35, y 72–78) (refs 22 e 14).
4. **Botões que leiam.**
   - Cada botão vira 2x1 px, #e0d6ce em cima e #a98170 embaixo como sombra, em (37–38,84), (36–37,92) e (35–36,100).
   - Ponha a carcela com 1 px #a98170 ao lado.
   - Um deles pode ganhar o único acento da paleta (ex.: #c88577).
5. **Limpar os resíduos.** Troque os 7 px #8c838c do queixo (x 37–44, y 56–61) por #a98170/#916a60. Troque o #11111c em (64–65, 56–63) por #3a3044 e o de (62,104) por #c8ad91.
6. **Pescoço com massa.** Alargue o pescoço para x 38–64, com sombra fria do lado direito, e suba o colarinho ~3 px (y ≈ 58–60), para a cabeça assentar.
7. **Composição.** Desloque toda a figura ~6 px para a direita (cabeça em x 33–74) e preencha a borda esquerda com o fundo #6a696e. Ganha respiro na direção do olhar e corrige o foco × terços.
