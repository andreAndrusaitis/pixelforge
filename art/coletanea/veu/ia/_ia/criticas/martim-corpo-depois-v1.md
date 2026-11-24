# Crítica — martim-corpo-depois — volta 1

Arte: `out/ia/prova/martim-corpo-depois/martim-corpo-depois.json` (104x152, fundo transparente) · tipo **personagem**
Folha: `out/estilo/comparar/martim-corpo-depois_comparar.png` · refs mais próximas: 11, 1, 21 (guia da receita 5.1: 21, 11, 10)

## Nota técnica: 95,5
Fora da faixa: variação de matiz nas rampas 85,4° (faixa 12,6–69,7) · espaço negativo 0,778 (0,387–0,622) · foco × terços 0,199 (0,131–0,189) · dithering 0,0007 (0,0009–0,0048).
A métrica passa porque mede ritmo de blocos e valor; os problemas são de identidade e de limpeza, e esses só aparecem quando se olha a imagem.

## Rubrica visual

| Critério | Peso | Nota | Observação |
|---|---|---|---|
| Silhueta e leitura | 10 | 6 | A cunha bege de fundo entre as pernas (x38–62, y104–131) e a mancha cinza no quadril fecham o vão das pernas; pixels cinza soltos na borda esquerda do moletom |
| Proporção e pose | 10 | 5 | Cabeça com 17 px (y16–32) para uma figura de 123 px dá ~7,2 cabeças: lê como adulto, não como um menino de 12 anos pequeno (a receita pede ~5,5 cabeças e 100–110 px). Perfil andando: a pose é crível, mas foge da 3/4 frontal da ref 21 |
| Rosto (discreto, sem anime) | 10 | 6 | Olhos em traço de 3x1 escuro (y24, x57–59 e x62–63): está certo. Mas a testa é um bloco liso de pele clara, sem franja e sem sombra de franja; o queixo e o maxilar são longos e de adulto; a orelha é um bloco vermelho (x50–53, y25–31) |
| Sombreamento em blocos | 15 | 6 | Calça em blocos aceitáveis; o moletom é ruído de 1 px sem 2 dobras grandes; o rosto fica chapado em d7; há mancha esfumada cinza-violeta no quadril/mão |
| Paleta contida + destaque | 10 | 4 | O moletom é **VERDE** (#4d6559/#304346), não cinza como no briefing; a calça é do mesmo verde (vira um agasalho de um só verde, sem destaque); o cabelo é **castanho-rosado claro**, não escuro; a variação de matiz de 85° é a única métrica fora da faixa com peso |
| Contorno seletivo | 5 | 7 | Contorno azul-escuro interrompido no material escuro: está bom; nos pés, quebra em xadrez |
| Luz e rim light | 10 | 6 | A luz vem da direita no rosto, mas o moletom não tem lado claro; não há rim light visível |
| Materiais e dobras | 10 | 6 | Os cordões de 1 px (x58–62, y40–55) e o capuz atrás funcionam; a calça não acumula no tornozelo; o tênis tem leitura confusa (xadrez de vermelho/creme/preto), mas não lê como gasto |
| Composição / pose no quadro | 10 | 6 | Figura deslocada para a esquerda (bbox x15–72 de 104) e sobra de 78% de espaço negativo; a sombra no chão (x15–30, y130–135) corta à esquerda |
| Não parece amador | 10 | 5 | O resto de fundo entre as pernas e a mancha no quadril denunciam na hora que foi recortado de uma imagem gerada |

**Rubrica** = (6·10+5·10+6·10+6·15+4·10+7·5+6·10+6·10+6·10+5·10)/10 = **56,5**

## NOTA FINAL = 0,4·95,5 + 0,6·56,5 = **72,1** — **REFAZER**
(5 critérios abaixo de 8. A nota técnica alta está enganando: a arte não é o Martim.)

## Contradições com o briefing
- Moletom verde, e não cinza; calça verde igual ao moletom.
- Cabelo castanho-claro/rosado, raspado e liso, e não escuro e crespo; não há sobrancelha grossa visível (a linha y24 é só o olho).
- Proporção adulta (~7 cabeças), e não de um menino de 12 anos pequeno e magro.
- Os tênis estão bem vermelhos e limpos; não leem como gastos.

## Restos de fundo na borda da silhueta
- **Cunha bege** #ada496 / #b3a99c (326 px) entre as pernas: x38–62, y104–131. É o fundo da bruta que ficou preso no recorte.
- **Mancha cinza-violeta/bege** no quadril, ao lado da mão: x47–55, y80–92 (cerca de 50 px de #9d8c89 e #ada496).
- **Pixels soltos cinza-claros** na borda esquerda do moletom/capuz: x39–44, y40–72 (cerca de 1–3 px por linha), e em (59,32) e (67,64).
- **Sombra no chão** #756f7d: x15–30 e x40–56, y129–135. Se a folha é de personagem com fundo transparente, ela sobra; se for mantida, use 1 tom só, em elipse, centrada sob os pés.

## Melhorias (da que mais sobe a nota para a que menos)
1. **Limpar o fundo** (código): torne transparentes todos os pixels com croma < 30 e valor > 110 que estejam *fora* dos cordões (x58–62, y40–55). Na prática, isso é a cunha x38–62/y104–131, a mancha x47–55/y80–92 e os pixels soltos x39–44/y40–72. Depois, feche o contorno interno das pernas com 1 px de #121826, como o contorno interrompido da ref 21. Só isso já tira "amador" e "silhueta" de 5–6 para 8.
2. **Moletom cinza** (retoque de paleta ou img2img): remapeie a rampa verde #27363d/#304346/#405751/#4d6559/#607264 para uma rampa de cinza frio de 4–5 tons (#22262e → #3a3f4a → #5a5f6a → #7d818a → #a3a6ad). No img2img, use o prompt "heather gray hoodie" e o negativo "green, olive, teal hoodie", com força 0,35–0,45. O cinza vira o neutro do personagem, como o marinho em 3 tons da ref 21.
3. **Calça separada do moletom** (paleta): a calça (y93–128) num neutro escuro azul-marinho/jeans de 3 tons (#151a26/#26304a/#3d4a66), diferente do cinza; o destaque fica só no tênis ou no capuz (receita 5.1 item 3: 1 destaque com 5–6 tons). Isso também derruba a variação de matiz de 85° para menos de 70°.
4. **Proporção de criança** (img2img, força 0,55–0,65): prompt "12 year old boy, small and skinny, big head, short legs, ~5.5 heads tall"; negativo "adult, teenager, tall, long legs, mature face". Meta: cabeça com ~20 px e figura com 100–110 px. Hoje a cabeça tem 17 px e a figura 123 px. Ref 21 (5,4 cabeças).
5. **Cabelo escuro e crespo + sobrancelha** (código, na área x48–64, y16–23): troque a rampa castanho-rosada (#705159, #835f5e, #a15f5a) por 4 tons quase pretos e quentes (#1a1218, #2b1d22, #3f2a2c, #5a3c38). Deixe a borda superior irregular, com 1 px de "pipoca" a cada 2–3 px (crespo na máquina, sem tufos longos). Ponha 2 px de sombra de pele na testa em y22–23 e uma **sobrancelha de 3x1 px escura** em y23, logo acima de cada olho (x57–59, x62–63). Ref 21 (sombra da franja) e ref 10.
6. **Rosto de criança** (código): encurte o queixo em 2 px (apague y31–32 abaixo de x56–62, trocando por contorno de pescoço em sombra); troque o bloco vermelho da orelha (x50–53, y25–31) por pele média com 1 px de sombra rosada; quebre o bloco liso d7 da bochecha com a pele em 3 tons (luz à direita, sombra rosada no maxilar esquerdo). Ref 21 (pele em 3 tons, maxilar só por troca de tom).
7. **Duas dobras grandes e luz no moletom** (img2img com força 0,3 ou retoque): 2 diagonais do ombro (x50, y38) para a cintura (x60, y70) no tom de sombra, e o lado direito (x62–67, y40–75) 1 tom mais claro, com rim light de 1 px quente em 3–4 pontos (ombro e manga). Hoje o moletom é só ruído de 1 px. Ref 21.
8. **Enquadramento e tênis gasto** (código): centralize a figura (desloque cerca de +16 px em x, para que o centro fique em ~x52); recorte a sombra do chão ou reduza-a a uma elipse de 1 tom de ~30x3 px sob os pés. Nos tênis (x29–45 e x55–72, y129–138), tire o xadrez: sola creme suja contínua de 1 px, cabedal em 2 tons dessaturados (#6e4a48/#8f6a5e) e 1–2 px de desgaste claro na ponta. Ref 21 (sola com 1 px claro).
