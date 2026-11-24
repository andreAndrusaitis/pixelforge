# PixelForge Vídeo por IA — Design

Data: 2026-10-22 · Status: implementado (`pixelforge/ai_video/`, `pixelforge/scene/ai.py`)

## Objetivo

Criar animação e vídeo **por IA local, de graça**, na máquina do autor (RTX 4060 Laptop
8 GB, 16 GB de RAM), sem perder a cara de pixel art: a IA dá o movimento; o PixelForge
devolve pixel art estável, na paleta da cena ou do personagem.

```
quadro / sprite / camada (pixel art nativa)
   └─ ampliada (vizinho) ─► Wan 2.2 TI2V-5B (imagem + "movimento") ─► clipe 24 fps, liso
        └─ pixelização temporal ─► quadros nativos, paleta travada, 8–12 fps
             └─ nota técnica (estilo comparar) ─► < 85: outra semente (até 3)
                  └─ cena: compõe no plano / camada / ator ─► GIF / MP4
```

## Modelo (pesquisa de out/2026)

| Opção | Licença | Cabe em 8 GB / 16 GB RAM? | Escolha |
|---|---|---|---|
| **Wan 2.2 TI2V-5B** | Apache-2.0, sem login | sim, com transformer GGUF Q8 + UMT5 4 bits + offload | ✅ |
| LTX-2 / LTX-2.3 (19–22B, com áudio) | LTX open weights | só GGUF agressivo, 512², 12–16 quadros | não |
| LTX-Video 0.9.x 2B destilado | LTX open weights | sim, mas qualidade/coerência menores | alternativa futura |
| Wan 2.2 A14B | Apache-2.0 | não (≥ 16 GB VRAM mesmo em GGUF Q4) | não |

Arranjo de memória (`pixelforge/ai_video/wan.py`):

- **transformer** em GGUF Q8_0 (`QuantStack/Wan2.2-TI2V-5B-GGUF`, 5,4 GB) em vez dos 20 GB fp32;
- **UMT5-XXL** (11,4 GB bf16) carregado em 4 bits NF4 com cálculo em bf16 (bitsandbytes) só para
  codificar a descrição e descarregado; os embeddings ficam em cache em disco (`models/video/embeds`).
  Medido: 50 s e 6,3 GB de pico na 1ª vez, 0,04 s do cache; cosseno 0,976 contra o 8 bits (que leva
  105 s, chega a 7,9 GB e passa por fp16, onde o T5 pode estourar);
- **VAE** do Wan 2.2 em float32; `enable_model_cpu_offload` troca transformer e VAE na GPU.
- Pesos em `~/.cache/pixelforge/models/video/` (`PIXELFORGE_MODELS` muda a raiz) — **fora do
  repositório**, que fica no OneDrive (sincronizar 20 GB de pesos seria ruim); a pasta `models/`
  do repositório continua ignorada pelo git. Nenhum dos repositórios exige aceitar licença ou
  login; `video-ia baixar` recusa e avisa se algum passar a exigir.
- Resolução de geração com a área de ~832×480, proporção da imagem, múltiplos de 32;
  24 passos, CFG 5, 24 fps, quadros em 4k+1.

## Pixelização temporal (`pixelize.py`)

1. **fps baixo**: quadros escolhidos do clipe a 24 fps para 8–12 fps.
2. **grade fixa**: recorte central na proporção do alvo + média de área (BOX) até a resolução
   nativa — cada pixel nativo é sempre a mesma célula do clipe.
3. **mediana temporal** (3 quadros) antes de quantizar: ruído de um quadro só some.
4. **paleta travada**: a da imagem de partida (cores opacas únicas; k-means se forem > 48),
   mais as artes em `paleta`; igual em todos os quadros, distância em Oklab.
5. **histerese de cor**: o pixel só troca de cor se a nova for melhor que a atual por 0,035 em
   Oklab — mata a cintilação entre duas cores vizinhas; o 1º quadro parte das cores originais.
6. **órfãos**: pixel sem vizinho 4-conexo igual vira a cor da maioria dos 8 vizinhos.
7. **só o que se move**: com o quadro original como base, um pixel só é repintado onde o clipe
   mudou (Oklab > 0,06) contra o 1º quadro do clipe **e** contra a média 3×3 do original;
   em todo o resto volta o pixel original — o dithering e os detalhes do artista sobrevivem,
   e onde a nuvem já passou o céu volta exatamente ao de antes.
8. **região** (`regiao`): fora dela, o quadro fica idêntico ao original.

Medido num clipe sintético "com cara de IA" (céu real do cap 01 ampliado, suavizado, nuvens
andando, ruído σ 4 e deriva de brilho por quadro; 49 quadros 896×448 → 16 quadros 720×360 a
8 fps, paleta de 11 cores): cintilação (pixels que mudam entre quadros) **12,96 % → 0,29 %**;
na faixa sem movimento **11,93 % → 0,00 %**; nenhuma cor fora da paleta; ~7 s de CPU.
9. **sprites**: fundo liso numa cor longe da paleta (verde, magenta…), recortado por distância
   Oklab com mediana temporal na máscara.

## Roteiro

`"ia"` no plano — `origem` `quadro` | `imagem` | `sprite` — ou numa camada do cenário (docs/manual.md,
seção "Animação por IA"). Campos: `movimento`, `dur` (≤ 5 s), `inicio`, `fps`, `regiao`,
`laco` (`segurar` | `vaivem` | `repetir`), `paleta`, `semente`. `cena`, `quadro` e
`storyboard` preparam os clipes antes de renderizar (`scene/ai.py:prepare`); o cache é por hash
de (imagem de partida, descrição, duração, semente, passos, tamanho, modelo), em
`out/<cena>/_ia/<hash>.npz` (clipe bruto; a pixelização é refeita, é rápida).

## Nota de estilo

`clips.make_clip` avalia 3 quadros do clipe pixelizado com `estilo comparar` (tipo `cena`,
`cenario` nas camadas, `personagem` nos sprites). Se a média for < 85 — ou < nota da imagem
original − 2, quando a própria arte de partida já está abaixo de 85 (a IA não deve ser
cobrada acima do que a cena já é) — gera de novo com a semente seguinte, até 3 vezes, e fica
com a de maior nota.

## Animação de sprite (`sprite.py`, `video-ia sprite`)

`parado`, `andar`, `falar` (ou outros, com descrição) a partir de um quadro do sprite: fundo
liso, Wan, pixelização no tamanho do sprite com a paleta dele e recorte do fundo. Grava
`<sprite>_ia.json` com os quadros antigos + novos, `animations` e o mesmo `anchor`.

## Prova: Véu, cap 01, o portão

`art/coletanea/veu/cenas/cap01-portao/cap01-portao-ia.json` (variante; o roteiro aprovado
não muda) + `cenario-ia.json`: céu com nuvens, poças tremulando (só a faixa das poças), e o
gesto de Seu Geraldo tirar o chapéu (plano 3, origem sprite, paleta + sprite sem chapéu).
Resultados e tempos: ver o fim deste documento.
