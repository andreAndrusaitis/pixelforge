---
name: pixel-som
description: Som para pixel art no PixelForge — efeitos chiptune procedurais (passo, pulo, moeda, magia, golpe, porta...), música chiptune por código, trilha/voz/ambiente por IA local (ACE-Step, Kokoro, AudioLDM2) e mixagem no MP4 de uma cena. Use para "põe som nessa cena", "efeito de porta", "trilha misteriosa", "narração/fala do personagem", "chuva de fundo", ou para ajustar volumes e tempos de um roteiro de áudio.
---

# Som (PixelForge)

Tudo sai em `out/som/` (WAV 16 bits). Núcleo (efeitos, música por código, mixagem) só
com numpy; IA local no extra `[audio-ia]` (voz, ambiente, trilha por descrição).
Referência: docs/manual.md, seção "Som"; exemplos em `docs/som/` (`tema_aventura.json`,
`roteiro_exemplo.json`).

## 1. Entrevista

Com `AskUserQuestion`, só o que faltar:

| Pergunta | Opções típicas |
|---|---|
| **O que soa** | efeitos pontuais · trilha · voz das falas · ambiente contínuo (chuva, floresta) |
| **Trilha** | chiptune por código (determinística, leve) · por IA (ACE-Step, ~2 min por 20 s) · nenhuma |
| **Voz** | sem voz (só texto na caixa) · Kokoro `pf_dora` (feminina) · `pm_alex` / `pm_santa` (masculinas) |
| **Clima** | tema (misterioso, aventura, calmo, tenso), bpm aproximado, instrumentos |

IA local exige o extra e baixa modelos no primeiro uso (vários GB): confirme com o
autor antes de rodar algo que vá baixar (veja docs/manual.md → "IA local").

## 2. Passos

1. **Tempos**: a partir do roteiro da cena, liste os instantes (s) de cada evento —
   passos durante `ate`, porta, falas (início de cada fala no diálogo). Use
   `python -m pixelforge storyboard <roteiro>` e o cabeçalho (duração, planos) para medir.
2. **Efeitos**:
   ```bash
   python -m pixelforge som efeito --lista
   python -m pixelforge som efeito pulo
   python -m pixelforge som efeito passo --variar 0.1 --semente 2 --nome passo_2
   python -m pixelforge som efeito art/sons/sino_grave.json --json   # parâmetros próprios
   ```
   Ajuste preset: `{"base": "porta", "camadas": [{"freq": 120}]}`.
3. **Música por código**: `docs/som/tema_aventura.json` como modelo (canais com notas em
   texto, `bpm`, `loop`; bateria com `k s h x`):
   `python -m pixelforge som musica art/sons/tema.json --loop`.
4. **IA** (com o extra): `som musica "mysterious theme, harpsichord and strings, 90 bpm" --duracao 30`,
   `som voz "Atrasada no primeiro dia." --voz pf_dora --nome fala_mestre`,
   `som ambiente "gentle rain on leaves, distant thunder" --duracao 10 --loop`.
   Prompts de música/ambiente em inglês.
5. **Roteiro de áudio** `art/sons/<cena>.audio.json` (formato de
   `docs/som/roteiro_exemplo.json`): `trilha` (loop, `volume`, `fade_in/out`), `eventos`
   (`t`, `efeito`|`arquivo`|`musica`, `volume`, `pan`), `falas` (abafam a trilha via
   `abafar`), `duracao`. Caminhos relativos à pasta do roteiro (em `art/sons/` o acervo o
   classifica como `som`; dentro de `art/cenas/` viraria `cena`).
6. **Mixar no vídeo**:
   ```bash
   python -m pixelforge som mix art/sons/<cena>.audio.json --video out/<cena>/<cena>.mp4
   python -m pixelforge som info out/som/*.wav
   ```
   Se o roteiro de cena já aceitar som (etapa 5 do motor), prefira declarar lá — confira
   no docs/manual.md antes; senão, use o `som mix`.

## 3. Ciclo gerar → ouvir/medir → ajustar

Você não ouve: **meça**. `som info` dá duração, pico e RMS. Critérios:

- pico ≤ -1 dBFS (sem clipping); falas ~-16 a -12 dBFS RMS, trilha 6–10 dB abaixo;
- duração do efeito casa com o gesto (passo < 0,15 s; porta 0,4–0,8 s);
- eventos alinhados aos quadros: confira o instante com `quadro --t`;
- peça ao autor para ouvir o WAV/MP4 e dizer o que mudar (uma versão por vez).

## 4. Pronto quando

- WAVs gerados e medidos; roteiro de áudio com tempos conferidos no storyboard;
- MP4 com som gerado (ou faixa `.wav` entregue, se não houver vídeo);
- autor ouviu e aprovou; caminhos informados.

## 5. Armadilhas

- Mesma entrada + mesma `--semente` = mesmo arquivo: para variar passos, mude a semente.
- Trilha sem `fade_out` corta seco no fim do vídeo.
- Vozes Kokoro em pt-BR soam melhor com frases curtas e pontuação explícita.
- Stable Audio Open é restrito (licença + login no Hugging Face): não aceite em nome do autor.
- Agente: o `sonoplasta` executa esta skill.
