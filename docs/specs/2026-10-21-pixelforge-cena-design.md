# PixelForge Cena — Design

Data: 2026-10-21 · Status: etapas 1–5 implementadas (ver "Etapa 5 e acabamento" no fim)

## Objetivo

Evoluir o PixelForge de "gerador de pixel art" para um **mini-estúdio de pixel**:
além de desenhar personagens, cenários e objetos, **animar cenas completas** e
exportar vídeo (estilo cutscene de RPG 16 bits).

Ideia emprestada do `latent-spaces/brag` (sem código copiado): separar o
**diretor** do **motor**.

```
diretor (skill do Claude)      decide o momento, os planos e o ritmo;
                               escreve o ROTEIRO DE CENA (JSON)
   │
   ├─► motor de ARTE           (já existe) sprites, cenários, retratos
   └─► motor de CENA           (novo) compõe camadas, move atores e câmera,
                               diálogos, efeitos → storyboard → GIF / WebP / MP4
```

O Claude é diretor e desenhista: desenha as artes por código, escreve o roteiro,
**revisa o storyboard renderizado** (Read) e ajusta antes do vídeo final — o
mesmo ciclo desenhar → pré-visualizar → ajustar da skill `pixel-art`.

Primeiro uso previsto: cenas dos livros do projeto `coletanea` (a skill
`/filmar` de lá é o diretor). O motor não conhece a coletânea; só lê roteiros.

## Restrições

- Mantidas: Python 3.11+, Pillow, numpy, testes com `unittest`, textos em português.
- **Nova dependência opcional**: MP4 precisa de FFmpeg. Proposta: extra
  `pip install -e .[video]` com `imageio-ffmpeg` (traz o binário, sem instalar nada
  à mão). Sem o extra, GIF e WebP animado continuam funcionando.
  → Muda a regra "só Pillow + numpy" do CLAUDE.md; **decisão do autor**.
- Pixel inteiro sempre: câmera e atores em coordenadas inteiras, escala final
  inteira com vizinho mais próximo. Nada de suavização, rotação livre ou subpixel.

## Padrões visuais

- Resolução lógica padrão **320×180**, escala 6 → 1920×1080 (16:9 exato).
- `fps` padrão 12 (animação de sprite) — o vídeo sai a 12 ou 24 (quadro duplicado).
- Personagem padrão 32 px de altura; retrato de diálogo 48×48 ou 64×64.

## Extensões no formato de arte

### Sprite com várias animações

A spec atual tem `frames` + `fps` (uma animação). Acrescenta-se, opcional:

```json
{
  "name": "heroi",
  "size": [32, 32],
  "anchor": [16, 31],
  "frames": [["..."], ["..."]],
  "animations": {
    "parado":  { "frames": [0, 1],       "fps": 3 },
    "andar":   { "frames": [2, 3, 4, 5], "fps": 8 },
    "falar":   { "frames": [6, 7],       "fps": 6 }
  }
}
```

- `anchor`: ponto do "pé" (onde o ator está posicionado na cena). Padrão: base central.
- Sprites desenhados olhando para a **direita**; esquerda = espelho automático.
- Sem `animations`, o sprite inteiro vira a animação `parado`. Specs antigas seguem válidas.

### Cenário

Um cenário é uma lista de **camadas** (cada uma uma arte `.json`/`.py`/`.png`),
de trás para a frente, com fator de parallax:

```json
{
  "name": "patio",
  "size": [640, 180],
  "camadas": [
    { "arte": "cenarios/patio/ceu",      "parallax": 0.1 },
    { "arte": "cenarios/patio/montanhas", "parallax": 0.4 },
    { "arte": "cenarios/patio/chao",      "parallax": 1.0 },
    { "arte": "cenarios/patio/frente",    "parallax": 1.3, "frente": true }
  ]
}
```

`frente: true` desenha a camada **sobre** os atores (folhagem, colunas).
Tilemap fica para depois.

## Roteiro de cena

