# Crítica — geraldo-retrato-depois — volta 6 (final do ciclo)

Arte: `out/ia/refino/geraldo-retrato-v6/geraldo-retrato-v6.json` (96x128, retrato; v5 + dobras afinadas, planos, acento, fundo)
Folha: `out/estilo/comparar/geraldo-retrato-v6_comparar.png`

## Nota técnica: 94,3 (v5: 95,4)
Fora da faixa:

| Métrica | Valor | Faixa | Nota | Peso |
|---|---|---|---|---|
| Pixels órfãos | 0,0456 | 0,070–0,248 | 0,81 | 10 |
| Tamanho médio dos blocos | 11,12 px | 2,6–9,6 | 0,84 | 15 |
| Cores efetivas | 16 | 17,6–55,6 | 0,89 | 10 |
| Densidade de detalhe | 0,400 | 0,421–0,889 | 0,94 | 10 |
| Desvio de valor | 0,148 | 0,151–0,266 | 0,96 | 4 |

Os planos grandes da camisa (#a98170 subiu de 442 para 748 px) melhoraram a leitura, mas aumentaram os blocos e reduziram o detalhe. Os tons novos têm poucos pixels: #d8c3a8 tem só 41 e não conta como cor efetiva. Refs mais próximas: 19, 20, 14.

## Conferência dos retoques
| Pedido | Resultado |
|---|---|
| Retas paralelas → dobras afinadas | As alças sumiram. Mas as dobras novas se perdem no ruído vertical que sobrou na camisa e não lêem como dobras na escala 1 |
| Mancha → #a98170 | Feito: a caixa x 60–76, y 95–126 ficou com 23 px #5d4a5e em 496 |
| 3 planos | O lado de sombra à esquerda (x 18–38) lê bem. O plano de luz no peito (x 60–85) ainda é cortado por riscos violeta curtos (x 60–92, y 85–125) |
| Luz no ombro | Sutil, ok |
| Acento #b8503a | Funciona: um ponto quente pequeno no botão (≈ (36,101)), único na figura (ref 1) |
| Fundo #5c5a60 | Ok; a cabeça destaca mais |
| Pescoço | Não feito |

## Rubrica visual
| Critério | Peso | Nota | Observação |
|---|---|---|---|
| Silhueta e leitura | 10 | 8 | Lê bem |
| Proporção e pose | 10 | 7 | Pescoço longo e fino (x 46–66, y 56–70); falta a massa do Geraldo |
| Rosto (discreto, sem anime) | 10 | 8 | Barbeado, discreto e sério |
| Sombreamento em blocos | 15 | 7 | Rosto bom; camisa com plano de sombra legível, mas o peito segue riscado |
| Paleta contida + destaque | 10 | 8 | Sombra fria, luz quente e um acento |
| Contorno seletivo | 5 | 8 | Ok |
| Luz e rim light | 10 | 8 | Duas temperaturas, coerente |
| Materiais e dobras | 10 | 7 | Mancha e alças resolvidas, botões e acento; dobras ainda ilegíveis no meio do ruído |
| Composição e enquadramento | 10 | 8 | Ok |
| "Não parece amador" | 10 | 7 | O rosto aguenta ao lado das refs; a camisa ainda parece "pintura pixelizada" |

Rubrica = 755 / 10 = **75,5**

## NOTA FINAL = 0,4 × 94,3 + 0,6 × 75,5 = **83,0**: **REFAZER** (volta 6, fim do ciclo sem aprovação)

## Evolução no ciclo
78,6 → 72,6 → 80,4 → 81,2 → 82,9 → 83,0. A rubrica subiu sempre desde a v2 (64,5 → 75,5). A técnica estacionou em ~95, presa em órfãos, blocos e cores efetivas.

## O que falta (resumo para o autor)
A cabeça está no nível das referências: barbeado, olhos discretos, sombra fria, rim de duas temperaturas, composição com respiro. **O que impede a aprovação está do pescoço para baixo**, e são 4 critérios em 7: proporção, sombreamento, materiais e "amador".

1. **Repintar a camisa à mão, não retocar a pixelização.** A textura vertical de origem (pinceladas da IA) é a causa de tudo o que sobrou.
   - Na máscara da camisa (y 66–128), apague tudo e pinte por cima com 4–5 tons: #d8c3a8 / #c8ad91 / #a98170 / #5d4a5e / #3a3044.
   - Planos: luz no peito em x 60–85, y 74–100; meia-sombra no centro; sombra contínua em x 18–38 e na faixa y 118–128.
   - Por cima, só as 2–3 dobras já desenhadas e mais nada (receita 5.2.4, ref 22).
   - Depois, 10–20 px de detalhe deliberado: costura do ombro, borda da carcela com 1 px de luz, quina do bolso. Isso traz de volta os órfãos (≥ 0,07), os blocos (≤ 9,5 px) e a densidade.
2. **Pescoço com massa** (o único item pedido desde a v2 que nunca foi feito). Alargue para x 44–70, encurte subindo o colarinho para y ≈ 59, com luz #c09882 à esquerda e sombra fria #4e4258 à direita. Sem isso, ele continua um senhor magro, não o Geraldo de ~2 m e ombros largos (receita 5.2.1, ref 5).
3. **Dar área aos tons de passagem.** #d8c3a8 (41 px), #3a3044 (47 px) e #e8a07a (16 px) precisam de ~60–100 px cada para contar como cor efetiva (≥ 18). Use-os nos planos da camisa e no rim do ombro.

Com esses 3 itens, a estimativa é proporção, sombreamento, materiais e "amador" em 8, a rubrica em ~83 e a técnica em ~98–99, o que daria uma final de ~89. Para chegar a 95, falta ainda a mão de acabamento que as refs têm (ref 22: tecido com dobras desenhadas, não filtradas). O caminho mais provável é pintar a roupa toda em código sobre a cabeça atual.
