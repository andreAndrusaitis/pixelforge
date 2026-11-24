# Manual do PixelForge

Pixel art gerada **por código**, feita para ser usada pelo Claude Code:

- **Descrição → pixel art**: o Claude escreve a arte como dados (grade de caracteres
  em JSON) ou como script Python com primitivas de desenho, e o motor renderiza.
- **Imagem de referência → pixel art**: conversão algorítmica (encaixe, redução de
  cores, dithering, remoção de fundo, contorno) + retoque manual na spec gerada.
- Saída em **PNG, JPG, WebP, GIF animado e SVG**, em qualquer tamanho e escala.
- **Cenas** (vídeo): cenário em camadas com parallax, câmera e transições →
  storyboard, GIF, WebP e MP4 (veja [Cenas](#cenas)).

Só depende de Python 3.11+, Pillow e numpy. Nenhum app externo. MP4 é opcional:
`pip install -e .[video]` (instala `imageio-ffmpeg`, que já traz o FFmpeg).
Servidor MCP para outros projetos: extra opcional `[mcp]` (veja [Servidor MCP](#servidor-mcp-outros-projetos)).
Som: efeitos chiptune, música por código e mixagem (numpy); voz, trilha e ambientes por IA
local no extra opcional `[audio-ia]` (veja [Som](#som)).
Segundo caminho de arte: **rascunho por IA de imagem local** (SDXL na GPU, extra
`[imagem-ia]`) + **pixelização de verdade** no PixelForge (veja [IA de imagem](#ia-de-imagem)).

## Uso com o Claude Code

Abra o Claude Code nesta pasta e peça, por exemplo:

> faz um cavaleiro 32x32 estilo NES, olhando para a direita, com 2 frames de idle

> transforma esta imagem em pixel art 48x48 na paleta do Game Boy: C:\fotos\gato.jpg

A skill [.claude/skills/pixel-art/SKILL.md](../.claude/skills/pixel-art/SKILL.md) é
carregada automaticamente e guia o processo: planejar → desenhar → renderizar →
revisar o preview → ajustar → entregar.

### Skills, agentes e comandos

O repositório traz um pequeno estúdio para o Claude Code (detalhes e contrato de
retorno dos agentes em [docs/agentes.md](agentes.md)):

| Skill (`.claude/skills/`) | Para quê | Comando | Agente (`.claude/agents/`) |
|---|---|---|---|
| `pixel-art` | uma arte avulsa, foto → pixel; aponta para as outras | — | `desenhista` |
| `pixel-personagem` | folha de personagem: retrato + sprite + animações + paleta | `/personagem` | `desenhista`, `animador` |
| `pixel-cenario` | cenário em camadas (parallax), tileset, mapa | `/cenario` | `cenografo` |
| `pixel-cena` | diretor: momento → planos → roteiro → storyboard → revisão → vídeo | `/cena` | `diretor-de-cena` |
| `pixel-som` | efeitos, trilha, voz, mixagem no MP4 | `/som` | `sonoplasta` |
| `pixel-revisao` | checklist visual + lint, problemas com coordenadas | `/revisar` | `revisor-visual` |
| (acervo) | buscar, listar, versões, tags | `/acervo` | — |

Cada skill começa com uma entrevista curta (o Claude pergunta o que você não disse),
segue o ciclo desenhar → pré-visualizar → ajustar e entrega uma versão por vez. Numa
cena, a sessão principal entrevista e coordena: diretor → (desenhista ∥ cenógrafo ∥
sonoplasta) → animador → revisor → render. Os agentes devolvem sempre
`STATUS / ARQUIVOS / RESUMO / PROBLEMAS`.

## Uso direto (linha de comando)

```bash
python -m pixelforge new heroi --size 32 --palette pico8   # cria art/heroi.json em branco
python -m pixelforge render art/heroi.json                  # renderiza spec
python -m pixelforge render art/examples/potion.py          # renderiza script
python -m pixelforge convert foto.jpg --preset sprite --to-spec
python -m pixelforge convert foto.jpg --size 64 --palette gameboy --dither bayer4
python -m pixelforge palettes            # lista paletas
python -m pixelforge palettes pico8 --swatch
python -m pixelforge presets             # lista presets de conversão
```

### Fotos fiéis (retratos, pessoas)

```bash
python -m pixelforge mask refs/foto.jpg --polygon "0.4,0.3 0.7,0.3 0.8,0.8 0.3,0.8" --out refs/foto_mask.png
python -m pixelforge convert refs/foto.jpg --preset photo --mask refs/foto_mask.png --size 64 --to-spec
python -m pixelforge compare art/foto.json     # painel foto | arte | sobreposição + notas
```

O preset `photo` combina: filtro **Kuwahara** (achata áreas, preserva bordas),
redução **detail** (média nos blocos lisos, cor dominante nos blocos com borda —
olhos e boca não borram), paleta **k-means em OKLab** com região de **foco**,
**merge** (funde salpicado de tons quase iguais) e **defringe** (tira franja do
fundo na borda). Fotos de referência ficam em `refs/` (ignorada pelo git).

Opções de saída em qualquer comando que gera imagem:
`--formats png,jpg,webp,gif,svg`, `--scales 1,8,16`, `--out pasta`, `--no-preview`.

Instalação opcional como comando `pixelforge`: `pip install -e .`

## Cenas

O motor de cena anima cenários e câmera a partir de um **roteiro JSON** (o Claude
é o diretor: escreve o roteiro, lê o storyboard e ajusta). Design completo em
[docs/specs/2026-10-21-pixelforge-cena-design.md](specs/2026-10-21-pixelforge-cena-design.md);
já existem as etapas 1–5: cenário com parallax, câmera (com folga, enquadramentos e
close), atores, diálogo, efeitos, transições, títulos, legendas, som e exportação.

```bash
python -m pixelforge cena art/examples/cena-demo/cena-demo.json          # storyboard + GIF + MP4
python -m pixelforge quadro art/examples/cena-demo/cena-demo.json --t 7.5 # PNG ampliado do instante
python -m pixelforge storyboard art/examples/cena-demo/cena-demo.json    # início/meio/fim de cada plano
python -m pixelforge golden                                              # testes de imagem de referência
```

Opções: `--resolucao hd|gba|snes|hd2|hd3|LxA`, `--escala 6`, `--fps 12`,
`--formats gif,webp,mp4` (só `cena`), `--sem-som`, `--sem-ia`, `--out pasta`. Saída em
`out/<nome>/`: `<nome>_storyboard.png`, `<nome>.gif`, `<nome>.mp4` (com som, se houver),
`<nome>.wav`, `<nome>_t7.5s.png`.
Sem o extra `[video]`, o MP4 é pulado com aviso e sai o GIF.

### Roteiro

```json
{
  "name": "chegada",
  "resolucao": "hd",
  "escala": 6,
  "fps": 12,
  "cenario": "cenarios/vale",
  "fundo": "#181425",
  "transicoes": { "entrada": "fade", "saida": { "tipo": "fade", "dur": 1.5 } },
  "planos": [
    { "dur": 2.5, "camera": { "pos": [0, 0] } },
    { "dur": 6,   "camera": { "de": [0, 60], "para": [320, 60], "curva": "suave" } },
    { "dur": 3,   "transicao": "fade-branco", "cenario": "cenarios/cabana" }
  ]
}
```

| Campo | O que é |
|---|---|
| `resolucao` | preset de `[cena.presets]` (`gba` 240×160, `snes` 256×224, `hd` 320×180, `hd2` 480×270, `hd3` 640×360), `"LxA"` ou `[L, A]` |
| `escala`, `fps` | ampliação inteira na exportação (hd × 6 = 1920×1080) e quadros por segundo |
| `cenario` | arte (`.json`/`.py`/`.png`, extensão opcional) ou cenário com `camadas`; um plano pode trocar (nova locação: câmera volta a [0, 0]) |
| `fundo` | cor onde nenhuma camada cobre |
| `planos[].dur` | duração em segundos (obrigatória, exceto em plano com diálogo); cada plano começa onde o anterior termina |
| `planos[].camera` | `pos` [x, y] parada, ou `de` → `para` com `curva` `linear`/`suave`; sem `de`, parte de onde está. Sem `camera`, fica onde parou. Sempre limitada ao cenário |
| `planos[].transicao` | como o plano entra: `corte` (padrão), `fade`, `fade-branco`, `cortina`; ou `{"tipo", "dur", "degraus", "cor"}` |
| `atores`, `planos[].acoes` | personagens e o que fazem (veja Atores) |
| `planos[].dialogo` | fala ou lista de falas (veja Diálogo) |
| `efeitos`, `planos[].efeitos` | chuva, neblina, partículas, tinta, luz, flash, vinheta (veja Efeitos) |
| `transicoes` | `entrada` e `saida` da cena (mesmos tipos) |
| `planos[].titulo`, `planos[].legenda` | cartela/título e legendas (veja Títulos e legendas) |
| `audio`, `planos[].sons`, `acoes[].som` | trilha, ambiente, efeitos e falas (veja Som na cena) |

Caminhos são procurados na pasta do roteiro e depois em `art/`. Campos que começam
com `_` são comentários; campos desconhecidos dão erro com a lista dos válidos. Padrões em `[cena]` do `pixelforge.toml`; a linha
de comando vence o roteiro, que vence a configuração.

### Cenário em camadas

```json
{
  "name": "vale",
  "size": [640, 240],
  "camadas": [
    { "arte": "ceu",       "parallax": 0.1 },
    { "arte": "montanhas", "parallax": 0.4, "pos": [0, 18], "repetir": "x" },
    { "arte": "chao",      "pos": [0, 60] },
    { "arte": "capim",     "parallax": 1.3, "pos": [0, 232], "repetir": "x", "frente": true }
  ]
}
```

De trás para a frente. Na tela, a camada fica em `pos − câmera × parallax`
(0 = parada, 1 = acompanha o chão, > 1 = primeiro plano). `repetir`: `"x"`, `"y"`
ou `"xy"` (arte emendável). `frente: true` desenha por cima dos atores. Arte com vários frames anima no próprio `fps` (ou no `fps` da camada).
`size` é o tamanho do mundo para a câmera; sem ele, vale a extensão das camadas de
parallax 1. Uma arte simples no lugar do cenário vira cenário de uma camada.

Tudo em pixel inteiro, composto na resolução lógica e ampliado só na exportação
(vizinho mais próximo). Fades em degraus (visual retrô). Mesmo roteiro → mesmo vídeo.

### Atores

```json
"atores": {
  "ana": { "sprite": "personagens/ana", "pos": [40, 150], "olhar": "direita", "nome": "Ana" }
},
"planos": [
  { "dur": 4, "camera": { "seguir": "ana" },
    "acoes": [
      { "ator": "ana", "ate": [190, 150] },
      { "ator": "ana", "inicio": 4, "olhar": "esquerda", "anim": "falar" }
    ] }
]
```

`pos` é onde fica o **pé** do ator (a âncora do sprite), em px do cenário; a ordem
de desenho segue o `y` (quem está mais embaixo fica na frente) e as camadas
`frente` passam por cima dos atores. Ações de um plano rodam em paralelo, cada uma
no seu `inicio` (s, relativo ao plano):

| Ação | Efeito |
|---|---|
| `ate` [x, y] | anda até o ponto (`vel` px/s, padrão 40, ou `dur`); usa `anim` (padrão `andar`), vira para o lado do movimento e, ao chegar, troca para `depois` (padrão `parado`). Continua no plano seguinte se não terminou |
| `pos` [x, y] | teletransporta |
| `anim` | troca a animação sem mover |
| `olhar` | `direita` / `esquerda` (espelha o sprite) |
| `aparecer` / `sumir` | `true`, com `fade` (s) opcional em dithering |

O estado (posição, animação, lado) persiste entre planos. O sprite do ator ganha,
na spec JSON, `anchor` [x, y] e `animations` (`{"andar": {"frames": [2, 3, 4, 5], "fps": 8}}`);
em scripts `.py`, as constantes `ANCHOR` e `ANIMATIONS`. Sem `animations`, todos os
frames viram `parado`. Desenhe olhando para a **direita**.

Câmera: além de `pos`/`de`/`para`, `seguir: "<ator>"` (centraliza na horizontal; com
`folga` px, só anda quando o ator sai da faixa central), `zoom` inteiro (1–4, persiste),
`tremor` [amplitude px, duração s] e enquadramentos prontos
`"enquadrar": "geral" | "medio" | "close", "em": "<ator>"` (zoom 1, 2 e 3).

### Diálogo

```json
{ "dialogo": [
    { "ator": "mestre", "retrato": "retratos/mestre", "texto": "Atrasada no primeiro dia." },
    { "ator": "ana", "texto": "Desculpe, mestre — a ponte caiu.", "posicao": "cima" }
] }
```

Caixa com fonte bitmap embutida (5×7, acentos do português), retrato opcional à
esquerda, nome do falante (o `nome` do ator, ou `"nome"` na fala; `""` esconde) e
texto letra a letra (`velocidade` letras/s, padrão 30). Texto longo vira páginas
(`pausa` s entre elas); a última fica `fim` s (padrão 1,5). O ator que fala usa a
animação `falar` (se tiver) enquanto o texto corre. Plano com diálogo e sem `dur`
dura o diálogo inteiro. `posicao`: `baixo` (padrão) ou `cima`; `inicio` posiciona a fala.
`"close": "retrato"` corta para o retrato ampliado sobre a cena escurecida; `"close": "ator"`
dá zoom no rosto de quem fala (fora da caixa) e volta ao plano normal no fim da fala.
`voz` (IA) ou `arquivo` (WAV gravado) dão som à fala (veja Som na cena).

### Títulos e legendas

```json
{ "titulo": { "texto": "Capítulo 7 — A vila", "subtitulo": "o retorno de Lia" } },
{ "dur": 4, "legenda": { "texto": "Três invernos depois, Lia voltou.", "narrar": true } }
```

`titulo`: cartela com `fundo` (padrão preto; `null` = sobre a cena), `cor`, `posicao`
(`centro`/`baixo`), `inicio`, `dur`, `fade` (0,5 s, em degraus). Plano só com título dura
3,5 s se não tiver `dur`. `legenda`: texto, objeto ou lista com `inicio`, `dur` (padrão pelo
tamanho do texto), `posicao`, `cor` e `narrar` (lida pela voz do narrador); contorno de 1 px,
e sobe sozinha se a caixa de diálogo estiver embaixo.

### Som na cena

```json
"audio": {
  "trilha":   { "musica": "tema.json", "volume": 0.55 },
  "ambiente": [{ "efeito": "grilos.json" }, { "descricao": "night forest, crickets" }],
  "eventos":  [{ "inicio": 3, "efeito": "porta", "pan": -0.5 }, { "plano": 4, "inicio": 0.5, "arquivo": "trovao.wav" }],
  "falas":    { "modo": "auto", "voz": "pf_dora", "narrador": "pm_santa" },
  "abafar": 0.35
}
```

Cada som tem uma fonte — `arquivo`, `efeito` (preset/`.json`), `musica` (sequenciador),
`texto` (voz por IA) ou `descricao` (trilha/ambiente por IA) — e `inicio`, `volume`,
`fade_in`, `fade_out`, `pan`, `loop`, `semente`, `variar`. Trilha e ambiente repetem pela cena
e acompanham os fades de entrada/saída. Efeitos também no plano (`"sons": ["porta"]`) e na ação
(`"som": {"efeito": "passo", "repetir": 0.33}` = passos enquanto anda). Falas: `auto` usa voz
por IA (voz da fala > `voz` do ator > `falas.voz`) se houver `[audio-ia]`; sem ela, viram bipes
de máquina de escrever no ritmo das letras (`tom` do ator em Hz), com aviso. `bip` e `nenhum`
fixam o modo. A trilha cai para `abafar` durante as vozes. O `cena` grava `<nome>.wav` e
junta ao MP4; resultados de IA ficam em cache em `out/<nome>/_som/`.

### Testes golden

`python -m pixelforge golden` renderiza os quadros listados em `tests/golden/golden.json` e
compara pixel a pixel com os PNGs de `tests/golden/` (diferenças e diffs em `out/golden/`);
`--regravar` aceita uma mudança visual intencional. Roda também em `unittest`.

### Animação por IA (extra `[video-ia]`)

Imagem → vídeo com **Wan 2.2 TI2V-5B** (Apache-2.0, sem login), local numa GPU de 8 GB, e
**pixelização temporal** de volta para pixel art estável. Design e números em
[docs/specs/2026-10-22-pixelforge-video-ia.md](specs/2026-10-22-pixelforge-video-ia.md).

```json
"planos": [{ "dur": 5, "ia": { "origem": "quadro", "movimento": "wind in the grass, light rain", "dur": 4,
                              "regiao": [[0, 0, 640, 140]] } },
           { "dur": 3, "ia": { "origem": "sprite", "ator": "geraldo", "movimento": "takes off his hat",
                              "paleta": ["geraldo_sem_chapeu"] } }]
"camadas": [{ "arte": "ceu", "parallax": 0.1, "ia": { "movimento": "clouds drifting", "dur": 4, "fps": 8 } }]
```

| Campo | O que é |
|---|---|
| `origem` | `quadro` (o mundo do plano no `inicio`; o clipe substitui cenário + atores, e efeitos/diálogo seguem por cima), `imagem` (`"imagem"`: arte do tamanho da tela) ou `sprite` (`"ator"`: só o sprite anima, fundo recortado). Numa camada do cenário, a origem é a própria camada |
| `movimento` | descrição do movimento (em inglês rende melhor) |
| `dur`, `inicio`, `fps` | segundos de clipe (máx. 5; padrão o plano), início no plano, fps da animação (8–12) |
| `regiao` | `[x, y, l, a]` (ou lista): só isso pode mudar; o resto fica idêntico ao original |
| `laco` | depois do fim do clipe: `segurar` (padrão no plano), `vaivem` (padrão na camada), `repetir` |
| `paleta` | artes cujas cores entram na paleta travada (ex.: o sprite sem chapéu) |
| `semente` | semente inicial |

A pixelização usa grade fixa, **paleta travada** (a da imagem de partida, igual em todos os
quadros), mediana temporal, **histerese de cor** (um pixel só troca de cor se a nova ganhar por
margem), limpeza de órfãos e fps baixo. Cada clipe passa por `estilo comparar` (quadros de
amostra); nota técnica < 85 (ou abaixo da imagem original, se ela já estiver abaixo) gera de
novo com a semente seguinte, até 3 vezes. Clipes brutos ficam em cache por hash em
`out/<cena>/_ia/` — renderizar de novo não regera. Sem o extra (ou com `--sem-ia`) tudo fica
parado, com aviso.

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu128
pip install -e .[video,video-ia]
python -m pixelforge video-ia baixar                     # ~19,6 GB em ~/.cache/pixelforge/models/video
python -m pixelforge video-ia clipe out/cena/cena_t7.5s.png --nativa 640x360 --movimento "light rain" --dur 3
python -m pixelforge video-ia sprite art/personagens/ana.json --anim parado,andar,falar --quem "a girl in a red coat"
python -m pixelforge video-ia pixelizar video.mp4 --tamanho 320x180 --paleta-de art/cenario.png
```

`video-ia sprite` grava `<sprite>_ia.json` com os quadros antigos + os novos, `animations` e o
mesmo `anchor`, pronto para `atores`. Teste da geração real: `PIXELFORGE_TESTES_IA=1`.

### Efeitos

`efeitos` no roteiro (a cena toda) ou no plano; cada um com `tipo`, `inicio`/`dur`
opcionais (s) e parâmetros:

| Tipo | Parâmetros (padrão) |
|---|---|
| `chuva` | `intensidade` 0.5, `vento` 1, `cor` |
| `neblina` | `intensidade` 0.4, `cor`, `velocidade` 6 px/s |
| `particulas` | `estilo` `poeira`/`folhas`/`brasas`/`neve`/`vagalumes`, `quantidade` 30, `cor` |
| `tinta` | `modo` `noite`/`dia`/`sepia`/`por-do-sol` ou `cor` (multiplica), `intensidade` 1 |
| `luz` | `pos` [x, y] no cenário (obrigatório), `raio` 24, `cor`, `intensidade` 0.5, `piscar` 0.3 |
| `flash` | `cor` (branco), `dur` 0.3 |
| `vinheta` | `intensidade` 0.5, `cor` |

Partículas e chuva vêm de uma semente fixa: o mesmo instante dá sempre o mesmo
quadro. Gradações (neblina, luz, vinheta, flash) usam degraus e dithering.
Transições aceitam também `cortina` (duas folhas fechando das laterais) e `cor`.

Exemplo completo: [art/examples/cena-demo/](../art/examples/cena-demo/) — cartela de título,
narração em legenda, céu, tilt, o viajante atravessando o vale com a câmera seguindo com folga,
diálogo com close no retrato e no rosto, batidas na porta; tema chiptune, grilos, vento, passos
e falas; vagalumes, luz da janela e vinheta.
Exemplo completo: [art/examples/cena-demo/](../art/examples/cena-demo/) — céu, tilt,
o viajante atravessando o vale com a câmera seguindo, diálogo com retrato,
vagalumes, luz da janela e vinheta.
## IA de imagem

Segundo caminho, ao lado do desenho por código (que continua sendo o padrão): uma IA de
imagem **local** faz o rascunho e o PixelForge o transforma em pixel art de verdade, com
grade, paleta contida e spec JSON editável. Nada vai para a nuvem.

```bash
python -m pixelforge ia gerar "skinny 12 year old boy, short dark coily buzz cut hair, gray hoodie" --preset retrato
python -m pixelforge ia gerar "tall old man, felt hat, boots" --preset personagem-corpo --ref out/ia/geraldo-retrato/geraldo-retrato_bruta.png
python -m pixelforge ia gerar "street at dusk after rain" --preset cenario --init esboco.png --forca 0.6
python -m pixelforge ia pixelizar qualquer.png --tamanho 128 --cores 24 --paleta endesga32
python -m pixelforge ia variar out/ia/rua/rua.json --forca 0.45      # nova semente, mesma composição
python -m pixelforge ia gerar "tall old man, felt hat" --preset personagem-corpo --refs-estilo 14,1,22 --ciclo
python -m pixelforge ia folha out/ia/rua/rua.json --preset cenario    # arte + 3 refs do tipo + nota técnica
python -m pixelforge ia treinar                                       # LoRA de estilo com as refs do autor
python -m pixelforge ia retocar out/ia/x/x.json ops.json              # retoque por código (ciclo do crítico)
python -m pixelforge ia modelos                                       # pesos baixados e tamanhos
python -m pixelforge ia modelos --baixar padrao
```

Saída em `out/ia/<nome>/`: `<nome>_bruta.png` (rascunho da IA, com o pedido gravado no PNG),
`<nome>.png` e `<nome>@8x.png` (pixel art), `<nome>.json` (spec para retoque por código ou
no estúdio), `<nome>_preview.png`, `<nome>_comparar.png` (rascunho × pixel, para revisar) e
`<nome>_ia.json` (prompt, negativo, semente, modelo, parâmetros, grade detectada e tempos —
tudo para reproduzir). `--semente N` repete uma geração; `--quantas N` gera N sementes seguidas.

**Geração** (`pixelforge/ai_image/`): DreamShaper XL Lightning (SDXL, 6 passos, DPM++ SDE
Karras) + LoRA `pixel-art-xl` fundido nos pesos, UNet guardada em **fp8** (2,6 GB) e offload
para a CPU — cabe em 8 GB de VRAM mesmo com outros apps usando a GPU. Modos: texto → imagem;
imagem → imagem (`--init`: esboço feito por código, quadro de cena ou foto; `--forca`);
referência de personagem (`--ref`, IP-Adapter Plus: mesma roupa e rosto entre gerações;
`--ref-tipo face` só o rosto). O prompt fica `pxfrg style, pixel art, <descrição>, <estilo do
preset>` (o gatilho só com o LoRA de estilo); descreva em inglês. Prompt e negativo acima de 77
tokens são codificados em pedaços (nada é cortado).

**As referências do autor dentro da geração** (o nível mínimo do
[guia visual](estilo/guia-visual.md)):
- **Imagens de estilo**: cada preset tem `tipo` e 3 `refs` do índice
  (`docs/estilo/referencias.json`); elas entram no IP-Adapter **só nas camadas de estilo** da
  UNet (técnica InstantStyle: cor, luz e textura passam, o conteúdo da referência não),
  reduzidas à resolução nativa e reampliadas em múltiplo inteiro. `--refs-estilo 14,1,22` troca
  (as receitas de personagem do estilo citam as suas), `--sem-refs-estilo` desliga. As refs com
  ruído de IA (17, 24, 25, 31; seção 7 de `estilo-pixelforge.md`) ficam de fora dos presets e do treino.
- **Receitas no prompt**: prompt e negativo dos presets saem das receitas e dos "erros de
  amador" de [estilo-pixelforge.md](estilo/estilo-pixelforge.md) (blocos pintados, rim de
  1 px, sombra fria, céu em faixas, reflexo quebrado; negativo: olho de anime, pillow shading,
  degradê, dithering, contorno preto em tudo, ruído).
- **Nota e folha em toda saída**: `<nome>_folha.png` (a arte + as 3 refs do preset + métricas
  fora da faixa) e a nota técnica de `estilo comparar` no `_ia.json`; `ia folha` monta a folha
  de qualquer arte.
- **LoRA de estilo** (`ia treinar`, uso pessoal e local — pesos e dataset ficam em `models/`,
  fora do git, e não se publicam): dataset = as refs na resolução nativa
  (`pixelforge.style`), reampliadas por vizinho (×4–×8) e recortadas em múltiplos de 64; legenda =
  gatilho `pxfrg style` + tipo + tags do índice + números da decomposição (paleta contida,
  contorno seletivo, rim, blocos grandes, sem dithering). Treino em 8 GB: UNet com o LoRA de
  pixel fundido, pesos congelados em fp8 calculados em bf16, gradient checkpointing, AdamW
  8-bit, latentes e textos cacheados, rank 16, min-SNR. O LoRA (`models/pixelforge-estilo/
  pxfrg-estilo.safetensors`, `[ia] estilo_lora`) entra por padrão em todos os presets quando
  existe; `--sem-lora-estilo` gera sem ele.
- **Ciclo por notas** (`ia gerar --ciclo`): N sementes → pixeliza → `estilo comparar` em cada uma;
  a pixelização se corrige pelas métricas fora da faixa (cores, contraste, limpeza); as melhores
  viram imagem → imagem (força 0,4) com prompt/negativo corrigidos pelas métricas, até a nota
  técnica ≥ 90 (`--ciclo-nota`, `--ciclo-voltas`, `--ciclo-variacoes`). A evolução fica em
  `<nome>_ciclo.json` e `<nome>_ciclo.png`; as tentativas em `ciclo/`. A aprovação final (NOTA
  ≥ 95) é do agente `critico-de-arte`.
- **Retoque por código** (`ia retocar <spec> <ops.json>`, `pixelforge/retouch.py`): aplica a
  lista de correções do `critico-de-arte` sobre a spec — troca de cor numa caixa ou de família,
  rampa de N tons, moda (ruído), traço que afina (dobras), rim de 1 px no lado da luz, fundo
  fora de um polígono, apagar, deslocar, escalar, olhos em traço. Grava spec, PNG, folha e nota.
  Na prova, 6 voltas de crítico × retoque levaram os personagens de 69–79 para 72–83: o que
  falta para 95 vem da base (pose, cabelo, volume da roupa) — gere uma base nova antes de retocar.

**Pixelização** (`pixelforge/pixelize.py`, só numpy + Pillow; vale para qualquer imagem):
1. detecta a escala e o deslocamento do pseudo-pixel da IA (perfil de bordas em OKLab;
   escolhe a menor grade com bordas próprias) e alinha as células a ela — `--grade 8` força;
2. reduz cada célula por **moda** (voto da cor, centro pesa mais) ou **mediana**;
3. quantiza para N cores (k-means OKLab no miolo das células), uma paleta nomeada, `.hex`
   ou a **paleta da cena** (`--paleta` com um `.png`/`.json` de outra arte);
4. limpa órfãos, funde tons quase iguais, remove o fundo (sprite) e põe contorno opcional
   (`--contorno seletivo`: cada pixel de contorno é a versão escura da cor vizinha).

**Presets** (`[ia.presets.*]` no `pixelforge.toml`, montados a partir de
`refs/estilo-referencias/`: pixel "pintado", paleta contida, luz lateral dramática, rosto
discreto sem olho de anime, perspectiva atmosférica): `retrato` (768×1024 → 96×128, 28 cores),
`personagem-corpo` (832×1216 → 104×152, 28 cores, fundo removido), `cenario` (1344×768 →
168×96, 40 cores), `cena-noturna`. Cada um tem prompt-base, negativo (anime eyes, big eyes,
blurry, 3d, photo...), resolução de geração, tamanho final (`"auto"` = grade detectada) e cores.

Instalação (Windows, GPU NVIDIA):

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu128
pip install -e .[imagem-ia]
python -m pixelforge ia modelos --baixar padrao
```

- **Pesos** em `models/` (ignorada pelo git; `[ia] modelos` ou `PIXELFORGE_MODELS` mudam).
  Nesta máquina `models/` é uma junção para `~/.cache/pixelforge/models`, fora do OneDrive.
  Todos são abertos (sem aceitar licença nem login); um repositório restrito nunca é baixado
  — o comando para e diz onde aceitar.
- Downloads: DreamShaper XL Lightning fp16 6,9 GB, IP-Adapter (encoder ViT-H + Plus + Plus
  Face) 4,2 GB, VAE fp16-fix 0,3 GB, LoRAs pixel-art-xl e PixelArtRedmond 0,17 GB cada —
  11,8 GB, ~4 min. PyTorch cu128 + diffusers no `.venv`: ~5 GB.
- Medido numa RTX 4060 Laptop 8 GB (com ~1,8 GB da VRAM ocupada por outros apps): carregar
  o modelo 60–100 s (≈ 3 min com IP-Adapter); 1ª imagem 40–70 s, as seguintes **17–25 s**
  (768×1024) e 25–45 s (1344×768); com `--ref`, ~2 min por imagem de corpo inteiro. Pico de
  VRAM ~2,9 GB em texto → imagem. Gerar várias de uma vez (`--quantas`) amortiza a carga.
- Por que SDXL e não um modelo mais novo: Z-Image Turbo (6B, Apache-2.0) e FLUX.2 klein dão
  imagens melhores em geral, mas pedem ~16–20 GB em bf16 (só cabem quantizados em GGUF),
  não têm IP-Adapter e o imagem → imagem com LoRA de pixel ainda não funciona bem neles. O SDXL
  tem o ecossistema completo (LoRA de pixel, IP-Adapter, img2img) dentro de 8 GB.
- Sem o extra, `ia pixelizar` funciona normalmente; `ia gerar` diz o que instalar.
- Testes: a pixelização roda sempre; os de geração só com `PIXELFORGE_TESTES_IA=1`.

## Acervo

Índice de todos os assets de `art/` em `art/acervo.json`: nome, tipo (`personagem`,
`cenario`, `objeto`, `cena`, `som`), tags, projeto de origem, versão, arquivo-fonte e
miniatura (`out/<nome>/<nome>_miniatura.png`).

```bash
python -m pixelforge acervo indexar                 # varre art/ e reconstrói o índice (+ miniaturas)
python -m pixelforge acervo listar --tipo personagem --tag floresta
python -m pixelforge acervo buscar "heroi noite"    # todas as palavras: nome, tag, tipo, projeto
python -m pixelforge acervo tag heroi_v2 noite capa --remover dia --tipo personagem --projeto coletanea
python -m pixelforge acervo versoes heroi_v2        # histórico: heroi → heroi_v2 → ...
```

- **Versões**: `heroi_v2` herda de `heroi_v1` (ou de `heroi`, a v1 implícita).
- **Metadados no próprio arquivo** (opcional, têm prioridade): spec/roteiro `.json` com
  `"acervo": {"tipo": "personagem", "tags": ["floresta"], "projeto": "coletanea", "herda": "heroi"}`;
  script `.py` com `ACERVO = {...}` (lido sem executar o script).
- Sem metadados, o tipo vem da pasta (`personagens/`, `cenarios/`, `cenas/`, `sons/`) ou do
  conteúdo (roteiro com `planos` = cena; `camadas` = cenário, e as artes dessas camadas
  também viram cenário). As pastas viram tags.
- Tags e tipo/projeto dados por `acervo tag` ficam no índice e sobrevivem à reindexação
  (tags declaradas no arquivo-fonte só saem editando o arquivo).

## Estúdio (interface web local)

```bash
python -m pixelforge studio            # http://127.0.0.1:8765  (--porta 0 = porta livre, --abrir)
```

Só stdlib + HTML/JS estático (funciona offline), escuta só em `127.0.0.1` e a API
nunca lê/grava fora do repositório. No Claude Code, o servidor está em
`.claude/launch.json` (`estudio`) para abrir no painel de navegador.

- **Galeria**: miniaturas do acervo, filtros por texto/tipo/projeto/tag, versões de
  cada família lado a lado; editar tags; botão *Reindexar*.
- **Visualizador**: zoom inteiro, grade, fundo xadrez, tocar animações (`frames`/`fps`
  e o campo opcional `animations`), trocar a paleta ao vivo (ou cor a cor).
- **Retoque**: lápis (B), borracha (E / botão direito), conta-gotas (I), balde (G),
  desfazer/refazer (Ctrl+Z / Ctrl+Y), cores novas; *Salvar na spec* grava o `.json`
  no mesmo formato (`dump_spec`, demais campos preservados) e atualiza o preview;
  *Salvar como nova versão* cria `<base>_vN.json` herdando da atual (único jeito para
  scripts `.py`, imagens e `art/examples/`, que é só leitura).
- **Comparar**: antes/depois entre versões (lado a lado, cortina, alternar) e com a
  foto de referência (painel do `compare`, para artes com `source`).
- **Cena**: vídeo, storyboard e linha do tempo com os planos como blocos e scrub por
  quadro; com o motor de cena (`pixelforge/scene/`) mostra o quadro exato do instante.
- **Pedidos ao Claude**: marque pontos/retângulos sobre uma arte ou um quadro, escreva
  o que mudar → grava `pedidos/<data>-<arte>.md` + a imagem anotada. O Claude lê
  `pedidos/` (veja [pedidos/README.md](../pedidos/README.md)).

## Servidor MCP (outros projetos)

Para outro projeto (ex.: a coletânea) usar o motor **sem shell**, o PixelForge tem um
servidor MCP local (stdio), no extra opcional `[mcp]` (SDK oficial `mcp`):

```bash
pip install -e .[mcp]
python -m pixelforge mcp            # stdio; quem inicia é o cliente MCP (Claude Code)
```

Ferramentas (caminhos **relativos à raiz do PixelForge**; nada fora do repositório é
aceito — artes de outros projetos ficam em `art/<projeto>/`, como `art/coletanea/`):

| Ferramenta | Faz | Devolve |
|---|---|---|
| `render` | `arquivos`, `formatos`, `escalas`, `ver` | arquivos gerados; com `ver`, o preview como imagem |
| `quadro` | `roteiro`, `t`, `resolucao`, `escala`, `ver` (padrão sim) | PNG do instante + imagem |
| `storyboard` | `roteiro`, `resolucao`, `escala`, `ver` (padrão sim) | storyboard + imagem (reduzida se > 1600 px) |
| `cena` | `roteiro`, `formatos` (`gif,webp,mp4`), `resolucao`, `escala`, `fps` | storyboard + vídeos |
| `personagem` | `modelo`, `variantes`, `paleta`, `mapa`, `aseprite`, `gravar_specs`, `ver` | folha, sprite, retrato, GIFs, specs |
| `lint` | `arquivos`, `verificacoes`, `fundo` | `problemas` por arquivo com `x`, `y`, quadro |
| `acervo_buscar` | `texto`, `tipo`, `tags`, `projeto` | `itens` do acervo |
| `som_efeito` | `fonte` (preset ou `.json`), `variar`, `semente`, `nome` | WAV em `out/som/` |

Cada resposta é um JSON com `ok`, `comando` (o equivalente na linha de comando),
`arquivos` (relativos à raiz), `saida` e `erro`/`avisos`. Cada chamada roda
`python -m pixelforge …` num subprocesso na raiz do repositório.

**Registrar em outro projeto** (rode na pasta do outro projeto; troque o caminho):

```bash
claude mcp add pixelforge -e PIXELFORGE_RAIZ=C:/caminho/pixel-IA -- C:/caminho/pixel-IA/.venv/Scripts/python.exe -m pixelforge mcp
```

O servidor não depende da pasta de trabalho em que o cliente o inicia: a raiz vem de `--raiz`,
`PIXELFORGE_RAIZ`, da pasta atual (se tiver `pixelforge.toml`) ou, por fim, da pasta do
pacote instalado com `pip install -e .`. Use `-s project` para gravar no `.mcp.json` do
projeto (compartilhado) ou `-s user` para todos os projetos. Equivalente em `.mcp.json`:

```json
{
  "mcpServers": {
    "pixelforge": {
      "command": "C:/caminho/pixel-IA/.venv/Scripts/python.exe",
      "args": ["-m", "pixelforge", "mcp", "--raiz", "C:/caminho/pixel-IA"]
    }
  }
}
```

Confira com `claude mcp list` (deve aparecer `pixelforge … ✓ Connected`). Teste
automatizado com o cliente MCP oficial: `tests/test_mcp.py` (pulado sem o extra).

## Estrutura

```
pixelforge.toml        configuração: formatos, escalas, presets de conversão, [cena]
art/                   suas artes-fonte (.json / .py); exemplos em art/examples/
palettes/              suas paletas .hex (sobrepõem as embutidas)
art/acervo.json        índice do acervo (python -m pixelforge acervo indexar)
pedidos/               pedidos do estúdio para o Claude (<data>-<arte>.md + .png)
out/<nome>/            arquivos gerados (ignorado pelo git)
pixelforge/            o motor
  palettes.py  cores e paletas      sprite.py   modelo + spec JSON
  draw.py      Canvas/primitivas    process.py  contorno, limpeza, merge, defringe
  convert.py   imagem → pixel art   export.py   formatos, escalas, preview
  color.py     OKLab + k-means      filters.py  Kuwahara, Sobel, blocos
  masks.py     máscaras por formas  compare.py  semelhança com a foto
  config.py    pixelforge.toml      cli.py      linha de comando
  artfile.py   carrega .json/.py/.png
  scene/       motor de cena: script.py (roteiro), library.py (artes e camadas),
               actors.py (sprites com animações), timeline.py (planos → quadros),
               compose.py (quadro, storyboard), dialog.py + font.py (caixa e fonte
               bitmap), effects.py (chuva, luz...), video.py (GIF/WebP/MP4)
  character.py folha de personagem   animate.py  animações + anchor
  recolor.py   troca de paleta      shading.py  sombra/contorno automáticos
  lint.py      lint de pixel art    tiles.py    tilesets, autotile, mapas
  aseprite.py  .ase e JSON/sheet    cli_art.py  comandos do motor de arte
  audio/       som: sfx (efeitos), music (sequenciador), mix (mixagem/MP4), wavio, ai/ (IA local)
  library.py   acervo (índice)      studio/     estúdio web (servidor + static/)
  mcp_server.py servidor MCP (stdio) para outros projetos
  pixelize.py  rascunho de IA → pixel art (grade, moda/mediana, paleta, limpeza)
  ai_image/    IA de imagem local: presets, models (catálogo/download), generate (SDXL), cli
refs/                  fotos de referência e máscaras (ignorado pelo git)
tests/                 python -m unittest discover -s tests
docs/specs/            documentos de design
docs/agentes.md        equipe de agentes, fluxo e contrato de retorno
.claude/               skills/, agents/, commands/ do Claude Code
```

## Formato da spec

```json
{
  "name": "slime",
  "size": [16, 16],
  "fps": 4,
  "palette": { ".": "transparent", "k": "#1a1c2c", "g": "#38b764" },
  "pixels": ["....kkkk....", "..."]
}
```

Use `frames` (lista de grades) no lugar de `pixels` para animação.

### Animações e âncora

Opcionalmente, a spec diz onde fica o "pé" (`anchor`) e quais quadros formam cada
animação (formato usado pelo motor de cena):

```json
{
  "anchor": [16, 31],
  "animations": {
    "parado": { "frames": [0, 1], "fps": 3 },
    "andar":  { "frames": [2, 3, 4, 5], "fps": 8 }
  }
}
```

Sprites são desenhados olhando para a **direita**; a esquerda é espelho automático.
Sem `animations`, o sprite inteiro vira `parado`.

## Motor de arte

### Folha de personagem (`character` / `personagem`)

> **Estilo pintado.** `"estilo": "pintado"` no modelo troca o acabamento pelo do nível das referências.
> - Sprite 64×104 com ~4,4 cabeças e retrato 112×112.
> - Rampas de 6 tons com hue shifting, sombra em blocos por parte e pincelada.
> - Olhos de 1–2 px, luz de borda dupla e contorno seletivo.
>
> O comando mostra a nota técnica de `estilo comparar`. A entrega passa pelo ciclo do crítico
> (`docs/agentes.md`). O kit de pintura (`pixelforge.paint`: `Paint` para figuras e `Scene` para cenários,
> com céu em faixas, nuvens em blocos, perspectiva atmosférica, folhagem, moldura de silhueta, reflexo
> quebrado, halo, partículas e fios) é o mesmo dos personagens finais em `art/coletanea/veu/final/`.

Um **modelo** de personagem (JSON) guarda o que não pode mudar entre artes — cores,
proporções, cabelo, roupa, acessórios — e gera **retrato**, **sprite de corpo** e
**animações** sempre coerentes. Exemplo completo: [art/examples/lia.personagem.json](../art/examples/lia.personagem.json).

```json
{
  "tipo": "personagem",
  "name": "lia",
  "tamanho": [32, 32],
  "retrato": 48,
  "idade": "adulto",
  "proporcoes": { "altura": 30, "cabeca": 13, "tronco": 9, "ombros": 10 },
  "cores": { "pele": "#e8b796", "cabelo": "#6b3a2a", "olhos": "#3b7d4f", "roupa": "#3b5dc9",
             "roupa2": "#f4f4f4", "calca": "#333c57", "sapato": "#4a2f2a",
             "acessorio": "#ffcd75", "boca": "#b55058" },
  "rampas": { "pele": ["#f6d3b8", "#e8b796", "#c98a6e", "#a0604f"] },
  "contorno": "selout",
  "luz": "cima-esquerda",
  "camadas": {
    "cabelo": { "estilo": "rabo", "franja": "lado", "volume": 1 },
    "roupa": { "estilo": "casaco", "mangas": "longas" },
    "pernas": { "estilo": "calca" },
    "acessorios": ["cachecol"],
    "marcas": [],
    "barba": "nenhuma"
  },
  "expressoes": ["neutro", "feliz", "bravo", "triste", "surpreso"],
  "andar": 4,
  "paletas": { "uniforme_vermelho": { "roupa": "#b13e53", "roupa2": "#ffcd75" } },
  "variantes": {
    "cicatriz": { "camadas": { "marcas": ["cicatriz"] } },
    "idosa": { "idade": "idoso" }
  },
  "extras": [
    { "nome": "broche", "vistas": ["frente", "retrato"], "presa_a": "tronco",
      "pos": [2, 1], "grade": ["y"], "paleta": { "y": "#ffcd75" } }
  ]
}
```

| Chave | Valores |
|---|---|
| `tamanho` / `retrato` | sprite `[L, A]` (pé na última linha) / lado do retrato (40–128) |
| `idade` | `crianca` (cabeça maior, mais baixo) · `adulto` · `idoso` (cabelo grisalho, rugas) |
| `proporcoes` | `altura`, `cabeca`, `largura_cabeca`, `tronco`, `ombros` (px; padrão pela idade) |
| `cores` | por material; `capa`, `chapeu`, `oculos` opcionais. Rampas [luz, base, sombra, escuro] automáticas (ou em `rampas`) |
| `camadas.cabelo` | `estilo`: curto, longo, rabo, coque, espetado, cacheado, careca · `franja`: reta, lado, repartida, nenhuma · `volume` (px) |
| `camadas.roupa` | `estilo`: camisa, casaco, vestido, manto · `mangas`: longas, curtas, sem |
| `camadas.pernas` | `estilo`: calca, short, saia |
| `camadas.acessorios` | oculos, chapeu, cachecol, capa, cinto |
| `camadas.marcas` / `barba` | cicatriz, sardas, rugas / nenhuma, cheia, bigode, cavanhaque |
| `contorno` / `luz` | `selout`, `#rrggbb` ou `nenhum` / `cima-esquerda`, `cima`, `direita`... |
| `paletas` | cores nomeadas (uniformes etc.), trocadas **antes** de sombrear |
| `variantes` | trechos do modelo mesclados por cima (listas são substituídas): roupa nova, cicatriz, idade |
| `extras` | camadas desenhadas à mão (grade + paleta) presas à `cabeca`, ao `tronco` ou à `tela` |

```bash
python -m pixelforge character art/examples/lia.personagem.json               # gera tudo
python -m pixelforge character art/examples/lia.personagem.json --variante cicatriz --paleta uniforme_vermelho
python -m pixelforge character art/examples/lia.personagem.json --mapa noite --no-spec --aseprite
```

Saída: `out/<nome>/<nome>_preview.png` (folha: expressões, 4 direções, andar, rampas),
`<nome>_sprite.png`, `<nome>_retrato.png`, um GIF por animação e, com `--aseprite`,
`.aseprite` **em camadas** (capa, cabelo_tras, corpo, roupa, rosto, cabelo, acessorio,
contorno). As specs `<nome>.json` (sprite) e `<nome>_retrato.json` vão para a pasta do
modelo (ou `--spec-dir`), prontas para a cena:

- sprite: `parado` (respira e pisca), `respirar`, `piscar`, `falar`, `andar` (4 ou 6
  quadros) olhando para a direita; `parado_frente`, `falar_frente`, `andar_frente`,
  `parado_costas`, `andar_costas`; `anchor` no pé.
- retrato: uma animação por expressão (`neutro`, `feliz`...), `<expressão>_falar`,
  `<expressão>_piscar`, além de `parado` e `falar` (primeira expressão).

### Animar qualquer sprite (`animate` / `animar`)

Para sprites desenhados à mão: gera `parado` (respirar + piscar), `respirar`, `piscar`,
`falar` e `andar` a partir da pose parada e grava `animations` + `anchor`.

```bash
python -m pixelforge animate art/heroi.json --hip 22 --eyes "13,10 18,10" --mouth 15,13,2,1 --walk 4 --to-spec art/heroi.json
```

`--hip` (linha do quadril; abaixo dela as pernas balançam), `--chest`, `--split`
(coluna entre a perna de trás e a da frente), `--no-idle`, `--walk 0|4|6`.

### Troca de paleta (`recolor`)

```bash
python -m pixelforge recolor art/examples/potion.py --swap "#b13e53:#3b5dc9"     # leva a rampa junto
python -m pixelforge recolor art/heroi.json --map noite                         # tintas: dia, noite, por-do-sol, fantasma, sepia
python -m pixelforge recolor art/heroi.json --maps palettes/uniformes.json --map casa_azul --to-spec art/heroi_azul.json
python -m pixelforge recolor art/heroi.json --palette gameboy
python -m pixelforge recolor art/heroi.json --ramps                             # mostra a rampa automática de cada cor
```

Arquivo de mapas: `{"mapas": {"casa_azul": {"#b13e53": "#3b5dc9", "#ffcd75": "#f4f4f4"}}}`.
`--swap` troca a cor **e os tons da rampa dela** (mantém o desvio de luz/matiz);
`--exact` troca só a cor exata. Rampas automáticas fazem *hue shifting* em OKLCh
(sombra puxa para azul-violeta, luz para amarelo, 12° por tom).

### Sombra e contorno automáticos (`shade` / `sombrear`)

Arte chapada (uma cor por material) → sombreada pela direção da luz e contornada:

```bash
python -m pixelforge shade art/examples/arbusto.json --light cima-esquerda --outline selout --keep "#b13e53"
```

`--outline selout|auto|#rrggbb|nenhum`, `--shadow 0–1` (maior = menos sombra),
`--highlight 0–1`, `--keep` (cores que ficam intactas: olhos, frutas, detalhes).

### Lint (`lint`)

```bash
python -m pixelforge lint art/heroi.json art/examples/slime.json
python -m pixelforge lint art/heroi.json --checks orfao,jaggies --bg "#1a1c2c" --strict --json
```

Verificações: `orfao` (pixel isolado de tom quase igual — não acusa olhos/brilhos),
`contorno` (falha no contorno), `cores` (cores demais para o tamanho; tons quase
iguais), `banding` (faixas paralelas acompanhando a borda), `jaggies` (degraus
irregulares como 3-1-3) e `contraste` (silhueta que some sobre o fundo; padrão
cinza médio, `--bg` para outros). Saída com coordenadas `(x, y)` e quadro;
`--strict` sai com código 1 se houver problema.

### Tilesets e mapas (`tileset`, `tilemap` / `mapa`)

```bash
python -m pixelforge tileset art/examples/campo.tileset.json   # folha + campo_tiles.json (máscara de cada tile)
python -m pixelforge tilemap art/examples/vila.mapa.json       # mapa montado a partir da grade
```

Terrenos com `modo` `blob47` (8 vizinhos, com cantos internos), `blob16` (4
vizinhos) ou `cheio`; gerados por código (`cor`, `borda`, `textura`: liso, pontos,
grama, ondas, tijolo; `recuo`, `espessura`) ou lidos de uma folha desenhada à mão
(`imagem`, 8 colunas, na ordem da folha gerada). O mapa é uma grade de caracteres com
`legenda`, `base` (terreno de fundo) e `ordem` opcional. Bits das máscaras:
N=1, NE=2, E=4, SE=8, S=16, SW=32, W=64, NW=128.

### Aseprite, Godot e Unity (`aseprite`)

```bash
python -m pixelforge aseprite export art/examples/lia.json --layout linhas --scale 2 --ase
python -m pixelforge aseprite import arte.aseprite --to-spec art/arte.json
python -m pixelforge aseprite import folha.json --to-spec art/arte.json      # JSON + PNG exportados pelo Aseprite
```

`export` grava `<nome>.png` (uma linha por animação) + `<nome>.json` no formato do
Aseprite (`frames`, `meta.frameTags` = animações, `meta.slices` "anchor" com o pivô),
que os importadores de Godot e Unity leem; `--ase` também grava `.aseprite`.
`import` lê `.ase`/`.aseprite` com parser próprio (RGBA, tons de cinza, indexado;
camadas visíveis, opacidade, modo normal; tags → `animations`) e quadros repetidos
viram um só.

## Paletas embutidas

`pico8` (16), `sweetie16` (16), `endesga32` (32), `gameboy` (4), `c64` (16),
`gray8` (8), `1bit` (2). Adicione outras em `palettes/` (veja o README de lá).

## Som

Tudo sai em `out/som/` (WAV PCM 16 bits). O núcleo (efeitos, música, mixagem) só usa
stdlib + numpy; a IA local é opcional (extra `[audio-ia]`).

```bash
python -m pixelforge som efeito pulo                        # preset → out/som/pulo.wav
python -m pixelforge som efeito --lista                     # passo, pulo, moeda, magia, golpe, porta, explosao, menu, dano, sino
python -m pixelforge som efeito --todos
python -m pixelforge som efeito golpe --variar 0.15 --semente 3   # variação determinística
python -m pixelforge som efeito meu_efeito.json --json      # parâmetros próprios
python -m pixelforge som musica docs/som/tema_aventura.json --loop   # chiptune por código
python -m pixelforge som musica "mysterious theme, harpsichord and strings, 90 bpm" --duracao 30   # IA
python -m pixelforge som voz "Atrasada no primeiro dia." --voz pf_dora                              # IA
python -m pixelforge som ambiente "gentle rain on leaves, distant thunder" --duracao 10 --loop      # IA
python -m pixelforge som voz "Atrasada no primeiro dia." --nome fala_chegada   # fala usada no exemplo abaixo
python -m pixelforge som mix docs/som/roteiro_exemplo.json --video out/cena/cena.mp4
python -m pixelforge som info out/som/*.wav                 # duração, pico e RMS
```

### Efeitos chiptune (estilo sfxr)

Um efeito é uma lista de **camadas** somadas. Cada camada: `onda` (`quadrada`, `triangulo`,
`serra`, `seno`, `ruido`), `freq` (Hz), `deslize` (oitavas/s; negativo desce), `deslize_acel`,
`duty` e `duty_varre` (quadrada), envelope `ataque`/`decaimento`/`sustentacao` (nível)/`manter`/
`soltura` (s) com `curva`, `vibrato` (semitons) e `vibrato_vel` (Hz), `arpejo` (semitons, ex.
`[0, 4, 7]`) com `arpejo_passo` e `arpejo_ciclo`, `harmonicos` (`[[razão, ganho], …]`),
`passa_baixa`/`passa_alta` (Hz), `bits`, `volume`, `atraso`. Acentos nas chaves são opcionais.

```json
{"camadas": [
  {"onda": "serra", "freq": 800, "deslize": -3, "decaimento": 0.2, "passa_baixa": 3000},
  {"onda": "ruido", "freq": 4000, "atraso": 0.05, "decaimento": 0.1, "volume": 0.3}
]}
```

`{"base": "pulo", "camadas": [{"freq": 400}]}` ajusta um preset. Mesma entrada + mesma
`--semente` = mesmo arquivo, byte a byte.

### Música por código

Canais com notas em texto (`docs/som/tema_aventura.json`): `C4`, `F#3`, `Bb5:0.5` (duração
em tempos), `.` pausa, `-` estende a anterior, `|` só separa compassos. `bpm`, `loop`
(repetições) e, por canal, `dur` padrão, `volume` e qualquer parâmetro de camada (onda, duty,
envelope, vibrato…). Canal com `"bateria": true` usa `k` bumbo, `s` caixa, `h` chimbal, `x` batida.

### Mixagem e vídeo (API para o motor de cena)

Roteiro de áudio (`docs/som/roteiro_exemplo.json`); tempos em segundos:

```jsonc
{
  "name": "chegada",
  "duracao": 12,                 // opcional: padrão = fim do último som ou duração do vídeo
  "abafar": 0.35,                // trilha cai para 35% enquanto houver fala
  "trilha": {"musica": "tema.json", "volume": 0.5, "fade_in": 1, "fade_out": 2},
  "eventos": [{"t": 3.0, "efeito": "porta", "pan": -0.5}, {"t": 4, "arquivo": "out/som/chuva.wav"}],
  "falas":   [{"t": 6.0, "arquivo": "out/som/fala1.wav"}, {"t": 9, "texto": "Bem-vinda.", "voz": "pm_alex"}],
  "video": "out/cena/cena.mp4"   // opcional: grava também <nome>.mp4 com o som
}
```

Cada item aceita uma fonte — `arquivo` (WAV), `efeito` (preset, `.json` ou objeto),
`musica` (`.json` do sequenciador) ou `texto` (voz por IA) — e `t`, `volume`, `fade_in`,
`fade_out`, `pan` (-1…1), `loop`, `semente`, `variar`. A trilha repete (loop) até o fim.
Caminhos relativos valem a partir da pasta do roteiro.

Em Python (o que a etapa 5 da cena vai chamar):

```python
from pixelforge.audio.mix import Clip, mix_clips, render_plan, mux_video
from pixelforge.audio.wavio import write_wav

samples, rate = render_plan(plano_dict, base_dir=Path("art/cenas"))   # (n, 2) float32, taxa
write_wav("out/cena/cena.wav", samples, rate)
mux_video("out/cena/cena.mp4", "out/cena/cena.wav", "out/cena/cena_som.mp4")   # extra [video]

# ou com amostras já prontas:
faixa = mix_clips([Clip(trilha, 44100, loop=True, volume=0.5),
                   Clip(fala, 24000, start=6.0, speech=True)], duration=12.0, duck=0.35)
```

`mux_video` copia o vídeo, codifica o áudio em AAC e completa com silêncio até o fim do vídeo.

### IA local (extra `[audio-ia]`)

| Comando | Modelo | Saída | Observações |
|---|---|---|---|
| `som voz` | Kokoro-82M (Apache-2.0) | 24 kHz mono | vozes pt-BR `pf_dora`, `pm_alex`, `pm_santa`; não precisa instalar espeak-ng (vem no `espeakng-loader`) |
| `som ambiente` | AudioLDM2 (`cvssp/audioldm2`) | 16 kHz mono | aberto, sem login; prompt em inglês |
| `som ambiente --modelo stable-audio` | Stable Audio Open 1.0 | 44,1 kHz estéreo | repositório **restrito**: aceite a licença no Hugging Face e rode `hf auth login` |
| `som musica "<descrição>"` | ACE-Step 1.5 (MIT) | 48 kHz estéreo | ambiente próprio (ver abaixo); prompt em inglês: gênero, instrumentos, clima, bpm |

Instalação (Windows, GPU NVIDIA):

```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128
pip install -e .[video,audio-ia]
python -m pixelforge som instalar musica      # clona o ACE-Step e cria o ambiente dele (uv)
```

- O **ACE-Step** fixa versões próprias (torch 2.7.1, transformers < 4.58), por isso roda num
  ambiente separado em `<modelos>/ace-step/.venv`, chamado por subprocesso.
- **Pesos** ficam em `~/.cache/pixelforge` (fora do repositório e do OneDrive); mude com
  `PIXELFORGE_MODELS` ou `[som] modelos` no `pixelforge.toml`. Baixam no primeiro uso.
- Medido numa RTX 4060 Laptop (8 GB), modelos já baixados: voz ~10 s por frase (a 1ª
  chamada carrega o modelo, ~35 s); ambiente 8–10 s em ~30 s (AudioLDM2, 100 passos);
  trilha de 20 s em ~2 min (ACE-Step turbo + LM 0.6B, INT8 e offload automáticos para 8 GB;
  `--sem-lm` cai para ~1 min com menos coerência).
- Downloads: PyTorch cu128 ~3 GB no `.venv`; Kokoro 0,3 GB; AudioLDM2 4,2 GB; ACE-Step
  ambiente 6,2 GB + pesos 10,8 GB (DiT turbo 4,5, LM 0.6B 1,3, LM 1.7B 3,5 — baixado junto
  com o repositório principal, não usado em 8 GB —, Qwen3-Embedding 1,2, VAE 0,3).
- Sem o extra, os comandos de IA dizem o que instalar; o resto do som funciona normalmente.
- Testes de IA: `voz` roda se o extra estiver instalado; trilha e ambiente só com
  `PIXELFORGE_TESTES_IA=1` (lentos).

## Inspiração

Ideias de arquitetura (sem código copiado) de:
[NousResearch/hermes-agent pixel-art](https://github.com/NousResearch/hermes-agent) (presets,
ordem reduzir → quantizar → dithering) e
[wanshuiyin/auto-claude-code-research-in-sleep pixel-art](https://github.com/wanshuiyin/auto-claude-code-research-in-sleep)
(ciclo desenhar → pré-visualizar → ajustar).
