# Crítica — geraldo-corpo-depois — volta 1

Arte: `out/ia/prova/geraldo-corpo-depois/geraldo-corpo-depois.json` (104x152, tipo personagem, via IA SDXL + LoRA + pixelização)
Folha de comparação: `out/estilo/comparar/geraldo-corpo-depois_comparar.png`
Referências mais próximas (métrica): 11, 21, 1 · guias da receita 5.2: 14, 1, 22

## Nota técnica: 95.1

Fora da faixa:
- proporção 7,37 cabeças (faixa 2,75–4,52) — **ignorar**: a receita 5.2 pede ~7 cabeças; a faixa vem de refs mais estilizadas.
- espaço negativo 0,683 (faixa 0,39–0,62) — figura estreita no quadro (bbox x 31–77).
- altura 140 px (teto 139,4) — ok pela receita (140–145).
- dithering 0,0007 — irrelevante.

A nota técnica está alta porque as estatísticas (contagem de cores, tamanho médio de bloco, órfãos) estão na faixa; o olho, não.

## Rubrica visual

| Critério | Peso | Nota | Observação |
|---|---|---|---|
| Silhueta e leitura | 10 | 6 | Lê "velho grande", mas a silhueta é pera: ombros 25 px (x 43–68, y 38) contra barriga 44 px (x 32–76, y 68). Braço esquerdo some na massa escura (x 32–37, y 55–72). Pernas fundidas. |
| Proporção e pose | 10 | 5 | ~7 cabeças ok, mas contradiz "ombros largos" e "base larga": pés juntos/cruzados (x 36–68, y 137–147), corpo inclinado para trás. |
| Rosto | 10 | 6 | Sem olho de anime (bom; faixa escura y=20). Mas sem sombra de aba no terço de cima, e bloco claro em (46–50, 26–28) lê como **bigode branco** — contradiz "barbeado". Testa com mancha clara (45–49, 17–19). |
| Sombreamento em blocos | 15 | 4 | Textura "sal e pimenta" da IA em camisa (x 54–75, y 40–72), calça (x 35–73, y 74–120) e botinas; muitos órfãos, nenhuma forma grande em degraus. |
| Paleta contida + destaque, sombra fria/luz quente | 10 | 6 | Terrosa e dessaturada (ok), sombras azuladas #2d333b/#363a40 (ok). Sem destaque pequeno único; a calça ferrugem (#984d40/#a36252) é área grande, não "brim escuro". Chapéu creme, não feltro marrom. |
| Contorno seletivo | 5 | 7 | Contorno #141522 parcial, ausente em parte do lado da luz — aceitável; mas engole o braço esquerdo. |
| Luz e rim light | 10 | 5 | Luz vem da esquerda (rosto e barriga claros), sombra à direita coerente. Nenhum rim de 1 px em aba/ombro/braço. |
| Materiais e dobras | 10 | 4 | Feltro não lê (parece boné/chapéu de palha claro); camisa não lê como "de botão" — aberta, mostrando barriga/camiseta creme; sem manga dobrada; calça sem dobras; **barra cinza vertical** (x 56–58, y 125–140) entre as botinas é artefato. |
| Composição e pose no quadro | 10 | 7 | Centrado, altura certa, margem de 8 px em cima e 4 em baixo. Inclinação para trás deixa o peso "caindo". |
| Não parece amador | 10 | 4 | Lado a lado com as refs 1 e 22, entrega-se como IA pixelizada: ruído, braço faltando, mão sem dedos, artefato na perna. |

**Rubrica** = 525 / 10 = **52,5**

## NOTA FINAL = 0,4 × 95,1 + 0,6 × 52,5 = **69,5**

## Veredito: **REFAZER**

## Melhorias (da que mais sobe a nota para a que menos)

