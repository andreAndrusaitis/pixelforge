# Estilo PixelForge — faixas, receitas e erros

Consolidação das 33 análises em `analises/<n>.md` (números de `estilo analisar` +
leitura visual). Medidas em **px nativos** (depois de desfazer a grade). Referências
citadas como "ref N" (índice em [referencias.json](referencias.json)). Este arquivo é
o manual de construção; o [guia-visual.md](guia-visual.md) é o checklist curto.

---

## 1. O que é o Estilo PixelForge

Pixel **pintado em blocos**: massas grandes e decididas (blocos médios de 3–10 px,
dithering ≈ 0), poucas cores (18–50 efetivas) quase todas dessaturadas, e **uma cor
dona** que aparece em menos de 1–2% da área como destaque puro. O valor faz o
trabalho: figura e fundo se separam por claro × escuro, e o contorno é **seletivo**
(70–98% da borda sem linha; onde existe, é vinho/marinho, não preto). Toda luz tem
**fonte visível** (chama, lanterna, cristal, sol) e chega à figura como **rim light de
1 px** só nas bordas que veem a fonte. As rampas giram de matiz (sombra fria/violeta,
luz quente). Rostos são **discretos**: traço de 1–3 px, órbita vazia, máscara ou
sombra de aba — nunca olho de anime. A expressão vem de pose, silhueta e luz.

---

## 2. Faixas por tipo

Como ler: cada célula é **p10–p90 (mediana)** das referências daquele tipo, medido por
`estilo analisar`. É a **régua do `estilo comparar`**: arte nova fora da faixa não está
"errada" por si, mas o crítico deve pedir justificativa (ex.: cena noturna com
contraste fora da faixa de propósito). "Retrato" tem só 2 refs (4 e 10); use as
receitas da seção 3.1 e os números dessas duas análises (rosto ~30 px de largura,
6 tons de pele, contraste ~0,79, dithering só no fundo).

| Métrica | retrato | personagem | cenario | cena |
|---|---|---|---|---|
| cores efetivas | — | 21–48 (med 25) | 25–75 (med 54) | 18–66 (med 38) |
| croma média | — | 0.01–0.05 (med 0.03) | 0.04–0.09 (med 0.07) | 0.02–0.09 (med 0.06) |
| variação de matiz nas rampas (°) | — | 13–70 (med 54) | 10–60 (med 18) | 12–67 (med 20) |
| tons por rampa | — | 2.80–7.67 (med 4.25) | 6.10–9.53 (med 7.78) | 3.97–9.23 (med 5.50) |
| níveis de valor | — | 11–19 (med 15) | 13–16 (med 16) | 11–16 (med 14) |
| densidade de detalhe | — | 0.38–0.91 (med 0.82) | 0.61–0.80 (med 0.69) | 0.56–0.84 (med 0.69) |
| contraste de valor | — | 0.46–0.85 (med 0.67) | 0.58–0.69 (med 0.61) | 0.49–0.71 (med 0.59) |
| desvio de valor | — | 0.14–0.28 (med 0.22) | 0.19–0.22 (med 0.20) | 0.16–0.24 (med 0.20) |
| tamanho médio dos blocos (px) | — | 2.25–9.41 (med 3.89) | 3.64–8.45 (med 4.95) | 3.47–9.64 (med 4.79) |
| pixels órfãos | — | 0.08–0.35 (med 0.18) | 0.09–0.20 (med 0.15) | 0.07–0.20 (med 0.15) |
| dithering | — | 0.00–0.00 (med 0.00) | 0.00–0.01 (med 0.01) | 0.00–0.01 (med 0.01) |
| contorno escuro | — | 0.02–0.57 (med 0.16) | — | — |
| contorno ausente (seletivo) | — | 0.43–0.98 (med 0.83) | — | — |
| luz de borda (rim light) | — | 0.00–0.50 (med 0.13) | — | — |
| força da direção de luz | — | 0.01–0.09 (med 0.02) | 0.02–0.12 (med 0.03) | 0.00–0.12 (med 0.04) |
| espaço negativo | — | 0.39–0.62 (med 0.53) | 0.15–0.34 (med 0.21) | 0.12–0.44 (med 0.24) |
| foco × terços | — | 0.13–0.19 (med 0.16) | 0.13–0.17 (med 0.16) | 0.12–0.17 (med 0.16) |
| proporção (cabeças) | — | 2.75–4.52 (med 3.72) | — | — |
| altura da figura (px) | — | 87–140 (med 116) | — | — |

Notas de leitura:
- **Pixels órfãos** medem textura pintada *e* ruído. O teto prático para a nossa arte é
  ~0,20; acima disso, só se for pelo/folhagem/partícula intencional (ver seção 7).
- **Proporção (cabeças)** do detector conta capuz/chapéu/cabelo volumoso como cabeça;
  por isso a mediana (3,7) sai menor que a proporção visual (5–6,5 nas refs 1, 10, 11,
  21). Para humanos, mire 5–7 cabeças a olho; chibi (refs 8, 31) fica em 2,3–3.
