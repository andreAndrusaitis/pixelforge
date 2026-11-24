# Crítica — martim-corpo-r3-1 — volta 3

Arte: `out/ia/r3/martim-corpo-r3-1/martim-corpo-r3-1.json` (104x152, fundo transparente) · tipo **personagem**
Folha: `out/estilo/comparar/martim-corpo-r3-1_comparar.png` · refs mais próximas: 11, 1, 3

## Nota técnica: 91,6 (v2: 95,7)
Fora da faixa:
- proporção (cabeças) 6,89 (faixa 2,75–4,52; nota 0,13, peso 6). É uma métrica nova, que não aparecia nas voltas 1 e 2, e é ela que derruba a técnica.
- cores efetivas 16 (20,4–47,9)
- espaço negativo 0,747
- foco × terços 0,118
- dithering 0,0005

Contradição a resolver no estúdio: a receita 5.1 e a análise da ref 21 pedem ~5,4–5,5 cabeças, mas a faixa medida nas refs vai de 2,75 a 4,52. Pelo olho, esta figura tem ~5,6 cabeças (cabeça y17–39, figura y17–140), o que está dentro da receita. Mesmo assim, ela tem 123 px de altura, acima dos 100–110 da receita.

## O que melhorou desde a v2
- Proporção de criança sem chibi.
- Passada crível com mão no bolso.
- Moletom cinza em blocos limpos, com bolso canguru (y68–82).
- Destaque laranja #dd6d2c único e bem usado no forro do capuz e nos cordões (x52–64, y38–62), na lógica da ref 21.

## Rubrica visual

