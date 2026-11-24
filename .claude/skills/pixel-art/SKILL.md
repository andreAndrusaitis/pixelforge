---
name: pixel-art
description: Gera pixel art por código com o PixelForge deste repositório — a partir de uma descrição (ex.: "cavaleiro 32x32 estilo NES") ou de uma imagem de referência que deve virar pixel art. Exporta PNG, JPG, WebP, GIF (animado) e SVG em qualquer tamanho (16, 32, 48, 64…). Use sempre que o pedido envolver uma arte de pixel avulsa — sprite, ícone retrô, objeto, retrato, paleta PICO-8/Game Boy/C64, ou "transformar imagem em pixel". É a porta de entrada do estúdio: personagem recorrente → pixel-personagem; cenário/tileset → pixel-cenario; cena animada/vídeo → pixel-cena; som → pixel-som; revisão → pixel-revisao.
---

# Pixel Art com PixelForge

Tudo roda localmente com Python + Pillow + numpy. **Não** use apps externos,
geradores de imagem por IA nem downloads. A arte é sempre escrita como código/dados
e renderizada pelo motor em `pixelforge/`.

## 0. Qual skill?

| Pedido | Skill |
|---|---|
| uma arte avulsa (sprite, ícone, objeto, retrato), foto → pixel | **esta** |
| personagem recorrente (retrato + sprite + animações), variações dele | `pixel-personagem` |
| cenário em camadas, tileset, mapa | `pixel-cenario` |
| cena animada / vídeo (câmera, atores, diálogo, efeitos) | `pixel-cena` |
| efeitos, trilha, voz, mixagem | `pixel-som` |
| revisar arte/storyboard com coordenadas | `pixel-revisao` |

Atalhos: `/personagem`, `/cenario`, `/cena`, `/som`, `/acervo`, `/revisar`. Equipe de
agentes e contrato de retorno: `docs/agentes.md`.

Rode os comandos a partir da raiz do repositório:

```bash
python -m pixelforge <comando> ...
```

## 1. Entrevista ANTES de gerar (obrigatória)

**Não assuma e não gere várias versões por conta própria.** Antes de desenhar ou
converter qualquer coisa, pergunte ao usuário com a ferramenta `AskUserQuestion`
(múltipla escolha, até 4 perguntas por chamada) tudo o que ele **não** especificou.
Pule só o que o pedido já deixa explícito. Gere **uma** arte, mostre, e pergunte o
que ajustar — variações, outros tamanhos ou estilos só se ele pedir.

### Rodada 1 — sempre

| Pergunta | Opções típicas |
|---|---|
| **Intenção** (quando há imagem de referência) | *Personagem*: traduzir a pessoa/objeto num personagem de pixel art, estilizado mas reconhecível · *Fiel à imagem*: a própria foto em pixel art |
| **Formato do personagem / peça** | Retrato busto (diálogo de RPG) · Corpo inteiro chibi (sprite de jogo) · Avatar ícone · Objeto/item · Cena/tile |
| **Tamanho** | 16 · 32 · 48 · 64 · 96/128 (mostre o trade-off: menor = mais icônico, maior = mais detalhe) |
| **Paleta / estilo de cor** | Cores da referência (N cores) · Retrô nomeada (pico8, gameboy, c64, endesga32, sweetie16) · Monocromática |

### Rodada 2 — só o que for relevante para a resposta da rodada 1

| Pergunta | Opções típicas |
|---|---|
| **Fundo** | Transparente · Cor sólida · Cenário simples |
| **Contorno** | Escuro completo · Selout (contorno tingido) · Sem contorno |
| **Sombreamento** | Cel shading (2–3 faixas chapadas) · Suave com mais tons · Chapado (flat) |
| **Animação** | Nenhuma · Idle (respirar) · Piscar · Andar |
| **Traços a enfatizar** (personagem a partir de foto) | Liste o que você observou (ex.: cabelo ondulado com volume, sorriso largo, olhos claros, camiseta cinza-azulada) e pergunte se algo deve ser exagerado, removido ou trocado (acessórios, expressão, roupa) |

Formatos de saída: use os de `pixelforge.toml`; pergunte só se ele mencionar uso
específico (GIF para animação, SVG para web, etc.).

Liste paletas com `python -m pixelforge palettes` e veja as cores de uma com
`python -m pixelforge palettes pico8`.

