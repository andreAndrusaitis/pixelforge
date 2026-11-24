# Crítica — geraldo-retrato-depois — volta 1

Arte: `out/ia/prova/geraldo-retrato-depois/geraldo-retrato-depois.json` (96x128, tipo retrato, via IA SDXL + LoRA, pixelizada)
Folha: `out/estilo/comparar/geraldo-retrato-depois_comparar.png`

## Nota técnica: 99,8
- Só uma métrica fora da faixa: pixels órfãos 0,0667 (faixa 0,0699–0,2477), nota 0,97. O resto está dentro: 25 cores efetivas, 3,12 tons por rampa (no limite de baixo), 16 níveis de valor.
- Refs mais próximas pela métrica: 19, 20, 18. Nenhuma delas é retrato; a métrica é genérica. A régua visual usada foi a das refs guia 14, 1 e 22 (receita 5.2).

## Rubrica visual
| Critério | Peso | Nota | Observação |
|---|---|---|---|
| Silhueta e leitura | 10 | 8 | Cabeça lê bem contra o fundo liso #554b53; o busto se mistura nas bordas de baixo |
| Proporção e pose | 10 | 6 | Pescoço fino e rosto magro: não é o Geraldo "~2 m, ombros largos, barriga". Ombro esquerdo caído (x 18–30, y 85–100) |
| Rosto (discreto, sem anime) | 10 | 6 | Olhos discretos (ok), mas há **bigode** cinza (contradiz "barbeado") e a testa tem rugas de foto em listras |
| Sombreamento em blocos | 15 | 6 | Rosto em blocos razoáveis, mas com cara de foto pixelizada; a roupa é ruído salpicado sem planos |
| Paleta contida + destaque | 10 | 7 | 26 cores, sombras violeta-quentes (#1a0415, #381424) ok; falta 1 destaque, e o verde-oliva/azul da roupa fica sujo |
| Contorno seletivo | 5 | 7 | Contorno escuro na orelha e na mandíbula, cabelo sem contorno: ok; a roupa tem traços escuros soltos |
| Luz e rim light | 10 | 6 | Rosto iluminado de frente-esquerda, mas o ombro direito (x 65–95, y 85–128) é a área mais clara: há duas luzes brigando. Não tem rim light |
| Materiais e dobras | 10 | 5 | Pedi camisa de botão e veio jaqueta camuflada/manchada; não dá para ler nenhuma dobra |
| Composição e enquadramento | 10 | 8 | Cabeça no terço de cima, olhar para a esquerda com espaço para respirar. Boa |
| "Não parece amador" | 10 | 6 | O rosto convence; a roupa entrega o "filtro de pixelização" |

Rubrica = 645 / 10 = **64,5**

## NOTA FINAL = 0,4 × 99,8 + 0,6 × 64,5 = **78,6** — **REFAZER**
(Abaixo de 95 e com 7 critérios abaixo de 8.)

## Contradições com o personagem (receita 5.2)
1. **Bigode** cinza em x 34–48, y 62–66 (#b4b0b4, #c3c0c1, #5b5d7a). O Geraldo é barbeado.
2. **Corpo magro**: pescoço estreito (x 40–55, y 72–90) e rosto chupado. Ele deveria ter ombros largos e massa.
3. **Roupa**: jaqueta de lona/camuflada com camiseta azul por baixo, quando o pedido era camisa de botão lisa com gola de 1–2 px.
4. Mancha azul-cinza na bochecha/costeleta direita (x 56–62, y 50–60) parece barba por fazer.

## Melhorias (da que mais sobe a nota para a que menos)
1. **Tirar o bigode (img2img + retoque).** Negativo: `mustache, moustache, beard, stubble, facial hair, goatee`. Positivo: `clean-shaven smooth upper lip`. Em código, pinte x 34–48, y 62–66 com a rampa da pele do lábio superior: #c79877 na luz, #a0614e na meia-sombra e #814c44 na fresta embaixo do nariz. Faça o mesmo com o cinza na costeleta (x 56–62, y 50–60), trocando por #b57a60/#a0614e.
2. **Roupa: camisa de botão em 3–4 blocos (img2img com força 0,45–0,55 só no busto, y ≥ 74).** Prompt: `plain light-blue button-up shirt, open collar, flat cel shading, large simple folds`; negativo: `jacket, camouflage, pattern, texture, noise, mottled`. Depois, em código, quantize a área y 74–128 para 4 tons de uma só rampa (ex.: #313450 / #5b5d7a / #737287 / #a2a0a6, ou uma rampa bege). Feche 2–3 dobras diagonais grandes por lado, tipo o tecido da ref 22, e faça a gola de 1–2 px escuro + 1 px claro. Vale também um filtro de moda 3x3 para matar os órfãos dessa área.
3. **Massa do corpo.** No prompt, use `broad shoulders, thick neck, heavyset, wide torso filling the frame` e coloque `thin, skinny, gaunt` no negativo. Se for por código, alargue o pescoço para x 36–60 com sombra #5c343a do lado da sombra. Os ombros devem chegar às bordas x 4 e x 92 na altura y ~88 (ref 5: corpo como massa).
4. **Uma luz só + rim light.** Escolha a luz quente da esquerda, que já ilumina o rosto, e escureça o ombro direito (x 65–95, y 85–128) dois degraus na rampa. Coloque 1 px de rim frio (#8e8c96 ou #a2a0a6) no contorno direito do cabelo, da orelha (x 64–70, y 46–62) e do ombro. Do lado da luz, ponha 1 px coral (#d9b291 → um coral tipo #e08a5a) no topo do cabelo à esquerda e no ombro esquerdo (refs 22 e 14: duas temperaturas).
5. **Testa sem rugas de foto.** As listras alternadas em x 30–55, y 30–42 viram 2 blocos: luz #e7caac no alto e #c79877 perto das sobrancelhas. Deixe no máximo 1 ruga de 1 px #a0614e. No img2img, adicione `smooth forehead, few wrinkles` e `deep wrinkles, photo-realistic skin` no negativo.
6. **Um destaque de cor.** Um único acento saturado e pequeno: botão ou bolso da camisa de 1–2 px, ou o rim coral do item 4. Hoje a paleta é toda dessaturada, sem ponto focal de cor (ref 1: o fogo é o único acento).
7. **Pontinho de luz no topo do cabelo.** O ponto claro em x 39–46, y 18 sai da silhueta e parece um defeito; alinhe ao contorno do crânio (troque por #554b53 ou uma linha contínua de #b4b0b4).
8. **Olho esquerdo do retrato (x 30–36, y 48–52).** Mantenha um traço de 1–2 px escuro dentro da sombra da sobrancelha, e o olho direito (x 46–54, y 48–50) no mesmo peso, sem ponto claro de íris (receita 5.2.3, ref 22: sobrancelha e olho num traço só, inclinado, para o rosto sério).
