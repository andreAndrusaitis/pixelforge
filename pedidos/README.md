# Pedidos ao Claude

O estúdio web (`python -m pixelforge studio` → aba **Pedidos ao Claude**) grava aqui um
pedido por arquivo:

- `<data>-<arte>.md` — o pedido: cabeçalho (`estado`, `arte`, `arquivo`, `quadro` ou
  `cena`/`t`), o texto do autor e a lista de **marcas** numeradas com coordenadas
  (pixels da arte; em quadros de cena, pixels da imagem e, entre colchetes, o pixel
  lógico da cena), origem no canto superior esquerdo;
- `<data>-<arte>.png` — a imagem com as marcas desenhadas e numeradas.

## Para o Claude

1. Procure arquivos com `estado: aberto`.
2. Abra o `.md` e a imagem anotada (Read); o número de cada marca bate com o texto.
3. Aplique na arte indicada em `arquivo` (ou no roteiro da `cena`), seguindo a skill
   `pixel-art`; renderize e revise o preview.
4. Rode `python -m pixelforge acervo indexar` se criou ou renomeou artes.
5. Troque o cabeçalho para `estado: feito` (ou `descartado`, explicando o porquê no fim
   do arquivo). O estúdio também tem botões para mudar o estado.
