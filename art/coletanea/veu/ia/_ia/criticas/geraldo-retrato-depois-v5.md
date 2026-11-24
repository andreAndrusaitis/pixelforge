# Crítica — geraldo-retrato-depois — volta 5

Arte: `out/ia/refino/geraldo-retrato-v5/geraldo-retrato-v5.json` (96x128, retrato; v4 + itens 1–5 e 7 da crítica v4)
Folha: `out/estilo/comparar/geraldo-retrato-v5_comparar.png`

## Nota técnica: 95,4 (v4: 95,7)
Fora da faixa:

| Métrica | Valor | Faixa | Nota | Peso |
|---|---|---|---|---|
| Pixels órfãos | 0,0475 | 0,070–0,248 | 0,83 | 10 |
| Desvio de valor | 0,140 | 0,151–0,266 | 0,87 | 4 |
| Cores efetivas | 16 | 17,6–55,6 | 0,89 | 10 |
| Tamanho médio dos blocos | 10,48 px | 2,6–9,6 | 0,90 | 15 |
| Densidade de detalhe | 0,418 | 0,421–0,889 | 0,99 | 10 |

O foco × terços entrou na faixa com o deslocamento de +6 px. As cores efetivas caíram para 16, porque os tons novos (#d8c3a8, #e8a07a, #3a3044) são poucos pixels e não contam como cor efetiva. Refs mais próximas: 19, 20, 14.

## Conferência dos retoques
| Pedido | Resultado |
|---|---|
| Dobras diagonais | Feitas, mas como **duas retas paralelas de largura constante**: à esquerda de (28,80) a (38,120), à direita de (83,72) a (67,120). Lêem como alças ou suspensórios, não como dobras |
| Mancha x 60–75, y 95–125 | **Não saiu de fato**: a região ainda tem 120 px #5d4a5e + 48 px #5e3f41 em 496 px, quase metade escura |
| Sombra fria na orelha, pescoço e queixo | Feita; o lado oculto da cabeça esfriou. Boa |
| Rim frio #a9a1a4 na direita da cabeça | Feito, sutil e correto (x 66–74, y 24–60) |
| Rim quente #e8a07a no ombro esquerdo | Feito (x 30–45, y 64–80); dá as duas temperaturas. Funciona |
| Botões 2x1 | Lêem como botões. O último em #c88577 **não é acento**: é a mesma cor da pele (138 px no rosto) |
| Resíduos | Queixo limpo; o #11111c restante fica só nos olhos (ok) |
| Deslocamento +6 px | Feito; o olhar ganhou respiro. Boa |

## Rubrica visual
| Critério | Peso | Nota | Observação |
|---|---|---|---|
| Silhueta e leitura | 10 | 8 | Lê bem |
| Proporção e pose | 10 | 7 | Pescoço ainda longo e fino (x 46–66, y 56–70); não tem a massa do Geraldo |
| Rosto (discreto, sem anime) | 10 | 8 | Barbeado, discreto e sério |
| Sombreamento em blocos | 15 | 7 | Rosto em blocos; camisa ainda em pinceladas verticais, e as dobras novas são riscos uniformes |
| Paleta contida + destaque | 10 | 8 | Sombra fria e luz quente presentes; falta um acento de verdade |
| Contorno seletivo | 5 | 8 | Ok |
| Luz e rim light | 10 | 8 | Luz principal coerente, rim frio de um lado e quente do outro (refs 22 e 14) |
| Materiais e dobras | 10 | 6 | Dobras parecem alças; mancha mantida; tecido sem volume (ombro e peito não arredondam) |
| Composição e enquadramento | 10 | 8 | Respiro na direção do olhar, cabeça no terço de cima |
| "Não parece amador" | 10 | 7 | As retas paralelas na camisa são o que mais denuncia |

Rubrica = 745 / 10 = **74,5**

## NOTA FINAL = 0,4 × 95,4 + 0,6 × 74,5 = **82,9**: **REFAZER**
Ainda abaixo de 8: proporção (7), sombreamento (7), materiais (6) e "amador" (7). Quase tudo o que falta está na camisa e no pescoço. A próxima é a volta 6, a última do ciclo.

## Melhorias (da que mais sobe a nota para a que menos)
1. **Transformar as retas em dobras.** Uma dobra de verdade afina nas pontas, quebra de direção e tem um lado de luz e um de sombra (ref 22).
   - Dobra esquerda, hoje de (28,80) a (38,120): sombra de 3 px de largura no meio (y 92–106), afinando para 1 px nas pontas. Do lado da luz, 1 px #d8c3a8 só no trecho do meio, não na reta toda. Quebre a dobra em 2 segmentos com ângulos diferentes, um mais inclinado acima de y 98.
   - Dobra direita, hoje de (83,72) a (67,120): ela deve **nascer na axila** (x 80, y 88) e abrir em leque até a cintura, com 2 ramos curtos em vez de uma reta, um indo a (70,112) e outro a (78,120).
2. **Apagar a mancha de verdade (x 60–76, y 95–126).** Troque #5d4a5e/#5e3f41 dessa caixa por #a98170 (meia-sombra) e deixe o escuro só na sombra do ramo de dobra que passar por ali.
3. **Volume do tronco, em vez de listras verticais.** Faça moda 2x2 na máscara da camisa e então pinte 3 planos:
   - luz #d8c3a8/#c8ad91 no peito do lado da luz (x 60–85, y 74–100);
   - meia-sombra #a98170 no centro;
   - sombra #5d4a5e contínua no lado esquerdo e embaixo (x 18–38, y 80–128, e a faixa y 118–128).
   Ombro direito com 1 px #d8c3a8 na curva (x 70–88, y 70–74).
   Isso também reduz os blocos e sobe as cores efetivas (#d8c3a8 passa a ter área).
4. **Pescoço com massa (o item que ficou de fora).** Alargue para x 44–70: a sombra fria #4e4258 cresce para a direita e a luz #c09882 para a esquerda. Suba o colarinho ~3 px, de y ≈ 62 para y ≈ 59, e encurte o pescoço.
5. **Acento de verdade.** O botão em #c88577 é cor de pele. Use uma cor que não exista na figura, pequena e saturada, como #b8503a (tijolo) ou #4f7a8c (azul-petróleo), em 2x1 px no último botão, ou num bolso de 2 px (ref 1: um único acento).
6. **Valor: espalhar a faixa.** O desvio de valor está baixo (0,140). Escureça o fundo #6a696e para ~#5c5a60 e leve a sombra mais funda da camisa (borda esquerda, x 18–24) a #3a3044. A cabeça destaca mais e o contraste sobe.