```json
{
  "name": "chegada-academia",
  "resolucao": [320, 180],
  "escala": 6,
  "fps": 12,
  "paleta": "endesga32",
  "cenario": "cenarios/patio",
  "atores": {
    "ana":   { "sprite": "personagens/ana",   "pos": [40, 150], "olhar": "direita" },
    "mestre": { "sprite": "personagens/mestre", "pos": [260, 150], "olhar": "esquerda" }
  },
  "planos": [
    {
      "dur": 3,
      "camera": { "de": [0, 0], "para": [120, 0], "curva": "suave" },
      "efeitos": [{ "tipo": "neblina", "intensidade": 0.4 }]
    },
    {
      "dur": 4,
      "acoes": [{ "ator": "ana", "anim": "andar", "ate": [190, 150] }]
    },
    {
      "dur": 5,
      "dialogo": { "ator": "mestre", "retrato": "retratos/mestre", "texto": "Atrasada no primeiro dia." }
    }
  ],
  "transicoes": { "entrada": "fade", "saida": "fade" },
  "audio": null
}
```

### Semântica

- **Tempo** em segundos; o motor converte em quadros. Cada plano começa quando o anterior termina.
- **Ações** (`acoes`) num plano rodam em paralelo; `inicio` opcional (s, relativo ao plano).
  - `andar`/`mover`: `ate` [x, y], velocidade padrão 40 px/s (ou `dur`), anima com `anim`.
  - `anim`: troca a animação sem mover. `olhar`: vira. `aparecer`/`sumir`: com `fade` opcional.
  - Ao fim, o ator fica onde parou (estado persiste entre planos).
- **Câmera**: `de` → `para` (canto superior esquerdo, em px do cenário), `curva`
  `linear | suave`; `zoom` 1 ou 2 (inteiro); `tremor` [amplitude px, duração s]; `seguir: "<ator>"`.
- **Diálogo**: caixa na parte de baixo (fonte bitmap embutida, acentos do português),
  retrato opcional, texto letra a letra (velocidade em letras/s), ator em `falar`
  enquanto o texto corre. Plano com diálogo sem `dur` dura o texto + 1,5 s.
- **Efeitos** (por plano ou cena): `chuva`, `neblina`, `particulas` (folhas, brasas, poeira),
  `tinta` (dia/noite/sépia, multiplicação por cor), `luz` (tocha piscando: raio + cor),
  `flash`, `vinheta`. Todos desenhados na resolução lógica, em pixel.
- **Transições** entre planos: `corte` (padrão), `fade`, `fade-branco`, `cortina`.
- **Cortes de cenário**: um plano pode trocar `cenario` (vira nova locação).

## Arquitetura

```
pixelforge/
  cena/
    __init__.py
    roteiro.py     lê e valida o roteiro; erros apontam plano/ação
    biblioteca.py  resolve caminhos de artes (art/), cache de sprites e cenários
    linha.py       linha do tempo: planos → quadros; estado dos atores e da câmera por quadro
    compor.py      compõe um quadro: camadas com parallax, atores (ordem por y), frente, efeitos, UI
    dialogo.py     caixa, quebra de linha, fonte bitmap, efeito máquina de escrever
    efeitos.py     chuva, neblina, partículas (semente fixa → determinístico), tinta, luz
    fonte.py       fonte bitmap 5×7 / 6×9 com acentos
    video.py       GIF / WebP (Pillow); MP4 via imageio-ffmpeg se instalado
  cli.py           novos comandos: cena, quadro, storyboard
```

- **Determinístico**: mesmo roteiro → mesmo vídeo (partículas com semente).
- Composição em numpy RGBA na resolução lógica; escala só na exportação.

## Linha de comando

```bash
python -m pixelforge cena art/cenas/chegada.json              # storyboard + GIF (+ MP4 com [video])
python -m pixelforge quadro art/cenas/chegada.json --t 7.5    # um quadro no instante t (revisão)
python -m pixelforge storyboard art/cenas/chegada.json        # folha com 1 quadro a cada N s, com tempo
```

