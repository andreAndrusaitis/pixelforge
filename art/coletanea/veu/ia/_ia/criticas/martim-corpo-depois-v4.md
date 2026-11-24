# Crítica — martim-corpo-v4 — volta 4

Arte: `out/ia/refino/martim-corpo-v4/martim-corpo-v4.json` (104x152, fundo transparente) · tipo **personagem**
Folha: `out/estilo/comparar/martim-corpo-v4_comparar.png` · refs mais próximas: 11, 1, 3

## Nota técnica: 91,8 (v3: 91,6)
Fora da faixa:
- proporção (cabeças) 6,89 (faixa 2,75–4,52; nota 0,13, peso 6). Continua o conflito com a receita 5.1, que pede ~5,5 cabeças; ver a v3.
- cores efetivas 17 (mínimo 20,4)
- espaço negativo 0,762
- foco × terços 0,115
- dithering 0,0007

## O que melhorou desde a v3
- A cunha de fundo entre as pernas e a sombra do chão saíram: de 794 px de #9393a3 para 28.
- O short em marinho #555a70/#3d4256 agora se separa do fundo e do moletom.
- As pernas em #d1887f/#bc726e ficaram coerentes com o rosto.
- O cabelo está escuro.
- O rim laranja no ombro direito (x65–67, y46–50) amarra a luz ao destaque.

## Rubrica visual

| Critério | Peso | Nota | Observação |
|---|---|---|---|
| Silhueta e leitura | 10 | 7 | O vão das pernas abriu. Sobram 28 px de #9393a3 soltos nas bordas das pernas e dos tênis, e um "dente" de short abaixo da virilha (x55–62, y102–105), que é o topo da cunha antiga (o flood fill parou em y106) recolorido como short |
| Proporção e pose | 10 | 7 | ~5,6 cabeças, a passada é boa; a figura tem 123 px, acima dos 100–110 (não foi reduzida) |
| Rosto (discreto, sem anime) | 10 | 6 | Olhos em traço: certo. A sobrancelha grossa continua ausente. A orelha (x48–53, y29–35) ainda tem pixels cinza-malva. O pescoço (x53–58, y39–45) tem ruído #8e6c70/#7f3f3c |
| Sombreamento em blocos | 15 | 7 | O moletom está bom. O short recolorido ainda carrega o ruído de manchas da v3 (1 px alternando #555a70/#3d4256/#62526e, x47–74, y85–105) em vez de 2 dobras. A perna esquerda ganhou blocos de luz e sombra aceitáveis |
| Paleta contida + destaque | 10 | 7 | Cinza + marinho + 1 laranja: certo. Ficou uma mancha lilás-avermelhada #8e6c70/#7f3f3c no topo do cabelo (x55–64, y17–23), lida como brilho rosado; e só 17 cores efetivas |
| Contorno seletivo | 5 | 7 | Bom no corpo; os tênis continuam em xadrez |
| Luz e rim light | 10 | 7 | O rim no ombro funciona; falta rim na manga, no tênis direito e na borda direita da perna |
| Materiais e dobras | 10 | 7 | Capuz, cordões, bolso e meias funcionam. Os tênis (x34–46, y128–140 e x66–84, y128–138) seguem como ruído preto, branco e lilás: não leem como tênis gasto |
| Composição / pose no quadro | 10 | 7 | Centrado, com a passada em diagonal; a figura está alta no quadro |
| Não parece amador | 10 | 7 | Já se sustenta de longe. De perto, os tênis, os pixels soltos e o cabelo liso de lado entregam a origem |

**Rubrica** = (7·10+7·10+6·10+7·15+7·10+7·5+7·10+7·10+7·10+7·10)/10 = **69,0**

## NOTA FINAL = 0,4·91,8 + 0,6·69,0 = **78,1** — **REFAZER**

## Contradições com o briefing
- O cabelo está escuro, mas continua **liso e penteado de lado**, com franja de topete. Não é crespo cortado na máquina.
- Falta a sobrancelha grossa.

## Restos de fundo
- #9393a3 (28 px): (37,120), (73,123), (69,125), (73,125), (35,128), (41,128), (34,130), (78,132), (33,133), (67,134), (76,135), (83,135), (36,136), (68–69,136), (75,136), (37,138), (39–40,138), (46,139).
- #626071 (5 px): (37,124), (73–75,128), (76,130), (38–39,131).
- Topo da cunha antiga recolorido como short: x55–62, y102–105, abaixo da sombra da virilha.

## Melhorias (da que mais sobe a nota para a que menos)
1. **Tênis gastos** (código, x34–46, y128–140 e x66–84, y128–138). É o maior defeito que sobrou e o que mais pesa em materiais e amador.
   - Redesenhe em blocos: cabedal em 2 tons de cinza-escuro (#3d4256/#555a70, que são os tons do short).
   - Biqueira e sola creme suja contínua de 1–2 px (#d8cfc6, com sombra #a89e96 na traseira).
   - Contorno #160e14, 1 px de cadarço #dd6d2c e 1–2 px de desgaste claro na ponta.
   - Ref 21 (bota em blocos com 1 px claro na sola).
2. **Sobrancelha + cabelo crespo** (retoque na cabeça, x46–66, y15–30):
   - Sobrancelha de 3x1 px #160e14 1 px acima de cada olho.
   - Troque a mancha #8e6c70/#7f3f3c do topo (x55–64, y17–23) por #2a1c22, com pontas #4a3a40 de 1 px só na borda direita.
   - Arredonde o topete: tire os pixels que passam de 2 px do crânio.
   - Quebre a borda em 1 px irregular (textura crespa).
   - Por img2img com máscara na cabeça, força 0,35: "short dark coily hair, buzz cut, thick eyebrows"; negativo "straight hair, side swept".
3. **Limpeza fina** (código):
   - Os 33 px soltos listados acima (#9393a3/#626071) viram transparentes, ou a cor de contorno vizinha se estiverem dentro da borda.
   - Em x55–62, y102–105, apague o "dente": transparente abaixo da linha da virilha, com 1 px #160e14 de contorno interno.
4. **Short em 2 dobras** (x47–74, y85–105): substitua o ruído de 1 px por 3 blocos:
   - luz #555a70 à direita;
   - meio #3d4256;
   - sombra #2a2d3e na virilha e numa diagonal da coxa esquerda até a barra.
   - Barra com 1 px mais escuro.
5. **Reduzir a altura para ~108 px:** escala 0,88 por vizinho mais próximo na bruta antes de pixelizar, ou nova geração com "small boy". Assim a figura volta à receita 5.1; ajuste o pé para y≈130.
6. **Orelha e pescoço:**
   - Orelha (x48–53, y29–35) em #e9a898 com 1 px #bc726e no fundo.
   - Pescoço (x53–58, y39–45) num só tom #bc726e, sem #8e6c70.
7. **Rim light completo:** 1 px #dd6d2c ou pêssego #f6c9b9 em 3 pontos a mais: manga direita (x68–70, y60–70), borda direita da canela direita (x75–76, y108–120) e lateral do tênis direito. Isso firma a luz de cima-direita (ref 21).
8. **Mais tons onde faltam:** use 1 tom intermediário no moletom (entre #626071 e #93939f) e 1 na pele (#e9a898) para chegar a ≥ 20 cores efetivas sem degradê.