## 2. Fluxo A — descrição → pixel art

### Até ~32×32: spec JSON (controle pixel a pixel)

1. `python -m pixelforge new <nome> --size 32 --palette pico8` cria `art/<nome>.json`
   com a grade vazia e as chaves da paleta (`0`–`f` na pico8).
2. Planeje antes de escrever: silhueta, proporções, de onde vem a luz.
3. Edite a spec. Formato:

```json
{
  "name": "slime",
  "size": [16, 16],
  "fps": 4,
  "palette": { ".": "transparent", "k": "#1a1c2c", "g": "#38b764" },
  "pixels": ["................", "......kkkk......", "..."],
  "frames": [["..."], ["..."]]
}
```

- Use `pixels` (1 frame) **ou** `frames` (animação). Todas as linhas com a mesma largura.
- Chaves de 1 caractere; renomear chaves para mnemônicos (`k` contorno, `s` pele…) ajuda.
- Conte as colunas: cada linha tem exatamente `largura` caracteres.

4. `python -m pixelforge render art/<nome>.json`

### 48×48 ou maior: script Python com primitivas

Crie `art/<nome>.py` com `build()` retornando `Canvas` (ou lista de Canvas = frames):

```python
from pixelforge import Canvas

FPS = 6  # opcional, para animação

def build():
    c = Canvas(64, palette={"pele": "#ffccaa", "sombra": "#ab5236", "k": "#1d2b53"})
    c.ellipse(31.5, 28, 14, 16, "pele")
    with c.only("pele"):                 # trava de cor: só pinta sobre "pele"
        c.rect(40, 0, 24, 64, "sombra")  # sombra do lado oposto à luz
    c.px(26, 26, "k")
    c.mirror_x()                          # simetria
    c.outline("k")
    return c
```

API do `Canvas` (coordenadas fora do canvas são ignoradas; cores = nome da paleta, hex ou tupla):

| Método | Uso |
|---|---|
| `px(x, y, c)` / `get(x, y)` | pixel individual |
| `line(x0, y0, x1, y1, c)` | linha Bresenham, sem anti-aliasing |
| `rect(x, y, w, h, c, fill=True)` | retângulo |
| `ellipse(cx, cy, rx, ry, c, fill=True)` / `circle(cx, cy, r, c)` | use `.5` no centro para larguras pares |
| `polygon([(x, y), ...], c, fill=True)` | polígono |
| `fill(x, y, c)` | balde de tinta |
| `dither(x, y, w, h, c1, c2, level, pattern)` | mistura; `checker`, `bayer2`, `bayer4` |
| `gradient(x, y, w, h, [cores], vertical=True)` | rampa com dithering nas transições |
| `with c.only(cor):` | trava de cor (sombras/luzes dentro de uma forma) |
| `mirror_x()` / `mirror_y()` | simetria |
| `shift(dx, dy)` / `copy()` / `paste(outro, x, y)` | animação e composição |
| `replace(velha, nova)` / `outline(c, diagonal=False)` / `clear()` | utilidades |

Render: `python -m pixelforge render art/<nome>.py`

## 3. Fluxo B — imagem de referência → pixel art

> **Regra de ouro para fotos de pessoas/objetos reais: nunca redesenhe do zero.**
> Desenhar "de cabeça" perde a semelhança. Converta, e retoque a spec convertida.

1. Copie a imagem recebida para `refs/` (pasta ignorada pelo git — fotos pessoais
   não vão para o repositório). Fotos de celular vêm rotacionadas via EXIF; o
   motor já corrige, mas use as coordenadas da imagem *corrigida*.
2. Escolha um preset (`python -m pixelforge presets`):
   - `photo`: **fiel à foto** — Kuwahara + redução `detail` + paleta OKLab 32 cores
     + `merge` + `defringe`. Para retratos e pessoas. 64px; prefira 96–128 se a
     semelhança importar mais que o visual retrô.
   - `sprite`: personagem/objeto com fundo liso, contorno, 12 cores, 32px
   - `icon`: 16px, 8 cores, legível
   - `portrait`: 64px, 24 cores, recorte `cover` (versão simples)
   - `pico8`, `gameboy`, `c64`, `endesga`: paletas de hardware com dithering
3. **Fundo poluído (rua, natureza)?** `remove_bg auto` não resolve. Isole a figura:

