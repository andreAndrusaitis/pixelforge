# Crítica — geraldo-corpo (v2) — volta 2

Arte: `out/ia/refino/geraldo-corpo-v2/geraldo-corpo-v2.json` (104x152, tipo personagem; 1 de 4 seeds + filtro de moda 3x3 em y 40–150)
Folha de comparação: `out/estilo/comparar/geraldo-corpo-v2_comparar.png`
Referências mais próximas (métrica): 3, 1, 18 · guias da receita 5.2: 14, 1, 22
Crítica anterior: `out/criticas/geraldo-corpo-depois-v1.md` (69,5)

## Nota técnica: 91.5 (caiu de 95.1)

Fora da faixa:
- **cores efetivas 16** (faixa 20–48), nota 0,65 peso 10 — paleta pobre demais; pele e camiseta vermelha dividem a mesma rampa.
- tons por rampa 2,67 (mín. 2,8) e pixels órfãos 0,074 (mín. 0,077) — o filtro de moda passou um pouco do ponto.
- proporção 7,15 cabeças — **ignorar** (receita 5.2 pede ~7).
- altura 143 px (teto 139,4) — ok pela receita (140–145).
- espaço negativo 0,687 — figura estreita no quadro (bbox x 30–79).

## O que melhorou desde a v1
Ombros largos (34 px, x 37–71 em y 36–40), chapéu com aba clara em cima (y 13) e faixa escura embaixo (y 14–16), rosto barbeado, dois braços, calça jeans azul-acinzentada, camisa bege com manga dobrada (x 68–78, y 58–62), blocos maiores na camisa.

## Rubrica visual

| Critério | Peso | Nota | Observação |
|---|---|---|---|
| Silhueta e leitura | 10 | 7 | Lê "homem alto de chapéu". Mas a perna direita tem **buraco transparente** em x 57–62, y 88–106 (sobra só um fiapo em x 62–65), e as pernas são finas para o tronco. |
| Proporção e pose | 10 | 6 | ~7 cabeças e ombros largos ok. **Sem barriga** (tronco reto, x 36–75). Pernas finas (≈10 px cada), base estreita (pés x 38–65), mãos pequenas: a esquerda tem ~5×8 px em (34–39, 86–95). |
| Rosto | 10 | 7 | Barbeado e olhos pequenos (bom). O traço dos olhos em y 17 (x 47–55), com pixel claro no meio, lê como **óculos**. Rosto todo claro #f0c9bd, sem o terço de cima em sombra de aba (ref 14). |
| Sombreamento em blocos | 15 | 6 | Camisa já em blocos, mas manchas aleatórias que não seguem dobra. Jeans ainda manchado (x 40–65, y 72–140), sem lado de luz nem de sombra. |
| Paleta contida + destaque | 10 | 6 | Só 16 cores. O vermelho #c4655e/#db8680 da camiseta (x 46–54, y 44–63) ocupa ~7% da figura (destaque deveria ser ≤1–2%) e é a **mesma rampa da pele**: a mão direita em (63–72, 60–72) some no vermelho. Copa do chapéu bege-rosado, não feltro marrom/cinza. |
| Contorno seletivo | 5 | 7 | Escuro #1c1020 nas bordas de sombra e ausente no lado da luz (ok). |
| Luz e rim light | 10 | 6 | Luz de cima e da esquerda coerente na camisa e no rosto. Nenhum rim de 1 px. |
| Materiais e dobras | 10 | 5 | Camisa **aberta** sobre camiseta: lê como jaqueta, não "camisa de botão". Jeans sem dobras no tornozelo. Botinas minúsculas (≈8×6 px). **Barra cinza #787b81** entre as pernas (x 50–54, y 103–141) é o fundo da bruta preenchido. |
| Composição e pose no quadro | 10 | 7 | Centrado, altura certa, sombra de chão (x 30–70, y 143–147) assenta a figura. |
| Não parece amador | 10 | 5 | Buraco na perna e barra cinza denunciam o processo. Do resto, já se aproxima mais da ref 1. |

**Rubrica** = 615 / 10 = **61,5**

## NOTA FINAL = 0,4 × 91,5 + 0,6 × 61,5 = **73,5** (v1: 69,5)

## Veredito: **REFAZER**

## Melhorias (da que mais sobe a nota para a que menos)