- **Força da direção de luz** é sempre baixa nas refs (gradiente global fraco): a luz
  delas é local (rim, halo), não um degradê de lado a lado. Ver seção 8.
- Criaturas (refs 6, 18) não entram na tabela; use as faixas de "personagem".

---

## 3. Receitas de construção

### 3.1 Rosto (sem olho de anime)
Escolha **uma** solução por personagem:
- **Traço sob a franja** (refs 21, 22, 1, 11): olho = traço horizontal de **2–3 × 1 px**
  (ou 1–2 px em cabeça < 10 px), marrom/vinho escuro, **nunca preto puro, sem brilho
  branco, sem íris**. A borda de cima do olho é coberta pelas pontas da franja; o olho
  do lado da sombra quase some. Sobrancelha + olho podem virar **um único traço
  inclinado** para o centro = carranca (ref 22).
- **Sombra da franja/aba** (refs 1, 21, 9, 14, 31): logo abaixo das pontas do cabelo,
  **1–2 px de pele um tom mais escuro** atravessando testa e linha dos olhos. Com
  chapéu/elmo: aba clara de 1–2 px em cima, faixa escura de 2–3 px embaixo, e o rosto
  vira **um ponto de 2–3 px** de pele tocada pela luz (ref 14) ou 2 × 2 px claro na
  sombra do elmo (ref 33).
- **Buraco/máscara** (refs 2, 7, 8, 16, 25, 28): capuz com interior preto (4×8 a
  12×10 px); se precisar de olhos, 2 quadrados de 2×2 px claros na metade de baixo do
  buraco, 4 px de separação (ref 8). Máscara clara 6×9 px com fendas verticais de 1 px
  (ref 2); viseira com 3–4 frestas de 1 px (ref 25) ou grade de furos de 1 px (ref 28).
  Órbitas vazias de 3×4 px para crânio (refs 6, 17, 32).
- **Rosto escondido / de costas** (refs 15, 20, 24, 29): cabeça como massa de cabelo em
  2–3 tons + halo de 1 px de rim; no máximo uma fatia de bochecha/orelha de ~3×5 px
  indicando para onde olha.
- **Nariz**: 1 px de sombra do lado oposto à luz, ou nada. **Boca**: 1–2 px escuro-
  rosado; em retrato (ref 4) 5×3 px em 3 tons com 1 px de brilho no lábio inferior.
- **Bochecha**: 1–2 px rosados sob os olhos (refs 10, 11), opcional.
- **Retrato de busto** (refs 4, 10): rosto ~30 px de largura, olhos na linha do terço
  superior; pele em 5–6 tons com sombra indo para vinho, sombras **só nos vãos**
  (franja, lateral do nariz, lábio inferior, queixo, pescoço). Mesmo em busto o olho
  fica pequeno: óculos/lente fazem o trabalho (lente ~10×6 px, íris 3×4, 1 px de
  brilho no máximo — ref 10); dithering só no fundo.
- **Expressão**: postura da cabeça + franja + boca curta. Se for para mostrar emoção,
  mova a cabeça e as mãos, não aumente o olho.

### 3.2 Cabelo em tufos
1. 4–5 tons com hue shift (ruivo: vinho → ferrugem → laranja → pêssego; refs 10, 21).
2. Desenhe **8–12 tufos de 2–4 px de largura** terminando em **ponta de 1 px**; base
   escura (raiz, nuca), ponta clara do lado da luz (ref 21).
3. Silhueta: 8–10 pontas saindo do contorno em direções diferentes, 1 "antena" de ~4 px
   no topo, pontas sobre orelhas e nuca; mechas longas em S de 2–4 px (ref 10).
4. Brilho em **grupos de 1–3 px** no topo e no lado da luz — **nunca faixa contínua**
   ("anel de anjo").
5. Fios soltos de 1 px nas pontas quebrando a silhueta (refs 10, 11); mechas voando
   separadas por **ar** (fundo entre elas — ref 16).
6. Cabelo escuro: 3 tons de preto-azulado/arroxeado, brilho roxo-azulado, não branco
   (refs 11, 22).

### 3.3 Pano e dobras (formas grandes)
1. Cada peça = **2–4 dobras grandes** (blocos de 3–6 px, ou faixas de 2–4 px × 20–40 px
   em mantos longos), nunca rugas paralelas finas (refs 1, 7, 14, 21, 28).
2. Tons: 3 no tecido escuro, 4–6 no tecido de cor; o **interior/avesso sempre no tom
   mais escuro** (dá espessura — refs 1, 11, 28).
3. Sombra principal = um **bloco escuro contínuo** (interior do casaco, vão entre capa e
   corpo), ~6×12 px numa figura de 85 px (ref 1).
4. Barra rasgada: dentes/tiras de **2–8 px** com ponta de 1 px, **todas na mesma
   direção** (vento coerente — refs 2, 6, 22).
5. Peso: calça larga acumula no tornozelo em 3–4 dobras horizontais de 3–5 px, mais
   largas que a perna (ref 21). Pano pesado/felpudo: hachura de traços de 2–4 px
   inclinados na direção da queda (ref 5).
