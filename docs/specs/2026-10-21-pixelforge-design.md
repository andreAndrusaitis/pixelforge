# PixelForge — Design

Data: 2026-10-21

## Objetivo

Gerar pixel art **por código** dentro do Claude Code, em dois fluxos:

1. **Descrição → pixel art**: Claude escreve uma definição (JSON com paleta + grade
   de caracteres, ou um script Python com primitivas de desenho) e o motor renderiza.
2. **Imagem de referência → pixel art**: conversão algorítmica (encaixe, redução de
   cores, dithering, limpeza, contorno) seguida de retoque manual pelo Claude
   sobre a definição JSON gerada.

Restrição: **nenhum app de terceiros**. Só Python + Pillow + numpy. Testes com
`unittest` (stdlib).

## Inspiração (sem cópia de código)

- `NousResearch/hermes-agent` skill pixel-art: presets nomeados, paletas de
  hardware, ordem *reduzir → quantizar → dithering*.
- `wanshuiyin/auto-claude-code-research-in-sleep` skill pixel-art: ciclo
  iterativo escrever → pré-visualizar → ajustar.
- Lospec: formato `.hex` de paleta (um hex por linha).

## Arquitetura

```
pixelforge.toml          configuração do projeto (saída, presets de conversão)
palettes/                paletas do usuário (*.hex) — sobrepõem as embutidas
art/                     definições-fonte (*.json, *.py)
out/<nome>/              arquivos gerados
pixelforge/
  config.py    carrega pixelforge.toml (procura do cwd para cima) + padrões
  palettes.py  parse de cores, paletas embutidas (pixelforge/palettes/*.hex) e do usuário
  sprite.py    Sprite (numpy RGBA HxWx4), Art (nome, frames, fps), leitura/escrita de spec JSON
  draw.py      Canvas: px, line, rect, ellipse, circle, fill, dither, mirror, outline
  process.py   outline, cleanup (pixels órfãos), trim, cor mais escura
  convert.py   imagem → Art (ConvertOptions)
  export.py    PNG/JPG/WebP/GIF/SVG, escalas, sprite sheet, preview com grade
  cli.py       render | convert | new | palettes
.claude/skills/pixel-art/SKILL.md   como o Claude usa tudo isso
```

## Formato de spec JSON

```json
{
  "name": "slime",
  "size": [16, 16],
  "fps": 6,
  "palette": { ".": "transparent", "k": "#1a1c2c", "g": "#38b764" },
  "pixels": ["....kkkk....", "..."],
  "frames": [["..."], ["..."]]
}
```

- `pixels` (um frame) **ou** `frames` (animação). `.` é transparente por padrão.
- Chaves de paleta: um caractere cada. Cores: `#rgb`, `#rrggbb`, `#rrggbbaa`, `transparent`.
- Erros apontam frame/linha/coluna.

## Script Python (64×64+)

Arquivo `.py` que define `build()` retornando `Canvas`, `Sprite`, `Art` ou lista
(frames). `FPS` opcional no módulo.

## Conversão

1. Abre, corrige orientação EXIF, reduz a fonte para ≤ 512 px.
2. Remove fundo (opcional: `auto` = cor dos cantos, flood-fill a partir da borda com tolerância).
3. Corta margens transparentes (`trim`).
4. Ajusta contraste / saturação / nitidez.
5. Encaixa no tamanho alvo (`contain` | `cover` | `stretch`), reservando 1 px de margem se houver contorno. Reamostragem `box` por padrão.
6. Limiar de alfa → pixels totalmente opacos ou transparentes.
7. Quantização: paleta nomeada ou adaptativa de N cores (median cut só sobre pixels opacos).
   Dithering: `none` | `floyd` | `bayer2` | `bayer4`, com distância "redmean".
8. Limpeza de pixels órfãos (N passadas).
9. Contorno (`auto` = cor mais escura da paleta, ou hex).
10. `--to-spec` grava o resultado como spec JSON para retoque manual.

## Exportação

- Formatos estáticos (png, jpg, webp, svg) com vários frames → sprite sheet horizontal.
- Animados (gif, webp) quando há mais de um frame.
- Nomes: `nome.png` (1x), `nome@16x.png`, `nome.svg`, `nome_preview.png`
  (xadrez de transparência + grade, para inspeção visual).
- JPG recebe cor de fundo (sem alfa); WebP lossless; GIF com índice transparente.

## Testes

`python -m unittest` — paletas, spec (ida e volta), primitivas, conversão
(tamanho, nº de cores, transparência), exportação (formatos válidos), CLI.

## Fora de escopo (por ora)

Edição interativa, IA de geração de imagem, servidores MCP, apps externos.

## v2 — conversão fiel à foto (2026-10-21)

Motivação: o primeiro retrato foi redesenhado do zero e perdeu a semelhança; a
conversão por média borrava olhos e boca. Restrição mantida: só numpy + Pillow.

- `color.py`: OKLab; k-means ponderado (k-means++) com cores agrupadas em 32 níveis/canal.
- `filters.py`: Kuwahara via imagens integrais (restrito aos pixels da figura), Sobel, blocos.
- Resolução de trabalho = tamanho final × K (K ≤ 8, ~512 px). Suavização e bordas rodam nela.
- `resample = "detail"`: blocos lisos → média (OKLab → cor mais próxima); blocos com
  borda (p90−p10 de L > `edge_spread`) → voto pela cor dominante, com peso para a
  minoria mais escura e para o centro do bloco.
- `lines`: escurece o lado escuro de bordas fortes (opcional, estilo ilustrado).
- Pós: `defringe` (franja do fundo), `cleanup`, `merge` (tons com ΔE < limiar).
- Entrada: `crop`, `mask` (comando `mask` cria por polígono/elipse + preview), `focus`, `background`.
- `compare`: foto preparada igual à conversão e reduzida por média; notas de cor
  (ΔE OKLab), traços (correlação de Sobel), forma (IoU) e limpeza (pixels com
  vizinho de mesma cor). A spec guarda `source` e `convert` para comparar após retoque.

Calibração na foto de teste (64px): box puro 96 de semelhança / 77 de limpeza (borrado);
`photo` 92 / 96 com olhos, boca e contorno nítidos.