1. **Consertar as pernas (silhueta, não amador, materiais)**: em código, preencher o buraco transparente em x 57–62, y 88–106 com o jeans médio #4c5462, sombra #413f4d na borda externa (x 63–65) e contorno #1c1020 só em x 65. Trocar a barra cinza #787b81 em x 50–54, y 103–141 pela sombra entre as pernas: #2b2e3f, com 1 px #1c1020 no centro (x 52). As duas pernas ficam separadas por um vão escuro, não por uma faixa clara. Ref 1: pernas escuras separadas.
2. **Encolher o destaque vermelho e separá-lo da pele (paleta 6→8)**: repintar a camiseta (x 46–54, y 44–63) com a rampa bege da camisa, como se estivesse **abotoada**: linha de botões de 1 px #725b5c em x 50, y 36–62, com 5 pontos claros #f0c9bd a cada 5 px. Deixar o vermelho só num lenço no pescoço em (47–55, 30–33) ou na fita do chapéu, em (46–59, 12). Tirar o vermelho da rampa da pele: para a camiseta ou o lenço, um vermelho mais frio e escuro (#9a3a44 / #6d2a36); para a pele, sombra #b0706a. Assim a contagem de cores sobe para 18–20. Refs 7 e 9 (destaque pequeno) e receita 5.2 §8. Para img2img, prompt "fully buttoned shirt, red neckerchief" e negativo "open shirt, t-shirt, jacket".
3. **Barriga (proporção 6→8)**: img2img com força 0,35 e prompt "big round belly, heavyset", ou retoque à mão: estufar a frente da camisa 2–3 px para a direita em y 48–62 (borda de x 71 para x 73–74). Pôr uma sombra em arco #725b5c sob a barriga, em y 60–63 (x 46–66), e o cinto #1c1020 em y 63–65 acompanhando a curva, mais baixo no centro. Ref 5 ("massa").
4. **Jeans em 3 blocos com lado da luz (sombreamento 6→8)**: em cada perna, coluna clara #787b81 de 3–4 px no lado da luz (perna esquerda em x 41–44, perna direita em x 55–58), meio #4c5462 no centro e sombra #413f4d de 2–3 px no lado oposto. Joelho com 1 px claro em (43,104) e (57,106). Duas ou três dobras horizontais de 3–5 px acumuladas no tornozelo (y 130–138). Rodar o filtro de moda **por perna** e não na roupa toda, para não comer tons. Refs 1 e 22.
5. **Rosto sob a aba sem óculos (rosto 7→8,5)**: trocar o traço em y 17 (x 47–55) por dois traços separados de 2 px, #4d2131, em (47–48, 17) e (52–53, 17), com o pixel do meio em pele de sombra #9a4a51. Escurecer as linhas y 15–17 (x 45–57) com #9a4a51 como sombra da aba e deixar 2–3 px claros #f0c9bd só no nariz e na maçã (50–52, 19–20). Ref 14.
6. **Mãos grandes (proporção, materiais)**: mão esquerda de (34–39, 86–95) para ≈8×9 px em (32–40, 86–95). Três divisões de 1 px #9a4a51 entre os dedos (x 34, 36, 38, em y 91–95) e 1 px claro no nó (y 89). É a pele mais clara depois do rosto. Na mão direita no bolso, nó dos dedos de 1 px claro na borda do bolso, em (64–68, 66). Receita 5.2 §5 e ref 1.
7. **Botinas maiores e com peso (materiais)**: botinas em (37–48, 139–146) e (57–66, 139–146), com 2 px a mais para fora e 1–2 px de cano. Três tons de marrom-escuro (#4d2131 / #6d3741 / #9a4a51 em vez do rosado #c4655e), sola #1c1020 1 px mais larga e 1 px de brilho na biqueira, em (39,143) e (64,143). Receita 5.2 §6.
8. **Chapéu de feltro e rim light (paleta, luz)**: remapear a copa (x 46–59, y 5–12) de #f0c9bd/#c5a893 para feltro marrom-acinzentado (#90716b / #725b5c / #4d2131), mantendo a aba clara de 1 px em y 13. Rim quente de 1 px #db8680 (ou laranja da cena) no topo da aba (x 40–48, y 13), no ombro esquerdo (x 37–41, y 36–38) e no antebraço esquerdo (x 33, y 68–84). Do lado direito, sem rim. Refs 22 e 14, receita 5.2 §7.
