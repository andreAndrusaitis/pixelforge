# Crítica — martim-corpo-v6 — volta 6 (final do ciclo)

Arte: `out/ia/refino/martim-corpo-v6/martim-corpo-v6.json` (104x152, fundo transparente) · tipo **personagem**
Folha: `out/estilo/comparar/martim-corpo-v6_comparar.png` · refs mais próximas: 11, 3, 1

## Nota técnica: 93,1 (v5: 94,0)
Fora da faixa:
- proporção (cabeças) 6,89 (faixa 2,75–4,52; nota 0,13, peso 6). É o conflito com a receita 5.1 apontado desde a v3.
- cores efetivas 19 (mínimo 20,4; a moda nos tênis tirou tons)
- tons por rampa 2,71 (mínimo 2,8)
- espaço negativo 0,762
- foco × terços 0,121

## Conferência das mudanças pedidas
- **Sobrancelha em y22 (x57–59, x62–63):** os pixels foram pintados, mas y22 ainda é massa de cabelo #2a1c22 (a pele começa em y23–24). A sobrancelha nova some dentro do cabelo e não se lê. O que se lê como sobrancelha é o traço que já existia em y28 (x55–57 e x61–63). O efeito colateral são os "pontos de couro cabeludo" #bc726e dentro do cabelo em (57–59,21), (61,21), (63,21), (58–59,19).
- **Olho com esclera:** em y31 o olho esquerdo é #160e14 em x55–56, ladeado por **dois px brancos #f5ece5** em (54,31) e (57,31). Isso é esclera aberta, o começo de "olho de anime"; a ref 21 usa só o traço escuro.
- **Rims em pontos:** o desenho está certo, mas o laranja em (67,46–48) e (67,58–59) está **solto, fora da silhueta**: a coluna x66 é transparente, então os pontos flutuam ao lado do ombro e da manga.
- **Virilha e barra:** resolvido; o short agora lê com duas pernas.
- **Tênis com filtro de moda:** ficaram mais em blocos, mas ainda não leem. O esquerdo (x33–46, y126–140) é uma massa preta, cinza e azul sem sola; o direito lê melhor (sola clara), mas o cadarço laranja tem 1 px.
- **Restos cinza ainda presentes:**
  - Cabelo: #626071/#4b4357 em (57–58,17), (57–60,18), (57,19), (57,20), (60,20), (65,21), (65,22), (60–61,22).
  - Rosto: (60,31) #4b4357, (48,33) #4b4357, (60,33) e (58,35) #8e6c70, (59,33) #7f3f3c, (53,34) e (64,34) #46272c.

## Rubrica visual

| Critério | Peso | Nota | Observação |
|---|---|---|---|
| Silhueta e leitura | 10 | 8 | Limpa e com a virilha aberta; 5 px laranja soltos fora da borda |
| Proporção e pose | 10 | 7 | ~5,6 cabeças e boa passada; 123 px (a altura não foi reduzida) |
| Rosto (discreto, sem anime) | 10 | 7 | A sobrancelha (y28) se lê. Contra: esclera branca no olho esquerdo, manchas cinza e castanhas e pontos de pele no cabelo |
| Sombreamento em blocos | 15 | 7 | Moletom bom; short ainda salpicado em 1 px; tênis em blocos sem lógica de forma |
| Paleta contida + destaque | 10 | 8 | Cinza, marinho, pele e 1 laranja: certo |
| Contorno seletivo | 5 | 7 | A sola e o cabedal do tênis esquerdo não se fecham |
| Luz e rim light | 10 | 7 | Rims em pontos, como pedido, mas flutuando fora do corpo |
| Materiais e dobras | 10 | 7 | Capuz, cordões, bolso, meias e short funcionam; os tênis não |
| Composição / pose no quadro | 10 | 7 | Centrado; a figura está alta para a receita |
| Não parece amador | 10 | 7 | De longe aguenta; de perto, os tênis, os pixels soltos e as manchas na cabeça entregam |

**Rubrica** = (8·10+7·10+7·10+7·15+8·10+7·5+7·10+7·10+7·10+7·10)/10 = **72,0**

## NOTA FINAL = 0,4·93,1 + 0,6·72,0 = **80,4** — **REFAZER** (volta 6, fim do ciclo sem aprovação)

## O que falta (resumo para o autor)
A figura chegou a um Martim reconhecível e limpo: proporção de criança, moletom cinza com destaque laranja, short em duas pernas e silhueta sem fundo. Para ficar do lado das referências (95), faltam:
1. **Tênis desenhados à mão, não filtrados** (x33–46, y126–140 e x66–84, y128–138):
   - sola #d8cfc6 contínua de 2 px, com 1 px #a89e96 atrás;
   - cabedal em 2 blocos, #3d4256 na luz e #2a2d3e na sombra;
   - contorno #160e14 fechado;
   - biqueira creme;
   - cadarço laranja de 2–3 px.
   É o item que mais pesa (materiais, sombreamento, amador).
2. **Cabeça limpa**:
   - apague a sobrancelha de y22 e os #bc726e dentro do cabelo (volte tudo para #2a1c22);
   - mantenha a de y28;
   - troque a esclera branca (54,31) e (57,31) por pele #f6c9b9;
   - troque os cinzas e castanhos listados acima pelo tom de pele ou de cabelo vizinho.
3. **Rims colados**: mova o laranja de x67 para x65–66 em y46–48 e y58–59 (sobre a borda do moletom) ou preencha x66 com o tom claro do moletom.
4. **Altura de ~108 px** com o pé em y≈130 (escala 0,88 por vizinho mais próximo na bruta e repetir os retoques), como pede a receita 5.1.
5. **Short em blocos** (x47–74, y85–105): luz à direita, diagonal de sombra na coxa esquerda, sem salpicado.
6. **Cabelo crespo na máquina**, pendente desde a v1: tire o topete liso (x52–64, y19–24) e deixe a borda redonda e irregular de 1 px.
7. **No estúdio**: revisar a faixa da métrica "proporção (cabeças)" (2,75–4,52), que contradiz a receita 5.1 e tira ~3 pontos de uma proporção correta.

Estimativa: com os itens 1 a 5 bem feitos, a rubrica vai para ~82–85 e a final para ~87–89. Para chegar a 95, o caminho mais curto é desenhar à mão os pés e a cabeça (ou fazer um img2img mascarado da cabeça com cabelo crespo) e depois aplicar o mesmo retoque.
