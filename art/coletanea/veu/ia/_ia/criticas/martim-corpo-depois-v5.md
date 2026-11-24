# Crítica — martim-corpo-v5 — volta 5

Arte: `out/ia/refino/martim-corpo-v5/martim-corpo-v5.json` (104x152, fundo transparente) · tipo **personagem**
Folha: `out/estilo/comparar/martim-corpo-v5_comparar.png` · refs mais próximas: 11, 1, 3

## Nota técnica: 94,0 (v4: 91,8)
Fora da faixa:
- proporção (cabeças) 6,89 (faixa 2,75–4,52; nota 0,13, peso 6). O conflito com a receita 5.1 (~5,5 cabeças) continua aberto.
- espaço negativo 0,763
- foco × terços 0,124
- cores efetivas 20 (praticamente na faixa, nota 0,97)

## O que melhorou desde a v4
- A silhueta está limpa: sem cunha, sem dente e sem pixels soltos de fundo.
- O short tem rampa de 3 tons.
- Cabelo escuro sem a mancha lilás grande.
- Orelha em pele.
- Rim na manga e na canela.
- 20 cores efetivas.

## Rubrica visual

| Critério | Peso | Nota | Observação |
|---|---|---|---|
| Silhueta e leitura | 10 | 8 | Limpa. Detalhe: o short virou um bloco contínuo de x46 a x75 até y105, sem a sombra da virilha, e lê como saia; falta a separação entre as pernas do short |
| Proporção e pose | 10 | 7 | ~5,6 cabeças, a passada é boa; continua com 123 px, acima dos 100–110 da receita |
| Rosto (discreto, sem anime) | 10 | 6 | Sem a sobrancelha grossa pedida no briefing. Há pixels lilás-cinza na bochecha e no maxilar direitos ((64,28), (65,30), (64,32)) e no pescoço ((50–51,37), (60,38), (61,37), (53–54,36–38) #8e6c70) |
| Sombreamento em blocos | 15 | 7 | Moletom bom. O short em 3 tons ainda está salpicado de 1 px em vez de blocos com dobra. Os tênis são uma rampa de 5 tons aplicada pixel a pixel, ainda manchada |
| Paleta contida + destaque | 10 | 8 | Cinza + marinho + pele + 1 laranja, com 20 cores efetivas. Restam 2 px lilás no cabelo, em (48,19) e (62,21) |
| Contorno seletivo | 5 | 7 | Bom no corpo; nos tênis não há contorno que feche a forma da sola |
| Luz e rim light | 10 | 7 | Os rims viraram **linhas contínuas**: laranja na manga (~x66–68, y46–70) e pêssego #f0b090 na canela (x73–74, y108–120, 13 px seguidos). A ref 21 usa rim em pontos de 1–3 px; linha contínua lê como contorno colorido |
| Materiais e dobras | 10 | 7 | Capuz, cordões, bolso e meias funcionam. Os tênis (x33–46, y126–140 e x66–84, y128–138) ainda não leem como tênis: sem sola contínua nem biqueira, e com o cadarço laranja quase invisível |
| Composição / pose no quadro | 10 | 7 | Centrado, com a passada em diagonal; a figura está alta para a receita |
| Não parece amador | 10 | 7 | De longe já aguenta. De perto, os tênis manchados e o rosto sem sobrancelha ainda denunciam |

**Rubrica** = (8·10+7·10+6·10+7·15+8·10+7·5+7·10+7·10+7·10+7·10)/10 = **71,0**

## NOTA FINAL = 0,4·94,0 + 0,6·71,0 = **80,2** — **REFAZER**
(A próxima é a volta 6, a última do ciclo.)

## Contradições com o briefing
- Falta a sobrancelha grossa; é a terceira volta pedindo.
- O cabelo continua liso e penteado de lado, com topete. Não é crespo na máquina.

## Melhorias (da que mais sobe a nota para a que menos)
1. **Sobrancelha grossa** (código): 3x1 px de #160e14, 1 px acima de cada traço de olho. No lado da sombra, 2x1. Encoste-a na sombra da linha do cabelo, com 1 px de pele em sombra #bc726e entre a sobrancelha e o cabelo. Sozinha, sobe o rosto de 6 para 8 (refs 21 e 10).
2. **Tênis redesenhados em blocos**, não em rampa pixel a pixel (x33–46, y126–140 e x66–84, y128–138):
   - Sola creme #d8cfc6 contínua de 2 px na base, com 1 px de sombra #a89e96 na traseira.
   - Cabedal em 2 blocos: #3d4256 na luz e #2a2d3e na sombra.
   - Contorno #160e14 fechado em cima e atrás.
   - Biqueira creme de 2–3 px.
   - Cadarço de 2–3 px #dd6d2c no peito do pé.
   - Desgaste: 1–2 px de #a89e96 na ponta.
3. **Rims em pontos** (código):
   - Corte o laranja da manga (x66–68, y46–70) em 3 trechos de 2–3 px nos topos das dobras e no ombro; o resto vira o tom claro do moletom.
   - Corte o pêssego da canela (x73–74, y108–120) em 2 trechos: joelho y108–110 e canela y116–118.
   - Ref 21 (rim de 1 px em 3–4 pontos).
4. **Limpar o rosto e o pescoço**:
   - (64,28), (65,30), (64,32) → pele de sombra #d1887f.
   - (61,37), (60,38), (50–51,37), (53–54,36–38) → #bc726e.
   - (48,19), (62,21) no cabelo → #2a1c22.
5. **Short com 2 pernas**: em y98–105, abra a separação da virilha com sombra #2a2d3e, de x56–61 em y98 até ~x55–62 em y105, encostando no vão transparente. Troque o salpicado por blocos: luz #555a70 à direita (x66–74) e sombra numa diagonal da coxa esquerda. Barra com 1 px escuro em y104–105.
6. **Reduzir para ~108 px** (escala 0,88 por vizinho mais próximo na bruta, ou "small boy" no img2img), com o pé em y≈130. Isso também melhora espaço negativo e foco × terços.
7. **Cabelo crespo** (img2img com máscara x44–68, y15–30, força 0,35): "very short dark coily hair, buzz cut, rounded silhouette"; negativo "straight hair, side swept, quiff". Ou por retoque: tire o topete que sobra sobre a testa (x52–64, y19–24) e deixe a borda irregular de 1 px.
8. **Rever a métrica "proporção (cabeças)"** no estúdio: a faixa 2,75–4,52 contradiz a receita 5.1 (5,5) e tira ~3 pontos técnicos de uma proporção correta.

## Para a volta 6 (resumo do que falta)
Sobrancelha grossa, tênis legíveis, rims em pontos e altura de ~108 px. Sem esses quatro itens, a rubrica não passa de ~75 e a nota final não chega a 95.
