# Crítica — geraldo-corpo (r3-2) — volta 3

Arte: `out/ia/r3/geraldo-corpo-r3-2/geraldo-corpo-r3-2.json` (104x152, tipo personagem; paleta da própria pixelização, sem filtro de moda)
Folha de comparação: `out/estilo/comparar/geraldo-corpo-r3-2_comparar.png`
Referências mais próximas (métrica): 3, 1, 11 · guias da receita 5.2: 14, 1, 22
Críticas anteriores: v1 69,5 · v2 73,5

## Nota técnica: 90.6 (v2: 91.5)

Fora da faixa:
- **cores efetivas 15** (faixa 20–48), nota 0,58 peso 10 — a pele e a camisa usam o mesmo #e5c2a4.
- tons por rampa 2,5 (mín. 2,8); níveis de valor 10 (mín. 10,6).
- **proporção 8,56 cabeças** — agora contra a própria receita 5.2 (~7): a cabeça ficou pequena (rosto ≈ 14×13 px, x 51–65, y 13–26) para 136 px de corpo.
- foco × terços 0,124 e espaço negativo 0,676 — figura deslocada para a direita (corpo em x 39–85, centro ≈ 62; quadro centro 52).

## O que melhorou desde a v2
Chapéu de feltro com copa, fita marrom e aba inclinada; camisa bege fechada com manga dobrada nos dois braços (x 39–46 e 74–84, y 50–57); cinto com fivela (x 46–76, y 58–63); tronco largo com volume de barriga; mãos em tamanho bom; botinas de cano com cadarço; sombra de chão. A leitura do "Seu Geraldo" já existe.

## Rubrica visual