Saída em `out/<nome>/`: `<nome>_storyboard.png`, `<nome>.gif`, `<nome>.mp4`.
`--out` como nos demais comandos.

## Fluxo do Claude (skill)

Nova seção (ou skill `pixel-cena`) com o ciclo:

1. Entrevista curta: o momento, duração (padrão 15–30 s), clima, quem está.
2. Inventário: quais sprites/cenários existem em `art/`; criar o que falta pela skill `pixel-art`
   (uma arte por vez, mostrando).
3. Roteiro em `art/cenas/<nome>.json`.
4. `storyboard` → ler a imagem → conferir enquadramento, posições, legibilidade do texto.
5. Ajustar e repetir (máx. 3 voltas); depois `cena` e entregar.

## Etapas de implementação

1. **Cena parada + câmera**: roteiro, cenário com parallax, câmera, `quadro`, `storyboard`, GIF.
2. **Atores**: `animations`, `anchor`, espelho, `andar`/`anim`/`olhar`, ordem por y.
3. **Diálogo**: fonte bitmap com acentos, caixa, retrato, máquina de escrever.
4. **Efeitos e transições**.
5. **MP4** (extra `[video]`) e áudio (trilha/efeitos sobrepostos via FFmpeg).
6. **Skill** do Claude para cenas.

Cada etapa com testes (`unittest`): validação de roteiro, contagem de quadros,
posições em instantes conhecidos, quadro de referência pixel a pixel.

## Fora de escopo (por ora)

Tilemaps, colisão, iluminação dinâmica por pixel, rotação/escala livre de sprite,
geração de música, edição interativa.

## Decisões do autor (2026-10-21)

1. **MP4 aceito**: extra `[video]` com `imageio-ffmpeg` (instalado no `.venv`).
2. **Resolução escolhível**: o motor é genérico (serve a outros projetos).
   `pixelforge.toml` ganha `[cena]` com padrão e presets nomeados
   (`gba` 240×160, `hd` 320×180, `hd2` 480×270, `hd3` 640×360, `snes` 256×224);
   o roteiro aceita nome de preset, `"LxA"` ou `[L, A]`; a CLI aceita `--resolucao`.
3. **Som por IA**, além de efeitos procedurais: ver `ROADMAP.md` (seção Som) —
   chiptune procedural (numpy), trilha com ACE-Step 1.5, voz com Kokoro (português),
   ambientes com Stable Audio Open. Dependências pesadas no extra `[audio-ia]`,
   instaladas quando a etapa 5 começar.

Nomes de código seguem o repositório (inglês: `pixelforge/scene/`); chaves do
roteiro em português, como neste documento.

## Etapa 5 e acabamento (implementado)

### Som: bloco `audio`

Usa a API de mixagem de `pixelforge/audio/mix.py` (`Clip`, `mix_clips`, `load_source`,
`mux_video`); o motor de cena só monta os clipes a partir da linha do tempo
(`pixelforge/scene/sound.py`).

```json
"audio": {
  "trilha":   { "musica": "tema.json", "volume": 0.55 },
  "ambiente": [{ "efeito": "grilos.json" }, { "descricao": "night forest, crickets" }],
  "eventos":  [{ "inicio": 3.0, "efeito": "porta", "pan": -0.5 },
               { "plano": 4, "inicio": 0.5, "arquivo": "sons/trovao.wav" }],
  "falas":    { "modo": "auto", "voz": "pf_dora", "narrador": "pm_santa", "bip": 0.3 },
  "abafar": 0.35,
  "volume": 1.0
}
```

- **Fonte** de cada som (exatamente uma): `arquivo` (WAV), `efeito` (preset, `.json` ou objeto
  de camadas), `musica` (`.json` do sequenciador), `texto` (voz por IA) ou `descricao` (IA:
  ACE-Step na `trilha`, AudioLDM2 nos demais). Ajustes: `inicio` (ou `t`), `volume`,
  `fade_in`, `fade_out`, `pan` (-1…1), `loop`, `semente`, `variar`, `voz`, `velocidade`,
  `duracao`. Um texto sozinho (`"porta"`) vale `{"efeito": "porta"}`.
