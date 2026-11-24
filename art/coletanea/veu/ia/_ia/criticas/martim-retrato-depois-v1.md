# Crítica — martim-retrato-depois — volta 1

Arte: `out/ia/prova/martim-retrato-depois/martim-retrato-depois.json` (96x128, tipo retrato)
Folha: `out/estilo/comparar/martim-retrato-depois_comparar.png`
Refs mais próximas (técnica): 11, 19, 21. Refs guia do personagem: 21, 11, 10.

## Nota técnica: 98,5
Fora da faixa: proporção 2,26 cabeças (faixa 2,75–4,52; nota 0,66) e dithering 0,001 (mínimo 0,0012).
A nota técnica é alta porque as estatísticas de paleta/blocos batem, mas o desenho em si não segue o estilo.

## Rubrica visual
| critério | peso | nota | observação |
|---|---|---|---|
| silhueta e leitura | 10 | 6 | massa do capuz lê bem; mancha preta do pescoço (x 60–70, y 70–100) funde capuz, gola e camiseta |
| proporção e pose | 10 | 5 | 3/4 bom, mas pescoço longo (y 68–95) e rosto de adulto: lê 20+ anos, não 12 |
| rosto (discreto, sem olho de anime) | 10 | 3 | rosto fotográfico: íris com esclera, olheiras, sulco nasolabial, barba por fazer no queixo |
| sombreamento em blocos | 15 | 4 | ruído de foto no rosto e no moletom; pontos claros soltos (57,30), (67,42); sem blocos planejados |
| paleta contida + 1 destaque, sombra fria/luz quente | 10 | 5 | 24 cores ok, mas 2 destaques competindo (verde + roxo #6f438c); moletom VERDE, não cinza; cabelo #774045 ruivo |
| contorno seletivo | 5 | 6 | contorno escuro existe por acaso (sombra), não por escolha; rosto direito sem borda |
| luz e rim light | 10 | 5 | luz da direita no rosto coerente, mas sem rim no capuz/ombro; capuz quase uniforme |
| materiais e dobras | 10 | 5 | moletom com riscos de textura, não dobras; capuz sem borda interna/externa; cordões ok |
| composição e enquadramento | 10 | 7 | busto bem enquadrado, cabeça no terço; orelha solta no capuz (x 31–34, y 42–52) quebra a leitura |
| "não parece amador" | 10 | 4 | parece foto pixelizada, não pixel art desenhada; ao lado das refs 21/11 destoa muito |

**Rubrica: 49,0**

## NOTA FINAL: 0,4 × 98,5 + 0,6 × 49,0 = **68,8**

## Veredito: REFAZER

Contradições com o briefing do Martim (receita 5.1):
- **Capuz levantado** cobrindo a cabeça (x 22–64, y 8–95); a receita pede capuz abaixado como colar ~18×6–7 px atrás do pescoço.
- **Moletom verde** (#3f6137/#2d503a; capuz #5d695f verde-acinzentado) em vez de cinza; camiseta roxa vira um 2º destaque.
- **Cabelo ruivo-marrom** (#774045, y 11–25) e liso, não escuro crespo na máquina.
- **Idade aparente ~20–25**: rosto largo e ossudo, olheiras, barba, pescoço comprido.

## Melhorias (da que mais sobe a nota para a que menos)
1. **Refazer o img2img com força alta (0,65–0,75) e prompt corrigido**: "12-year-old boy, small thin child, narrow face, round childlike cheeks, short dark kinky hair buzz cut, thick eyebrows, plain GRAY hoodie with hood DOWN around neck, flat colors, pixel art, cel shading". Negativo: "hood up, hood over head, adult, man, stubble, beard, eye bags, wrinkles, realistic, photo, green, purple, red hair, detailed iris". Sem isso as demais correções são remendo (ref 21 para a lógica do moletom; receita 5.1).
2. **Rosto 12 anos, olho discreto** (se retocar em código): olhos em (55–58,41) e (71–74,41) viram traço de 2–3×1 px #161520 sem esclera nem branco; apague olheiras y 43–45; nariz = 1 px de sombra em ~(68,50); boca 2 px em (68–69,58); queixo y 60–66 limpo, sem a barba #a85656/#90484c salpicada. Ref 11 e 21.
3. **Sombreamento em blocos no rosto**: reduza a pele a 3–4 tons (#ebb29a luz, #dc9382 meio, #bc6b68 sombra, #774045 só no oclusão) e redesenhe em 3 áreas: luz à direita (x 62–77), meio-tom, sombra à esquerda (x 45–55) com borda limpa; elimine pixels soltos #d9cac3 em (57,30) e (67,42). Ref 21 (rosto em 3 blocos).
4. **Paleta do moletom para cinza**: remapeie #3f6137→#6e6f78, #2d503a→#4a4b57, #283f3b/#233337→#2e2f3d, #5d695f→#8a8a92 (cinza com sombra fria azulada); remova o roxo #6f438c da camiseta (x 60–70, y 112–127) ou troque por um único destaque coerente (ex.: estampa ~8×10 px no peito). Receita 5.1 item 3.
5. **Cabelo escuro crespo**: #774045 → rampa #1e202c/#2e2a36/#3d334d, topo y 11–25 em tufos curtos de 1–2 px (corte na máquina), sem pele vazando nas falhas em (62–78,18–22). Ref 21 (tufos com ponta).
6. **Pescoço e gola**: encurte o pescoço (base do queixo de y≈68 para ~66 e gola começando em ~y 80) e quebre a mancha #100d16 de x 60–70, y 70–100 em sombra de colo projetada pelo capuz-colar (2 tons, não preto chapado). Receita 5.1 item 6.
7. **Remover a orelha solta** em (31–34, 42–52) pintada sobre o capuz; se o capuz ficar abaixado, a orelha vai junto da face em ~(46–48, 44–50).
8. **Rim light e contorno seletivo**: 1 px quente (#ebb29a ou bege do fundo clareado) no contorno do ombro direito e do capuz/colar do lado da luz, 3–4 pontos; contorno 1 px #161520 só onde a roupa clara encosta no fundo. Ref 21 e 10.
