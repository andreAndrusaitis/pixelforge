# Guia visual do PixelForge — o nível mínimo

O PixelForge **não entrega arte simples**. Toda arte (personagem, retrato, cenário,
cena, quadro de vídeo) mira o nível das referências do autor: 33 imagens em
`refs/estilo-referencias/` (local, fora do git: são de outros artistas, só para
estudo; nada é copiado), indexadas por tipo e tag em
[referencias.json](referencias.json).

Antes de desenhar ou gerar, abra 2–3 referências do mesmo tipo. Antes de entregar,
compare lado a lado. Se a arte parecer "de gerador" (formas chapadas, degradê liso,
olho de anime, cores saturadas sem rumo), ela não está pronta.

## Personagem e retrato

| Critério | Alvo | Referências |
|---|---|---|
| Proporção | estilizada, 5–7 cabeças (criança ~5,5); chibi atarracado só quando pedido | 1, 11, 21, 22 · chibi: 8, 31 |
| Pose | gesto e peso: contrapposto, ombro caído, mão no bolso/quadril, nunca "boneco em T" | 1, 10, 16, 19, 21 |
| Rosto | discreto: olhos de 1–2 px, muitas vezes na sombra da franja/aba/capuz; **nada de olho de anime** (íris grande, brilho duplo, cílios) | 1, 21, 22, 28 |
| Volume | sombreamento em **blocos pintados** (clusters), 3–5 tons por material; dobras de pano como formas grandes; nada de degradê liso nem pillow shading | 5, 12, 21, 22 |
| Silhueta | legível em tamanho real; bordas de pano irregulares/rasgadas quando couber | 2, 6, 22, 25 |
| Contorno | seletivo: escuro só onde define a silhueta, colorido ou ausente na luz | 2, 4, 12, 20 |
| Luz | uma direção clara + **rim light** (às vezes de cor oposta) + brilho/halo de fonte de luz | 2, 17, 22 |
| Tamanho | corpo inteiro 90–140 px (cena 640×360); retrato de busto 96–128 px | — |

## Cenário e cena

| Critério | Alvo | Referências |
|---|---|---|
| Profundidade | **perspectiva atmosférica**: o distante mais claro, mais azulado, com menos contraste | 23, 26, 27 |
| Moldura | silhuetas escuras em primeiro plano (árvores, folhas, colunas) emoldurando | 15, 23, 27 |
| Céu | manchas grandes de cor, nuvens em blocos, poucas cores por faixa | 13, 24, 27, 33 |
| Paleta | **uma paleta dominante por cena** (tudo vermelho, tudo azul, rosa e laranja) + 1 destaque | 26, 29, 33 |
| Vida | partículas luminosas (brasas, vagalumes, neve, poeira de luz) | 8, 25, 27, 29 |
| Água e chão molhado | reflexo em faixas horizontais quebradas | 2, 16, 23 |
| Escala | figura pequena contra algo enorme quando a cena pede | 24, 29, 30 |

## Paleta e cor

- Contida e coesa: 16–32 cores por arte, dessaturadas, com **um** destaque saturado.
- Sombras puxam para o frio (azul/violeta), luzes para o quente (hue shifting).
- Valores bem separados: a imagem precisa funcionar em preto e branco.

## Checklist de entrega (todo comando/skill/agente)

1. Abri 2–3 referências do mesmo tipo antes de começar?
2. A silhueta lê em tamanho real (escala 1)?
3. Tem blocos de sombra (não degradê), contorno seletivo e rim light?
4. Rosto sem olho de anime?
5. Paleta contida com um destaque? Sombras frias, luz quente?
6. Cenário: profundidade atmosférica, moldura, paleta dominante, algum elemento vivo?
7. Comparei lado a lado com as referências e a minha arte "aguenta" do lado delas?

Se qualquer resposta for não, ajuste antes de mostrar ao autor.

Receitas e faixas numéricas: [estilo-pixelforge.md](estilo-pixelforge.md); análise de cada referência em `analises/<n>.md`.
