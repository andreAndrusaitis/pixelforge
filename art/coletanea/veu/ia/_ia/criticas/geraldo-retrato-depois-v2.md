# Crítica — geraldo-retrato-depois — volta 2

Arte: `out/ia/refino/geraldo-retrato-v2/geraldo-retrato-v2.json` (96x128, retrato; geração nova com refs a 0,25, camisa lilás recolorida para bege e filtro de moda 3x3)
Folha: `out/estilo/comparar/geraldo-retrato-v2_comparar.png`

## Nota técnica: 84,8 (v1: 99,8)
Fora da faixa, do pior para o melhor:

| Métrica | Valor | Faixa | Nota | Peso |
|---|---|---|---|---|
| Tamanho médio dos blocos | 16,61 px | 2,6–9,6 | 0,53 | 15 |
| Foco × terços | 0,21 | 0,12–0,19 | 0,59 | 4 |
| Pixels órfãos | 0,030 | 0,070–0,248 | 0,71 | 10 |
| Densidade de detalhe | 0,326 | 0,42–0,89 | 0,74 | 10 |
| Contraste de valor | 0,45 | 0,47–0,84 | 0,92 | 10 |
| Tons por rampa | 2,83 | 3,1–8,5 | 0,93 | 10 |
| Dithering | 0,0003 | 0,0012–0,0131 | 0,94 | 4 |
| Cores efetivas | 17 | 17,6–55,6 | 0,96 | 10 |
| Desvio de valor | 0,150 | 0,151–0,266 | 0,99 | 4 |

Diagnóstico: o filtro de moda 3x3 e a recoloração em bege **lavaram demais**. A camisa virou um campo chapado de #cdbb9d (3392 px, 28% do quadro), sem dobras, o que explica os blocos grandes, a falta de detalhe e de órfãos e as rampas curtas. Refs mais próximas: 19, 14, 20.

## Rubrica visual
| Critério | Peso | Nota | Observação |
|---|---|---|---|
| Silhueta e leitura | 10 | 8 | Cabeça + ombros largos leem bem; o fundo #7a7176 tem valor próximo da sombra da camisa e as bordas baixas somem |
| Proporção e pose | 10 | 7 | Ombros largos ok (corrigido). Rosto e pescoço ainda magros para o "barrigudo"; pose frontal rígida, de foto 3x4 |
| Rosto (discreto, sem anime) | 10 | 7 | **Barbeado ok**, olhos discretos, sobrancelha branca boa. Ainda há 3 listras de ruga na testa e as orelhas são manchas escuras |
| Sombreamento em blocos | 15 | 6 | Rosto em blocos razoáveis; camisa sem planos: um bloco único com riscos escuros soltos nas laterais |
| Paleta contida + destaque | 10 | 7 | 20 cores, sombra violeta coerente; o pescoço em bordô (#753b42/#562e41) foge da rampa da pele e não há destaque |
| Contorno seletivo | 5 | 7 | Sem contorno duro (ok); a gola escura funciona como contorno grosso no meio do peito |
| Luz e rim light | 10 | 6 | Rim lilás no topo dos ombros e no cabelo é bom, mas a luz principal é frontal e chapada, o rosto é quase simétrico e sem lado de sombra |
| Materiais e dobras | 10 | 5 | Camisa de botão sem botões, sem carcela e sem dobras; a gola (x 35–62, y 82–100) é um "V" cinza-escuro que não lê como tecido |
| Composição e enquadramento | 10 | 6 | Centralizado e simétrico, foco fora dos terços; metade de baixo do quadro é camisa vazia |
| "Não parece amador" | 10 | 6 | O rosto evoluiu; a camisa chapada e o pescoço bordô ainda entregam o processo |

Rubrica = 645 / 10 = **64,5** (igual à v1: ganhou no personagem, perdeu em composição e na roupa)

## NOTA FINAL = 0,4 × 84,8 + 0,6 × 64,5 = **72,6**: **REFAZER** (v1: 78,6)

## O que melhorou desde a v1
- Bigode e costeleta saíram: rosto barbeado.
- Jaqueta camuflada e o ruído salpicado saíram; os ombros agora são largos e enchem o quadro.
- O rim lilás frio no cabelo e nos ombros dá um começo de duas temperaturas.

## Melhorias (da que mais sobe a nota para a que menos)
1. **Dobras e planos na camisa (y 66–128), sem filtro de moda 3x3 nessa área.**
   - Use moda 2x2 ou nenhuma, e recolora mapeando a rampa inteira, não para um bege só. Use 4 tons: luz #e2d3b5, base #cdbb9d, meia-sombra #a99379, sombra #857063, e a mais escura puxando para violeta, #5f4c58.
   - Desenhe 2–3 dobras diagonais por lado, saindo das axilas (x 14→30, y 92→116 e x 82→66, y 92→116), cada uma com 1 px claro e 1–2 px de sombra (ref 22).
   - O lado oposto à luz (direita, x 70–95) vai inteiro um degrau abaixo.
   - Isso deve levar a camisa para a faixa de blocos 3–9 px, densidade de detalhe ≥ 0,42 e órfãos ≥ 0,07.
2. **Pescoço na rampa da pele (x 36–64, y 59–82).** Troque o bordô por pele: #bc887e no lado iluminado, #a5736c na meia-sombra, #8f5656 na sombra sob o queixo (só y 60–64) e #753b42 só como fresta de 1 px. Hoje parece um lenço vermelho.
3. **Gola e carcela.**
   - Gola aberta em "V", com borda de 1 px #e2d3b5 em cima e 1 px #857063 embaixo (x 35–62, y 82–100), em vez do bloco cinza #5f4c58.
   - Carcela vertical de 2 px um tom mais claro, de (49,100) a (49,128).
   - 3 botões de 1 px #f3f0ed em y 104, 113 e 122: é o "camisa de botão" e dá o detalhe que falta.
4. **Luz lateral definida.**
   - Escolha a esquerda. Escureça um degrau a metade direita do rosto (x 50–64, y 30–64), com sombra puxando para violeta #8f5656/#562e41, e mantenha a esquerda em #e6cdc1/#cb9e91.
   - O rim lilás fica só do lado direito (ombro x 75–92, y 78–84, cabelo e orelha direitos). Do lado esquerdo, ponha 1 px quente, tipo #e8a07a, no topo do ombro (x 8–25, y 80) e no cabelo (refs 22 e 14).
5. **Pose e composição (img2img).** Prompt `three-quarter view, head turned slightly, looking off to the side`; negativo `front view, symmetrical, passport photo`. Desloque a cabeça para o terço da esquerda (centro em x ≈ 36–40) para devolver o foco × terços à faixa.
6. **Testa: troque as 3 listras (x 37–60, y 24–31) por 2 blocos.** #e6cdc1 no alto e #cb9e91 junto às sobrancelhas, com no máximo 1 ruga de 1 px #a5736c.
7. **Orelhas (x 28–36 e x 64–70, y 36–51).** Faça 2–3 tons: base #a5736c, concha interna #753b42 com 1 px, e 1 px de luz na borda do lado da luz. Hoje são manchas escuras.
8. **Limpeza e acento.**
   - Remova o pixel escuro solto em (50,118) e os 2 px claros no lábio superior (x 50–56, y 50–51), que lembram o bigode da v1.
   - Pense num único acento de cor, por exemplo 1 px quente nos botões ou no rim do lado da luz.
   - Escureça o fundo para ~#5a5258 e afaste a camisa do fundo: o contraste de valor volta à faixa (≥ 0,47).