```bash
python -m pixelforge mask refs/foto.jpg --polygon "x,y x,y ..." --out refs/foto_mask.png
```

   Coordenadas em frações (0–1) da imagem corrigida; `--ellipse cx,cy,rx,ry` e
   `--subtract` também valem. **Abra o `_mask_preview.png` com Read** (vermelho =
   removido) e ajuste o polígono até contornar cabelo, orelhas e ombros sem pegar
   fundo. Alternativas: `--crop x,y,w,h` (enquadrar) e `--background "#hex"` (fundo chapado).
4. Converta gerando a spec (ela guarda a foto e as opções usadas, para o compare):

```bash
python -m pixelforge convert refs/foto.jpg --preset photo --mask refs/foto_mask.png \
    --focus "0.25,0,0.55,0.7" --size 64 --name retrato --to-spec
```

   `--focus x,y,w,h` (frações do quadro final) dá mais tons da paleta ao rosto.
5. **Compare com a foto** e leia o painel (foto reduzida | pixel art | sobreposição):

```bash
python -m pixelforge compare art/retrato.json
```

   Notas: *semelhança* (cor, traços, forma) e *limpeza* (% de pixels sem salpicado).
   A semelhança é medida contra a foto reduzida por média, então um resultado borrado
   pontua alto — por isso olhe o painel e equilibre com a limpeza (≥ 90 é bom).
6. **Retoque cirúrgico na spec**, guiado por medida e não por chute:
   - Meça a posição de olhos/boca na grade de referência antes de editar
     (`pixelforge.compare.reference_grid` + luminosidade OKLab por pixel).
   - Detalhes pequenos demais para a média (dentes, íris clara, brilho do olho)
     somem na conversão: realce com 1–2 cores novas na paleta, **sutis** — branco
     puro e olhos grandes viram caricatura (a nota cai e o painel mostra).
   - Remova vazamentos de fundo na borda (folhas, céu, rua) trocando pela cor vizinha.
   - Rode `render` e `compare` de novo; o retoque não deve derrubar a semelhança.

Ajustes de conversão: `--palette 10|gameboy`, `--resample box|detail`, `--detail 0..2`,
`--edge-spread 0.1..0.4`, `--smooth kuwahara`, `--merge 0.04..0.08`, `--defringe 1..2`,
`--lines 0..1` (traço escuro nas bordas, estilo ilustrado), `--dither none|floyd|bayer2|bayer4`,
`--remove-bg auto|#ffffff`, `--fit contain|cover|stretch`, `--contrast`, `--saturation`,
`--outline auto|#000000|""`, `--cleanup 0..3`.

## 3b. Fluxo C — foto → **personagem** (estilizado, reconhecível)

Quando a intenção é "personagem", a foto fornece a **identidade** e as regras de
pixel art fornecem o **estilo**. Nem conversão direta (fica foto), nem desenho de
cabeça (perde a semelhança).

1. Entrevista (seção 1): formato, tamanho, paleta, contorno, sombreamento, traços a enfatizar.
2. **Guia de identidade** (não é entrega): máscara + `convert --preset photo --to-spec`
   no tamanho escolhido, com `--name <nome>_guia`. Dele, meça na grade:
   - silhueta do cabelo (largura, volume, para que lado cai a franja), linha do cabelo
   - linha dos olhos, nariz, boca, queixo, largura do rosto, orelhas, ombros
   - cores-base por material (cabelo, pele, olhos, boca, roupa) — use as cores da
     paleta do guia nessas regiões
   Para retrato de jogo, mantenha as proporções medidas; para chibi/ícone,
   exagere (cabeça maior, olhos maiores) mas mantenha formato do cabelo, cores e
   expressão — é isso que faz a pessoa ser reconhecida.
3. **Rampas de estilo**: para cada material, 3 tons a partir da cor-base
   (sombra = mais escura e puxando para frio/roxo; luz = mais clara e quente) —
   nada de dezenas de tons da foto.
4. Desenhe `art/<nome>.py` com `Canvas` (polígonos/elipses nas posições medidas,
   `with c.only(...)` para sombras em faixas, olhos e boca como glifos de pixel art,
   contorno ou selout conforme a entrevista).
5. Confira lado a lado com o guia — a silhueta e a posição dos traços devem bater:
   `python -m pixelforge compare art/<nome>.py --like art/<nome>_guia.json`
   (a nota de *forma* mede a silhueta; cor e traços serão menores de propósito).