| Critério | Peso | Nota | Observação |
|---|---|---|---|
| Silhueta e leitura | 10 | 8 | Massa larga, chapéu, braços soltos, base com pés afastados. Só o vão cinza entre as pernas atrapalha. |
| Proporção e pose | 10 | 7 | Ombros e tronco certos, mas a cabeça é pequena (8,6 cabeças; receita ~7) e as pernas estão compridas e balofas (y 63–118). |
| Rosto | 10 | 6 | Olhos pequenos e escuros (ok). Cinza #878690/#434853 no maxilar e no queixo, em (53, 19–24), (59–61, 21–25) e (54–58, 25), lê como **barba grisalha**: contradiz "barbeado". Rosto todo claro, sem a sombra da aba no terço de cima. |
| Sombreamento em blocos | 15 | 6 | Na camisa, as dobras são linhas finas vinho (x 55–56, y 34–50; x 66–72, y 40–55), não blocos. Jeans ainda manchado em y 95–118. Botinas com salpico rosa (#cb7071) em x 44–48 e 63–66, y 120–138. |
| Paleta contida + destaque | 10 | 6 | 15 cores. **Pele = camisa** (#e5c2a4 nos dois), e o antebraço se funde na manga. Nenhum destaque pequeno (o vermelho saiu e nada entrou). Sombra fria no jeans ok. |
| Contorno seletivo | 5 | 6 | Linha vinho #51242e quase contínua em volta da camisa, inclusive no lado da luz (x 41–45, y 34–50). |
| Luz e rim light | 10 | 6 | Luz da esquerda e de cima coerente. Sem rim. |
| Materiais e dobras | 10 | 7 | Feltro, camisa de manga dobrada, cinto e botina leem. Faltam os botões. Mancha ferrugem no jeans em (59–60, 94–96). Cinza #878690 no meio do antebraço direito, em (71–73, 58–62). |
| Composição e pose no quadro | 10 | 7 | Altura boa (136 px), mas a figura está 10 px à direita do centro. |
| Não parece amador | 10 | 6 | O vão cinza entre as pernas (x 53–60, y 105–140), igual ao da v2, e a barba cinza ainda entregam o processo. |

**Rubrica** = 650 / 10 = **65,0**

## NOTA FINAL = 0,4 × 90,6 + 0,6 × 65,0 = **75,2** (v1 69,5 · v2 73,5)

## Veredito: **REFAZER**

## Melhorias (da que mais sobe a nota para a que menos)

1. **Separar a pele da camisa e criar o destaque (paleta 6→8, técnica: cores)**: duas rampas distintas.
   - Pele em 4 tons, mais quente e mais escura que a camisa: #d9a184 / #b97561 / #8a4d48 / #5a2c34.
   - Camisa em 4 tons mais frios e acinzentados: #d8c3a5 / #b8a084 / #8a7262 / #5a4549.
   - Remapear os pixels de pele (rosto x 51–65, y 13–26; antebraços x 39–46 e 69–79, y 57–86) para a rampa nova.
   - Destaque único: fita do chapéu em vermelho-terroso #a8403a, em (54–67, 10–11), repetido em 1–2 px no lenço ou bolso.
   Isso leva as cores efetivas a ~20. Refs 7 e 9, receita 5.2 §8.
2. **Tirar a barba (rosto 6→8)**: trocar o cinza #878690/#434853 em (53, 19–24), (59–61, 21–25) e (54–58, 25) por pele de sombra (#b97561 e #8a4d48). Na nuca, junto ao chapéu, o cinza fica (cabelo branco rente, em 63–64, 14–17). Sombra da aba sobre y 13–15 (x 52–64), em #8a4d48, com 2–3 px claros só no nariz e na maçã, em (56–57, 18–19). Para img2img, negativo "beard, stubble, grey jaw, goatee". Ref 14.
3. **Vão entre as pernas (não amador, silhueta)**: o cinza claro #878690 em x 53–60, y 105–140 é fundo da imagem bruta. Do gancho até a canela, pintar como sombra #201927 em 1–2 px de largura. Abaixo, em y 118–140, apagar para transparente, para que o vão das botinas mostre o fundo. É o mesmo problema da v2: tratar no pipeline e remover pixels da cor do fundo da bruta que ficaram dentro da silhueta.
4. **Cabeça maior (proporção 7→8)**: escalar a cabeça e o chapéu em ~1,2× (rosto de 14×13 para 17×16 px, aba de ~22 para ~27 px), mantendo o pescoço em y≈27. Ou subir o chapéu 2 px e baixar a barra da camisa. Alvo: ~7–7,5 cabeças em 136–140 px. No img2img: "large head, older man proportions", força 0,35. Receita 5.2 §1.
5. **Dobras em blocos (sombreamento 6→8)**: as linhas vinho na camisa (x 55–56, y 34–50; x 66–72, y 40–55) devem virar 2–3 formas de sombra de 2–4 px de largura, em #8a7262, com o avesso em #5a4549. Uma diagonal do ombro direito à cintura e um bloco escuro sob o peito, do lado direito (x 70–80, y 44–56). A linha de botões vira 1 px em x≈60, y 32–57, com 4 pontos claros. Ref 1 (casaco em 3 massas) e receita 5.2 §4.
6. **Jeans e botinas limpos (sombreamento, materiais)**: tirar a mancha ferrugem (59–60, 94–96). Em y 95–118, aplicar moda 3x3 **só no jeans**, depois uma coluna clara #878690 de 3 px no lado da luz de cada perna (x 42–45 e x 61–64) e 1 px de luz no joelho, em (44,98) e (63,98). Nas botinas, remover o salpico #cb7071 em x 44–48 e 63–66, y 120–138, deixando 3 tons marrom-escuros, 1 px de brilho na biqueira em (36,137) e (60,139) e sola #201927. Receita 5.2 §6.
7. **Contorno seletivo e rim light (contorno, luz)**: no lado da luz, trocar o vinho #51242e da borda esquerda da camisa (x 41–45, y 34–50), da aba (x 48–52, y 11) e do braço esquerdo (x 39, y 57–75) por 1 px de rim quente (#f0d2b0 ou laranja da cena). No lado da sombra (direita), manter o contorno escuro. Ref 22 e receita 5.2 §7.
8. **Centralizar e limpar artefatos (composição, materiais)**: deslocar a figura 8–10 px para a esquerda (corpo para x≈30–76), sem mexer na sombra de chão, só encurtando-a para x ≤ 84. Trocar o cinza dentro do antebraço direito, em (71–73, 58–62), por pele média.