6. Estampa: 6–8 motivos de 3–6 px espaçados, alguns cortados pela dobra; padrão denso
   só numa faixa (bainha — ref 12).

### 3.4 Preto que não é preto
1. Roupa preta = **4–5 tons de preto-azulado** (~#121218 a #4a4a58); dobras como
   diagonais longas de 1–2 px em cinza-chumbo (ref 10).
2. Contorno "escuro" = vinho/marinho/ameixa (refs 1, 21, 20), não #000.
3. Preto puro só onde é **buraco** (interior do capuz, viseira, órbita — refs 8, 16),
   para os brilhos ao lado ganharem força.
4. Preto encostado em fundo escuro ganha **1 px de rim** frio ou da cor do fundo (refs
   4, 10).

### 3.5 Metal
1. 4–6 tons; cada placa = tom base + **1 px escuro embaixo** + **1 px claro na aresta de
   cima** + **2–4 px brancos** no ponto mais alto da curva (refs 16, 25, 28).
2. Armadura laminada: pilhas de retângulos de 2–4 px, cada um com 1 linha escura
   embaixo (ref 3); faixas horizontais de 2 px alternando claro/escuro (ref 9).
3. Ouro: só amarelo + ocre/laranja, **traços de 1 px** com o pixel claro sempre do lado
   de cima (refs 3, 28); joia/colar: 3 tons + brilhos de 1 px isolados (ref 6).
4. Lâmina: 4 tons, fio de 1 px claro, canaleta escura no centro (refs 5, 19).
5. Lustroso escuro (luva, couro polido): preto + grafite + brilho de 1–2 px **frio** nos
   nós (ref 4). Metal se distingue de pano por croma levemente maior e brilho pontual,
   não por textura.

### 3.6 Pele
1. 3 tons em personagem (90–140 px), 5–6 em retrato.
2. Sombra **quente** (rosa-vinho, #bb626c-ish), nunca cinza ou marrom sujo (refs 11, 22,
   4); aplique o rosado em joelhos, cotovelos, dedos, laterais.
3. Sem contorno no maxilar: a troca para o tom escuro marca a forma (ref 21).
4. Pele costuma ser o **valor mais alto** de uma figura escura; use isso como foco
   (ref 22). Pele tocada por fonte colorida recebe a cor da fonte (lente laranja na
   bochecha — ref 4; chama — ref 1).

### 3.7 Rim light (uma e duas temperaturas)
- **Uma temperatura** (refs 1, 8, 14, 27, 33): 1 px (às vezes 2) **na cor da fonte**,
  só nas bordas que veem a fonte — topo da cabeça, ombro, manga, arestas de cima. O
  lado oposto fica sem rim e sem contorno claro: **a assimetria é o que vende a fonte**.
  Repita o mesmo traço numa quina do cenário (chão, beiral) para amarrar (ref 8).
- **Duas temperaturas** (ref 22): quente (coral/laranja) do lado da luz principal, fria
  (azul-violeta) do lado oposto, ambas 1 px; elimine o contorno preto onde há rim.
- **Rim refletido do fundo** (ref 10): bordas escuras recebem 1 px da cor do fundo
  (lavanda) — conecta figura e ambiente.
- **Borda de luz larga** (ref 20): 2 px do tom mais claro + 1 px intermediário por
  dentro, só na borda de ataque.
- Rim é **pontual**: em personagem com luz suave, 3–4 pontos do lado da luz bastam
  (ref 21). Em contraluz, rim só onde o fundo atrás é claro (ref 30).

### 3.8 Luz motivada por fonte visível + halo
1. Ponha a fonte **dentro do quadro**, num terço superior ou fora da massa da figura
   (refs 1, 2, 6, 14).
2. Chama: núcleo branco-amarelo 2–3 px (3×3) → anel amarelo → anel laranja → pontas
   vermelhas; 8–12 brasas de 1 px subindo (refs 1, 8).
3. Lanterna: núcleo 2×4 a 4×4 px, armação de 1–2 px desenhada, chaminhas de 1–2 px
   escapando (refs 2, 6).
4. Cristal/gema: núcleo ~5×5 quase branco na cor fria, forma interna em 2 tons, **halo
   como disco chapado de 1–2 tons** (~20 px — ref 14), nunca degradê suave. Gemas
   pequenas: núcleo claro de 1–2 px + borda escura (ref 31).
5. Estrela mágica: núcleo 4×4 branco + raios em cruz de 1 px (ref 17); brilhos de 4
   pontas com braços de 2–4 px (ref 31).
6. A fonte **tinge** o que toca: mão que segura fica âmbar, manga ganha patch de 3–5 px
   da cor da luz (refs 1, 6); o fundo atrás clareia 1 tom em mancha, não degradê (ref 8);
   em parede, leque de faixas de 1 tom + rachaduras de 1 px irradiando (ref 14).
7. Uma fonte quente num mundo frio (ou o contrário) — refs 2, 8, 26.

### 3.9 Céu em faixas e anéis
1. **Faixas horizontais**: 4–6 faixas de uma família, 2–14 px de altura cada, mais
   claro no horizonte do lado da luz (refs 23, 27, 33, 19).
2. **Anéis concêntricos** em volta do ponto de luz (sol, clarão, nebulosa): faixas de
   2–6 px com borda em degraus de 1–3 px (refs 13, 30).
3. Fronteiras **onduladas em degraus de 1–2 px**, interpenetrando; nunca dithering,
   nunca gradiente liso (ref 27). Dithering xadrez de 1–2 linhas só em fundo escuro de
   retrato (ref 4).
4. Hue shift ao longo do céu (~30–40°): magenta → coral → salmão → pêssego → creme
   (ref 27); azul-cinza → creme (ref 23).
5. Cirros: riscos de 1 px, 8–30 px de comprimento, mais claros, na altura do sol ou
   inclinados (refs 24, 27, 33). Estrelas: 4–6 px únicos no alto; grandes em cruz de
   5 px (refs 27, 30).

### 3.10 Nuvens
- **Em blocos com borda em escada** (degraus de 1–3 px), sem contorno, 4–5 tons; o lado
  voltado à luz clareia 1 tom (ref 13).
- **Contra a luz** (pôr do sol): nuvem **mais escura e mais saturada que o céu atrás**;
  borda de baixo iluminada (laranja), de cima rosa (ref 27).
- **Cúmulo** de dia: bolhas de 10–25 px, topo claro, base na cor do céu (sombra
  colorida, nunca cinza); bolhas de baixo menores e mais frias (ref 24).
- **Estratos**: faixas de 1–3 px de altura, 15–30 px de comprimento, claras com borda
  inferior quente (ref 33).
- Uma nuvem fina atravessando o disco do sol faz o sol "afundar" (ref 27).

### 3.11 Reflexo quebrado
1. Espelhe a silhueta, **escureça 2 tons** e puxe para a cor do fundo/céu (mais fria).
2. Corte em **tiras horizontais de 1–2 px**, comprimentos diferentes, **deslocadas 1–3 px**
   lateralmente; entre as tiras, faixas do céu refletido (refs 23, 2).
3. Luzes quentes refletem como **colunas verticais curtas** de 2–4 px (ref 23); faixa de
   1–2 px clara logo abaixo do horizonte (ref 13).
4. Chão de estúdio: linha de 1 px + reflexo invertido desbotado (~40% no tom do fundo,
   10–14 px visíveis — ref 16).

### 3.12 Névoa e perspectiva atmosférica
1. Monte a rampa de profundidade: **perto = escuro e mais saturado/azul-marinho; longe =
   mais claro, menos contraste, puxado para a cor do céu** (refs 26, 27, 32).
2. Dê a cada plano um **valor fixo** (4–5 planos). Ex. inverno (ref 26): #111534 →
   #182b50 → #233d5d → #5f95c5 → #6fa4d6 → neve #ecfbf6. Ex. pôr do sol (ref 27):
   malva #623a4e → névoa #59354e → casas #253458 → floresta #0c1d37 → #021732.
3. **Uma faixa de névoa clara de 3–5 px** entre o plano médio e o fundo, apagando a base
   do que está atrás (refs 23, 26, 27). Base de coisa enorme dissolvida em névoa clara
   (ref 29).
4. Distância por matiz em dia claro: verde → verde-azulado → ciano (ref 24).
5. Névoa como forma: manchas sem contorno, com buracos (ref 6), borda em blocos de
   2–4 px (ref 29).

### 3.13 Moldura de silhueta
1. Massa escura em 1–2 lados, altura total ou canto (árvore, coluna, folhagem), quase
   preta e fria (refs 23, 26, 27, 29).
2. Borda **interna** (virada para a luz) rendilhada: pixels soltos e buracos de céu de
   1 px — a silhueta respira (refs 23, 27); borda externa toca o limite da tela.
3. Feche também embaixo (folhagem quente-escura no canto inferior — ref 27).
4. Moldura dentro da moldura: arco/porta/véu com 50–65% da largura (refs 15, 4).
5. Moldura saturada (folhas vermelhas) em cenário dessaturado: profundidade por
   temperatura (ref 23).

### 3.14 Partículas (vaga-lumes, brasas, neve)
- **Onde pôr**: só **sobre áreas escuras** (floresta, frente de casas, folhagem), nunca
  no céu claro; longe da silhueta do foco, sem encostar nela (refs 27, 31).
- **Quantas**: 8–12 por tela; uma ou duas por região, **espaçadas 15–30 px**, sem grade.
- **Perspectiva**: tamanho cresce para baixo/para a frente — no fundo só núcleo de 1 px,
  no primeiro plano 1 px de núcleo + halo de 1–2 px mais escuro (ref 27).
- **Brasas**: 1 px laranja/vermelho subindo em diagonal acima da fonte (ref 8).
- **Neve**: pixels únicos ~1 a cada 15×15 px, mais visíveis sobre o escuro, alguns de
  2 px; **e** 1 px branco em todo topo horizontal (ref 26).
- **Desintegração** (magia, pano): parta da forma sólida, tire pixels da borda e espalhe
  1–2 px se afastando, densidade caindo a cada 2–3 px (ref 25 — só a ideia).
- Magia em uma cor só, sempre em pixels de 1–3 px (ref 17).

### 3.15 Escala (figura pequena × massa grande)
1. Massa grande em **2–4 tons próximos, sem textura**, recortada contra o claro (refs
   29, 30).
2. Figura pequena (~1/2,5 da altura da ameaça, ou 20% da largura) **sobre o ponto mais
   claro** e com o **maior contraste local** (lâmina branca, roupa clara — refs 29, 30).
3. Cor complementar na figura pequena: laranja contra azul/verde (ref 24).
4. De costas, olhando para o espaço aberto (refs 24, 29, 15).
5. Corte a coisa grande pela moldura (asas/planeta saindo do quadro — refs 20, 30) e
   dissolva a base em névoa (ref 29).
6. Figura minúscula escura na vertical do foco dá escala a paisagem (barco de 12×3 px —
   ref 23).

### 3.16 Cor-assinatura / destaque único
1. **Uma** cor saturada por arte, em ≤1–2% da área como tom puro (refs 1, 9, 22: 0,2–0,7%).
2. Repita-a em **3 pontos** para criar caminho de leitura (cabeça → cintura → pés; lente →
   cordão → bochecha — refs 4, 9, 12).
3. Um pixel **complementar** como ponto de vida: 1 px ciano no elmo vermelho (ref 3),
   olho ciano no crânio quente (ref 18), olhos quentes na massa fria (ref 29).
4. Rima de cor/símbolo: verde do olho = verde da roupa (ref 12); emblema repetido no
   estandarte e na manta (ref 33); céu rosa → flores rosa no chão (ref 29).
5. Em cenário, a cor-tema pode ocupar 5–12% (céu coral — refs 27, 29), mas aí todo o
   resto vem dela ou da sua complementar escura.

### 3.17 Paleta por famílias com hue shift
1. Defina **2–3 famílias** (ex.: dentro quente × fora saturado — ref 15; rosa × violeta —
   ref 29; ameixa/malva/creme — ref 20) + 1 destaque.
2. Por material, uma família própria com 3–5 tons (osso = creme, carne = laranja, pelo
   = marrom-roxo — ref 18); diferencie material por **número de tons** (tecido escuro 3,
   tecido de cor 6 — ref 21) e por **tamanho do bloco** (ref 3).
3. **Hue shift**: sombra para vinho/roxo/azul, luz para laranja/creme; personagem gira
   ~50–65° por rampa (refs 1, 21), cenário 10–40° (refs 23, 27).
4. Total: personagem ~25 cores, cena ~38, cenário ~54 (seção 2); 7–11 cores também
   funcionam (refs 3, 14).
5. Teste em preto e branco: precisa de **3 massas de valor** distintas (ref 24).

---

## 4. Receita: rua de casas baixas em Goiânia, fim de tarde depois da chuva

Base: ref 27 (contraluz, céu em faixas, rim nas cumeeiras, vaga-lumes), ref 23 (reflexo
quebrado, névoa entre planos) e ref 13 (silhueta sobre clarão, faixa clara sob o
horizonte, poucas cores em duas famílias). Tela 640×360 do projeto → trabalhe em
**~320×180 nativos** (×2) ou 213×120 (×3); números abaixo para 320×180.

1. **Divisão de valor**: céu claro nos ~40% de cima; rua e casas escuras embaixo; a
   faixa de transição é a névoa/ar úmido. Horizonte (linha de telhados do fundo) em
   y≈70–80. Duas zonas de valor (ref 27), não meio-termo espalhado.
2. **Paleta**: família quente do céu (magenta-rosado → coral → salmão → laranja → creme)
   + família fria das silhuetas (malva → azul-ardósia → marinho → quase preto azulado).
   Destaque único: o laranja do sol/janelas. ~35–45 cores.
3. **Céu**: 5–6 faixas horizontais de 6–14 px, fronteiras onduladas em degraus de
   1–2 px; laranja mais intenso perto do sol, que fica baixo, logo acima dos telhados,
   parcialmente coberto (disco ~20–30 px, núcleo creme #fefdb2-ish, anel de 4–6 px).
   Depois da chuva: 2–3 faixas de nuvem ainda pesadas no alto, **mais escuras e mais
   saturadas que o céu**, borda de baixo acesa em laranja (ref 27); estratos finos de
   1–2 px × 15–30 px perto do sol (ref 33); clarão em anéis atrás do sol se a nuvem abrir
   uma janela (ref 13).
4. **Planos de silhueta** (cada um com valor fixo, mais perto = mais escuro e azul):
   (a) caixa-d'água, antena, copas de mangueira/ipê ao fundo em malva-rosado;
   (b) faixa de névoa úmida rosa-lilás de 3–5 px apagando a base delas;
   (c) casas baixas de um pavimento em azul-ardósia: muro + portão, telhado de duas
       águas em faixas de 1 px (telha), platibanda reta em algumas;
   (d) postes, fios, árvore de calçada em marinho;
   (e) primeiro plano quase preto (muro, carro estacionado, folhagem).
5. **Rim light rosa-coral de 1 px** só nas arestas viradas para o sol: cumeeiras,
   beirais, topo de muros e de postes, topo da cabeça de quem estiver na rua. Nunca nas
   fachadas frontais nem nas bases (contraluz coerente).
6. **Fios de poste**: linhas de 1 px escuras em catenária, cruzando o céu — dão escala e
   "cidade" sem detalhe; 1 px de rim por cima em trechos.
7. **Chão molhado e poças**: asfalto em 2–3 tons escuros; cada poça é uma forma
   horizontal achatada (ex. 20–50 × 3–8 px) que reflete **o céu**, não a rua: copie as
   faixas do céu correspondentes, 1–2 tons mais escuras, em **tiras horizontais de
   1–2 px deslocadas 1–3 px** (ref 23). Silhuetas de casas/poste refletidas na poça
   escurecidas e quebradas; janelas/luzes refletem como colunas verticais curtas de
   2–4 px. Uma faixa clara de 1 px na borda da poça mais próxima do sol (ref 13). Meio-
   fio molhado com 1 px de brilho no topo.
8. **Sinais de vida**: janelas pequenas (2×3 px) refletindo o céu em azul-acinzentado;
   no máximo 1–3 janelas quentes começando a acender; luz de poste ainda fraca (núcleo
   2–3 px + halo chapado de 1 tom); fumaça de uma chaminé ou churrasqueira em pixels
   esparsos lilás (ref 27).
9. **Moldura**: árvore ou muro alto escuro de um lado, poste do outro; folhagem quente-
   escura num canto de baixo.
10. **Partículas**: depois da chuva, em vez de vaga-lumes no céu, 6–10 gotas/brilhos de
    1 px sobre áreas escuras (folhas, beiral pingando), ou insetos laranja de 1 px com
    halo perto do poste — só sobre o escuro, maiores no primeiro plano.
11. **Personagens na rua** (se houver): silhuetas escuras com rim de 1 px no topo da
    cabeça e ombros, rosto sem detalhe; o protagonista no ponto de maior contraste,
    contra a parte mais clara do céu ou da poça.

---

## 5. Receitas de personagem

### 5.1 Martim, 12 anos, de moletom (guia: ref 21; apoio 11 e 10)
1. **Tamanho e proporção**: corpo inteiro ~100–110 px (é criança: um pouco menor que os
   114 px da ref 21) em cena 640×360 nativa, ou ~110 em folha 72×128; **~5,5 cabeças**
   (cabeça com cabelo ~19–20 px; rosto visível ~12×9 px).
2. **Pose**: frente com leve 3/4, peso numa perna, um pé virado para fora, ombros
   caídos; mão no bolso do moletom ou solta (ref 21; contrapposto da ref 10).
3. **Paleta** (lógica da ref 21, cores do Martim): uma cor de destaque com 5–6 tons (no
   moletom ou no capuz) + neutro escuro com 3 tons (calça/corpo) + neutro claro com 3
   tons (cordões, cinto, sola) + pele em 3 tons com sombra rosada. Fundo liso claro e
   quente nas folhas de referência.
4. **Cabelo**: 4–5 tons; 8–12 tufos de 2–4 px com ponta de 1 px, base escura, pontas
   claras do lado da luz; 1 antena no topo; sem faixa de brilho.
5. **Rosto**: franja com 3–4 pontas até a linha dos olhos e uma mecha central até o
   nariz; **1–2 px de sombra de pele** abaixo; olhos = **traço de 2–3 × 1 px** marrom-
   escuro, borda de cima coberta, o do lado da sombra quase oculto; nariz 1 px; boca
   2 px; 1–2 px de bochecha rosada opcional (ref 11). Expressão de 12 anos vem da
   cabeça (levemente baixa ou erguida), não do olho.
6. **Moletom**: corpo em 3 tons; **capuz abaixado** como "colar" de ~18 × 6–7 px atrás do
   pescoço, borda interna escura e externa clara, projetando sombra no colo; **2 cordões
   de 1 px** de 6–8 px; estampa de ~8 × 10 px no peito; 2 dobras grandes no tronco (ombro
   → cintura), 1–2 por manga; ribana de 1 px na barra e no punho; manga arregaçada se
   couber.
7. **Calça**: reta, 3–4 dobras horizontais de 3–5 px acumuladas no tornozelo, mais
   largas que a perna. Tênis com sola clara de 1–2 px (ponto claro da base — ref 10).
8. **Contorno**: 1 px preto-azulado, omitido onde o material escuro já encosta no fundo.
   **Rim** de 1 px na cor quente da luz da cena em 3–4 pontos do lado da luz (ombro,
   manga, borda do tênis); em cena de fim de tarde, rim rosa-coral no topo do cabelo.
9. **Escala reduzida** (cena aberta, 40–60 px): mantenha só silhueta do cabelo, capuz,
   1 px de olho ou nenhum, destaque de cor no moletom (refs 19, 10).

### 5.2 Seu Geraldo, ~2 m, chapéu de feltro (refs 14, 1, 22; apoio 5, 9, 28)
1. **Tamanho**: sendo ~2 m ao lado de um menino de 12 anos, **~1,35–1,4× a altura do
   Martim** (Martim ~105 px → Geraldo ~140–145 px), ~7 cabeças; ombros largos, base
   larga (pés afastados), corpo como massa (ref 5: "escala usada para massa").
2. **Chapéu de feltro**: copa de 3 tons; **aba clara de 1–2 px em cima, faixa escura de
   2–3 px embaixo** (ref 14, 31). Fita da copa 1–2 px mais escura. Aba ~1,3–1,5× a largura
   da cabeça.
3. **Rosto sob a aba** (ref 14): o terço de cima do rosto em sombra; olhos = traço de
   1–2 px escuro dentro da sombra (ou omitidos); **um ponto de pele de 2–3 px** tocado
   pela luz (nariz/maçã do rosto), repetido na mão. Sobrancelha + olho como um traço
   inclinado se ele estiver sério (ref 22). Bigode/barba, se houver: listras de 1 px ou
   bloco de 2 tons.
4. **Camisa de manga dobrada**: 3–4 tons, 2–3 dobras grandes por lado; manga dobrada =
   bloco de 3–4 px mais claro na borda de cima com 1 px escuro embaixo, acima do
   cotovelo; antebraço à mostra em pele de 3 tons (sombra quente). Gola: 1–2 px.
   Sombra principal: bloco escuro sob o peito/ao lado do tronco no lado oposto à luz.
5. **Mãos grandes**: ~1,5× o tamanho "normal" para a figura (ex. 7–8 × 8–9 px), dedos em
   blocos separados por 1 px de sombra (ref 1), nó dos dedos com 1 px claro; a palma do
   lado da luz é a área de pele mais clara depois do rosto (ref 1, 22). Mãos penduradas
   ou segurando algo dão o peso.
6. **Calça e botina**: calça em 2–3 tons, joelho com 1 px de destaque (ref 1); botina
   marrom-escura em 2–3 tons, cano curto, 1 px de brilho na biqueira, sola mais escura
   e um pouco mais larga (peso).
7. **Rim light** (ref 22, 14): em fim de tarde, 1 px coral/laranja no topo da aba, no
   ombro e no braço do lado do sol; do outro lado, se houver céu azul, 1 px frio
   (duas temperaturas). Costas no escuro, sem contorno.
8. **Paleta**: terrosa e dessaturada (feltro marrom/cinza, camisa clara gasta, calça
   escura), com **um** destaque pequeno (lenço, fita do chapéu ou cinto) — refs 7, 9.
9. **Dupla com o Martim**: o grande escuro e largo, o pequeno com a cor de destaque;
   ponha a cabeça do Martim na altura do peito/ombro do Geraldo e deixe o maior
   contraste local no menino (seção 3.15).

---

## 6. Erros que denunciam arte amadora

| # | Erro | Conserto |
|---|---|---|
| 1 | Olho de anime (íris grande, brilho duplo, cílios) | Traço de 2–3×1 px escuro sob a franja, ou buraco/máscara/sombra de aba (3.1) |
| 2 | Contorno preto contínuo em tudo | Contorno seletivo: vinho/marinho só onde formas se fundem; rim de cor no lado da luz (3.4, 3.7) |
| 3 | Pillow shading (sombra em volta, luz no centro) | Uma direção de luz; sombra principal num bloco do lado oposto (3.3) |
| 4 | Degradê liso / dithering em pele e roupa | Faixas de 2–6 px em degraus; dithering só em fundo de retrato (3.9) |
| 5 | Rampa que só escurece a mesma cor | Hue shift: sombra para vinho/roxo/azul, luz para laranja/creme (3.17) |
| 6 | Cores saturadas por toda parte | Base dessaturada + uma cor dona ≤1–2% repetida em 3 pontos (3.16) |
| 7 | Dobras como linhas paralelas finas | 2–4 formas grandes por peça; avesso no tom mais escuro (3.3) |
| 8 | Preto chapado #000 em roupa escura | 4–5 tons azulados; #000 só em buracos (3.4) |
| 9 | Brilho sem fonte (rim em volta de tudo) | Rim só nas bordas que veem a fonte; lado oposto sem rim (3.7, 3.8) |
| 10 | Halo em degradê suave/blur | Disco chapado de 1–2 tons, ou mancha 1 tom mais clara (3.8) |
| 11 | Cabelo como capacete com faixa de brilho | Tufos de 2–4 px com ponta de 1 px; brilho em grupos de 1–3 px (3.2) |
| 12 | Reflexo como espelho perfeito | Escurecer 2 tons, esfriar, cortar em tiras de 1–2 px deslocadas (3.11) |
| 13 | Céu em gradiente de ruído | 4–6 faixas com fronteira em degraus; nuvens em blocos (3.9, 3.10) |
| 14 | Fundo tão detalhado quanto a figura | Detalhe concentrado no foco; fundo liso ou em faixas largas (refs 2, 15, 19) |
| 15 | Distante tão escuro e contrastado quanto o perto | Rampa de profundidade com valor fixo por plano + faixa de névoa (3.12) |
| 16 | Partículas espalhadas em grade ou sobre o céu | 8–12, só sobre o escuro, espaçadas 15–30 px, maiores à frente (3.14) |
| 17 | Pixels soltos/ruído por toda parte | Órfãos ≤ ~0,20, só em pelo/folhagem/partícula; blocos ≥3–4 px nas áreas grandes |
| 18 | Pose de boneco em T, simétrica | Contrapposto, peso numa perna, assimetrias pequenas (refs 10, 11, 21) |
| 19 | Silhueta que não lê em escala 1 | Extremidades marcadas (chapéu, cabelo, arma, capa); teste a silhueta chapada (refs 3, 33) |
| 20 | Rosto detalhado demais em cabeça pequena | Abaixo de ~10 px de cabeça: 1 px de olho ou nenhum; expressão pela pose (refs 19, 29) |

---

## 7. O que NÃO copiar das refs

Algumas referências são boas em **composição, valor e cor**, mas têm marcas de imagem
gerada por IA ou reamostrada. Delas, copie a ideia, nunca a textura:

- **Ref 17** (necromante): 29% de órfãos, grade irregular (confiança 1,35), 73 cores
  quase duplicadas, fumaça da base feita de ruído. Copiar: silhueta de 2 valores,
  rosto mínimo, cor só na magia.
- **Ref 24** (menino no penhasco): textura de tecido sobre os pixels, bordas suaves,
  23% de órfãos, grama ruidosa, grade de confiança 0. Copiar: 3 massas de valor
  empilhadas, figura complementar pequena, sombra de nuvem colorida.
- **Ref 25** (cavaleiro vermelho): 43% de órfãos, blocos médios de 1,85 px, bordas
  "sujas". Copiar: uma cor + neutros, metal por arestas de 1 px, desintegração com
  densidade decrescente feita **pixel a pixel escolhido**.
- **Ref 31** (mago chibi): 253 cores totais, 44% de órfãos, clusters de 2 px. Copiar:
  proporção chibi, máscara com olhos sólidos, gemas em triângulo; limitar a 40–50
  cores e blocos ≥3 px.
- **Grade estimada**: nas refs 2, 6, 7, 10, 13, 19, 20, 24, 25, 26, 27, 28, 29, 31 e 33 a
  grade veio "por corridas" com confiança 0 (e a 17 tem confiança 1,35). Tamanhos em
  px dessas análises são **aproximados**; na ref 27, os detalhes finos (rim dos
  telhados, vaga-lumes) têm ~0,6 px da grade ×8 — trabalhe a ~140×250 para a mesma
  finura.
- Também não copie: textura pintada de 21–25% de órfãos (refs 5, 10, 21) como se fosse
  regra — ela vem de pinceladas direcionais; ruído aleatório não é a mesma coisa.
- Nada de nomes, emblemas, letreiros (ref 19) ou personagens das refs: só técnica.

---

## 8. Limitações conhecidas do detector (para o crítico ponderar)

- **Direção da luz medida errada** quando o valor global engana: ref 18 dá "baixo"
  (por causa das patas escuras; a luz real é cima-esquerda/frente) e ref 19 dá
  "baixo" (por causa do degradê do fundo; no personagem a luz é cima-frente). Também
  ref 4 ("baixo-esquerda", a real é frontal-superior), ref 30 ("baixo-esquerda", é
  contraluz) e refs com fonte interna (1, 6, 14) onde o gradiente global é fraco e a
  luz que manda é local. **A força da direção de luz é baixa em quase todas** — não
  reprove arte por força baixa; reprove por luz **incoerente** (rim do lado errado,
  fonte sem efeito).
- **Figura tomou o quadro** na ref 16: o detector mediu 126 px (quadro inteiro); a olho
  são ~82 px. O "luz de borda" de 86% medido lá é o fundo lavanda lido como borda, não
  rim. Desconfie de figura ≈ tamanho do quadro e de rim > 0,5 em fundo claro.
- **Grade estimada por corridas** (confiança 0) em 15 refs (lista na seção 7): tamanho
  nativo, tamanho de bloco e órfãos dessas refs são aproximados e puxam as faixas da
  seção 2 — sobretudo "cenario" (23–27 quase todas por corridas) e o teto de órfãos.
- **Proporção em cabeças** conta capuz, chapéu, cabelo volumoso e cachecol como cabeça
  (ref 22: 27 px medidos × ~15 px reais; ref 17: capuz 34 px × crânio 11 px). Confira a
  olho antes de cobrar proporção.
- **Destaque** mede só o tom mais puro: em cenas de cor-tema (refs 27, 29) ele sai 5–12%
  e é a cor do céu, não um acento; em refs 9, 14, 20, 26 o destaque real (pequeno
  demais) não é detectado.
- **Tipo** do índice nem sempre bate com a máscara (ref 28 personagem tratado como
  "cena"; ref 10 é folha busto + corpo). Compare com o tipo que a arte nova realmente é.
- **Cores totais** incluem ruído de compressão (webp/jpg); use sempre as **efetivas**.