6. Mostre UMA versão e pergunte o que ajustar.

## 4. Revisar SEMPRE antes de entregar

Todo `render`/`convert` gera `out/<nome>/<nome>_preview.png`: ampliado, fundo
xadrez = transparente, grade em cada pixel e linha forte a cada 8 pixels (para
achar coordenadas). **Abra esse arquivo com Read e avalie** — normalmente 2–4 rodadas:

- A silhueta é reconhecível só pela forma?
- Luz coerente (padrão: vinda de cima à esquerda; sombra embaixo/direita)?
- Pixels órfãos, "escadas" irregulares (jaggies) em curvas, linhas de largura dupla?
- Contraste suficiente entre áreas vizinhas? Cores demais?

Só entregue quando o preview estiver bom. Informe os caminhos gerados.

## 5. Regras de estilo (pixel art que parece pixel art)

- **Paleta limitada**: 4–16 cores em 16–32px; até ~32 em 64px. Reuse cores.
- **Rampas de cor**: 3–4 tons por material; ao escurecer, desloque o matiz para
  frio/roxo; ao clarear, para quente/amarelo (hue shifting), em vez de só preto/branco.
- **Sem pillow shading**: não sombreie contornando a forma por dentro; sombra segue a luz.
- **Curvas limpas**: segmentos em progressão regular (3-2-1, 1-1-2-2), nunca 3-1-3.
- **Linhas de 1px** sem cantos duplos (remova o pixel que forma "L" grosso).
- **Contorno**: escuro e completo em 16px; em 32+ pode usar selout (contorno tingido
  com a cor vizinha mais escura) para ficar menos duro.
- **Dithering** com moderação: transições grandes, céus, texturas; evite em sprites pequenos.
- **Leitura em 1x**: confira também o PNG em tamanho nativo; o detalhe precisa ler pequeno.
- **Animação**: poucos frames bem escolhidos; mantenha volume (squash & stretch) e
  pixels "âncora" estáveis para não tremer.

## 5b. Cenas → skill `pixel-cena`

Cenário animado, cutscene, "o personagem chega e fala": siga a skill **`pixel-cena`**
(momento → planos → roteiro → storyboard → revisão → vídeo). Camadas do cenário:
`pixel-cenario`; atores: `pixel-personagem`; som: `pixel-som`.

## 6. Saída e configuração

- Arquivos em `out/<nome>/`: `<nome>.png` (1x), `<nome>@16x.png`, `<nome>.svg`,
  `<nome>.gif`/`.webp` (animados quando há frames), `<nome>.jpg` (fundo de
  `jpg_background`), `<nome>_preview.png`. Vários frames em formato estático = sprite sheet horizontal.
- Opções por comando: `--formats png,gif,svg`, `--scales 1,8,16`, `--out pasta`, `--no-preview`.
- Padrões do projeto em `pixelforge.toml` (formatos, escalas, presets; `[cena]`: resolução, escala, fps, formatos).
- Paletas novas: arquivo `palettes/<nome>.hex` (um hex por linha, sem `#`).
- Erros de spec apontam frame/linha/coluna — corrija e rode de novo.

## 7. Motor de arte (ver docs/manual.md, "Motor de arte")

- **Personagem recorrente** → skill `pixel-personagem` (modelo `*.personagem.json` →
  `python -m pixelforge character`; sprite à mão que precisa animar → `animate`).
- Arte chapada → `shade` (sombra pela luz + selout). Outra paleta/hora do dia → `recolor`.
- Cenário grande → `tileset` + `tilemap` (skill `pixel-cenario`).
- Aseprite/Godot/Unity → `aseprite export|import`.
- Na revisão (seção 4), rode também `python -m pixelforge lint <arte>` e siga a skill
  `pixel-revisao` (o lint é aviso, não regra: olhos e brilhos isolados são intencionais).

## Nível mínimo (guia visual)

Antes de desenhar, gerar ou revisar, leia `docs/estilo/guia-visual.md` e abra 2–3 referências do mesmo
tipo em `refs/estilo-referencias/` (índice por tipo e tag em `docs/estilo/referencias.json`). A entrega só
passa se cumprir o checklist do guia e "aguentar" lado a lado com as referências; arte simples, chapada
ou com olho de anime volta para ajuste.