- `trilha` e `ambiente` repetem (loop) pela cena inteira; sem `fade_in`/`fade_out`, seguem
  a duração das transições de entrada/saída da cena.
- Efeitos em instantes: `audio.eventos` (tempo absoluto, ou relativo a `plano`), `sons` no
  plano (relativo ao plano) e `som` na ação (no início da ação; `repetir` s = passos enquanto
  o ator anda, com semente diferente a cada passo).
- **Falas** (`falas.modo`): `auto` (padrão) usa voz por IA (Kokoro) se o extra `[audio-ia]`
  estiver instalado; sem ele, vira **bipes de máquina de escrever** sincronizados com as letras
  (um a cada 2, tom do ator em `tom` Hz) e avisa. `bip` força os bipes; `nenhum` cala as falas.
  Voz: `voz` da fala > `voz` do ator > `falas.voz`. Fala gravada: `"arquivo"` na fala (vale em
  qualquer modo). Legendas com `"narrar": true` usam `narrador`. A trilha cai para `abafar`
  enquanto há voz. Aviso se a voz durar mais que a caixa de diálogo.
- Sem `[audio-ia]` nada quebra: o procedural toca, o resto é pulado com aviso. Saídas de IA
  ficam em cache em `out/<nome>/_som/` (mesma entrada → não gera de novo).
- `cena` grava `<nome>.wav` e o MP4 com o som (AAC). `--sem-som` ignora o bloco;
  `--sem-ia` força só o procedural. GIF/WebP continuam mudos.

### Títulos e legendas

- Plano com `"titulo": {"texto": "Capítulo 7 — A vila", "subtitulo": "...", "fundo": "#000000",
  "cor", "posicao": "centro" | "baixo", "inicio", "dur", "fade": 0.5}` (ou só o texto).
  Com `fundo` (padrão preto) é cartela opaca; `"fundo": null` escreve sobre a cena, com sombra.
  Fonte bitmap dobrada, subtítulo com fio laranja; o texto entra/sai em degraus de dithering.
  Plano só com título pode omitir `dur` (3,5 s).
- `"legenda"` no plano: texto, objeto ou lista `{"texto", "inicio", "dur", "posicao", "cor",
  "narrar", "voz"}`. Sem `inicio`, uma depois da outra; sem `dur`, 1 s + 15 letras/s (mín. 1,5 s).
  Centralizada com contorno de 1 px; foge da caixa de diálogo se ela estiver no mesmo lado.

### Câmera "cinema"

- `"seguir": "<ator>", "folga": 40`: a câmera só anda quando o ator sai da faixa central ±folga.
- `"enquadrar": "geral" | "medio" | "close", "em": "<ator>"` (calcula a posição no início do
  plano; com `seguir`, acompanha na horizontal). Zoom padrão 1, 2 e 3 (`zoom` explícito vence);
  geral: pé a 4/5 da altura; médio: ator centrado; close: cabeça no centro.
- Falas com `"close": "retrato"` (retrato ampliado em escala inteira sobre a cena escurecida
  em dithering) ou `"close": "ator"` (zoom 3 no rosto de quem fala, acima/abaixo da caixa);
  ao fim da fala a câmera volta ao plano normal.

### Testes golden

`tests/golden/golden.json` lista roteiros e instantes; os quadros (resolução lógica) ficam em
`tests/golden/<cena>/t<s>.png` e `tests/test_scene_cinema.py` compara pixel a pixel. A cena de
referência (`tests/golden/cena/`) usa a Lia gerada pelo motor de arte, congelada em JSON.

```bash
python -m pixelforge golden                 # compara; diferenças e diffs em out/golden/
python -m pixelforge golden --regravar      # aceita uma mudança visual intencional
```