| Critério | Peso | Nota | Observação |
|---|---|---|---|
| Silhueta e leitura | 10 | 6 | O pior resto de fundo até agora: uma cunha lilás-cinza #9393a3 entre as pernas (x43–67, y106–133, ~400 px) mais uma sombra no chão #626071 (x27–84, y134–137) fecham o vão das pernas |
| Proporção e pose | 10 | 7 | ~5,6 cabeças e a passada lê bem; a figura de 123 px está alta para a receita (100–110); as pernas ficam arqueadas, com o joelho esquerdo para fora |
| Rosto (discreto, sem anime) | 10 | 6 | Olhos em traço de 1 px escuro: certo. Mas a sobrancelha grossa não aparece; a orelha é um bloco vermelho (x48–52, y29–35); a pele do pescoço tem ruído castanho |
| Sombreamento em blocos | 15 | 6 | O moletom está bom (3 blocos com dobra no braço). O short tem manchas castanhas (#8e6c70, #462b2c) sem lógica de dobra (x47–74, y85–105). A sombra da perna esquerda é um bloco vermelho-tijolo #7f3f3c chapado (x38–50, y106–125) |
| Paleta contida + destaque | 10 | 7 | Cinza + 1 laranja: certo. Mas o cabelo é castanho-avermelhado (#46272c/#26111d), a sombra da pele é saturada demais e há só 16 cores efetivas |
| Contorno seletivo | 5 | 7 | Bom no moletom; nos tênis vira xadrez preto-e-branco |
| Luz e rim light | 10 | 6 | O moletom tem lado claro à direita, mas o rosto e as pernas não seguem a mesma luz (perna esquerda quase toda em sombra vermelha); sem rim light |
| Materiais e dobras | 10 | 7 | Capuz, cordões e bolso funcionam; o short não lê como tecido (manchas); as meias brancas (y124–128) funcionam; o tênis é ruído xadrez |
| Composição / pose no quadro | 10 | 7 | Centrado (x23–84), com a passada dando diagonal; a sombra do chão vaza para a esquerda |
| Não parece amador | 10 | 6 | A cunha de fundo e o short manchado denunciam o recorte; o resto aguenta |

**Rubrica** = (6·10+7·10+6·10+6·15+7·10+7·5+6·10+7·10+7·10+6·10)/10 = **64,5**

## NOTA FINAL = 0,4·91,6 + 0,6·64,5 = **75,3** — **REFAZER**

## Contradições com o briefing
- O cabelo é **castanho e liso, penteado de lado**, e não escuro e crespo na máquina. É uma regressão em relação à v2.
- A sobrancelha grossa não aparece.
- O short é uma escolha nova (não vem do briefing original, que pedia moletom e tênis gasto). Ele só serve se o autor quiser; hoje ele tem a mesma cor do fundo.

## Restos de fundo
- **#9393a3** (794 px no total). Entre as pernas, em x43–67, y106–133, é fundo puro. **Atenção:** o short (x47–74, y85–105) usa a mesma cor, então a limpeza não pode ser só por cor; use uma máscara de região (y ≥ 106 entre as pernas) ou um flood fill a partir do vão.
- **#626071** na sombra do chão: x27–84, y134–137.
- Pixels soltos de #9393a3 na cabeça: (48,19) e (50–51,37).

## Melhorias (da que mais sobe a nota para a que menos)
1. **Limpar a cunha** (código):
   - Faça um flood fill transparente a partir de (55,120) sobre #9393a3/#626071, limitado a y ≥ 106. Remova também a faixa y134–137 fora dos tênis (x27–42 e x46–66).
   - Contorne as bordas internas das pernas com 1 px de #26111d.
   - Silhueta e "não parece amador" sobem de 6 para 8.
2. **Cabelo escuro e crespo na máquina:**
   - Por img2img (força 0,35–0,45, máscara só na cabeça y15–32): prompt "very short dark coily hair, buzz cut, thick eyebrows"; negativo "straight hair, side swept hair, brown hair, bangs".
   - Ou por retoque: troque #46272c→#2a1c22, #26111d→#160e14 e #8e6c70 do cabelo→#4a3a40; deixe a silhueta redonda, a 2 px do crânio, com borda irregular de 1 px.
   - Acrescente uma sobrancelha de 3x1 px #26111d acima de cada olho, 1 px acima do traço.
   - Refs 21 e 10.
3. **Short separado do fundo** (paleta, x47–74, y85–105):
   - Use um cinza-azulado escuro (#3d4256/#555a70/#6e7388) ou um jeans, diferente de #9393a3.
   - Troque as manchas castanhas por 2 dobras: uma vertical na virilha e uma diagonal na barra.
   - Ou volte à calça marinho da v2, se o autor não pediu short.
4. **Pele das pernas** (x38–50, y106–125, e x66–76, y104–124):
   - Troque o bloco #7f3f3c por uma rampa de 3 tons coerente com o rosto (#f6c9b9 / #d1887f / #a3605e).
   - A sombra deve ficar só no lado oposto à luz (2–3 px de largura) e no joelho, não na perna inteira.
   - A sombra violácea fica em ≤ 2 px (ref 21: pele em 3 tons).
5. **Orelha e pescoço** (código): a orelha (x48–52, y29–35) passa a pele média, com 1 px de sombra rosada. O pescoço (x53–60, y36–41) fica em 1 tom de sombra liso sob o queixo, sem ruído castanho.
6. **Tênis gastos** (x34–46, y128–140 e x66–84, y128–138):
   - Tire o xadrez: cabedal cinza-escuro em 2 tons, sola creme suja contínua de 1 px (#d8cfc6) e cadarço com 1 px laranja.
   - Esse laranja repete o destaque, como a bota da ref 21.
7. **Altura e enquadramento:**
   - Reduza a figura para ~108 px (escala 0,88 com vizinho mais próximo antes da pixelização, ou "smaller figure" no img2img).
   - Suba-a para que o pé fique em y≈130.
   - A sombra do chão vira uma elipse de 1 tom de ~28x2 px sob os pés, ou some.
8. **Rim light quente** (código): 3–4 px de #dd6d2c ou de pêssego no ombro direito (x64–66, y44–50), na manga direita e na borda do tênis direito. Isso amarra a luz e o destaque (ref 21).
