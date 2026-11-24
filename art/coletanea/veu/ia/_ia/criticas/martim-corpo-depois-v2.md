# Crítica — martim-corpo (v2) — volta 2

Arte: `out/ia/refino/martim-corpo-v2/martim-corpo-v2.json` (104x152, fundo transparente) · tipo **personagem**
Folha: `out/estilo/comparar/martim-corpo-v2_comparar.png` · refs mais próximas: 11, 1, 21

## Nota técnica: 95,7 (v1: 95,5)
Fora da faixa: cores efetivas 17 (faixa 20,4–47,9; nota 0,73, peso 10; o filtro de moda achatou a roupa) · espaço negativo 0,792 (0,387–0,622) · força da direção de luz 0,064 (0,096–0,540) · dithering 0,0005.

## O que melhorou desde a v1
- A identidade agora bate com o briefing: moletom cinza frio em 5 tons, jeans marinho, cabelo escuro, sobrancelha grossa (o traço escuro de cima, em y≈54), tênis acinzentados e gastos, mão no bolso.
- A cunha de fundo do quadril sumiu e a figura está centrada (bbox x32–73).

## Rubrica visual

| Critério | Peso | Nota | Observação |
|---|---|---|---|
| Silhueta e leitura | 10 | 7 | Lê como menino de moletom; mas há uma faixa de fundo bege #a39990 entre as pernas (x52–58, y121–141) e pixels bege soltos na borda do cabelo e do moletom |
| Proporção e pose | 10 | 5 | **Correção exagerada**: cabeça de ~34 px (y36–69) numa figura de 107 px (y36–142) dá ~3,1 cabeças, que é chibi. A receita 5.1 pede ~5,5 cabeças (cabeça de ~20 px, figura de 100–110 px). A pose de mão no bolso com peso numa perna está boa |
| Rosto (discreto, sem anime) | 10 | 6 | Olho em traço escuro sem brilho e sobrancelha grossa: certo. Mas o rosto é um bloco de pele #eabbac de ~20x18 px sem nariz, sem boca e sem sombra de cabelo; o maxilar ganhou contorno escuro grosso; há um pixel escuro na orelha (≈(57,63)) que parece brinco |
| Sombreamento em blocos | 15 | 6 | Moletom com bloco médio #7d7f88 grande e chapado, e "furos" pretos sem lógica de dobra (x59–62, y91–97); pele chapada; o filtro de moda deixou a calça em 2 blocos lisos |
| Paleta contida + destaque | 10 | 7 | Cinza + marinho + pele: certo, mas **sem destaque** (a receita pede 1 cor com 5–6 tons) e só 17 cores efetivas |
| Contorno seletivo | 5 | 7 | Contorno escuro-violeta bom no corpo; no rosto fica pesado |
| Luz e rim light | 10 | 5 | Não há lado claro definido (força de luz 0,064, fora da faixa); sem rim light |
| Materiais e dobras | 10 | 6 | Cordão de 1 px (x53, y78–88) e capuz atrás (x60–66, y70–80) funcionam; mancha branca sem função no peito (x46–48, y82–86); a calça não acumula no tornozelo |
| Composição / pose no quadro | 10 | 6 | Figura colada embaixo (y36–142), com 36 px vazios no topo; espaço negativo de 0,79; linha de chão de 1 px (y142, x34–73) |
| Não parece amador | 10 | 6 | O cabelo em espetos de 4–5 px parece de anime e não "crespo na máquina"; restos de fundo; o rosto chapado e enorme |

**Rubrica** = (7·10+5·10+6·10+6·15+7·10+7·5+5·10+6·10+6·10+6·10)/10 = **60,5**

## NOTA FINAL = 0,4·95,7 + 0,6·60,5 = **74,6** — **REFAZER**

## Restos de fundo na borda
- Bege #a39990 entre as pernas: x52–58, y121–141 (~70 px, a faixa vertical).
- Pixels soltos de #a39990: no cabelo em (40,40), (59,42), (65,44), (64–65,45), (35,46), (34,49), (33,51), (33,53), (39,55), (37,57), (39,59); na borda direita do moletom em (66–67, y49–59), (64,63), (66,85), (69,92), (68,97), (66,101); nos tênis em (44–46, y120–138) e (49–51,136).
- Creme #e7e2dd na lateral do peito, x46–48, y82–86 (não é cordão; o cordão é x53).

## Melhorias (da que mais sobe a nota para a que menos)
1. **Proporção de 5,5 cabeças** (img2img com força 0,5–0,6, ou nova seed): no prompt, troque "big head" por "slightly large head, 5.5 heads tall, child proportions" e ponha "chibi, super deformed, oversized head" no negativo. Meta: cabeça de ~20 px (cabelo incluso) e figura de ~105 px. Ref 21 (5,4 cabeças) e ref 10.
2. **Limpar o fundo** (código): torne transparente todo #a39990 e todo pixel com croma < 15 e valor > 140 fora dos cordões. Feche o vão entre as pernas (x52–58, y121–141) com 1 px de contorno #1c141d de cada lado. A mancha creme do peito (x46–48, y82–86) vira cinza-sombra #5f6069.
3. **Cabelo crespo na máquina** (img2img: "short tight coily hair, buzz cut, rounded hair silhouette"; negativo "spiky hair, anime hair, long strands"; ou retoque): silhueta arredondada a 2–4 px do crânio, sem espetos acima de y40. A textura sai de 1 px alternando #1c141d/#36262f/#42352f; pontas claras #78696e só do lado da luz, em grupos de 1–2 px (ref 21, sem faixa de brilho).
4. **Rosto em 3 tons + nariz e boca** (código, área x40–60, y50–70): sombra de cabelo de 2 px #c97f7f sob a linha do cabelo; o lado oposto à luz em #dd988f; 1 px de nariz em sombra; boca de 2 px #a95f62 ~3 px acima do queixo. Troque o contorno do maxilar de preto para a sombra da pele e tire o pixel escuro da orelha (≈57,63). Ref 21 (maxilar só por troca de tom).
5. **Luz definida no moletom** (código): luz de cima-direita. Lado direito do tronco e da manga (x60–68, y72–105) com 1 tom acima (#9b9da6); lado esquerdo em #5f6069. Substitua os furos pretos (x59–62, y91–97) por 2 dobras diagonais grandes, do ombro até o bolso, e ponha 3–4 px de rim light no ombro e na manga direita. Isso sobe a força de luz para a faixa. Ref 21.
6. **Destaque único** (paleta): 1 cor de destaque com 4–5 tons, por exemplo um laranja-ferrugem ou mostarda no forro do capuz (x60–66, y70–80) e nos cordões, ou nos cadarços e na sola do tênis. Isso devolve as cores efetivas para ≥ 20. Ref 21 (laranja em 6 tons sobre neutro).
7. **Calça sem achatamento** (código, x44–64, y110–132): o filtro de moda deixou 2 blocos lisos. Devolva 3 tons de marinho (#2c2d3a/#535366/#6a6c80), com 2–3 dobras horizontais grossas acumuladas no tornozelo (y126–132), mais largas que a perna. Aplique o filtro de moda só em janelas 2x2, não na área toda. Ref 21.
8. **Enquadramento** (código): suba a figura ~14 px (topo em y≈22, pé em y≈128) ou recorte o quadro; remova a linha de chão de y142 ou troque-a por uma elipse de 1 tom de ~26x2 px sob os pés.