1. **Limpar o ruído em blocos (sombreamento 4→7)** — em código: filtro de moda 3x3 por rampa (ou "mesclar órfãos ao vizinho majoritário") na camisa (x 54–75, y 40–72), calça (x 35–73, y 74–120) e botinas (x 35–68, y 122–147); depois reduzir cada peça a 3 tons (luz/meio/sombra) por limiar de valor. Alvo: blocos de 3–6 px como na ref 1 (casaco vermelho em 3 massas). No img2img: negativo `noisy, grainy, texture noise, dithering, jpeg artifacts`, força 0,35–0,45 para manter a pose.
2. **Camisa de botão fechada com manga dobrada (materiais 4→7)** — a área creme (x 37–54, y 44–70) lê como barriga à mostra. Prompt: `buttoned work shirt, light beige shirt fully closed, rolled sleeves above elbow, visible button line`; negativo `open shirt, exposed belly, undershirt, jacket`. Em código: repintar o creme com a rampa da camisa e pôr linha de botões de 1 px em x≈50, y 38–72; sombra principal num bloco escuro à direita (x 62–75). Manga dobrada no braço direito: bloco de 3–4 px mais claro em y≈66–69 com 1 px escuro em y=70, acima do antebraço (x 67–74) — receita 5.2 §4.
3. **Ombros largos e braço esquerdo (silhueta 6→8, proporção 5→7)** — img2img com `broad shoulders, both arms hanging at sides, wide stance, feet apart`, negativo `narrow shoulders, leaning back, crossed legs`, força 0,5. Alvo: ombros ≥ 34 px (x 38–72 em y 38) e barriga logo abaixo, não mais larga que os ombros + 6 px. Braço esquerdo visível em x 31–37, y 42–76 com mão na lateral (y 76–88), separada do tronco por 1 px de fundo — como os dois braços soltos da ref 1.
4. **Chapéu de feltro marrom (materiais, paleta)** — hoje creme #ede9dd/#e3d1b2 (x 41–60, y 8–14). Remapear essas cores para rampa de feltro marrom-acinzentado 3 tons (ex. #8a6a52 / #6a4b49 / #3b2a2e); aba de x 38–63 (≈1,4× a cabeça), 1 px claro em cima (y 12) e faixa escura 2 px embaixo (y 13–14); fita 1 px escura em y 11 — receita 5.2 §2, ref 14. Prompt: `brown felt fedora, wide brim`, negativo `cap, straw hat, white hat`.
5. **Rosto barbeado sob a aba (rosto 6→8)** — trocar o bloco claro do bigode (46–50, 26–28) por pele média/sombra (#b27961/#a36252); escurecer o terço de cima do rosto (x 43–58, y 15–19) com a sombra da aba (#6a4b49 sobre #553f47), deixando 2–3 px claros só no nariz/maçã (≈ 48–50, 22–23) — ref 14. Olhos: manter 1–2 px escuros dentro da sombra.
6. **Calça de brim escura (paleta 6→8)** — remapear a rampa ferrugem (#984d40, #a36252, #853e38, #ac5343, #6d3032) para azul-acinzentado escuro de brim em 3 tons (#2d333b / #454f5c / #627374), joelho com 1 px de luz (≈ 44,102 e 62,104), 2–3 dobras horizontais no tornozelo (y 115–122) — ref 1 (meia escura com 1 px de luz), ref 22 (calça azul em 3 tons). Isso libera o vermelho para **um** destaque pequeno (fita do chapéu ou lenço no pescoço, x 47–55, y 31–33).
7. **Mão grande com dedos (materiais)** — mão direita (x 66–73, y 76–94) é um bloco esticado sem dedos. Encurtar para 8×9 px (x 66–73, y 84–92), 3 divisões de 1 px de sombra entre dedos, 1 px claro no nó; palma do lado da luz mais clara depois do rosto — ref 1 (mão estendida), ref 22 (punho). Repetir na mão esquerda do item 3.
8. **Artefatos e rim** — apagar a barra cinza #5a5b58 (x 56–58, y 125–140) pintando com o escuro da botina; botinas em 2–3 tons marrom-escuros, sola 1 px mais escura e mais larga, 1 px de brilho na biqueira (≈ 39,141 e 64,145). Rim de 1 px quente (#c79373) no topo da aba (y 12, x 40–48), no ombro esquerdo (x 38–42, y 38–41) e no braço do lado da luz — ref 22 (rim laranja), receita 5.2 §7.

Nota: a métrica "proporção (cabeças)" vai continuar fora da faixa com ~7 cabeças — é o pedido da receita; não persiga essa métrica.
